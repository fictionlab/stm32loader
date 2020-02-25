# Author: byq77
# GitHub repository: https://github.com/byq77/stm32loader
#
# This file is part of stm32loader.
#
# stm32loader is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 3, or (at your option) any later
# version.
# 
# stm32loader is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with stm32loader; see the file LICENSE.  If not see
# <http://www.gnu.org/licenses/>.

"""
Handle RS-232 serial communication through pyserial.

Offer support for toggling RESET and BOOT0.
"""

# not naming this file itself 'serial', becase that name-clashes in Python 2
from __future__ import print_function
import serial
import sys

# fixes the problem with setters method
# https://stackoverflow.com/questions/598077/why-does-foo-setter-in-python-not-work-for-me
class SerialConnectionRpi(object):
    """Wrap a serial.Serial connection and toggle reset and boot0."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, serial_port, baud_rate=115200, parity="E", gpio_reset_pin=int(12), gpio_boot0_pin=int(11)):
        """Construct a SerialConnectionRpi (not yet connected)."""
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.parity = parity
        self.can_toggle_reset = True
        self.can_toggle_boot0 = True
        self.reset_active_high = False
        self.boot0_active_low = False

        # call connect() to establish connection
        self.serial_connection = None

        self._timeout = 5
        self._gpio_reset_pin = gpio_reset_pin
        self._gpio_boot0_pin = gpio_boot0_pin
        self._gpio_reset_init = False
        self._gpio_boot0_init = False

        try:
            import RPi.GPIO as GPIO
        except ImportError as e:
            print("Couldn't import RPi.GPIO. Check if the RPi.GPIO is installed on your system", file=stderr)
            exit(1)
        try:
            self._gpio_instance = GPIO
            self._gpio_instance.setmode(self._gpio_instance.BOARD)
            self._gpio_instance.setwarnings(False)
        except:
            print("Couldn't initialise the GPIO instance. Try use the script with sudo.", file=stderr)
            exit(1)
        
    @property
    def timeout(self):
        """Get timeout."""
        return self._timeout

    @timeout.setter
    def timeout(self, timeout):
        """Set timeout."""
        self._timeout = timeout
        self.serial_connection.timeout = timeout

    def connect(self):
        """Connect to the RS-232 serial port."""
        self.serial_connection = serial.Serial(
            port=self.serial_port,
            baudrate=self.baud_rate,
            # number of write_data bits
            bytesize=8,
            parity=self.parity,
            stopbits=1,
            # don't enable software flow control
            xonxoff=False,
            # don't enable RTS/CTS flow control
            rtscts=False,
            # set a timeout value, None for waiting forever
            timeout=self._timeout
        )

    def write(self, *args, **kwargs):
        """Write the given data to the serial connection."""
        return self.serial_connection.write(*args, **kwargs)

    def read(self, *args, **kwargs):
        """Read the given amount of bytes from the serial connection."""
        return self.serial_connection.read(*args, **kwargs)

    def enable_reset(self, enable=True):
        """Enable or disable the reset IO line."""
        # by default reset is active low
        if not self._gpio_reset_init:
            self._gpio_instance.setup(self._gpio_reset_pin, self._gpio_instance.OUT)
            self._gpio_reset_init = True

        if self.reset_active_high:
        	level = (self._gpio_instance.HIGH if enable else self._gpio_instance.LOW)  # active HIGH
        else:
        	level = (self._gpio_instance.LOW if enable else self._gpio_instance.HIGH)  # active LOW
        self._gpio_instance.output(self._gpio_reset_pin, level)

    def enable_boot0(self, enable=True):
        """Enable or disable the boot0 IO line."""
        # by default boot0 is active high
        if not self._gpio_boot0_init:
            self._gpio_instance.setup(self._gpio_boot0_pin, self._gpio_instance.OUT)
            self._gpio_boot0_init = True
        
        if self.boot0_active_low:
        	level = (self._gpio_instance.LOW if enable else self._gpio_instance.HIGH)  # active LOW
        else:
        	level = (self._gpio_instance.HIGH if enable else self._gpio_instance.LOW)  # active HIGH
        self._gpio_instance.output(self._gpio_boot0_pin, level)

    def clean_gpio_pins(self):
        pass
        # self._gpio_instance.cleanup()


class SerialConnectionUpboard(object):
    """Wrap a serial.Serial connection and toggle reset and boot0."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, serial_port, baud_rate=115200, parity="E", gpio_reset_pin=int(18), gpio_boot0_pin=int(17)):
        """Construct a SerialConnectionRpi (not yet connected)."""
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.parity = parity
        self.can_toggle_reset = True
        self.can_toggle_boot0 = True
        self.reset_active_high = False
        self.boot0_active_low = False
        self.GPIO_DEV = '/dev/gpiochip4'

        # call connect() to establish connection
        self.serial_connection = None

        self._timeout = 5
        self._gpio_reset_pin = gpio_reset_pin
        self._gpio_boot0_pin = gpio_boot0_pin

        try:
            from periphery import GPIO
        except ImportError as e:
            print("Couldn't import periphery.GPIO. Check if the periphery is installed on your system")
            exit(1)
        try: 
            self._reset = GPIO(self.GPIO_DEV, self._gpio_reset_pin, "out")
            self._boot0 = GPIO(self.GPIO_DEV, self._gpio_boot0_pin, "out")
        except:
            print("Couldn't initialise the GPIO instance. Try use the script with sudo.", file=stderr)
            exit(1)
        
    @property
    def timeout(self):
        """Get timeout."""
        return self._timeout

    @timeout.setter
    def timeout(self, timeout):
        """Set timeout."""
        self._timeout = timeout
        self.serial_connection.timeout = timeout

    def connect(self):
        """Connect to the RS-232 serial port."""
        self.serial_connection = serial.Serial(
            port=self.serial_port,
            baudrate=self.baud_rate,
            # number of write_data bits
            bytesize=8,
            parity=self.parity,
            stopbits=1,
            # don't enable software flow control
            xonxoff=False,
            # don't enable RTS/CTS flow control
            rtscts=False,
            # set a timeout value, None for waiting forever
            timeout=self._timeout
        )

    def write(self, *args, **kwargs):
        """Write the given data to the serial connection."""
        return self.serial_connection.write(*args, **kwargs)

    def read(self, *args, **kwargs):
        """Read the given amount of bytes from the serial connection."""
        return self.serial_connection.read(*args, **kwargs)

    def enable_reset(self, enable=True):
        """Enable or disable the reset IO line."""
        # by default reset is active low

        if self.reset_active_high:
        	level = (True if enable else False)  # active HIGH
        else:
        	level = (False if enable else True)  # active LOW
        self._reset.write(level)

    def enable_boot0(self, enable=True):
        """Enable or disable the boot0 IO line."""
        # by default boot0 is active high

        if self.boot0_active_low:
        	level = (False if enable else True)  # active LOW
        else:
        	level = (True if enable else False)  # active HIGH
        self._boot0.write(level)
    
    def clean_gpio_pins(self):
        self._boot0.close()
        self._reset.close()