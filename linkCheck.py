#!/usr/bin/env python
"""
Description:
    Automate speedtests using FTP:
        - ping FTP server (latency)
        - upload & download speed
        - transport device stats

Usage:
    linkCheck.py <ftp_server_ip>
    linkCheck.py (-h | --help)
    linkCheck.py --version

Options:
    -h --help       Show this screen
    -v --version    Show version
    -i --server_ip  IP address of FTP server
    -u --user       Username for FTP server
    -p --password   Password for FTP user

Author:
    Jeff Wright <jeff.wright@hughes.com>
"""

# VERSION
__version__ = "0.5"

# GLOBAL EXCUTION VARS
num_pings = '2'
logfilename = 'modemtestreport.csv'
csv_header = "Time,Ping Min,Ping Avg,Ping Max,Ping Dev,Upload Speed(KBps),Download Speed(KBps),Modem ID,Group,MDN,Carrier,IMEI,RSSI,RSRP,RSRQ,SINR,Firmware"

import sys, os, socket, traceback, re, subprocess, datetime
from ftplib import FTP
from docopt import docopt


def main (arguments):
    result = runIt(arguments)
    logIt (result)


def runIt(arguments):
    """
    Run following in order:
      - ping FTP server <num_pings> times, & write results to file
      - push upload to ftp server & write speed to file
      - fetch download from ftp server & write speed to file
      - get modem stats and write to file
    """

    # Ping FTP server
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


def logIt(data):
    
    print "  data: ", data, type(data)

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
                    print "Unable to write data to file."
                    raise e

    except IOError as e:
        print "Unable to open file."
        raise e


if __name__ == '__main__':
    arguments = docopt(__doc__, version=__version__)
    main(arguments)
    sys.exit(0)
