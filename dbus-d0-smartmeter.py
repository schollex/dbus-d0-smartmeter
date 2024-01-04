#!/usr/bin/env python
 
# import normal packages
import logging
from logging.handlers import RotatingFileHandler
import sys
import struct
import os
import platform
if sys.version_info.major == 2:
    import gobject
else:
    from gi.repository import GLib as gobject
import sys
import time
import requests # for http GET
import configparser # for config/ini file

import serial
from re import match
from math import cos, pi

import signal
def signal_term_handler(signal, frame):
  logging.warning('got SIGTERM')
  smrtmtr_output._setConnected(0)
  exit(1)
signal.signal(signal.SIGTERM, signal_term_handler)


#import subprocess

obis = {
        # SML Protocol
        '100700': 'w',
        '240700': 'w_l1',
        '380700': 'w_l2',
        '4c0700': 'w_l3',
        '010800': 'wh',
        '020800': 'whgiven',
        '200700': 'v_l1',
        '340700': 'v_l2',
        '480700': 'v_l3',
        '1f0700': 'a_l1',
        '330700': 'a_l2',
        '470700': 'a_l3',
        '0e0700': 'hz',
        '510701': 'd_v2v1',
        '510702': 'd_v3v1',
        '510704': 'd_a1v1',
        '51070f': 'd_a2v2',
        '51071a': 'd_a3v3',
        # D0 Protocol
        '312e372e323535': 'w',
        '32312e372e323535': 'w_l1',
        '34312e372e323535': 'w_l2',
        '36312e372e323535': 'w_l3',
        '312e382e30': 'wh',
        '322e382e30': 'whgiven',
       }
calcs = {
         #'240700': 'cos(values[\'510704\']/180.0*pi)*values[\'200700\']*values[\'1f0700\']',
         #'380700': 'cos(values[\'51070f\']/180.0*pi)*values[\'340700\']*values[\'330700\']',
         #'4c0700': 'cos(values[\'51071a\']/180.0*pi)*values[\'480700\']*values[\'470700\']',
        }

