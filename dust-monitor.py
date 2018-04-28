#!/usr/bin/env python3
# file: dust-monitor.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Copyright © 2018 R.F. Smith <rsmith@xs4all.nl>.
# SPDX-License-Identifier: MIT
# Created: 2018-04-11T18:52:43 +0200
# Last modified: 2018-04-28T10:40:00+0200
"""
Monitoring program for the plantower PMS5003 air monitoring sensor.
The sensor is connected to the computer via an FT232H, used as a serial to
USB converter.

Connect the 5V from the FT232H to VCC on the PMS5003. Conncect GND to GND.
Connect D0 to RXD and D1 to TXD. This program does not use the SET or RST pins.

This version does not use the native ftdi driver, but the userspace pyftdi driver.
The native driver needs to be unloaded for this progam to be used. The user
running this program will need read and write access to the USB device used.

This runs the sensor in passive mode. Note that for passive mode,
both TX and RX must be connected! It logs the data to a file.
"""

from datetime import datetime
from enum import Enum
import argparse
import struct
import sys
import time
from serial import SerialException
import pyftdi.serialext

__version__ = '1.1'


# See Appendix II (page 15) of the (annotated) PMS5003 manual.
class Cmd(Enum):
    PASSIVE_READ = b'\x42\x4d\xe2\x00\x00\x01\x71'
    PASSIVE_MODE = b'\x42\x4d\xe1\x00\x00\x01\x70'
    ACTIVE_MODE = b'\x42\x4d\xe1\x00\x01\x01\x71'
    SLEEP = b'\x42\x4d\xe4\x00\x00\x01\x73'
    WAKEUP = b'\x42\x4d\xe4\x00\x01\x01\x74'


def main(argv):
    """
    Entry point for dust-monitor.py

    Arguments:
        argv: command line arguments
    """
    now = datetime.utcnow().strftime('%FT%TZ')
    args = process_arguments(argv)

    # Open the files
    ft232h = pyftdi.serialext.serial_for_url(args.port, baudrate=9600, timeout=1)
    datafile = open(args.path.format(now), 'w')

    # Set the sensor to passive mode. See page 15 of the (annotated) manual.
    ft232h.write(Cmd.PASSIVE_MODE)
    # Drop all exesting active mode data.
    ft232h.flushInput()

    # Write datafile header.
    datafile.write(
        '# PMS5003 data. (passive mode)\n# Started monitoring at {}.\n'.format(
            now))
    datafile.write('# Per line, the data items are:\n')
    datafile.write('# * UTC date and time in ISO8601 format\n')
    datafile.write('# * PM 1.0 in μg/m³\n')
    datafile.write('# * PM 2.5 in μg/m³\n')
    datafile.write('# * PM 10 in μg/m³\n')
    datafile.write('# * number of particles >0.3 μm / 0.1 dm³ of air\n')
    datafile.write('# * number of particles >0.5 μm / 0.1 dm³ of air\n')
    datafile.write('# * number of particles >1.0 μm / 0.1 dm³ of air\n')
    datafile.write('# * number of particles >2.5 μm / 0.1 dm³ of air\n')
    datafile.write('# * number of particles >5 μm / 0.1 dm³ of air\n')
    datafile.write('# * number of particles >10 μm / 0.1 dm³ of air\n')
    datafile.flush()

    # Read and write the data.
    try:
        while True:
            # Request data
            ft232h.write(Cmd.PASSIVE_READ)
            # Read data
            data = ft232h.read(32)
            now = datetime.utcnow().strftime('%FT%TZ ')
            if len(data) != 32 and not data.startswith(b'BM'):
                datafile.write('# ' + now + 'read error\n')
                datafile.flush()
                continue
            try:
                numbers = struct.unpack('>HHHHHHHHHHHHHHHH', data)
            except struct.error:
                datafile.write('# ' + now + 'unpack error\n')
                datafile.flush()
                continue
            # The data-sheet says "Low 8 bits" in the checksum calculation.
            # But looking at the numbers that doesn't match. It looks like
            # that is a typo?
            cksum = sum(data[0:30])
            if cksum != numbers[-1]:
                cserr = ' # checksum mismatch'
            else:
                cserr = ''
            # First is PM atmospheric, second is raw counts.
            items = numbers[5:8] + numbers[8:14]
            line = now + ' '.join(str(num) for num in items) + cserr + '\n'
            datafile.write(line)
            datafile.flush()
            if cserr:
                continue
            time.sleep(args.interval)
    except (SerialException, KeyboardInterrupt):
        sys.exit(1)


def process_arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-p',
        '--port',
        default='ftdi://ftdi:232h/1',
        type=str,
        help='serial port to use (default ftdi://ftdi:232h/1)')
    parser.add_argument(
        '-i',
        '--interval',
        default=5,
        type=int,
        help='interval between measurements in seconds (≥5 s, default 5 s)')
    parser.add_argument(
        '-v', '--version', action='version', version=__version__)
    parser.add_argument(
        'path',
        nargs=1,
        help=r'path template for the data file. Should contain {}. '
        r'For example "/tmp/dust-monitor-{}.d"')
    args = parser.parse_args(argv)
    args.path = args.path[0]
    if not args.path or r'{}' not in args.path:
        parser.print_help()
        sys.exit(0)
    if args.interval < 5:
        args.interval = 5
    return args


if __name__ == '__main__':
    main(sys.argv[1:])
