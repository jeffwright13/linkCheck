#!/usr/bin/env python

"""
Description:
    Automate speedtests using FTP:
        - ping FTP server (latency)
        - upload & download speed
        - transport device stats

Usage:
    linkCheck.py <ftp_server_ip> <username> <password>
    linkCheck.py (-h | --help)
    linkCheck.py --version

Options:
    -h --help       Show this screen
    -v --version    Show version

Author:
    Jeff Wright <jeff.wright@hughes.com>
"""

# VERSION
__version__ = "0.6"


# GLOBAL EXCUTION VARS
num_pings = '2'
testfile = "1mb.test"
logfilename = 'modemtestreport.csv'
csv_header = "Time,Ping Min,Ping Avg,Ping Max,Ping Dev,Upload Speed(Bps),Download Speed(Bps),Modem ID,Group,MDN,Carrier,IMEI,RSSI,RSRP,RSRQ,SINR,Firmware"


# IMPORTS
import sys, os, socket, re, subprocess, datetime
from ftplib import FTP
from docopt import docopt


# MAIN DRIVER SECTION
def main (arguments):

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
    result = getModemStats(arguments)
    logModemStats(result)

# PING FTP SERVER
def runPing(arguments):

    print "Pinging FTP server..."
    try:
        ping = subprocess.Popen(["ping", "-c", num_pings,
                                 arguments['<ftp_server_ip>']],
                                 stdout = subprocess.PIPE,
                                 stderr = subprocess.PIPE)
        out, error = ping.communicate()
        matcher = re.compile("rtt min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)")
    except socket.error, e:
        print "Ping Error:", e
        raise e
    return matcher.search(out).groups()


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

    except IOError as e:
        print "Unable to open file."
        raise e

# UPLOAD TEST FILE TO FTP SERVER
def runFtpUpload(arguments):

    #session = FTP(arguments['<ftp_server_ip>'])
    #session.set_pasv(True)
    #response = session.login(arguments['<username>'], arguments['<password>'])
    #if not 'successful' in response:
    #    print "FTP login not successful."
    #    raise IOError
    #file = open(testfile, 'wb')
    #session.storbinary("STOR", testfile)
    #session.quit()
    
    print "Uploading to FTP server..."

    # Establish FTP session
    session = FTP(arguments['<ftp_server_ip>'])
    session.set_pasv(True)
    response = session.login(arguments['<username>'], arguments['<password>'])
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

    except IOError as e:
        print "Unable to open file."
        raise e

# DOWNLOAD TEST FILE FROM FTP SERVER
def runFtpDownload(arguments):
    print "Downloading from FTP server..."

    # Establish FTP session
    session = FTP(arguments['<ftp_server_ip>'])
    session.set_pasv(True)
    response = session.login(arguments['<username>'], arguments['<password>'])
    if not 'successful' in response:
        print "FTP login not successful."
        raise IOError

    # Get file, then terminate FTP session
    try:
        fileh = open(testfile, 'wb')
    except IOError as e:
        print "Cannot open local file to write to."
        session.quit()
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
    print "Download rate (bytes/sec): ", data
    print "Download rate (bits/sec): ", data * 8

    try:
        with open('modemtestreport.csv', 'a') as file:
            try:
                file.write(str(data) + ',')
            except IOError as e:
                print "Unable to write upload data to file."
                raise e

    except IOError as e:
        print "Unable to open file."
        raise e

# 
def getModemStats(arguments):
    pass

# 
def logModemStats(data):
    pass


if __name__ == '__main__':
    arguments = docopt(__doc__, version=__version__)
    main(arguments)
    sys.exit(0)
