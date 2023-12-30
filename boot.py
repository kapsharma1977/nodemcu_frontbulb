import os, machine, gc,network, esp, uio, uselect
from machine import RTC, Timer
import utime
from time import sleep
try:
  import usocket as socket
except:
  import socket
esp.osdebug(None)
gc.collect()
rtc = RTC()
wlan = network.WLAN()