#!/usr/bin/env python

"""
Description:
    Automate speedtests using FTP:
        - get ping times from FTP server
        - perform upload & download speed tests
        - retrieve transport device stats
          (currently supported: cradlepoint 350 & 750; zyxel)

Usage:
    linkCheck.py  <ftp_server_ip> <ftp_username> <ftp_password>
                  (no_modem | 350 | 750 | zyxel)
                  [<modem_ip> <modem_username> <modem_password>]
                  [-d | --debug]
    linkCheck.py  (-h | --help)
    linkCheck.py  (-v | --version)

Arguments:
    ftp_server_ip   IPv4 address (in DDN) of FTP server
    ftp_username    Username for FTP server
    ftp_password    Password for FTP server
    modem_type      Optional; valid types are "no_modem", "350", "750", "zyxel"
    modem_ip        IPv4 address (in DDN) of modem  \  Required if modem
    modem_username  Username for modem              |  type is specified
    modem_password  Password for modem              /  as 350, 750 or zyxel

Options:
    -h --help       Show this screen
    -v --version    Show version
    -d --debug      Enable debug during execution (verbose mode)

Author:
    Jeff Wright <jeff.wright@hughes.com>
"""

# VERSION
__version__ = "linkCheck.py version 0.99"

          
# IMPORTS
import sys, os, socket, re, subprocess, datetime, paramiko, json
from ftplib import FTP
from docopt import docopt


# GLOBAL EXCUTION VARS
num_pings = '5'
testfile = '1mb.test'
logfilename = 'modemtestreport.csv'
csv_header = 'Date-Time,Ping Min,Ping Avg,Ping Max,Ping Dev,Upload Speed(bps),Download Speed(bps),Hostname,Carrier,ServiceType,SignalStrength,RSRP,RSRQ,FW_Version'
modem_stats_dict = {'HOMECARRID':   '',
                    'SERDIS':       '',
                    'SS':           '',
                    'RSRP':         '',
                    'RSRQ':         '',
                    'VER_PRETTY':   ''}


# REGULAR EXPRESSIONS USED IN MATCHING
ping_regex = "rtt min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)"


# MAIN EXECUTION SECTION
def main (arguments):

    if arguments['--debug']:
        print "Command line arguments:", arguments

    # Ping test
    result = runPing(arguments)
    logPing(result)

    # FTP Upload
    result = runFtpUpload(arguments)
    logFtpUpload(result)

    # FTP Download
    result = runFtpDownload(arguments)
    logFtpDownload(result)

    # Modem stats
    if arguments['no_modem'] or arguments['zyxel']:
        return
    else:
        hostname = getModemStats(arguments)
        logHostname(hostname)
        logModemStats()


# PING FTP SERVER
def runPing(arguments):

    if arguments['--debug']:
        print "Pinging FTP server..."
    try:
        ping = subprocess.Popen(["ping", "-c", num_pings,
                                 arguments['<ftp_server_ip>']],
                                 stdout = subprocess.PIPE,
                                 stderr = subprocess.PIPE)
        out, error = ping.communicate()
        matcher = re.compile(ping_regex)
    except socket.error, e:
        print "Ping Error:", e
        raise e
    
    try:
        g = matcher.search(out).groups()
    except:
        print "No FTP connectivity? Bailing out."
        raise RuntimeError

    return g


# WRITE PING RESULTS TO FILE
def logPing(data):

    try:
        with open('modemtestreport.csv', 'a') as file:
            # If file is size zero, write header into it
            if os.stat(logfilename).st_size == 0:
                file.write(csv_header)

            # Add date/timestamp
            now = datetime.datetime.now()
            try:
                file.write('\n' + str(now) + ',')
            except IOError as e:
                print "Unable to write date-time to file."
                raise e

            # Add ping results
            for item in data:
                try:
                    file.write(item + ',')
                except IOError as e:
                    print "Unable to write ping data to file."
                    raise e
        file.close()

    except IOError as e:
        print "Unable to open file."
        raise e


# UPLOAD TEST FILE TO FTP SERVER
def runFtpUpload(arguments):

    if arguments['--debug']:
        print "Uploading file", testfile, "to FTP server..."

    # Establish FTP session
    session = FTP(arguments['<ftp_server_ip>'])
    session.set_pasv(True)
    response = session.login(arguments['<ftp_username>'], arguments['<ftp_password>'])
    if not 'successful' in response:
        print "FTP login not successful."
        raise IOError

    # Put file, then terminate FTP session
    try:
        fileh = open(testfile, "rb")
    except IOError as e:
        print "Cannot open local file for upload."
        raise e
        session.quit()
    start_time = datetime.datetime.now()
    session.storbinary('STOR ' + testfile, fileh)
    end_time = datetime.datetime.now()
    fileh.close()
    session.quit()
    
    # Calculate upload rate
    delta = end_time - start_time # timedelta object
    elapsed = delta.total_seconds()
    statinfo = os.stat(testfile)
    size = statinfo.st_size
    upload_rate = size / elapsed
    
    return upload_rate * 8


