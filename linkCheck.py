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
__version__ = "linkCheck.py version 1.0.1"

          
# IMPORTS
import sys, os, socket, re, subprocess, time, datetime, paramiko, json
from ftplib import FTP
from docopt import docopt


# GLOBAL EXCUTION VARS
num_pings = '25'
testfile = '1mb.test'
logfilename = 'modemtestreport.csv'

csv_header = 'Date-Time,Ping Min,Ping Avg,Ping Max,Ping Dev,FTP Up Speed (bps),FTP Down Speed (bps),Device Hostname,CP_Carrier,CP_ServiceType,CP_SignalStrength,CP_RSRP,CP_RSRQ,CP_FW_Version,Zy_Status,Zy_Upstream_Rate,Zy_Downstream_Rate'

cp_modem_stats_dict =   {'HOMECARRID':  '',
                        'SERDIS':       '',
                        'SS':           '',
                        'RSRP':         '',
                        'RSRQ':         '',
                        'VER_PRETTY':   ''}

zy_modem_stats_dict =   {'STATUS':      '',
                        'UPSTREAM':     '',
                        'DOWNSTREAM':   '',
                        'VERSION':      ''}


# REGULAR EXPRESSIONS USED IN MATCHING
regex_ping = "rtt min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)"
regex_zyhost = ""

# MAIN EXECUTION SECTION
def main (arguments):

    if arguments['--debug']:
        print "Command line arguments:\n", arguments

    # Ping test
    result = runPing(arguments)
    logPing(result)

    # FTP Upload
    result = runFtpUpload(arguments)
    logFtpUpload(result)

    # FTP Download
    result = runFtpDownload(arguments)
    logFtpDownload(result)

    # Retrieve modem stats
    if arguments['no_modem']:
        return
    elif arguments['zyxel']:
        hostname = getZyStats(arguments)
        logHostname(hostname)
        logZyModemStats()
    elif arguments['350'] or arguments['750']:
        hostname = getCpStats(arguments)
        logHostname(hostname)
        logCpModemStats()
    else:
        print "Invalid modem type. Terminating."
        raise SystemError

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
        matcher = re.compile(regex_ping)
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
        with open(logfilename, 'a') as file:
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

    return int(upload_rate * 8)


# WRITE UPLOAD RESULTS TO FILE
def logFtpUpload(data):

    if arguments['--debug']:
        print "Upload rate (bytes/sec): ", data / 8
        print "Upload rate (bits/sec): ", data

    try:
        with open(logfilename, 'a') as file:
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
    
    return int(download_rate * 8)
    

# WRITE DOWNLOAD RESULTS TO FILE
def logFtpDownload(data):

    if arguments['--debug']:
        print "Download rate (bytes/sec): ", data / 8
        print "Download rate (bits/sec): ", data

    try:
        with open(logfilename, 'a') as file:
            try:
                file.write(str(data) + ',')
            except IOError as e:
                print "Unable to write download data to file."
                raise e
        file.close()

    except IOError as e:
        print "Unable to open file."
        raise e


# LOG INTO CRADLEPOINT AND RETRIEVE INFO
def getCpStats(arguments):

    # CRADLEPOINT:
    # SSH in and navigate to /status/wan/devices, then enumerate wan interfaces
    # We need to find which one is active in order to retrieve stats
    if arguments['--debug']:
        print "SSH'ing into Cradlepoint and retrieving stats..."

    try:
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
        for key in cp_modem_stats_dict:
            cp_modem_stats_dict[key] = parsed_json['devices'][wan_device]['diagnostics'][key]
            
        # Populate the hostname
        hostname = parsed_json['devices'][wan_device]['config']['hostname']

        ssh.close()

    except IOError as e:
        print "Cannot establish SSH connection to modem."
        raise e

    return hostname


# LOG INTO ZYXEL AND RETRIEVE INFO
def getZyStats(arguments):

    # ZYXEL:
    # SSH in and retrieve hostname and SW version, then line stats info
    if arguments['--debug']:
        print "SSH'ing into Zyxel and retrieving stats..."

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(arguments['<modem_ip>'], 22,
                    arguments['<modem_username>'],
                    arguments['<modem_password>'],
                    timeout = 20)
        try:
            stdin, stdout, stderr = ssh.exec_command('?')
        except Exception as e:
            print "SSH Exception executing command."
            raise e
        
        time.sleep(5)
        ssh.close()

        # make it a list, then a string
        modemStats = stdout.readlines()
        modemStatsString = str(modemStats[0]).strip(' > ')

    except IOError as e:
        print "Cannot establish SSH connection to modem."
        raise e

    return modemStatsString


# WRITE HOSTNAME INTO FILE
def logHostname(hostname):

    if arguments['--debug']:
        print "Writing hostname to CSV:", hostname

    try:
        with open(logfilename, 'a') as file:
            file.write(hostname + ',')

    except IOError as e:
        print "Unable to open file."
        raise e

# WRITE CRADLEPOINT MODEM STATS INTO FILE
def logCpModemStats():

    if arguments['--debug']:
        print "Cradlepoint stats dictionary to write to CSV:", cp_modem_stats_dict

    try:
        with open(logfilename, 'a') as file:
            file.write(cp_modem_stats_dict['HOMECARRID'] + ',')
            file.write(cp_modem_stats_dict['SERDIS'] + ',')
            file.write(cp_modem_stats_dict['SS'] + ',')
            file.write(cp_modem_stats_dict['RSRP'] + ',')
            file.write(cp_modem_stats_dict['RSRQ'] + ',')
            file.write(cp_modem_stats_dict['VER_PRETTY'] + ',')

    except IOError as e:
        print "Unable to open file."
        raise e


# WRITE ZYXEL MODEM STATS INTO FILE
def logZyModemStats():

    if arguments['--debug']:
        print "Zyxel stats dictionary to write to CSV:", zy_modem_stats_dict

    try:
        with open(logfilename, 'a') as file:
            # Write blanks in Cradlepoint stat columns
            for k in range(len(cp_modem_stats_dict)):
                file.write(',')
            file.write(zy_modem_stats_dict['STATUS'] + ',')
            file.write(zy_modem_stats_dict['UPSTREAM'] + ',')
            file.write(zy_modem_stats_dict['DOWNSTREAM'] + ',')
            file.write(zy_modem_stats_dict['VERSION'] + ',')
    except IOError as e:
        print "Unable to open file."
        raise e


# Standard Python wrapper for module
if __name__ == '__main__':
    arguments = docopt(__doc__, version=__version__)
    main(arguments)
    sys.exit(0)
