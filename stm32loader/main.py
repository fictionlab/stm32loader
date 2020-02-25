#!/usr/bin/env python
# Authors: Ivan A-R, Floris Lambrechts
# GitHub repository: https://github.com/florisla/stm32loader
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

"""Flash firmware to STM32 microcontrollers over a serial connection."""


from __future__ import print_function

import getopt
import os
import sys

from . import bootloader
from .uart import SerialConnection

# sbc_type = os.getenv('STM32LOADER_SBC',None)

# if sbc_type == 'rpi' or sbc_type == 'tinker':
#     from .uart_gpios import SerialConnectionRpi
# elif sbc_type == 'upboard':
#     pass

DEFAULT_VERBOSITY = 5


class Stm32Loader:
    """Main application: parse arguments and handle commands."""

    # serial link bit parity, compatible to pyserial serial.PARTIY_EVEN
    PARITY = {"even": "E", "none": "N"}

    BOOLEAN_FLAG_OPTIONS = {
        "-e": "erase",
        "-W": "write-unprotect",
        "-u": "unprotect",
        "-w": "write",
        "-v": "verify",
        "-r": "read",
        "-s": "swap_rts_dtr",
        "-n": "hide_progress_bar",
        "-R": "reset_active_high",
        "-B": "boot0_active_low",
    }

    SBC_TYPES = ["tinker", "rpi", "upboard"]

    INTEGER_OPTIONS = {"-b": "baud", "-a": "address", "-g": "go_address", "-l": "length"}

    def __init__(self):
        """Construct Stm32Loader object with default settings."""
        self.stm32 = None
        self.configuration = {
            "port": os.environ.get("STM32LOADER_SERIAL_PORT"),
            "baud": 115200,
            "parity": self.PARITY["even"],
            "family": os.environ.get("STM32LOADER_FAMILY"),
            "address": 0x08000000,
            "core2_mode": None,
            "write-unprotect": False,
            "erase": False,
            "unprotect": False,
            "write": False,
            "verify": False,
            "read": False,
            "go_address": -1,
            "swap_rts_dtr": False,
            "reset_active_high": False,
            "boot0_active_low": False,
            "hide_progress_bar": False,
            "data_file": None,
        }
        self.verbosity = DEFAULT_VERBOSITY

    def debug(self, level, message):
        """Log a message to stderror if its level is low enough."""
        if self.verbosity >= level:
            print(message, file=sys.stderr)

    def parse_arguments(self, arguments):
        """Parse the list of command-line arguments."""
        try:
            # parse command-line arguments using getopt
            options, arguments = getopt.getopt(arguments, "hqVeuwvrsnRBWP:p:b:a:l:g:f:c:", ["help"])
        except getopt.GetoptError as err:
            # print help information and exit:
            # this prints something like "option -a not recognized"
            print(str(err))
            self.print_usage()
            sys.exit(2)

        # if there's a non-named argument left, that's a file name
        if arguments:
            self.configuration["data_file"] = arguments[0]

        self._parse_option_flags(options)

        if not self.configuration["port"]:
            print(
                "No serial port configured. Supply the -p option "
                "or configure environment variable STM32LOADER_SERIAL_PORT.",
                file=sys.stderr,
            )
            sys.exit(3)

    def connect(self):
        """Connect to the RS-232 serial port."""
        if self.configuration["core2_mode"] is not None:
            if self.configuration["core2_mode"] in [ "rpi", 'tinker']:
                try:
                    from .uart_gpios import SerialConnectionRpi
                except ImportError as e:
                    print("There was an error during importing SerialConnectionRpi:" + e.message)
                    exit(1)
                else:
                    serial_connection = SerialConnectionRpi(
                        self.configuration["port"], 
                        self.configuration["baud"], 
                        self.configuration["parity"]
                    )
            elif self.configuration["core2_mode"] == "upboard":
                try:
                    from .uart_gpios import SerialConnectionUpboard
                except ImportError as e:
                    print("There was an error during importing SerialConnectionUpboard:" + e.message)
                    exit(1)
                else:
                    serial_connection = SerialConnectionUpboard(
                        self.configuration["port"], 
                        self.configuration["baud"], 
                        self.configuration["parity"]
                    )
        else:
            serial_connection = SerialConnection(
                self.configuration["port"], 
                self.configuration["baud"], 
                self.configuration["parity"]
            )            
        self.debug(
            10,
            "Open port %(port)s, baud %(baud)d"
            % {"port": self.configuration["port"], "baud": self.configuration["baud"]},
        )
        
        serial_connection.swap_rts_dtr = self.configuration["swap_rts_dtr"]
        serial_connection.reset_active_high = self.configuration["reset_active_high"]
        serial_connection.boot0_active_low = self.configuration["boot0_active_low"]

        serial_connection.enable_boot0(False)
        serial_connection.enable_reset(False)

        show_progress = not self.configuration["hide_progress_bar"]

        self.stm32 = bootloader.Stm32Bootloader(
            serial_connection, verbosity=self.verbosity, show_progress=show_progress
        )

        try:
            serial_connection.connect()
        except IOError as e:
            print(str(e) + "\n", file=sys.stderr)
            print(
                "Is the device connected and powered correctly?\n"
                "Please use the -p option to select the correct serial port. Examples:\n"
                "  -p COM3\n"
                "  -p /dev/ttyS0\n"
                "  -p /dev/ttyUSB0\n"
                "  -p /dev/tty.usbserial-ftCYPMYJ\n",
                file=sys.stderr,
            )
            exit(1)

        try:
            self.stm32.reset_from_system_memory()
        except bootloader.CommandError:
            print(
                "Can't init into bootloader. Ensure that BOOT0 is enabled and reset the device.",
                file=sys.stderr,
            )
            self.reset()
            sys.exit(1)

    def perform_commands(self):
        """Run all operations as defined by the configuration."""
        # pylint: disable=too-many-branches
        binary_data = None
        if self.configuration["write"] or self.configuration["verify"]:
            with open(self.configuration["data_file"], "rb") as read_file:
                binary_data = bytearray(read_file.read())
        if self.configuration["unprotect"]:
            try:
                self.stm32.readout_unprotect()
            except bootloader.CommandError as e:
                # may be caused by readout protection
                self.debug(0, "Read unprotect failed:" + e.message)
                self.debug(0, "Quit")
                self.reset()
                sys.exit(1)
            else:
                self.debug(0, "read unprotect done")
        if self.configuration["write-unprotect"]:
            try:
                self.stm32.write_unprotect()
            except bootloader.CommandError as e:
                self.debug(0, "Write unprotect failed:" + e.message)
                self.debug(0, "Quit")
                self.reset()
                sys.exit(1)
            else:
                self.debug(0, "write unprotect done")
        if self.configuration["erase"]:
            try:
                self.stm32.erase_memory()
            except bootloader.CommandError as e:
                # may be caused by readout protection
                self.debug(
                    0,
                    "Erase failed -- probably due to readout protection\n"
                    "consider using the -u (unprotect) option." + e.message 
                )
                self.reset()
                sys.exit(1)
        if self.configuration["write"]:
            #TODO: erase required sectors
            self.stm32.write_memory_data(self.configuration["address"], binary_data)
        if self.configuration["verify"]:
            read_data = self.stm32.read_memory_data(
                self.configuration["address"], len(binary_data)
            )
            try:
                bootloader.Stm32Bootloader.verify_data(read_data, binary_data)
                print("Verification OK")
            except bootloader.DataMismatchError as e:
                print("Verification FAILED: %s" % e, file=sys.stdout)
                sys.exit(1)
        if not self.configuration["write"] and self.configuration["read"]:
            read_data = self.stm32.read_memory_data(
                self.configuration["address"], self.configuration["length"]
            )
            with open(self.configuration["data_file"], "wb") as out_file:
                out_file.write(read_data)
        if self.configuration["go_address"] != -1:
            self.stm32.go(self.configuration["go_address"])

    def reset(self):
        """Reset the microcontroller."""
        self.stm32.reset_from_flash()
        if( self.configuration['core2_mode'] is not None and self.configuration['core2_mode'] in ['rpi','tinker','upboard']):
            self.stm32.connection.clean_gpio_pins()

    @staticmethod
    def print_usage():
        """Print help text explaining the command-line arguments."""
        help_text = """Usage: %s [-hqVeuwvrsRB] [-l length] [-p port] [-b baud] [-P parity]
          [-a address] [-g address] [-f family] [file.bin]
    -e          Erase (note: this is required on previously written memory)
    -u          Unprotect in case erase fails
    -w          Write file content to flash
    -v          Verify flash content versus local file (recommended)
    -r          Read from flash and store in local file
    -l length   Length of read
    -p port     Serial port (default: /dev/tty.usbserial-ftCYPMYJ)
    -b baud     Baudrate (default: 115200)
    -a address  Target address (default: 0x08000000)
    -g address  Start executing from address (0x08000000, usually)
    -f family   Device family to read out device UID and flash size; e.g F1 for STM32F1xx

    -h          Print this help text
    -q          Quiet mode
    -V          Verbose mode

    -s          Swap RTS and DTR: use RTS for reset and DTR for boot0
    -c		    sbc used to update CORE2 (rpi | tinker | upboard)
    -W          write unprotect
    -R          Make reset active high
    -B          Make boot0 active low
    -u          Readout unprotect
    -n          No progress: don't show progress bar
    -P parity   Parity: "even" for STM32 (default), "none" for BlueNRG

    Example: ./%s -p COM7 -f F1
    Example: ./%s -e -w -v example/main.bin
"""
        current_script = sys.argv[0] if sys.argv else "stm32loader"
        help_text = help_text % (current_script, current_script, current_script)
        print(help_text)

    def read_device_details(self):
        """Show MCU details (bootloader version, chip ID, UID, flash size)."""
        boot_version = self.stm32.get()
        self.debug(0, "Bootloader version: 0x%X" % boot_version)
        device_id = self.stm32.get_id()
        self.debug(
            0, "Chip id: 0x%X (%s)" % (device_id, bootloader.CHIP_IDS.get(device_id, "Unknown"))
        )
        family = self.configuration["family"]
        if not family:
            self.debug(0, "Supply -f [family] to see flash size and device UID, e.g: -f F1")
        else:
            # special fix for F4 devices
            if family == "F4":
                try:
                    device_uid, flash_size = self.stm32.get_flash_size_and_uid_f4()
                except bootloader.CommandError as e:
                    self.debug(0,"Something was wrong with reading chip family data: " + e.message)
                else:
                    device_uid_string = self.stm32.format_uid(device_uid)
                    self.debug(0, "Device UID: %s" % device_uid_string)
                    self.debug(0, "Flash size: %d KiB" % flash_size)
            else:
                try:
                    flash_size = self.stm32.get_flash_size(family)
                    device_uid = self.stm32.get_uid(family)
                except bootloader.CommandError as e:
                    self.debug(0,"Something was wrong with reading chip family data: " + e.message)
                else:
                    device_uid_string = self.stm32.format_uid(device_uid)
                    self.debug(0, "Device UID: %s" % device_uid_string)
                    self.debug(0, "Flash size: %d KiB" % flash_size)

    def _parse_option_flags(self, options):
        # pylint: disable=eval-used
        for option, value in options:
            if option == "-V":
                self.verbosity = 10
            elif option == "-c":
                if value not in self.SBC_TYPES:
                    print("Incorrect SBC type!")
                    exit(1)
                self.configuration["core2_mode"] = value
                if value == 'rpi':
                    self.configuration["port"] = '/dev/serial0'                
                elif value == 'tinker':
                    self.configuration["port"] = '/dev/ttyS1'
                elif value == 'upboard':
                    self.configuration["port"] = '/dev/ttyS4'
                self.configuration["reset_active_high"] = True
            elif option == "-q":
                self.verbosity = 0
            elif option in ["-h", "--help"]:
                self.print_usage()
                sys.exit(0)
            elif option == "-p":
                self.configuration["port"] = value
            elif option == "-f":
                self.configuration["family"] = value
            elif option == "-P":
                assert (
                    value.lower() in Stm32Loader.PARITY
                ), "Parity value not recognized: '{0}'.".format(value)
                self.configuration["parity"] = Stm32Loader.PARITY[value.lower()]
            elif option in self.INTEGER_OPTIONS:
                self.configuration[self.INTEGER_OPTIONS[option]] = int(eval(value))
            elif option in self.BOOLEAN_FLAG_OPTIONS:
                self.configuration[self.BOOLEAN_FLAG_OPTIONS[option]] = True
            else:
                assert False, "unhandled option %s" % option

def main(*args, **kwargs):
    """
    Parse arguments and execute tasks.

    Default usage is to supply *sys.argv[1:].
    """
    try:
        loader = Stm32Loader()
        loader.parse_arguments(args)
        loader.connect()
        try:
            loader.read_device_details()
            loader.perform_commands()
        finally:
            loader.reset()
    except SystemExit:
        if not kwargs.get("avoid_system_exit", False):
            raise


if __name__ == "__main__":
    main(*sys.argv[1:])
