import os, machine, gc, network, ntptime, esp, ujson, uio
from machine import Pin, RTC
import utime
from time import sleep
try:
  import usocket as socket
except:
  import socket
def set_datetime_element(rtc, h=5, m=30):
    date = list(rtc.datetime())
    date[4] = date[4] + h
    date[5] = date[5] + m
    rtc.datetime(date)
def initializeRTC():
    if wlan.isconnected():
        ntptime.settime()
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
wlan = network.WLAN(network.STA_IF)