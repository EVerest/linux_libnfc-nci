# linux_libnfc-nci - EVerest

Find the original README at the bottom.

branch **everest**: Modified branch **NCI2.0_PN7160**, working with PN7160 NFC controllers on 64bit Linux platforms, and optimized for used with [EVerest](https://github.com/EVerest).

## Modifications Notice

The [original upstream source code](https://github.com/NXPNFCLinux/linux_libnfc-nci), released under the Apache 2.0 license and re-distributed here under the same license, has been modified as indicated below:

- Applied 64bit patches
- Added CMakeLists.txt
- Allow for runtime configuration of interface properties for alternative I²C/SPI interface
- Allow configuration files to be in a custom path
- Added support for using GPIO line names via libgpiod

## Building

### As Dependency

When using this library in EVerest, retrieval of the source code will be handled automatically.

Use `add_subdirectory()` or `find_package(libnfc-nci)` and link against
`libnfc_nci::libnfc_nci`. The library searches for `libnfc-nci.conf` and
`libnfc-nxp.conf` directly in the sysconfdir selected at build time.

GNUInstallDirs controls both installation and the compiled default:

- Default configuration: `/usr/local/etc`.
- `-DCMAKE_INSTALL_PREFIX=/usr`: `/etc`.
- `-DCMAKE_INSTALL_SYSCONFDIR=/etc`: explicitly select `/etc`.
- A relative `CMAKE_INSTALL_SYSCONFDIR` is resolved using GNUInstallDirs.

Both files are installed there when `LIBNFCNCI_INSTALL=ON`. When installation
is disabled, the consuming project must supply them. `DESTDIR` only stages
installation; it is not part of the compiled path. Changing the install prefix
at installation time does not change the library's compiled default.

`LIBNFCNCI_CONFIG_INSTALL_PATH` and its former target property have been removed;
use `CMAKE_INSTALL_SYSCONFDIR` for build-time configuration instead.

Applications may select another directory before any configuration access
(including `InitializeLogLevel()`) and before `doInitialize()`:

```c
setConfigPath("/etc/everest/libnfc_config");
```

This selects the directory for all configuration readers. There is no fallback
to `/etc` or another directory. Relative paths refer to the working directory;
a trailing slash is optional. NULL and empty paths are ignored. The last valid
call before configuration is read wins; already loaded settings are not reloaded.
The library does not select its configuration directory from environment variables.

### As Standalone Build

Standalone test builds can be done as follows:
```
git clone git@github.com:EVerest/linux_libnfc-nci.git
cd linux_libnfc-nci
git checkout everest
mkdir build
cd build
CMAKE_PREFIX_PATH=<path to everest-cmake> cmake -DCMAKE_INSTALL_PREFIX=<prefered install location> ..
# or, if standalone examples are required:
CMAKE_PREFIX_PATH=<path to everest-cmake> cmake -DCMAKE_INSTALL_PREFIX=<prefered install location> -DLIBNFCNCI_BUILD_EXAMPLES=ON ..
cmake --build . --parallel -j
cmake --install .
```
This will also install the configuration files into the expected folder.

### Demo configuration directory

Both demos use the library default unless overridden with a global command-line
option or `NFC_CONFIG_DIR`. Command-line options take precedence over the
non-empty environment variable. Put global options before the command:

```sh
nfc_demo --config-dir /etc/everest/libnfc_config poll
nfc_demo --config-dir=/etc/everest/libnfc_config poll
NFC_CONFIG_DIR=/etc/everest/libnfc_config nfc_cb_example
```

The former `MW_CONFIG_DIR` prefix mechanism is no longer supported. Use
`NFC_CONFIG_DIR` for the demos or `setConfigPath()` in library consumers.
Storage, firmware and device paths are configured independently of this directory.

After successful reader initialization, `nfc_demo` prints the firmware version
reported by the reader, for example `Reader firmware version: 12.50.11`.
This uses hexadecimal version bytes, independently of debug logging and any
firmware image installed on disk. If no version is available, it prints
`Reader firmware version: unavailable`.

For a native build with examples enabled, hardware-free regression checks can
be run with `python3 tests/test_config_paths.py build --sysconfdir /usr/local/etc`.
Pass the actual compiled sysconfdir; the checks require C/C++ compilers and
`strace` and never initialize NFC hardware.
Reader-version API and startup checks are available separately via
`python3 tests/test_reader_version.py build`.

### libgpiod

Building against `libgpiod` can be enabled by passing the property `LIBNFCNCI_LIBGPIOD` set to `ON` to cmake.
By default, this is disabled.
Using libgpiod and GPIO line names should be the preferred way to access GPIO lines from user-space since
the older Linux' sysfs interface is deprecated since ages.

## Runtime Configuration

Runtime configuration (debug output levels, detailled NFC behaviour, interface specification) happens via the above-mentioned files.

Templates, which are also the defaults to be installed in a standalone build, can be found in ```conf/```:

- ```conf/libnfc-nci.conf```
- ```conf/libnfc-nxp.conf```

The specification of the interface to the NFC chip is defined in ```libnfc-nxp.conf```.
Relevant settings are:

```
NXP_TRANSPORT=0x02
PIN_INT=535
PIN_ENABLE=536
PIN_FWDNLD=537
I2C_ADDRESS=0x28
I2C_BUS="/dev/i2c-1"
SPI_BUS="/dev/spidev0.0"
```

When compiled with libgpiod support, then instead of using integers for Linux' legacy sysfs interface,
it is possible to use GPIO line names. These are usually defined via Device Tree for your board.
Such line names must be enclosed in quotation marks to indicate that the configuration value is a string.
And it cannot be mixed: all pin configuration values needs to be GPIO line names.

```
NXP_TRANSPORT=0x02
PIN_INT="RFID_IRQ"
PIN_ENABLE="nRESET_RFID"
PIN_FWDNLD="RFID_DWL_REQ"
I2C_ADDRESS=0x28
I2C_BUS="/dev/i2c-1"
```

Applications can override these transport-related settings in memory, after calling
`setConfigPath()` but before calling `doInitialize()`, via:

```c
setNxpConfigValue("NXP_TRANSPORT", "0x02");
setNxpConfigValue("PIN_INT", "535");
setNxpConfigValue("PIN_ENABLE", "536");
setNxpConfigValue("PIN_FWDNLD", "537");
setNxpConfigValue("I2C_ADDRESS", "0x28");
setNxpConfigValue("I2C_BUS", "/dev/i2c-1");
setNxpConfigValue("SPI_BUS", "/dev/spidev0.0");
```

The configuration file is still loaded, so settings not supplied through the
API continue to come from `libnfc-nxp.conf`. Runtime values supplied through
`setNxpConfigValue()` take precedence over values from the file and are kept
separately from the file-backed configuration. They therefore remain active
even if the internal configuration cache is reset during initialization.

The library does not require `libnfc-nxp.conf` to exist on disk for every
setting. If individual runtime transport settings are missing, the code falls
back to built-in defaults for `PIN_INT`, `PIN_ENABLE`, `PIN_FWDNLD`,
`I2C_ADDRESS`, `I2C_BUS` and `SPI_BUS`. `NXP_TRANSPORT` is the exception:
there is no built-in default transport selection, so initialization still
requires either `libnfc-nxp.conf` to define it or the application to call
`setNxpConfigValue("NXP_TRANSPORT", ...)`.


---

  Original README:

---

linux_libnfc-nci
================

branch NCI2.0_PN7160: Linux NFC stack for PN7160 NCI2.0 based NXP NFC Controller.
For previous NXP NFC Controllers support (PN7150, PN7120) refer to branch master.

Information about NXP NFC Controller can be found on [NXP website](https://www.nxp.com/products/identification-and-security/nfc/nfc-reader-ics:NFC-READER).

Further details about the stack [here](https://www.nxp.com/doc/AN13287).

Release version
---------------
- NCI2.0-R1.1 fix limitation about multiple T5T, fix issue with MIFARE Classic read after write, cleanup of alternate transport definition, cleanup of logs 
- NCI2.0-R1.0 is the first official release of Linux libnfc-nci stack for PN7160

Possible problems, known errors and restrictions of R1.1:
---------------------------------------------------------
- LLCP1.3 support requires OpenSSL Cryptography and SSL/TLS Toolkit (version 1.0.1j or later)
- To install on 64bit OS, apply patch
