#!/usr/bin/env python3
# file: air-monitor.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# Created: 2018-04-11 18:52:43 +0200
# Last modified: 2018-04-12 10:05:02 +0200
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
import struct
import time
import serial

now = datetime.utcnow().strftime('%FT%TZ')

ft232h = serial.Serial('/dev/cuaU0', 9600, timeout=1)
datafile = open('/tmp/dust-monitor-{}.d'.format(now), 'w')

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

while True:
    data = ft232h.read(32)
    skip = data.find(b'\x42\x4d')
    if skip > 0:
        ft232h.read(skip)  # Skip to next block.
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
#    print(line, end='')
    datafile.write(line)
    datafile.flush()
#    print(now)
#    print('Concentration units (standard):')
#    print('  PM 1.0: {:d}\tPM 2.5: {:d}\tPM 10: {:d}\n'.format(pm10std, pm25std, pm100std))
#    print('Particles 0.3-0.5 μm / dm³: {:>5d}'.format(brackets[0]))
#    print('Particles   0.5-1 μm / dm³: {:>5d}'.format(brackets[1]))
#    print('Particles   1-2.5 μm / dm³: {:>5d}'.format(brackets[2]))
#    print('Particles   2.5-5 μm / dm³: {:>5d}'.format(brackets[3]))
#    print('Particles    5-10 μm / dm³: {:>5d}'.format(brackets[4]))
#    print('Particles    > 10 μm / dm³: {:>5d}'.format(part100*10))
#    print('----------------------------------------')
    time.sleep(300)
