# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import os, machine
#os.dupterm(None, 1) # disable REPL on UART(0)
import gc
#import webrepl
#webrepl.start()

import network
import ntptime
from machine import Pin, RTC # import RTC from machine
import utime

from time import sleep
try:
  import usocket as socket
except:
  import socket
import network
import esp, ujson, uio, ubinascii
from micropython import const

# Wifi SSID and Password
SSID="Jiya"
PASS="9971989772"
PASSFILE = 'paswd.json'

# Time slice for sleep
SLEEPSECONDS = const(0.5) #59
# pins 0, 2, 4, 5, 12, 13, 14, 15, and 16
_D0GPIO16 = const(16) # doesn't support pull Pin.PULL_UP. OnBoard LED switch on after call off(). HIGH at boot, used to wake up from deep sleep
_D1GPIO5 = const(5) # OK, often used as SCL (I2C)
_D2GPIO4 = const(4) # OK, often used as SCL (I2C)
_D3GPIO0 = const(0) # pulled up, connected to FLASH button, boot fails if pulled LOW
_D4GPIO2 = const(2) # ONBOARDLED,pulled up, HIGH at boot, connected to on-board LED, boot fails if pulled LOW
_D5GPIO2 = const(14) # OK, SPI (SCLK)
_D6GPIO12 = const(12) # OK, SPI (MISO)
_D7GPIO5 = const(13) # OK, SPI (MOSI)
_D8GPIO12 = const(15) # pulled to GND, pulled to GND

# dictionary that maps string date names to indexes in the RTC's datetime tuple
DATETIME_ELEMENTS = {
    "year": 0,
    "month": 1,
    "day": 2,
    "day_of_week": 3,
    "hour": 4,
    "minute": 5,
    "second": 6,
    "millisecond": 7
}
#India is 5.30 hours ahead of GMT
_GMTHOURINDIA = const(5)
_GMTMINUTESINDIA = const(30)
sunrise = {
            "Jan":{'h':7,'m':0}
            ,"Feb":{'h':6,'m':30}
            ,"Mar":{'h':6,'m':30}
            ,"Apr":{'h':6,'m':0}
            ,"May":{'h':6,'m':0}
            ,"Jun":{'h':5,'m':30}
            ,"Jul":{'h':5,'m':30}
            ,"Aug":{'h':5,'m':30}
            ,"Sep":{'h':6,'m':0}
            ,"Oct":{'h':6,'m':0}
            ,"Nov":{'h':6,'m':30}
            ,"Dec":{'h':7,'m':0}
        }
sunset = {
            "Jan":{'h':17,'m':30}
            ,"Feb":{'h':18,'m':0}
            ,"Mar":{'h':18,'m':30}
            ,"Apr":{'h':18,'m':30}
            ,"May":{'h':19,'m':0}
            ,"Jun":{'h':19,'m':0}
            ,"Jul":{'h':19,'m':0}
            ,"Aug":{'h':19,'m':0}
            ,"Sep":{'h':18,'m':30}
            ,"Oct":{'h':18,'m':0}
            ,"Nov":{'h':17,'m':30}
            ,"Dec":{'h':17,'m':30}
        }
# set an element of the RTC's datetime to a different value GMT +5:30
def set_datetime_element(rtc, h=_GMTHOURINDIA, m=_GMTMINUTESINDIA): # India Calcuta GMT +5:30 
    date = list(rtc.datetime())
    date[DATETIME_ELEMENTS["hour"]] = date[DATETIME_ELEMENTS["hour"]] + h
    date[DATETIME_ELEMENTS["minute"]] = date[DATETIME_ELEMENTS["minute"]] + m
    rtc.datetime(date)
def wlanconnect(wlan):
    # wlan.config(dhcp_hostname="foo-bar-baz")
    wlan.active(True)
    wlan.connect(SSID, PASS)
    # Note that this may take some time, so we need to wait
    # Wait 5 sec or until connected
    tmo = 50
    while not wlan.isconnected():
        utime.sleep_ms(300)
        tmo -= 1
        if tmo == 0:
            break
    # check if the station is connected to an AP
    if wlan.isconnected():
        print("=== Station Connected to WiFi \n")
        config = wlan.ifconfig()
        print("IP:{0}, Network mask:{1}, Router:{2}, DNS: {3}".format(*config))
        utime.sleep_ms(100)
        return True
    else:
        return False

def initializeRTC():
    if wlan.isconnected():
        ntptime.settime() # set the RTC's time using ntptime # this queries the time from an NTP server
        return True
    else:
        return False
def free(full=False):
  gc.collect()
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))
esp.osdebug(None)
gc.collect()
rtc = RTC()
# Create Pins
D1 = Pin(_D1GPIO5, Pin.OUT, value=1)
D2 = Pin(_D2GPIO4, Pin.OUT, value=1)
# create station interface - Standard WiFi client
wlan = network.WLAN(network.STA_IF)