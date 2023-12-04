#import frontgateblub
from frontgateblub import bulb
#Server url end points
PASSWORD = '/password'
SSIDS = '/ssid'
def wlandisconnect():
    frontbulb.relaysoff(D1=D1,D2=D2)
    wlan.disconnect()
    utime.sleep_ms(200)
    #print("led D1={0} D2={1}".format(D1.value(),D2.value()))
def json_savepaswdtofile(jsonpaswd):
    with open(PASSFILE, 'wt') as fd:
        ujson.dump(jsonpaswd, fd)
def json_getpaswdfromfile():
    with open(PASSFILE, 'rt') as fd:
        return ujson.load(fd)
##
try:
    ssidpswd_jsonstr = json_getpaswdfromfile()
    ssidpswd_json = ujson.loads(ssidpswd_jsonstr)
    SSID=ssidpswd_json["ssid"]
    PASS=ssidpswd_json["paswd"]
    del ssidpswd_jsonstr
    del ssidpswd_json
except ValueError as er:
    SSID="Jiya"
    PASS="9971989772"
    print(f"ValueError : {er}")
##
frontbulb = bulb()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)
while True:
    gc.collect()
    utime.sleep_ms(100)
    if not wlan.isconnected():
        print('Blub ESP8266 is not Conneted to Wifi')
        if wlanconnect(wlan=wlan):
            initializeRTC()
            set_datetime_element(rtc) # RTC initlized and time zone applied
            print("!!! connected to WiFi")
            #print(rtc.datetime())
            utime.sleep_ms(100)
        else:
            print("!!! Not able to connect to WiFi")
            # You are not conneted to internet so turn off D1 and D2
            wlandisconnect()
            print("led D1={0} D2={1}".format(D1.value(),D2.value()))
            utime.sleep_ms(200)
            continue
    else:
        frontbulb.checkclockandupdaterelays(rtc_initlized=rtc,D1=D1,D2=D2)
        try:
            response = ""
            conn, addr = s.accept() # <class 'socket'>, <class 'tuple'>
            print('Got a connection from %s' % str(addr))
            request = conn.recv(1024) # bytes()
            conn.settimeout(None)
            request = str(request)
            #print('GET Request Content = %s' % request)
            if request.find(PASSWORD) == 6:
                #Show page so user can click on page; GET request without params in url. eg. GET /password HTTP/1.1
                response = frontbulb.web_page_password()
            if request.find(SSIDS) == 6:
                #Show page so user can click on page; GET request without params in url. eg. GET /password HTTP/1.1
                response = frontbulb.web_page_ssid(sleepfn = utime.sleep_ms,wlan = wlan)
                utime.sleep_ms(100)
            request = str(request).replace("b'","").replace("'","")
            request = request.split("\\r\\n")
            params = {}
            for part in request:
                if "/?" and "GET" in part:
                    try:
                        params = frontbulb.parse_params(part)
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
                    SSID = params['ssid']
                    PASS = params['paswd']
                    frontbulb.ssidpasswordchanged()
                    jsonparams = ujson.dumps(params)
                    json_savepaswdtofile(jsonpaswd=jsonparams)
            if response == "":
                response = frontbulb.web_page(rtc_initlized=rtc,memstr = free(full=True))
            conn.send('HTTP/1.1 200 OK\n')
            conn.send('Content-Type: text/html\n')
            conn.send('Connection: close\n\n')
            conn.sendall(response)
            utime.sleep_ms(150) # Wait for transmission of response
            conn.close()
            del request
            del response
            del params
            del addr
            del conn
        except OSError as er: #OSError : [Errno 104] ECONNRESET
            print(f"OSError : {er}")
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