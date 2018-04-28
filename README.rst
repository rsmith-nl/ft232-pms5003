Using the PMS5003 particulate matter sensor with Python 3
#########################################################

:date: 2018-04-28
:tags: PMS5003, Python 3, FT232H
:author: Roland Smith

.. Last modified: 2018-04-29T00:00:43+0200

Introduction
------------

The ``dust-monitor.py`` program allows you to read and log particulate matter
(“PM”) data from the plantower PMS5003 sensor on computer. I bought mine from
a local Adafruit reseller.

The PMS5003 outputs data over a serial connection. I've used an FT232H
serial ↔ USB bridge to connect it to my PC.

Except from the hardware, this program uses the pyftdi_ module to connect to
the device. This module in turn requires pyserial_ and pyusb_.  The advantage
of ``pyftdi`` is that it is a pure python solution. It does not require native
libraries which makes installing it easier.

.. _pyftdi: https://github.com/eblot/pyftdi
.. _pyusb: https://github.com/pyusb/pyusb
.. _pyserial: https://github.com/pyserial/pyserial

Note that for this to work, any *native* driver for FTDI chips needs to be
unloaded. On FreeBSD this is accomplished by commenting out the ``nomatch``
statement in ``/etc/devd/usb.conf`` that loads ``uftdi`` driver and restarting
``devd``.

This program has been written for Python 3 on the FreeBSD operating system
version 11.1. I expect it will work on other POSIX systems, and maybe even on
ms-windows. But I haven't tested that.

To use the sensor I had to read the manual but also look at e.g. the adafruit
sample code because some points were not completely clear to me from the
documentation. In the process I made some annotations in the manual. Since
there don't seem to be restrictions to modifications and redistribution of
that manual, I've made my `annotated version`_ available.

.. _annotated version: data/plantower-pms5003-manual_annotated.pdf


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

    ./dust-monitor.py -p ftdi://ftdi:232h/2 -i 900 '/tmp/pmdata-{}.txt'

The program would open the ``ftdi://ftdi:232h/2`` device (the second FT232H
connected to the system) to read data every fifteen minutes. The data would be
written to ``/tmp/pmdata-2018-04-14T21:39:59Z.txt``, where the datetime is
just an example.


Data
----

The data is stored as plain text so that is is readable by both humans and
computers. Apart from a header (lines starting with ``#``), the data looks
like this::

    2018-04-13T15:21:54Z 11 14 17 2154 604 82 4 4 2

Each line is a single data point. The columns are separated by spaces. Apart
from the first column, all columns are unsigned integers. The meaning of the columns is:

* UTC date and time in ISO-8601 format
* PM 1.0 in μg/m³ [i.e particles ≤ 1 μm]
* PM 2.5 in μg/m³ [particles ≤ 2.5 μm]
* PM 10 in μg/m³ [particles ≤ 10 μm]
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
