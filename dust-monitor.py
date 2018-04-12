#!/usr/bin/env python3
# file: air-monitor.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# Created: 2018-04-11 18:52:43 +0200
# Last modified: 2018-04-12 16:43:35 +0200
#
# To the extent possible under law, R.F. Smith has waived all copyright and
# related or neighboring rights to air-monitor.py. This work is published
# from the Netherlands. See http://creativecommons.org/publicdomain/zero/1.0/
"""
Monitoring program for the plantower PMS5003 air monitoring sensor.
The sensor is connected to the computer via an FT232H, used as a serial to
USB converter.

Logs the data to a file.
"""

from datetime import datetime
import argparse
import struct
import sys
import time
import serial

__version__ = '0.2'


def main(argv):
    """
    Entry point for dust-monitor.py.

    Arguments:
        argv: command line arguments
    """
    now = datetime.utcnow().strftime('%FT%TZ')
    args = process_arguments(argv)

    # Open the files
    ft232h = serial.Serial(args.port, 9600, timeout=1)
    datafile = open(args.path.format(now), 'w')

    # Write datafile header.
    datafile.write('# PMS5003 data.\n# Started monitoring at {}.\n'.format(now))
    datafile.write('# Per line, the data items are:\n')
    datafile.write('# * UTC date and time in ISO8601 format\n')
    datafile.write('# * PM 1.0 in μg/m³\n')
    datafile.write('# * PM 2.5 in μg/m³\n')
    datafile.write('# * PM 10 in μg/m³\n')
    datafile.write('# * number of particles 0.3 - 0.5 μm per dm³ of air\n')
    datafile.write('# * number of particles 0.5 - 1.0 μm per dm³ of air\n')
    datafile.write('# * number of particles 1.0 - 2.5 μm per dm³ of air\n')
    datafile.write('# * number of particles 2.5 -   5 μm per dm³ of air\n')
    datafile.write('# * number of particles   5 -  10 μm per dm³ of air\n')
    datafile.write('# * number of particles     >  10 μm per dm³ of air\n')
    datafile.flush()

    # Read and write the data.
    try:
        while True:
            data = ft232h.read(32)
            skip = data.find(b'\x42\x4d')
            if skip > 0:
                ft232h.read(skip)  # Skip to next block to synchonize.
                time.sleep(0.5)
                continue
            now = datetime.utcnow().strftime('%FT%TZ ')
            try:
                numbers = struct.unpack('>xxxxHHHHHHHHHHHHHH', data)
            except struct.error:
                datafile.write('# ' + now + 'unpack error\n')
                datafile.flush()
                continue
            cksum = sum(data[0:30])
            if cksum != numbers[-1]:
                datafile.write('# ' + now + 'checksum error\n')
                datafile.flush()
                continue
            (pm10std, pm25std, pm100std, pm10env, pm25env, pm100env) = numbers[0:6]
            part100 = numbers[11]
            counts = numbers[6:-2]
            brackets = tuple(round((counts[j] - sum(counts[j+1:]))*10) for j in range(6))
            items = numbers[3:6] + brackets[:5] + (part100,)
            line = now + ' '.join(str(num) for num in items) + '\n'
            datafile.write(line)
            datafile.flush()
            time.sleep(args.interval)
    except (serial.serialutil.SerialException, KeyboardInterrupt):
        sys.exit(1)


def process_arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-p',
        '--port',
        default='/dev/cuaU0',
        type=str,
        help='serial port to use (default /dev/cuaU0)')
    parser.add_argument(
        '-i',
        '--interval',
        default=300,
        type=int,
        help='interval between measurements (default 300 s)')
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
    return args


if __name__ == '__main__':
    main(sys.argv[1:])
