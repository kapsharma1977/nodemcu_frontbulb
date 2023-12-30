class env:
    def __init__(self, rtc, STA_AP):
        self.rtc = rtc
        self.month = ''
        self.week = {}
        self.sr_h = 0
        self.sr_m = 0
        self.ss_h = 0
        self.ss_m = 0
        self.updated = False
        self.startmonth = ''
        self.ntp_poll = 0 #60*60/env.SLEEP
        self.STA_AP = STA_AP
        self.pass_ch = 0
    def update(self):
        self.month = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec",][list(self.rtc.datetime())[1] - 1]
        if not self.updated:
            import ujson
            from env_static import loadweek, sunrise, sunset, json_savetofile
            loadweek(self.week)
            sr_dict = sunrise(self.month)
            self.sr_h = sr_dict['h']
            self.sr_m = sr_dict['m']
            ss_dict = sunset(self.month)
            self.ss_h = ss_dict['h']
            self.ss_m = ss_dict['m']
            self.startmonth = self.month
            _jsonstr = ujson.dumps(list(self.rtc.datetime()))
            json_savetofile('time.json',_jsonstr)
            self.updated = True
        if self.month != self.startmonth:
            from env_static import sunrise, sunset
            sr_dict = sunrise(self.month)
            self.sr_h = sr_dict['h']
            self.sr_m = sr_dict['m']
            ss_dict = sunset(self.month)
            self.ss_h = ss_dict['h']
            self.ss_m = ss_dict['m']
    def sleepornap(self, sleep = 5,nap = 3):
        date = self.rtc.datetime()
        h = date[4]
        if h <= self.sr_h: # midnight
            if self.sr_h - h > 2:
                return sleep
            else:
                return nap
        else:
            if h <= self.ss_h:
                if self.ss_h - h > 2:
                    return sleep
                else:
                    return nap
            else:
                return sleep
    def clocksync(self, wlan, seconds = 3600):
        if self.ntp_poll <= 0:
            from env_static import initializeRTC
            if not initializeRTC(wlan, self.rtc):
                    print("=== RTC not Init \n")
            self.update()
            self.ntp_poll = seconds/self.sleepornap()
            #print(f"\n ntp_poll_0 = {self.ntp_poll} time  H:{list(self.rtc.datetime())[4]} M:{list(self.rtc.datetime())[5]} S:{list(self.rtc.datetime())[6]}")
        else:
            self.ntp_poll = self.ntp_poll - 1
            #print(f"ntp_poll = {self.ntp_poll} time  H:{list(self.rtc.datetime())[4]} M:{list(self.rtc.datetime())[5]} S:{list(self.rtc.datetime())[6]}")
    def isevening(self):
        self.update()
        date = list(self.rtc.datetime())
        if date[4] == self.ss_h:
            if date[5] == self.ss_m:
                return True
            else:
                if date[5] < self.ss_m:
                    return False
                else:
                    return True
        else:
            if date[4] > self.ss_h:
                return True
            else:
                if date[4] == self.sr_h:
                    if date[5] == self.sr_m:
                        return False
                    else:
                        if date[5] < self.sr_m:
                            return True
                        else:
                            return False
                else:
                    if date[4] < self.sr_h:
                        return True
                    else:
                        return False
    def ismorning(self):
        self.update()
        date = list(self.rtc.datetime())
        if date[4] == self.sr_h:
            if date[5] == self.sr_m:
                return True
            else:
                if date[5] < self.sr_m:
                    return False
                else:
                    return True
        else:
            if date[4] < self.sr_h:
                return False
            else:
                if date[4] == self.ss_h:
                    if date[5] == self.ss_m:
                        return False
                    else:
                        if date[5] < self.ss_m:
                            return True
                        else:
                            return False
                else:
                    if date[4] < self.ss_h:
                        return True
                    else:
                        return False
    def _midnighttosunrise(self):
        self.update()
        date = list(self.rtc.datetime())
        h = date[4]
        m = date[5]
        if h <= self.sr_h:
            if h == self.sr_h:
                if m >= self.sr_m:
                    return False
                else:
                    return True
            else:
                return True
        else:
            return False
    def is_bulbturn_day(self):
        self.update()
        date = list(self.rtc.datetime())
        if self._midnighttosunrise():
            if date[3] == 0:
                previous_day = "6"
            else:
                previous_day = str(date[3] - 1)
            if previous_day in self.week:
                if self.week[previous_day] != '':
                    return True
                else:
                    return False
            else:
                print(f'previous day is not in week: {previous_day}')
        else:
            if str(date[3]) in self.week:
                if self.week[str(date[3])] != '':
                    return True
                else:
                    return False
    def w_notconnected(self,wlan,rtc,fb: bulb,vne: env, tmo_count=100):
        import machine, network, utime
        
        if self.STA_AP == 'STA_IF':
            if not wlan.active():
                wlan.active(True)
            from env_static import getsidpaswd
            import utime
            _json = getsidpaswd()
            wlan.connect(_json['ssid'], _json['paswd'])
            tmo = tmo_count
            while not wlan.isconnected():
                utime.sleep_ms(100)
                tmo -= 1
                if tmo == 0:
                    break
            if tmo != 0:
                print("=== Station Connected to WiFi \n")
                config = wlan.ifconfig()
                print("IP:{0}, Network mask:{1}, Router:{2}, DNS: {3}".format(*config))
                utime.sleep_ms(1000)
                from env_static import initializeRTC
                if not initializeRTC(wlan, rtc):
                    print("=== RTC not Init \n")
                    wlan.disconnect()
                    return False
                vne.update()
                utime.sleep_ms(100)
                return True
            else:
                self.STA_AP = 'AP_IF'
        if self.STA_AP == 'AP_IF':
            from utime import sleep_ms
            from config import AP_IP,ESSID,PASS_ESSID
            wlan.active(False)
            #wlan.disconnect()
            fb.relaysoff()
            utime.sleep_ms(200)
            print("led D1={0} D2={1}".format(fb.D1.value(),fb.D2.value()))
            wlan = network.WLAN(network.AP_IF)
            ap_c = 100
            while wlan.active() == False:
                utime.sleep_ms(100)
                ap_c -= 1
                if ap_c == 0:
                    self.STA_AP = 'STA_IF'
                    machine.reset()
            print(f"ap_c = {ap_c}")
            wlan.config(essid=ESSID, password=PASS_ESSID)
            wlan.ifconfig(AP_IP)
            print("=== Station Access Point \n")
            config = wlan.ifconfig()
            print("IP:{0}, Network mask:{1}, Router:{2}, DNS: {3}".format(*config))
            return True
        return False