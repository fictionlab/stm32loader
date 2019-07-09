STM32Loader
=========== 
[florisa/stm32loader](https://github.com/florisla/stm32loader) with added support for CORE2 board update using SBC gpios.

Most of this software is copyrighted by their respective owners:

* **Floris Lambrechts** 
    * License: `GPLv3`
    * GitHub: [florisa/stm32loader](https://github.com/florisla/stm32loader)

Usage
-----

```
./stm32loader.py [-hqVewvrsRB] [-l length] [-p port] [-b baud] [-P parity] [-a address] [-g address] [-f family] [file.bin]
    -e          Erase (note: this is required on previously written memory)
    -u          Readout unprotect
    -w          Write file content to flash
    -v          Verify flash content versus local file (recommended)
    -r          Read from flash and store in local file
    -l length   Length of read
    -p port     Serial port (default: /dev/tty.usbserial-ftCYPMYJ)
    -b baud     Baud speed (default: 115200)
    -a address  Target address (default: 0x08000000)
    -g address  Start executing from address (0x08000000, usually)
    -f family   Device family to read out device UID and flash size; e.g F1 for STM32F1xx

    -h          Print this help text
    -q          Quiet mode
    -V          Verbose mode

    -s          Swap RTS and DTR: use RTS for reset and DTR for boot0
    -c          Use CORE2 mode
    -R          Make reset active high
    -B          Make boot0 active low
    -u          Readout unprotect
    -n          No progress: don't show progress bar
    -P parity   Parity: "even" for STM32 (default), "none" for BlueNRG
```


Example (CORE2 + Raspberry Pi 3B)
-------

On RPi create environment variable (permanent):

Execute only once:
```
bash -c "echo 'export=STM32LOADER_SBC=rpi' >> ~/.profile"
```

To perform firmware update run:

```
stm32loader -p /dev/serial0 -c -R -w -v firmware.bin
```
