#!/usr/bin/env python

"""
Description:
    Automate speedtests using FTP:
        - get ping times from FTP server
        - perform upload & download speed tests
        - retrieve transport device stats

Usage:
    linkCheck.py  <ftp_server_ip> <ftp_username> <ftp_password>
                  (no_modem | 350 | 750 | zyxel)
                  [<modem_ip> <modem_username> <modem_password>]
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

Author:
    Jeff Wright <jeff.wright@hughes.com>
"""

# VERSION
__version__ = "linkCheck.py version 0.9"


# GLOBAL EXCUTION VARS
num_pings = '2'
testfile = '1kb.test'
logfilename = 'modemtestreport.csv'
csv_header = 'Date-Time,Ping Min,Ping Avg,Ping Max,Ping Dev,Upload Speed(Bps),Download Speed(Bps),APN,Get Community String,Set Community String,Modem ID,Group,MDN,Carrier,IMEI,IMSI,RSSI,RSRP,RSRQ,SINR,Group,GPGGA,Service Type,Firmware1,Firmware2,RX Chann,TX Chann'
modem_stats_dict = {'activeapn': '',
                    'getcommunity': '', 
                    'setcommunity': '',
                    'modemid': '',
                    'mdn': '',
                    'carrid': '',
                    'imei': '',
                    'imsi': '',
                    'rssi': '',
                    'rsrp': '',
                    'rsrq': '',
                    'sinr': '',
                    'group': '',
                    'gpgga': '',
                    'servicetype': '',
                    'modemfw1': '',
                    'modemfw2': '',
                    'rxchannel': '',
                    'txchannel': ''}  # Needs to match regex dict below

# REGULAR EXPRESSIONS USED IN MATCHING
ping_regex = "rtt min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)"

# "int1: Active APN: VZWINTERNET"

modem_regex_dict = {'activeapn': 'Active APN:\s+\w+\"',
                    'getcommunity': '', 
                    'setcommunity': '',
                    'modemid': '',
                    'mdn': '',
                    'carrid': '',
                    'imei': '',
                    'imsi': '',
                    'rssi': '',
                    'rsrp': '',
                    'rsrq': '',
                    'sinr': '',
                    'group': '',
                    'gpgga': '',
                    'servicetype': '',
                    'modemfw1': '',
                    'modemfw2': '',
                    'rxchannel': '',
                    'txchannel': ''}
          
# IMPORTS
import sys, os, socket, re, subprocess, datetime, paramiko
from ftplib import FTP
from docopt import docopt


# MAIN EXECUTION SECTION
def main (arguments):

    #print "Arguments:\n", arguments

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
    if arguments['no_modem']:
        return
    else:
        getModemStats(arguments)
        print "Modem Stats Dictionary:\n", modem_stats_dict
        #logModemStats()


# PING FTP SERVER
def runPing(arguments):

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

    print "Uploading to FTP server..."

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
    
    return upload_rate


# WRITE UPLOAD RESULTS TO FILE
def logFtpUpload(data):

    print "Upload rate (bytes/sec): ", data
    print "Upload rate (bits/sec): ", data * 8

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
    
    return download_rate
    

# WRITE DOWNLOAD RESULTS TO FILE
def logFtpDownload(data):
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


# LOG INTO MODEM DEVICE AND RETRIEVE STATS
def getModemStats(arguments):

    # Login to the modem
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(arguments['<modem_ip>'], 22,
                    arguments['<modem_username>'],
                    arguments['<modem_password>'])
    except IOError as e:
        print "Cannot establish SSH connection to modem."
        raise e
    
    # If Cradlepoint, SSH into it and retrieve stats using "get"
    if arguments['350'] or arguments['750']:
        # Issue 'get' command to modem and close SSH session
        stdin, stdout, stderr = ssh.exec_command('get')
        modemStats = stdout.readlines() # generates a list
        ssh.close()
        modemStatsString = ''.join(modemStats) # convert list to string for regex

    # If Zyxel, SSH into it and retrieve stats using ??? <<TO DO>>
    elif arguments['zyxel']:
        modemStatsString = ''.join('')

    # Invalid modem type called internally
    else:
        print "Cannot SSH into invalid modem type. Terminating"
        raise SystemError

    # Parse the modem stats string and populate stats dictionary
    for key in modem_stats_dict:
        print "matching for expression:", modem_regex_dict[key]
        matcher = re.compile(modem_regex_dict[key])
        print "group:", matcher.search(modemStatsString).group()
        print "groups:", matcher.search(modemStatsString).groups()
        g = matcher.search(modemStatsString).group()

        if type(g) == None:
            print "Found nothing while processing", modem_regex_dict[key]
        else:
            print "Found match:", str(g), "while processing", key
        modem_stats_dict[key] = str(g)


# WRITE MODEM STATS INTO FILE
def logModemStats():
    try:
        with open('modemtestreport.csv', 'a') as file:
            for key in modem_stats_dict:
                try:
                    print "Writing:", modem_stats_dict[key] + ','
                    file.write(modem_stats_dict[key] + ',')
                except IOError as e:
                    print "Unable to write modem stats to file."
                    raise e
        file.close()

    except IOError as e:
        print "Unable to open file."
        raise e



if __name__ == '__main__':
    arguments = docopt(__doc__, version=__version__)
    main(arguments)
    sys.exit(0)
