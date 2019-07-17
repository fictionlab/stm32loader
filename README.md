STM32Loader
=========== 
[florisa/stm32loader](https://github.com/florisla/stm32loader) with added support for CORE2 board update using SBC gpios.

Most of this software is copyrighted by their respective owners:

* **Floris Lambrechts** 
    * License: `GPLv3`
    * GitHub: [florisa/stm32loader](https://github.com/florisla/stm32loader)

### Prerequisites

Read [REQUIREMENTS](https://www.evernote.com/shard/s498/client/snv?noteGuid=19e2a091-b3eb-4149-b751-610999ab7ec5&noteKey=e21ccabdee185f5fdac3802928e6a262&sn=https%3A%2F%2Fwww.evernote.com%2Fshard%2Fs498%2Fsh%2F19e2a091-b3eb-4149-b751-610999ab7ec5%2Fe21ccabdee185f5fdac3802928e6a262&title=Uploading%2Bfirmware%2Bto%2BCORE2%2Busing%2BSBC) document and follow the instructions for your SBC.

### Installation

```bash
$ sudo python setup.py install
```

### Usage

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
    -c          sbc used to update CORE2
    -W          write unprotect
    -R          Make reset active high
    -B          Make boot0 active low
    -u          Readout unprotect
    -n          No progress: don't show progress bar
    -P parity   Parity: "even" for STM32 (default), "none" for BlueNRG
```

-------

To perform firmware update of CORE2 board run:

```bash
$ stm32loader -c <sbc_type> -e -w -v firmware.bin
```
where `<sbc_type>`:
* `rpi` for Raspberry Pi
* `tinker` for Asus Tinker Board
* `upboard` for UpBoard