crc16_x25_table = [
        0x0000, 0x1189, 0x2312, 0x329B, 0x4624, 0x57AD, 0x6536, 0x74BF,
        0x8C48, 0x9DC1, 0xAF5A, 0xBED3, 0xCA6C, 0xDBE5, 0xE97E, 0xF8F7,
        0x1081, 0x0108, 0x3393, 0x221A, 0x56A5, 0x472C, 0x75B7, 0x643E,
        0x9CC9, 0x8D40, 0xBFDB, 0xAE52, 0xDAED, 0xCB64, 0xF9FF, 0xE876,
        0x2102, 0x308B, 0x0210, 0x1399, 0x6726, 0x76AF, 0x4434, 0x55BD,
        0xAD4A, 0xBCC3, 0x8E58, 0x9FD1, 0xEB6E, 0xFAE7, 0xC87C, 0xD9F5,
        0x3183, 0x200A, 0x1291, 0x0318, 0x77A7, 0x662E, 0x54B5, 0x453C,
        0xBDCB, 0xAC42, 0x9ED9, 0x8F50, 0xFBEF, 0xEA66, 0xD8FD, 0xC974,
        0x4204, 0x538D, 0x6116, 0x709F, 0x0420, 0x15A9, 0x2732, 0x36BB,
        0xCE4C, 0xDFC5, 0xED5E, 0xFCD7, 0x8868, 0x99E1, 0xAB7A, 0xBAF3,
        0x5285, 0x430C, 0x7197, 0x601E, 0x14A1, 0x0528, 0x37B3, 0x263A,
        0xDECD, 0xCF44, 0xFDDF, 0xEC56, 0x98E9, 0x8960, 0xBBFB, 0xAA72,
        0x6306, 0x728F, 0x4014, 0x519D, 0x2522, 0x34AB, 0x0630, 0x17B9,
        0xEF4E, 0xFEC7, 0xCC5C, 0xDDD5, 0xA96A, 0xB8E3, 0x8A78, 0x9BF1,
        0x7387, 0x620E, 0x5095, 0x411C, 0x35A3, 0x242A, 0x16B1, 0x0738,
        0xFFCF, 0xEE46, 0xDCDD, 0xCD54, 0xB9EB, 0xA862, 0x9AF9, 0x8B70,
        0x8408, 0x9581, 0xA71A, 0xB693, 0xC22C, 0xD3A5, 0xE13E, 0xF0B7,
        0x0840, 0x19C9, 0x2B52, 0x3ADB, 0x4E64, 0x5FED, 0x6D76, 0x7CFF,
        0x9489, 0x8500, 0xB79B, 0xA612, 0xD2AD, 0xC324, 0xF1BF, 0xE036,
        0x18C1, 0x0948, 0x3BD3, 0x2A5A, 0x5EE5, 0x4F6C, 0x7DF7, 0x6C7E,
        0xA50A, 0xB483, 0x8618, 0x9791, 0xE32E, 0xF2A7, 0xC03C, 0xD1B5,
        0x2942, 0x38CB, 0x0A50, 0x1BD9, 0x6F66, 0x7EEF, 0x4C74, 0x5DFD,
        0xB58B, 0xA402, 0x9699, 0x8710, 0xF3AF, 0xE226, 0xD0BD, 0xC134,
        0x39C3, 0x284A, 0x1AD1, 0x0B58, 0x7FE7, 0x6E6E, 0x5CF5, 0x4D7C,
        0xC60C, 0xD785, 0xE51E, 0xF497, 0x8028, 0x91A1, 0xA33A, 0xB2B3,
        0x4A44, 0x5BCD, 0x6956, 0x78DF, 0x0C60, 0x1DE9, 0x2F72, 0x3EFB,
        0xD68D, 0xC704, 0xF59F, 0xE416, 0x90A9, 0x8120, 0xB3BB, 0xA232,
        0x5AC5, 0x4B4C, 0x79D7, 0x685E, 0x1CE1, 0x0D68, 0x3FF3, 0x2E7A,
        0xE70E, 0xF687, 0xC41C, 0xD595, 0xA12A, 0xB0A3, 0x8238, 0x93B1,
        0x6B46, 0x7ACF, 0x4854, 0x59DD, 0x2D62, 0x3CEB, 0x0E70, 0x1FF9,
        0xF78F, 0xE606, 0xD49D, 0xC514, 0xB1AB, 0xA022, 0x92B9, 0x8330,
        0x7BC7, 0x6A4E, 0x58D5, 0x495C, 0x3DE3, 0x2C6A, 0x1EF1, 0x0F78]
 
# our own packages from victron
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService

#from ve_utils import exit_on_error
from settingsdevice import SettingsDevice
from dbus import SystemBus, SessionBus
from traceback import print_exc
def exit_on_error(func, *args, **kwargs):
  try:
    return func(*args, **kwargs)
  except:
    try:
      print ('exit_on_error: there was an exception. Printing stacktrace will be tried and then exit')
      print_exc()
      smrtmtr_output._setConnected(0)
    except:
      pass
    # sys.exit() is not used, since that throws an exception, which does not lead to a program
    # halt when used in a dbus callback, see connection.py in the Python/Dbus libraries, line 230.
    os._exit(1)

def handle_changed_setting(setting, oldvalue, newvalue):
  logging.info('setting %s changed: %s => %s' % (setting, oldvalue, newvalue))

