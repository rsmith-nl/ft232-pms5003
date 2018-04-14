Using the PMS5003 particulate matter sensor with Python 3
#########################################################

:date: 2018-04-14
:tags: PMS5003, Python 3, FT232H
:author: Roland Smith

.. Last modified: 2018-04-15 00:04:10 +0200

Introduction
------------

The ``dust-monitor.py`` program allows you to read and log particulate matter
(“PM”) data from the plantower PMS5003 sensor on computer. I bought mine from
a local Adafruit reseller.

The PMS5003 outputs data over a serial connection. I've used an FT232H
serial ↔ USB bridge to connect it to my PC. This device shows up on my
(FreeBSD) machine as ``/dev/cuaU*``, but this will vary based on the OS used.
On ms-windows you might need to install a driver for the FT232H.

Except from the hardware, this program uses the pyserial_ module to connect to
the device.

.. _pyserial: https://github.com/pyserial/pyserial

This program has been written for Python 3 on the FreeBSD operating system
version 11.1. I expect it will work on other POSIX systems, and maybe even on
ms-windows. But I haven't tested that.


The program
-----------

The ``dust-monitor.py`` program is designed to be started from the command
line, where it should probably be started so as to run in the background. The
main options are:

* ``-p`` or ``--port`` Select the serial port to use. Defaults to
  ``/dev/cuaU0``. Note that the user running this program should have
  read/write access to this port.
* ``-i`` or ``--interval`` Sets the interval between measurements. Defaults to
  5 s, which is also the minimum interval.

There is one *required* argument, which is a filename template. This template
should contain *one* ``{}``-pair, which will be replaced by the full ISO-8601
notation of the UTC date and time when the program was started. This serves to make
the filenames unique and as a reminder.

An example:

.. code-block:: console

    ./dust-monitor.py -p /dev/cuaU1 -i 10 '/tmp/pmdata-{}.txt'

The program would open the ``/dev/cuaU1`` device to read data every ten
seconds. The data would be written to
``/tmp/pmdata-2018-04-14T21:39:59Z.txt``, where the datetime is just an
example.


Data
----

The data is stored as plain text so that is is readable by both humans and
computers. Apart from a header (lines starting with ``#``), the data looks
like this::

    2018-04-13T15:21:54Z 11 14 17 2154 604 82 4 4 2

Each line is a single data point. The columns are separated by spaces. Apart
from the first column, all columns are unsigned integers. The meaning of the columns is:

* UTC date and time in ISO-8601 format
* PM 1.0 in μg/m³
* PM 2.5 in μg/m³
* PM 10 in μg/m³
* number of particles >0.3 μm / 0.1 dm³ of air
* number of particles >0.5 μm / 0.1 dm³ of air
* number of particles >1.0 μm / 0.1 dm³ of air
* number of particles >2.5 μm / 0.1 dm³ of air
* number of particles >5 μm / 0.1 dm³ of air
* number of particles >10 μm / 0.1 dm³ of air

Many programs could be used to load and analyze/manipulate this data. Below is
an example how to read the data in Python with numpy.

.. code-block:: python

    import numpy as np

    columns = np.genfromtxt('/tmp/pmdata-2018-04-14T21:39:59Z.txt',
                            comments="#", delimiter=" ",
                            usecols=tuple(range(1, 10))).T

    # Every of these columns pmX is particulate matter < X/10 μm in μg/m³.
    pm10 = columns[0]
    pm25 = columns[1]
    pm100 = columns[2]

    # Every of these columns partN is a count of particles > N/10 μm in 0.1 dm³ or air.
    part03 = columns[3]
    part05 = columns[4]
    part10 = columns[5]
    part25 = columns[6]
    part50 = columns[7]
    part100 = columns[8]
