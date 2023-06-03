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


| Config value        | Explanation   |
|-------------------- | ------------- |
| Logging | set loglevel for `current.log` respectivly `/var/log/dbus-d0-smartmeter/current.log`. Possible values among others are `DEBUG`, `INFO`, `WARING` |
| SignOfLiveLog | if >0, interval in minutes to give stats (= number of received correct SML-data) |
| CustomName | user-friendly name for the gridmeter within the Venus web-GUI |
| TimeoutInterval | if no valid data is received within this millisencods-interval, the DBUS-service-property Connected will be set to 0 |
| ExitOnTimeout | if set to `1` instead of `0`, the script will terminate itself which erases service from DBUS. This is indicated as "not connected" within the web-GUI |
| ExitAfterHours | if >0. the script will terminate itself after these hours |
| ChangeSmartmeter | if set to `1` instead of `0`, DBUS-property com.victronenergy.settings/Settings/CGwacs/RunWithoutGridMeter respectivly the web-GUI-setting Settings > ESS > Grid Metering is changed. If { no } grid metering can be done, property is set to `1` { `0` } respectivly GUI to `Inverter/Charger` { `External meter` }. Without this, e.g. if grid metering is stall, ESS would work on old power-assumptions. If set to `External meter` and the battery is fully charged, Victron OS would stop MPPT from producing power. With setup `Inverter/Charger`, MPPT is still producing power which is completly fed in to AC by Multiplus. |
| PostRawdata | if set to `1` instead of `0`, SML-rawdata is post to DBUS-gridmeter-property `/rawdata` |
| Regex | Here is the magic. See Debugging-section below. |
| ReadInterval within [USB]-Section | millisecond-interval the script reads data from TTY. This should be obviously <1000. Otherwise, the TTY-buffer would fill up resulting in outdated data |
| Devicename within [USB]-Section | provides the correct name listed within /dev/serial/by-id/. This TTY is only used when the scipt is manually started without command-line-arguments. |

You have to set the `DEV`-variable within `service/run` to your USB-TTY-adapter. E.g. for me, it's `DEV='/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0'`. Because `service/run` will identify the corresponding /dev/ttyUSB-device, stop the serial-starter for this TTY and start the script with this TTY as command-line-argument.
 
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
2023-06-03 06:07:30,107 root DEBUG 600100 => 010101010b0a01445a4700016e70f501
2023-06-03 06:07:30,109 root DEBUG ---
2023-06-03 06:07:30,110 root DEBUG ['1e', 'ff', '6', '3', 'd5ba']
2023-06-03 06:07:30,111 root DEBUG 5471.400000000001
2023-06-03 06:07:30,113 root DEBUG 010800 => 641c21047262016417fd30621e52ff63d5ba01
2023-06-03 06:07:30,114 root DEBUG wh
2023-06-03 06:07:30,115 root DEBUG ---
2023-06-03 06:07:30,117 root DEBUG ['1e', 'ff', '6', '4', '598acd']
2023-06-03 06:07:30,118 root DEBUG 586823.7000000001
2023-06-03 06:07:30,119 root DEBUG 020800 => 017262016417fd30621e52ff64598acd01
2023-06-03 06:07:30,120 root DEBUG whgiven
2023-06-03 06:07:30,121 root DEBUG ---
2023-06-03 06:07:30,125 root DEBUG 100700 => 0101621b52fe59000000000004d85f01010163bd0100760536a6460[...]
2023-06-03 06:07:30,128 root DEBUG ---
2023-06-03 06:07:30,129 root DEBUG obisdata={'010800': 5471.400000000001, '020800': 586823.7000000001}
2023-06-03 06:07:30,131 root WARNING OBIS 10.7.0 current power is missing
2023-06-03 06:07:30,204 root DEBUG rawdata=False
2023-06-03 06:07:30,305 root DEBUG rawdata=False
[...]
````

OBIS 10.7.0 cannot be evaluated. This means that you have to adjust `Regex`. In the example above, the data could be evaluated with `Regex=^(?:..){2,}?62(.{2})52([0f].)([56])([2-9])((?:..){1,8})01` instead of `Regex=^(?:..){2,}?62(.{2})52([0f].)([56])([2-5])((?:..){1,4})01`

Why?
(For explanation on OBIS, see https://www.stefan-weigert.de/php_loader/sml.php)

This ...`f50177070100010800ff641c21047262016417fd30621e52ff63d5ba0177070100020800ff017262016417fd30621e52ff64598acd0177070100100700ff0101621b52fe59000000000004d85f01010163bd0100760536a6460`... is the relevant extract of rawdata.
Splitting is done on `77070100` which leads to
````
f501
77070100
010800ff641c21047262016417fd30621e52ff63d5ba01
77070100
020800ff017262016417fd30621e52ff64598acd01
77070100
100700ff0101621b52fe59000000000000d85f01010163bd0100760536a6460
````
We want to analyse the last element `100700ff0101621b52fe59000000000000d85f01010163bd0100760536a6460`:
`01` and `01` are the first 2 elements in this structure. They have a minimum length of 2 bytes (regex `^(?:..){2,}?`).
The next element is always unsigned `6` and the data-part is 1 byte `2`: `1b` (regex `62(.{2})`) - this is the physical unit.
The value itself has an power-10-exponent which is always signed `5` and the data-part is always 1 byte `2`: `fe` = -2 (regex `52([0f].)`).
The value itself is signed `5` and the data-part are 8 bytes `9`: `000000000000d85f` = 55391. Regex was `([56])([2-5])((?:..){1,4})` which will not match her. But regex 
`([56])([2-9])((?:..){1,8})` will match. After the value, the data-structure ends with `01` (regex `01`). But in this example, further bytes follow because this was the last OBIS-data.
The real value ist 55391*10^(-2) W = 553.91 W

If you have to modify the regex, take care of the match-groups. These match-groups

* physical unit
* power-10-exponent
* sign of value
* length of value
* value itself

must remain. Regex-hint: `(?:` is not the beginning of a match-group!
For rare situations where the value-match-group contains too much bytes, there is a logic built in the script that truncates the value-bytes according to "length of value".