# WRITE UPLOAD RESULTS TO FILE
def logFtpUpload(data):

    if arguments['--debug']:
        print "Upload rate (bytes/sec): ", data / 8
        print "Upload rate (bits/sec): ", data

    try:
        with open('modemtestreport.csv', 'a') as file:
            try:
                file.write(str(data) + ',')
            except IOError as e:
                print "Unable to write upload data to file."
                raise e
        file.close()

    except IOError as e:
        print "Unable to open file."
        raise e


# DOWNLOAD TEST FILE FROM FTP SERVER
def runFtpDownload(arguments):

    if arguments['--debug']:
        print "Downloading from FTP server..."

    # Establish FTP session
    session = FTP(arguments['<ftp_server_ip>'])
    session.set_pasv(True)
    response = session.login(arguments['<ftp_username>'], arguments['<ftp_password>'])
    if not 'successful' in response:
        print "FTP login not successful."
        raise IOError

    # Get file, then terminate FTP session
    try:
        fileh = open(testfile, 'wb')
    except IOError as e:
        print "Cannot open local file to write to."
        session.quit()
        raise e
    start_time = datetime.datetime.now()
    session.retrbinary('RETR ' + testfile, fileh.write)
    end_time = datetime.datetime.now()
    fileh.close()
    session.quit()
    
    # Calculate download rate
    delta = end_time - start_time # timedelta object
    elapsed = delta.total_seconds()
    statinfo = os.stat(testfile)
    size = statinfo.st_size
    download_rate = size / elapsed
    
    return download_rate * 8
    

# WRITE DOWNLOAD RESULTS TO FILE

def logFtpDownload(data):

    if arguments['--debug']:
        print "Download rate (bytes/sec): ", data / 8
        print "Download rate (bits/sec): ", data

    try:
        with open('modemtestreport.csv', 'a') as file:
            try:
                file.write(str(data) + ',')
            except IOError as e:
                print "Unable to write download data to file."
                raise e
        file.close()

    except IOError as e:
        print "Unable to open file."
        raise e


# LOG INTO MODEM DEVICE AND RETRIEVE INFO
def getModemStats(arguments):

    if arguments['--debug']:
        print "SSH'ing into modem and retrieving stats..."

    # CRADLEPOINT:
    # SSH in and navigate to /status/wan/devices, then enumerate wan interfaces
    # We need to find which one is active in order to retrieve stats
    if arguments['350'] or arguments['750']:
        try:
            # paramiko.util.log_to_file("paramiko.log")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(arguments['<modem_ip>'], 22,
                        arguments['<modem_username>'],
                        arguments['<modem_password>'],
                        timeout = 1200)
       
            stdin, stdout, stderr = ssh.exec_command('get status/wan')

            
            # make it a list, then a string
            modemStats = stdout.readlines()
            modemStatsString = str(''.join(modemStats)).lstrip()[1:]

            # Parse the string into a nested dictionary using JSON module
            parsed_json = json.loads(modemStatsString)

            # Determine the WAN device that is currently connected
            for device in parsed_json['devices']:
                if parsed_json['devices'][device]['status']['connection_state'] == "connected":
                    wan_device = device

            # Populate the modem stats dictionary
            for key in modem_stats_dict:
                modem_stats_dict[key] = parsed_json['devices'][wan_device]['diagnostics'][key]
                
            # Populate the hostname
            hostname = parsed_json['devices'][wan_device]['config']['hostname']

            ssh.close()

        except IOError as e:
            print "Cannot establish SSH connection to modem."
            raise e

    # Invalid modem type called internally
    else:
        print "Cannot SSH into modem type. Terminating."
        raise SystemError

    return hostname

# WRITE MODEM STATS INTO FILE
def logHostname(hostname):

    if arguments['--debug']:
        print "Writing hostname to CSV:", hostname

    try:
        with open('modemtestreport.csv', 'a') as file:
            file.write(hostname + ',')

    except IOError as e:
        print "Unable to open file."
        raise e

# WRITE MODEM STATS INTO FILE
def logModemStats():

    if arguments['--debug']:
        print "Modem stats dictionary to write to CSV:", modem_stats_dict

    try:
        with open('modemtestreport.csv', 'a') as file:
            file.write(modem_stats_dict['HOMECARRID'] + ',')
            file.write(modem_stats_dict['SERDIS'] + ',')
            file.write(modem_stats_dict['SS'] + ',')
            file.write(modem_stats_dict['RSRP'] + ',')
            file.write(modem_stats_dict['RSRQ'] + ',')
            file.write(modem_stats_dict['VER_PRETTY'] + ',')

    except IOError as e:
        print "Unable to open file."
        raise e


# Standard Python wrapper for module
if __name__ == '__main__':
    arguments = docopt(__doc__, version=__version__)
    main(arguments)
    sys.exit(0)
