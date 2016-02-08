#!/usr/bin/env python
"""
SYNOPSIS

    TODO linkCheck [-h,--help] [-v,--verbose] [--version]

DESCRIPTION

    Script to automate speedtests using FTP:
        - ping
        - upload speed
        - download speed
        - transport device stats

AUTHOR

    Jeff Wright <jeff.wright@hughes.com>

LICENSE

    This script is in the public domain, free from copyrights or restrictions.

VERSION

    $Id$

TO DO
    Add in transport device support for CP 350LPE, 750B, Zyxel

"""

import sys, os, traceback, docopt, time, re
from ftplib import FTP

def main ():
    global options, args
    pingFTP()
    uploadFTP()
    downloadFTP()

def pingFTP():
    pass

def uploadFTP():
    pass

def downloadFTP():
    pass

if __name__ == '__main__':
    try:
        start_time = time.time()
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
