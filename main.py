from frontgateblub import bulb
PASSWORD = '/password'
EVENODDALL ='/evenodd'
def wlandisconnect(fb):
    fb.relaysoff()
    utime.sleep_ms(200)
def json_savetofile(fname,jsondata):
    with open(fname, 'w') as fd:
        ujson.dump(jsondata, fd)
def json_getfromfile(fname):
    with open(fname, 'r') as fd:
        return ujson.load(fd)
def parse_params(part):
    parameters = {}
    for piece in part.split(" "):
        if "/?" in piece:
            piece = piece.replace("/?", "")
            amp_split = piece.split("&")
            for param_set in amp_split:
                eq_split = param_set.split("=")
                parameters[eq_split[0]] = eq_split[1]
    return parameters
class env:
    def __init__(self):
        self.month = ''
        self.week = {}
        self.today = ''
        self.sr_h = 0
        self.sr_m = 0
        self.ss_h = 0
        self.ss_m = 0
        self.updated = False
        self.startmonth = ''
    def update(self,rtc):
        self.month = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec",][list(rtc.datetime())[1] - 1]
        self.today = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][list(rtc.datetime())[3]]
        if not self.updated:
            self.loadweek()
            utime.sleep_ms(100)
            self.sunrise()
            utime.sleep_ms(100)
            self.sunset()
            utime.sleep_ms(100)
            self.startmonth = self.month
            _jsonstr = ujson.dumps(list(rtc.datetime()))
            json_savetofile('time.json',_jsonstr)
            utime.sleep_ms(100)
            self.updated = True
        if self.month != self.startmonth:
            self.sunrise()
            self.sunset()
    def isevening(self,rtc):
        self.update(rtc)
        date = list(rtc.datetime())
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
    def ismorning(self,rtc):
        self.update(rtc)
        date = list(rtc.datetime())
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
    def timestring(self,rtc):
        date = list(rtc.datetime())
        return "%s, %02d %s %04d, %02d:%02d:%02d, %s" % (
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][date[3]],date[2],
        ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec",][date[1] - 1],
        date[0],date[4],date[5],date[6],"+5:30",)
    def _midnighttosunrise(self):
        self.update(rtc)
        date = list(rtc.datetime())
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
    def is_bulbturn_day(self,rtc):
        self.update(rtc)
        date = list(rtc.datetime())
        if self._midnighttosunrise():
            if date[3] == 0:
                previous_day = "Sun"
            else:
                previous_day = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][date[3] - 1]
            if previous_day in self.week:
                if self.week[previous_day] == 1:
                    return True
                else:
                    return False
            else:
                print(f'previous day is not in week: {previous_day}')
        else:
            if self.today in self.week:
                if self.week[self.today] == 1:
                    return True
                else:
                    return False
    
    def sunrise(self):
        try:
            _jsonstr = json_getfromfile('sunrise.json')
            _json = ujson.loads(_jsonstr)
            self.sr_h = _json[self.month]['h']
            self.sr_m = _json[self.month]['m']
        except Exception as e:
            import sys
            sys.print_exception(e)
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
            self.sr_h = sunrise[self.month]['h']
            self.sr_m = sunrise[self.month]['m']
            _jsonstr = ujson.dumps(sunrise)
            json_savetofile('sunrise.json',_jsonstr)
    def sunset(self):
        try:
            _jsonstr = json_getfromfile('sunset.json')
            _json = ujson.loads(_jsonstr)
            self.ss_h = _json[self.month]['h']
            self.ss_m = _json[self.month]['m']
        except Exception as e:
            import sys
            sys.print_exception(e)
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
            self.ss_h = sunset[self.month]['h']
            self.ss_m = sunset[self.month]['m']
            _jsonstr = ujson.dumps(sunset)
            json_savetofile('sunset.json',_jsonstr)
    def loadweek(self):
        try:
            _jsonstr = json_getfromfile('week.json')
            self.week = ujson.loads(_jsonstr)
            #print(f"at load {self.week}")
        except Exception as e:
            import sys
            sys.print_exception(e)
            self.week = {'1':'Mon', '2':'Tue', '3':'Wed', '4':'Thu', '5':'Fri', '6':'Sat', '7':'Sun'}
            _jsonstr = ujson.dumps(self.week)
            json_savetofile('week.json',jsondata=_jsonstr)
    def updatedays_selection(self,params):
        for key in self.week:
            self.week[key] = ''
        for key in params:
            if key in self.week:
                self.week[key] = params[key]
        _jsonstr = ujson.dumps(self.week)
        json_savetofile('week.json',jsondata=_jsonstr)
    def daysstr_turn(self):
        wk = []
        for key in self.week:
            wk.append(int(key))
        wk.sort()
        dstr = ''
        for ikey in wk:
            if self.week[str(ikey)] != '':
                dstr = dstr + self.week[str(ikey)] + ' '
        return dstr
    def _getsidpaswd(self):
        try:
            _jsonstr = json_getfromfile('paswd.json')
            return ujson.loads(_jsonstr)
        except:
            self.u_sidpaswd({"ssid":"Jiya","paswd":"9971989772"})
            return {"ssid":"Jiya","paswd":"9971989772"}
    def u_sidpaswd(self,params):
        _jsonstr = ujson.dumps(params)
        json_savetofile('paswd.json',jsondata=_jsonstr)
    def w_notconnected(self,wlan):
        if not wlan.active():
            wlan.active(True)
        _json = self._getsidpaswd()
        wlan.connect(_json['ssid'], _json['paswd'])
        tmo = 50
        while not wlan.isconnected():
            utime.sleep_ms(100)
            tmo -= 1
            if tmo == 0:
                break
        if tmo != 0:
            return True
        else:
            return False
