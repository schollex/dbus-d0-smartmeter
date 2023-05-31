# dbus-d0-smartmeter
use IR-sensor on D0-interface of SML-smartmeter as gridmeter in an Victron Energy Venus OS installation

## Introduction and motivation

Why using an extra gridmeter on an Victron Energy ESS System if you have a modern smartmeter with IR-Interface (INFO-LED) from your locale electricity supplier?
Just attach an IR-sensor to the INFO-LED and connect it via USB-TTY-adapter to your Venus OS installation.
This project/script will catch the received data and supply it as external gridmeter to Venus OS.
It is very important for me that venus directly receives the smartmeter-data without the need of a working network-connect (e.g. if one wants to receive smartmeter-data via MQTT)

> **Attention:**
> This project is corrently not well documented. Thus, you should have advanced Venus OS and Linux experience.

## Preparation

### Hardware

You need
 * a tty-IR-sensor for D0-interfaces.<br />
E.g. search for //lesekopf smartmeter// on ebay. I can suggest the version from -Hichi- (seller hicbelm-8).
 * a good USB-TTY-adapter. Please read https://tasmota.github.io/docs/Getting-Started/#needed-hardware It's nice to have a adapter with LEDs because the indicate with 1 Hz blinking when data is received from the IR-sensor. (I decided not to use the RX/TX-GPIO-pins on the Raspberry because these pins are used by Venus OS for serial console.)
 * a wired connection between both. I use an network-patch-cable (of course with cut-off RJ45-connectors)
 * a smartmeter sending at least OBIS 1.8.0 (= counter bought energy) and OBIS 10.7.0 (= current power >0 consuming from grid respectivly <0 feeding in to grid).
   For all smartmeter I know, you have to
   * unlock the smartmeter with the PIN you can request from your electricity supplier and then
   * set the smartmeter to send extended data-packages (INF ON)

### Software

To provide the software on your Venus OS, execute there these commands:

````
wget https://github.com/schollex/dbus-d0-smartmeter/archive/refs/heads/main.zip
unzip main.zip "dbus-d0-smartmeter-main/*" -d /data
rm main.zip
mv /data/dbus-d0-smartmeter-main /data/dbus-d0-smartmeter
chmod a+x /data/dbus-d0-smartmeter/install.sh
````
## Configuration

You have to edit `config.ini`. Please note the comments there as explanation!

You also have to set the `DEV`-variable within `service/run` to your USB-TTY-adapter. E.g. for me, it's `DEV='/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0'`

TODO: further explanations!
 
## Usage

I refer to https://github.com/henne49/dbus-opendtu#usage

Additionally as my script handles with a serial-device, special preparation is necessary. For details, see https://github.com/victronenergy/venus/wiki/howto-add-a-driver-to-Venus#3-installing-a-driver

First, I took the ``etc/udev/rules.d/serial-starter.rules`` and ``ignore`` approach. But this file is on a RO-mountpoint. You have to remount as RW to edit the file. This modification also gets lost during a firmware update. Therefore I switch to this implementation...

You do not have to modify serial-starter.rules beause `service/run` stops the corresponding `serial-starter`-process. This frees the TTY from `serial-starter` so that my script can correctly read from TTY.

## Starting and Debugging

If you have good luck, just run `install.sh` and the gridmeter appears within the Venus-GUI.
If not, have a look in `current.log`. Then, temporarily edit `Logging=DEBUG` within `config.ini` and `restart.sh` to relook `current.log`.