class DbusttysmartmeterService:
  def __init__(self, config, servicename, paths, productname='ttysmartmeter', connection='ttysmartmeter service'):
    #config = self._getConfig()
    accesstype = config['DEFAULT']['AccessType']
    self._protocol = config['DEFAULT']['Protocol']
    deviceinstance = int(config['DEFAULT']['Deviceinstance'])
    customname = config['DEFAULT']['CustomName']
    devicename = config[accesstype]['Devicename']
    deviceserialid = '/dev/serial/by-id/%s' %devicename
    devicepath = os.popen('readlink -f /dev/serial/by-id/%s' %devicename).read().replace('\n', '')
    ttyname = devicepath.replace('/dev/', '')
    os.system('/opt/victronenergy/serial-starter/stop-tty.sh %s' %ttyname)

    self._initialized = not (len(sys.argv) >= 2)
    logging.info("current initialized-state = %r" %self._initialized)

    devicebaudrate = int(config[accesstype]['Baudrate'])
    devicebytesize = int(config[accesstype]['Bytesize'])
    readinterval = int(config[accesstype]['ReadInterval'])
    self._timeoutInterval = int(config['DEFAULT']['TimeoutInterval'])
    self._exitOnTimeout = int(config['DEFAULT']['ExitOnTimeout'])
    exitAfterHours = float(config['DEFAULT']['ExitAfterHours'])
    self._eurPerKwh = float(config['DEFAULT']['EurPerKwh'])
    self._SMLregex = config['SML']['Regex']
    self._D0regex = config['D0']['Regex']
    self._postRawdata = int(config['DEFAULT']['PostRawdata'])
    self._changeSmartmeter = int(config['DEFAULT']['ChangeSmartmeter'])
    if self._changeSmartmeter:
      self._settings = SettingsDevice(
        bus=SystemBus() if (platform.machine() == 'armv7l') else SessionBus(),
        supportedSettings={
          'RunWithoutGridMeter': ['/Settings/CGwacs/RunWithoutGridMeter', 1, 0, 1],
        },
        eventCallback=handle_changed_setting
      )
      self._setConnected(0)

    # get len of real end characters and start, end, intro commands
    global hexcount, start, end, obisintro
    if self._protocol == 'SML':
        hexcount = 3
        start = '1b1b1b1b01010101'
        end = '1b1b1b1b1a'
        obisintro = '77070100'
    elif self._protocol == 'D0':
        hexcount = 2
        start = '2f'
        end = '21'
        obisintro='312d303a'

    logging.info("Opening %s" %devicepath)
    self._port = serial.Serial(
      port=devicepath,
      baudrate=devicebaudrate,
      parity=serial.PARITY_NONE,
      stopbits=serial.STOPBITS_ONE,
      bytesize=devicebytesize
    )
    self._port.reset_input_buffer()
    self._port.reset_output_buffer()

    # last update
    self._lastUpdate = time.time()
    self._stats = 0

    # tty-data
    self._rawdata = ''

    while not self._initialized:
      if self._update():
        self._initialized = True
        logging.info("received smartmeter-data - start DBUS initialization...")
      else:
        time.sleep(readinterval/1000)
    
    self._dbusservice = VeDbusService("{}.{}".format(servicename, devicename))
    self._paths = paths
    
    logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))
    
    # Create the management objects, as specified in the ccgx dbus-api document
    self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
    self._dbusservice.add_path('/Mgmt/ProcessVersion', 'Unkown version, and running on Python ' + platform.python_version())
    self._dbusservice.add_path('/Mgmt/Connection', connection)

    # Create the mandatory objects
    self._dbusservice.add_path('/DeviceInstance', deviceinstance)
    #self._dbusservice.add_path('/ProductId', 45069) # value used in ac_sensor_bridge.cpp of dbus-cgwacs
    self._dbusservice.add_path('/ProductId', 0xFFFF) # id assigned by Victron Support from SDM630v2.py
    self._dbusservice.add_path('/ProductName', productname)
    self._dbusservice.add_path('/CustomName', customname)    
    self._dbusservice.add_path('/Connected', 0)
    
    self._dbusservice.add_path('/Latency', None)    
    self._dbusservice.add_path('/FirmwareVersion', 0.1)
    self._dbusservice.add_path('/HardwareVersion', 0)
    self._dbusservice.add_path('/Position', 0) # normaly only needed for pvinverter
    self._dbusservice.add_path('/Serial', devicename)
    #self._dbusservice.add_path('/UpdateIndex', 0)
    self._dbusservice.add_path('/StatusCode', 0)  # Dummy path so VRM detects us as a PV-inverter.

    self._dbusservice.add_path('/Rawdata', '')  # Dummy path so VRM detects us as a PV-inverter.
    
    # add path values to dbus
    for path, settings in self._paths.items():
      self._dbusservice.add_path(
        path, settings['initial'], gettextcallback=settings['textformat'], writeable=True, onchangecallback=self._handlechangedvalue)

    # last update
    #self._lastUpdate = time.time()

    # tty-data
    #self._rawdata = ''

    # add _update function 'timer'
    gobject.timeout_add(readinterval, exit_on_error, self._update) # pause readlinterval before the next request
    
    # add _signOfLife 'timer' to get feedback in log every SignOfLifeLog minutes
    gobject.timeout_add(int(config['DEFAULT']['SignOfLifeLog'])*60*1000, self._signOfLife)
 
    # exit after hours?
    if exitAfterHours > 0:
      logging.info('exitAfterHours will stop this service after %0.1fh' %exitAfterHours)
      gobject.timeout_add(exitAfterHours*60*60*1000, exit_on_error, self._exit)

  def _setConnected(self, what):
    try:
      self._dbusservice['/Connected'] = what
      logging.info('changed /Connected to %d' %what)
    except:
      pass
    what = 1-what
    if self._changeSmartmeter:
      logging.info('changing RunWithoutGridMeter to %d' %what)
      self._settings['RunWithoutGridMeter'] = what

  def _exit(self):
    logging.info('exitAfterHours reached')
    raise Exception('exitAfterHours reached') 
  
  def _getTtyRawData(self):
    chars = self._port.read(self._port.inWaiting())
    for char in chars:
      self._rawdata += format(char, '02x')

    pos = self._rawdata.find(end)
    if (pos == -1) or (pos+len(end)+(hexcount*2) > len(self._rawdata)):
        return False
    data = self._rawdata[:pos+len(end)+(hexcount*2)]
    self._rawdata = self._rawdata[pos+len(end)+(hexcount*2):]
    pos = data.rfind(start)
    if (pos == -1):
        return False
    return data[pos:]
   

  # https://www.stefan-weigert.de/php_loader/sml.php
  def _validateChecksum(self, data):
    global crc16_x25_table
    data = bytes.fromhex(data)
    crc_rx = data[-1]*256 + data[-2] #CRC Bytes getauscht in eine Variable speichern
    crcsum = 0xffff
    for byte in data[0:-2]:
      crcsum = crc16_x25_table[(byte ^ crcsum) & 0xff] ^ (crcsum >> 8 & 0xff)
    crcsum ^= 0xffff
    return (crc_rx == crcsum)

  def _extractObisFromSMLRawData(self, data):
    values = {}
    for s in data.split(obisintro):
       value = None
       g = match('^(.{6})ff(.+)', s)
       if not g: continue
       (object, raw) = (g.group(1), g.group(2))
       # Groups: physical unit, scalar, signed or unsigned, value-length 2-5 repectivly 1-4 bytes, value itself
       #g2 = match('^(?:..){2,}?62(.{2})52([0f].)([56])([2-5])((?:..){1,4})01', raw)
       g2 = match(self._SMLregex, raw)
       if g2 and len(g2.group(5))/2 >= int(g2.group(4))-1:
         logging.debug([g2.group(1), g2.group(2), g2.group(3), g2.group(4), g2.group(5)])
         signed = (g2.group(3) == '5')
         extract = g2.group(5)[:(int(g2.group(4))-1)*2]
         factor = pow(10, int.from_bytes(bytes.fromhex(g2.group(2)), byteorder='big', signed=True))
         value = int.from_bytes(bytes.fromhex(extract), byteorder='big', signed=signed)*factor
         logging.debug(value)
       ###
       if not self._initialized:
         if object in obis:
           configured = obis[object]
         else:
           configured = 'unused'
         logging.info('received OBIS Code %s (%s)' %(object, configured))
       logging.debug(object + ' => ' + raw)
       if object in obis and value is not None:
         values[object] = value
         logging.debug(obis[object])
       logging.debug('---')
    #for k in calcs.keys():
    #  if k in values:
    #    continue
    #  try:
    #    values[k] = eval(calcs[k])
    #  except:
    #    logging.debug('could not evaluate %s' %k)

    return values

  def _extractObisFromD0RawData(self, data):
    values = {}
    for s in data.split(obisintro):
       value = None
       g = match(self._D0regex, s)
       if not g: continue
       (object, raw) = (g.group(1), g.group(2))
       # Groups: obis, value itself, physical unit
       if bytes.fromhex(g.group(3)).decode('utf-8') == '*W':
          value = int(float(bytes.fromhex(g.group(2)).decode('utf-8')))
       elif bytes.fromhex(g.group(3)).decode('utf-8') == '*kWh':
          value = float(bytes.fromhex(g.group(2)).decode('utf-8'))
       logging.debug(value)

       ###
       if not self._initialized:
         if object in obis:
           configured = obis[object]
         else:
           configured = 'unused'
         logging.info('received OBIS Code %s (%s)' %(object, configured))
       logging.debug(object + ' => ' + raw)
       if object in obis and value is not None:
         values[object] = value
         logging.debug(obis[object])
       logging.debug('---')

    return values

  def _convertD0ObisToValues(self, values):
    if '312e372e323535' not in values:
      logging.warning('OBIS Code 312e372e323535 (power) is missing')
      return False
    try:
      ret = {
        '/Ac/Power': values['312e372e323535'],
        '/Ac/Energy/Forward': values['312e382e30'],
        '/Ac/Energy/Reverse': values['322e382e30'],

        '/Ac/L2/Energy/Forward': round(values['322e382e30']*self._eurPerKwh, 2),
        '/Ac/L3/Energy/Forward': values['322e382e30'],

        '/Ac/L1/Voltage': 230,
        '/Ac/L2/Voltage': 230,
        '/Ac/L3/Voltage': 230,
        '/Ac/L1/Current': round(values['32312e372e323535']/230, 0),
        '/Ac/L2/Current': round(values['34312e372e323535']/230, 0),
        '/Ac/L3/Current': round(values['36312e372e323535']/230, 0),
        '/Ac/L1/Power': values['32312e372e323535'],
        '/Ac/L2/Power': values['34312e372e323535'],
        '/Ac/L3/Power': values['36312e372e323535'],
      }
      logging.debug('%s' %ret)
    except Exception as e:
      logging.debug('Error at _convertD0ObisToValues', exc_info=e)
      return False
    self._stats = self._stats+1
    return ret

  def _convertSMLObisToValues(self, values):
    if '100700' not in values:
      logging.warning('OBIS Code 100700 (power) is missing')
      return False
    try:
      if not ('240700' in values and '380700' in values and '4c0700' in values):
        try:
          values['240700'] = cos(values['510704']/180*pi)*values['200700']*values['1f0700']
          values['380700'] = cos(values['51070f']/180*pi)*values['340700']*values['330700']
          values['4c0700'] = cos(values['51071a']/180*pi)*values['480700']*values['470700']
        except:
          wthird = values['100700']/3
          values['240700'], values['380700'], values['4c0700'] = wthird, wthird, wthird
      thirddiff = (values['100700']-(values['240700']+values['380700']+values['4c0700']))/3
      ret = {
        '/Ac/Power': round(values['100700'], 1),
        '/Ac/Energy/Forward': '010800' in values and round(values['010800']/1000, 1) or None,
        '/Ac/Energy/Reverse': '020800' in values and round(values['020800']/1000, 1) or None,
        #'/Ac/L1/Energy/Forward': 0,
        #'/Ac/L2/Energy/Forward': 0,
        '/Ac/L2/Energy/Forward': '020800' in values and round(values['020800']/1000*self._eurPerKwh, 2) or None,
        #'/Ac/L3/Energy/Forward': 0,
        '/Ac/L3/Energy/Forward': '020800' in values and round(values['020800']/1000, 1) or None,
        #'/Ac/Energy/Reverse': 0,
        #'/Ac/L1/Energy/Reverse': 0,
        #'/Ac/L2/Energy/Reverse': 0,
        #'/Ac/L3/Energy/Reverse': 0,
        '/Ac/L1/Voltage': '200700' in values and round(values['200700'], 1) or None,
        '/Ac/L2/Voltage': '340700' in values and round(values['340700'], 1) or None,
        '/Ac/L3/Voltage': '480700' in values and round(values['480700'], 1) or None,
        '/Ac/L1/Current': '1f0700' in values and round(values['1f0700'], 2) or None,
        '/Ac/L2/Current': '330700' in values and round(values['330700'], 2) or None,
        '/Ac/L3/Current': '470700' in values and round(values['470700'], 2) or None,
        '/Ac/L1/Power': round(values['240700']+thirddiff, 1),
        '/Ac/L2/Power': round(values['380700']+thirddiff, 1),
        '/Ac/L3/Power': round(values['4c0700']+thirddiff, 1),
      }
    except Exception as e:
      logging.debug('Error at _convertSMLObisToValues', exc_info=e)
      return False
    self._stats = self._stats+1
    return ret
 
 
  def _signOfLife(self):
    logging.info("Got %d measurements, last _update() call: %d" % (self._stats, self._lastUpdate))
    self._stats = 0
    #logging.info("Last '/Ac/Power': %s" % (self._dbusservice['/Ac/Power']))
    return True
 
  def _update(self):
    news = False
    try:
      # get data from ttysmartmeter
      rawdata = self._getTtyRawData()
      logging.debug('rawdata=%s' %rawdata)
      if rawdata:
        if self._protocol == 'SML':
            # use SML Protocol
            if self._validateChecksum(rawdata):
                # extract obis from rawdata
                obisdata = self._extractObisFromSMLRawData(rawdata)
                logging.debug('obisdata=%s' %obisdata)
                if obisdata:
                    # convert obis to usable values
                    values = self._convertSMLObisToValues(obisdata)
                    logging.debug('values=%s' %values)
            else:
                logging.info('checksum failed for rawdata=%s' %rawdata)
        elif self._protocol == 'D0':
            # use D0 Protocol
            obisdata = self._extractObisFromD0RawData(rawdata)
            logging.debug('obisdata=%s' %obisdata)
            if obisdata:
                # convert obis to usable values
                values = self._convertD0ObisToValues(obisdata)
                logging.debug('values=%s' %values)

        if values:
            # real power meter data were received
            if not self._initialized:
                return True
            if self._postRawdata:
                values['/Rawdata'] = rawdata
            for k in values:
                self._dbusservice[k] = values[k]
            if self._dbusservice['/Connected'] == 0:
                logging.info('smartmeter-data received')
                self._setConnected(1)
            self._lastUpdate = time.time()
            news = True

      #if self._lastUpdate+self._timeoutInterval/1000 < time.time():
      #  #raise ConnectionError('No correct data received')
      #  logging.debug('No correct data received')
       
    except Exception as e:
       logging.critical('Error at _update', exc_info=e)

    # is the timeout exceeded
    if self._lastUpdate+self._timeoutInterval/1000 < time.time():
      if not self._initialized or self._dbusservice['/Connected'] == 1:
        if self._initialized:
          self._setConnected(0)
        logging.warning('no smartmeter-data received since %d ms' %self._timeoutInterval)
        news = True
      if self._exitOnTimeout:
        logging.warning('...exiting due to missing smartmeter-data since %d ms' %self._timeoutInterval)
        raise Exception('Exception due to missing smartmeter-data since %d ms' %self._timeoutInterval)

    #if news:
    #   # increment UpdateIndex - to show that new data is available
    #   self._dbusservice['/UpdateIndex'] = (self._dbusservice['/UpdateIndex']+1)%256  # increment index
 
    # return true, otherwise add_timeout will be removed from GObject - see docs http://library.isr.ist.utl.pt/docs/pygtk2reference/gobject-functions.html#function-gobject--timeout-add
    return self._initialized
 
  def _handlechangedvalue(self, path, value):
    logging.debug("someone else updated %s to %s" % (path, value))
    return True # accept the change
 


