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
   * set the smartmeter to send extended data-packages (InF On)

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

`current.log` will look like this:

````
2023-05-31 19:13:16,534 root INFO Starting...
2023-05-31 19:13:16,545 root INFO current initialized-state = False
2023-05-31 19:13:16,589 root INFO Setting /Settings/CGwacs/RunWithoutGridMeter does not exist yet or must be adjusted
2023-05-31 19:13:16,657 root INFO changing RunWithoutGridMeter to 1
2023-05-31 19:13:16,663 root INFO Opening /dev/ttyUSB1
2023-05-31 19:13:17,185 root INFO received OBIS Code 600100 (unused)
2023-05-31 19:13:17,187 root INFO received OBIS Code 010800 (wh)
2023-05-31 19:13:17,188 root INFO received OBIS Code 020800 (whgiven)
2023-05-31 19:13:17,190 root INFO received OBIS Code 100700 (w)
2023-05-31 19:13:17,192 root INFO received smartmeter-data - start DBUS initialization...
2023-05-31 19:13:17,197 root INFO registered ourselves on D-Bus as com.victronenergy.grid.ttyUSB1
2023-05-31 19:13:17,214 root INFO exitAfterHours will stop this service after 24.0h
2023-05-31 19:13:17,216 root INFO Connected to dbus, and switching over to gobject.MainLoop() (= event based)
2023-05-31 19:13:17,223 root INFO setting RunWithoutGridMeter changed: 1 => 1
2023-05-31 19:13:18,240 root INFO smartmeter-data received
2023-05-31 19:13:18,247 root INFO changed /Connected to 1
2023-05-31 19:13:18,252 root INFO changing RunWithoutGridMeter to 0
2023-05-31 19:13:18,321 root INFO setting RunWithoutGridMeter changed: 1 => 0
2023-05-31 19:28:17,216 root INFO Got 901 measurements, last _update() call: 1685561297
2023-05-31 19:43:17,216 root INFO Got 900 measurements, last _update() call: 1685562197
2023-05-31 19:58:17,217 root INFO Got 900 measurements, last _update() call: 1685563097
2023-05-31 20:13:17,218 root INFO Got 900 measurements, last _update() call: 1685563997
2023-05-31 20:28:17,220 root INFO Got 900 measurements, last _update() call: 1685564897
[...]
````
You'll get stats every `SignOfLiveLog` minutes - see the 15 min interval of the last log lines above.

If you see something like this

````
2023-06-02 13:20:42,903 root INFO Starting...
2023-06-02 13:20:42,916 root INFO current initialized-state = False
2023-06-02 13:20:43,0 root INFO changing RunWithoutGridMeter to 1
2023-06-02 13:20:43,7 root INFO Opening /dev/ttyUSB3
2023-06-02 13:20:43,838 root INFO received OBIS Code 600100 (unused)
2023-06-02 13:20:43,840 root INFO received OBIS Code 010800 (wh)
2023-06-02 13:20:43,842 root INFO received OBIS Code 020800 (whgiven)
2023-06-02 13:20:43,844 root INFO received OBIS Code 100700 (w)
2023-06-02 13:20:43,845 root WARNING OBIS Code 100700 (power) is missing
2023-06-02 13:20:44,759 root INFO received OBIS Code 600100 (unused)
2023-06-02 13:20:44,761 root INFO received OBIS Code 010800 (wh)
2023-06-02 13:20:44,763 root INFO received OBIS Code 020800 (whgiven)
2023-06-02 13:20:44,764 root INFO received OBIS Code 100700 (w)
2023-06-02 13:20:44,766 root WARNING OBIS Code 100700 (power) is missing
2023-06-02 13:20:45,786 root INFO received OBIS Code 600100 (unused)
2023-06-02 13:20:45,789 root INFO received OBIS Code 010800 (wh)
2023-06-02 13:20:45,791 root INFO received OBIS Code 020800 (whgiven)
2023-06-02 13:20:45,794 root INFO received OBIS Code 100700 (w)
````

OBIS-data is received, but OBIS 10.7.0 which is power consumption is missing. See the "InF On" part above for solving this.

Otherwise, you shoud set `Logging=Debug`. After modifying `config.ini` you have to execute `restart.sh` to apply. Then, the log could look like this (some parts are truncated):

````
[...]
2023-06-02 10:59:23,95 root DEBUG rawdata=False
2023-06-02 10:59:23,194 root DEBUG rawdata=1b1b1b1b0101010176......00001b1b1b1b1a01afde
2023-06-02 10:59:23,198 root DEBUG 600100 => 010101010b0a....01
2023-06-02 10:59:23,199 root DEBUG ---
2023-06-02 10:59:23,200 root DEBUG ['1e', 'ff', '6', '3', 'd1bc']
2023-06-02 10:59:23,202 root DEBUG 5369.200000000001
2023-06-02 10:59:23,203 root DEBUG 010800 => 641c79047262016416f017621e52ff63d1bc01
2023-06-02 10:59:23,204 root DEBUG wh
2023-06-02 10:59:23,206 root DEBUG ---
2023-06-02 10:59:23,207 root DEBUG ['1e', 'ff', '6', '4', '55c65e']
2023-06-02 10:59:23,208 root DEBUG 562134.2000000001
2023-06-02 10:59:23,210 root DEBUG 020800 => 017262016416f017621e52ff6455c65e01
2023-06-02 10:59:23,211 root DEBUG whgiven
2023-06-02 10:59:23,212 root DEBUG ---
2023-06-02 10:59:23,219 root DEBUG 100700 => 0101621b52fe590000000000f58274010101630402007605eb7e43006200620072630201710163617800001b1b1b1b1a01afde
2023-06-02 10:59:23,221 root DEBUG ---
2023-06-02 10:59:23,223 root DEBUG obisdata={'010800': 5369.200000000001, '020800': 562134.2000000001}
2023-06-02 10:59:23,224 root DEBUG OBIS 10.7.0 current power is missing
2023-06-02 10:59:23,226 root DEBUG values=False
2023-06-02 10:59:23,295 root DEBUG rawdata=False
2023-06-02 10:59:23,396 root DEBUG rawdata=False
````

OBIS 10.7.0 cannot be evaluated. This means that you have to adjust `Regex`. In the example above, the data could be evaluated with `Regex=^(?:..){2,}?62(.{2})52([0f].)([56])([2-9])((?:..){1,8})01` instead of `Regex=^(?:..){2,}?62(.{2})52([0f].)([56])([2-5])((?:..){1,4})01`
