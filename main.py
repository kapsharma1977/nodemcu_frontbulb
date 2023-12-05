from frontgateblub import bulb
PASSWORD = '/password'
EVENODDALL ='/evenodd'
SSID=""
PASS=""
def wlandisconnect(fb):
    fb.relaysoff()
    utime.sleep_ms(200)
def json_savetofile(fname,jsondata):
    with open(fname, 'wt') as fd:
        ujson.dump(jsondata, fd)
def json_getfromfile(fname):
    with open(fname, 'rt') as fd:
        return ujson.load(fd)
def loadpaswd():
    global SSID
    global PASS
    try:
        _jsonstr = json_getfromfile(PASSFILE)
        _json = ujson.loads(_jsonstr)
        SSID = _json["ssid"]
        PASS = _json["paswd"]
    except:
        return {"ssid":"Jiya","paswd":"9971989772"}
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
    WEEKFILE = 'week.json'
    SRFILE = 'sunrise.json'
    SSFILE = 'sunset.json'
    def __init__(self):
        self.month = ''
        self.week = {}
        self.today = ''
        self.sunrise_h = 0
        self.sunrise_m = 0
        self.sunset_h = 0
        self.sunset_m = 0
        self.updated = False
        self.startmonth = ''
    def update(self,rtc):
        self.month = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec",][list(rtc.datetime())[1] - 1]
        self.today = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][list(rtc.datetime())[3]]
        if not self.updated:
            self.loadweek()
            self.sunrise()
            self.sunset()
            self.startmonth = self.month
            _jsonstr = ujson.dumps(list(rtc.datetime()))
            json_savetofile('time.json',_jsonstr)
            self.updated = True
        if self.month != self.startmonth:
            self.sunrise()
            self.sunset()
    def isevening(self,rtc):
        self.update(rtc)
        date = list(rtc.datetime())
        if date[4] == self.sunset_h:
            if date[5] == self.sunset_m:
                return True
            else:
                if date[5] < self.sunset_m:
                    return False
                else:
                    return True
        else:
            if date[4] > self.sunset_h:
                return True
            else:
                if date[4] == self.sunrise_h:
                    if date[5] == self.sunrise_m:
                        return False
                    else:
                        if date[5] < self.sunrise_m:
                            return True
                        else:
                            return False
                else:
                    if date[4] < self.sunrise_h:
                        return True
                    else:
                        return False
    def ismorning(self,rtc):
        self.update(rtc)
        date = list(rtc.datetime())
        if date[4] == self.sunrise_h:
            if date[5] == self.sunrise_m:
                return True
            else:
                if date[5] < self.sunrise_m:
                    return False
                else:
                    return True
        else:
            if date[4] < self.sunrise_h:
                return False
            else:
                if date[4] == self.sunset_h:
                    if date[5] == self.sunset_m:
                        return False
                    else:
                        if date[5] < self.sunset_m:
                            return True
                        else:
                            return False
                else:
                    if date[4] < self.sunset_h:
                        return True
                    else:
                        return False
    def timestring(self,rtc):
        date = list(rtc.datetime())
        return "%s, %02d %s %04d, %02d:%02d:%02d, %s" % (
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][date[3]],date[2],
        ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec",][date[1] - 1],
        date[0],date[4],date[5],date[6],"calcutta +5:30",)
    def is_bulbturn_day(self,rtc):
        self.update(rtc)
        if self.today in self.week:
            if self.week[self.today] == 1:
                return True
            else:
                return False
        else:
            return False
    def daysstr_turn(self):
        daysstr = ''
        for day in self.week:
            if self.week[day] == 1:
                daysstr = daysstr + day + ' '
        return daysstr
    def loadweek(self):
        try:
            _jsonstr = json_getfromfile(env.WEEKFILE)
            self.week = ujson.loads(_jsonstr)
        except Exception as e:
            import sys
            sys.print_exception(e)
            self.week = {"Mon":1, "Tue":1, "Wed":1, "Thu":1, "Fri":1, "Sat":1, "Sun":1}
            _jsonstr = ujson.dumps(self.week)
            json_savetofile(env.WEEKFILE,jsondata=_jsonstr)
    def sunrise(self):
        try:
            _jsonstr = json_getfromfile(env.SRFILE)
            _json = ujson.loads(_jsonstr)
            self.sunrise_h = _json[self.month]['h']
            self.sunrise_m = _json[self.month]['m']
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
            self.sunrise_h = sunrise[self.month]['h']
            self.sunrise_m = sunrise[self.month]['m']
            _jsonstr = ujson.dumps(sunrise)
            json_savetofile(env.SRFILE,_jsonstr)
    def sunset(self):
        try:
            _jsonstr = json_getfromfile(env.SSFILE)
            _json = ujson.loads(_jsonstr)
            self.sunset_h = _json[self.month]['h']
            self.sunset_m = _json[self.month]['m']
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
            self.sunset_h = sunset[self.month]['h']
            self.sunset_m = sunset[self.month]['m']
            _jsonstr = ujson.dumps(sunset)
            json_savetofile(env.SSFILE,_jsonstr)
    def updatedays_selection(self,params):
        for day in self.week:
            self.week[day] = 0
        for day in params['week'].split("-"):
            if day in self.week:
                self.week[day] = 1
        _jsonstr = ujson.dumps(self.week)
        json_savetofile(env.WEEKFILE,jsondata=_jsonstr)
    def updatessidpaswd(self,params):
        SSID = params['ssid']
        PASS = params['paswd']
        _jsonstr = ujson.dumps(params)
        json_savetofile(PASSFILE,jsondata=_jsonstr)
##
loadpaswd()
print(SSID)
print(PASS)
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
        if not wlan.active():
            wlan.active(True)
        wlan.connect(SSID, PASS)
        tmo = 50
        while not wlan.isconnected():
            utime.sleep_ms(100)
            tmo -= 1
            if tmo == 0:
                break
        if tmo == 0:
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
        utime.sleep_ms(3000)
        frontbulb.updaterelays(is_bulbturnday = vne.is_bulbturn_day(rtc),is_morning = vne.ismorning(rtc),is_evening = vne.isevening(rtc))
        try:
            response = ""
            conn, addr = s.accept()
            print('Got a connection from %s' % str(addr))
            request = conn.recv(1024)
            #conn.settimeout(None)
            request = str(request)
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
                    vne.updatessidpaswd(params)
                if 'week' in params:
                    vne.cleardays_selection()
                    vne.updatedays_selection(params)
            if response == "":
                response = frontbulb.web_page(memstr = free(full=True),sunrise_h=vne.sunrise_h,sunrise_m=vne.sunrise_m,sunset_h=vne.sunset_h,sunset_m=vne.sunset_m,is_morning=vne.ismorning(rtc),daysstr=vne.daysstr_turn(),timestr=vne.timestring(rtc))
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
            del request
            del response
            del params
            del addr
            del conn
            utime.sleep_ms(200)
            gc.collect()
            #machine.soft_reset()