def main():

  config = configparser.ConfigParser()
  config.read("%s/config.ini" % (os.path.dirname(os.path.realpath(__file__))))

  global smrtmtr_output, logging
  logging.basicConfig(      format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            #level=logging.DEBUG,
                            level=config['DEFAULT']['Logging'],
                            handlers=[
                                #logging.FileHandler("%s/current.log" % (os.path.dirname(os.path.realpath(__file__)))),
                                RotatingFileHandler('%s/current.log' % (os.path.dirname(os.path.realpath(__file__))), maxBytes=1000000, backupCount=3),
                                logging.StreamHandler()
                            ])
 
  try:
      logging.info("Starting...");
  
      from dbus.mainloop.glib import DBusGMainLoop
      # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
      DBusGMainLoop(set_as_default=True)

      #formatting 
      _kwh = lambda p, v: (str(round(v, 2)) + 'KWh')
      _a = lambda p, v: (str(round(v, 1)) + 'A')
      _w = lambda p, v: (str(round(v, 1)) + 'W')
      _v = lambda p, v: (str(round(v, 1)) + 'V')   

      #start our main-service
      smrtmtr_output = DbusttysmartmeterService(
        config=config,
        servicename='com.victronenergy.grid',
        paths={
          '/Ac/Energy/Forward': {'initial': None, 'textformat': _kwh}, # energy produced by pv inverter
          '/Ac/Energy/Reverse': {'initial': 0, 'textformat': _kwh}, # energy produced by pv inverter
          '/Ac/Power': {'initial': 0, 'textformat': _w},
          
          '/Ac/Current': {'initial': 0, 'textformat': _a},
          '/Ac/Voltage': {'initial': 0, 'textformat': _v},
          
          '/Ac/L1/Voltage': {'initial': 0, 'textformat': _v},
          '/Ac/L2/Voltage': {'initial': 0, 'textformat': _v},
          '/Ac/L3/Voltage': {'initial': 0, 'textformat': _v},
          '/Ac/L1/Current': {'initial': 0, 'textformat': _a},
          '/Ac/L2/Current': {'initial': 0, 'textformat': _a},
          '/Ac/L3/Current': {'initial': 0, 'textformat': _a},
          '/Ac/L1/Power': {'initial': 0, 'textformat': _w},
          '/Ac/L2/Power': {'initial': 0, 'textformat': _w},
          '/Ac/L3/Power': {'initial': 0, 'textformat': _w},
          '/Ac/L1/Energy/Forward': {'initial': None, 'textformat': _kwh},
          '/Ac/L2/Energy/Forward': {'initial': None, 'textformat': _kwh},
          '/Ac/L3/Energy/Forward': {'initial': None, 'textformat': _kwh},
          '/Ac/L1/Energy/Reverse': {'initial': None, 'textformat': _kwh},
          '/Ac/L2/Energy/Reverse': {'initial': None, 'textformat': _kwh},
          '/Ac/L3/Energy/Reverse': {'initial': None, 'textformat': _kwh},
        })

      logging.info('Connected to dbus, and switching over to gobject.MainLoop() (= event based)')
      mainloop = gobject.MainLoop()
      mainloop.run()            
  except Exception as e:
    logging.critical('Error at %s', 'main', exc_info=e)
  finally:
    smrtmtr_output._setConnected(0)
if __name__ == "__main__":
  main()
