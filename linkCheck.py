#!/usr/bin/env python
"""
Description:
    Automate speedtests using FTP:
        - ping
        - upload speed
        - download speed
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

VERSION = "0.1"

import sys, os, platform, traceback, time, re
from ftplib import FTP
from docopt import docopt

def main (arguments):
    #print(arguments)
    print "IP: " + arguments['<ftp_server_ip>']

    pingFTP(arguments)
    uploadFTP(arguments)
    downloadFTP(arguments)

def pingFTP(arguments):
    print "In function 'pingFTP'"
    num_iterations = '20'
    response = os.system("ping -c " + num_iterations + ' ' + arguments['<ftp_server_ip>'])

def uploadFTP(arguments):
    print "In function 'uploadFTP'"

def downloadFTP(arguments):
    print "In function 'downloadFTP'"

def logIt():
    print "In function 'logIt'"

def getStats():
    print "In function 'getStats'"

if __name__ == '__main__':
    try:
        arguments = docopt(__doc__, version=VERSION)
        main(arguments)
        sys.exit(0)
    except KeyboardInterrupt, e: # Ctrl-C
        raise e
    except SystemExit, e: # sys.exit()
        raise e
    except Exception, e:
        print 'ERROR, UNEXPECTED EXCEPTION'
        print str(e)
        traceback.print_exc()
        os._exit(1)
