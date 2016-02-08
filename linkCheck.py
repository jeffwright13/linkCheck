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
    --version       Show version
    -i --server_ip  IP address of FTP server
    -u --user       Username for FTP server
    -p --password   Password for FTP user

Author:
    Jeff Wright <jeff.wright@hughes.com>

To Do:
    - Add transport device support for 350LPE, 750B, Zyxel
"""

import sys, os, traceback, time, re
from ftplib import FTP
from docopt import docopt

def main ():
    global options, args
    pingFTP()
    uploadFTP()
    downloadFTP()

def pingFTP():
    print "In function 'pingFTP'"

def uploadFTP():
    print "In function 'uploadFTP'"

def downloadFTP():
    print "In function 'downloadFTP'"

def logIt():
    print "In function 'logIt'"

def getStats():
    print "In function 'getStats'"

if __name__ == '__main__':
    try:
        arguments = docopt(__doc__, version='linkCheck.py 0.1')
        print(arguments)
        main()
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