##
vne = env()
frontbulb = bulb()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    s.bind(('', 80))
except Exception as e:
    import sys
    sys.print_exception(e)
s.listen(5)
while True:
    if not wlan.isconnected():
        print('Blub ESP8266 is not Conneted to Wifi')
        W = vne.w_notconnected(wlan)
        if not W:
            print("!!! Not able to connect to WiFi")
            wlandisconnect(frontbulb)
            print("led D1={0} D2={1}".format(frontbulb.D1.value(),frontbulb.D2.value()))
            utime.sleep_ms(2000)
            continue
        else:
            initializeRTC()
            set_datetime_element(rtc)
            print("=== Station Connected to WiFi \n")
            config = wlan.ifconfig()
            print("IP:{0}, Network mask:{1}, Router:{2}, DNS: {3}".format(*config))
            vne.update(rtc)
            utime.sleep_ms(100)
    else:
        gc.collect()
        frontbulb.updaterelays(is_bulbturnday = vne.is_bulbturn_day(rtc),is_morning = vne.ismorning(rtc),is_evening = vne.isevening(rtc))
        utime.sleep(3)
        try:
            response = ""
            conn, addr = s.accept()
            #print('Got a connection from %s' % str(addr))
            request = conn.recv(1024)
            #conn.settimeout(None)
            request = str(request)
            #print(request)
            if request.find(PASSWORD) == 6:
                #Show page so user can click on page; GET request without params in url. eg. GET /password HTTP/1.1
                response = frontbulb.web_page_password()
            if request.find(EVENODDALL) == 6:
                response = frontbulb.web_page_evanoddall()
                utime.sleep_ms(100)
            request = str(request).replace("b'","").replace("'","")
            request = request.split("\\r\\n")
            params = {}
            for part in request:
                if "/?" and "GET" in part:
                    try:
                        params = parse_params(part)
                    except IndexError as er:
                        print(f"IndexError : {er}")
                        params = None
            if params:
                # take Action by MCU based on params after pressing button on page shown in response
                if 'manual'in params:
                    if params['manual'] == 'on':
                        frontbulb.manualmodeon()
                    if params['manual'] == 'off':
                        frontbulb.manualmodeoff()
                if 'bulb'in params:
                    if params['bulb'] == 'on':
                        frontbulb.bulbon()
                    if params['bulb'] == 'off':
                        frontbulb.bulboff()
                if 'ssid' in params and 'paswd' in params:
                    vne.u_sidpaswd(params)
                if 'w' in params:
                    vne.updatedays_selection(params)
            if response == "":
                response = frontbulb.web_page(memstr = free(full=True),sr_h=vne.sr_h,sr_m=vne.sr_m,ss_h=vne.ss_h,ss_m=vne.ss_m,is_morning=vne.ismorning(rtc),daysstr=vne.daysstr_turn(),timestr=vne.timestring(rtc))
            conn.send('HTTP/1.1 200 OK\n')
            conn.send('Content-Type: text/html\n')
            conn.send('Connection: close\n\n')
            conn.sendall(response)
            conn.close()
            #utime.sleep_ms(150) # Wait for transmission of response
#             del request
#             del response
#             del params
#             del addr
#             del conn
        except Exception as e:
            import sys
            sys.print_exception(e)
        #except OSError as er: #OSError : [Errno 104] ECONNRESET
            print(f"OSError : {e}")
            utime.sleep_ms(100)
            conn.close()
            utime.sleep_ms(200)
            gc.collect()
            #machine.soft_reset()