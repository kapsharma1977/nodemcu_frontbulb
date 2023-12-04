import gc
from boot import DATETIME_ELEMENTS,sunrise,sunset, D1, D2
# ### Bulb State Module veriables
MANUAL_SWITCH_ON = 1
MANUAL_SWITCH_OFF = 0
BULB_ON = 1
BULB_OFF = 0
###
class bulb:
#     EVENINGTIME = const(19) # 7pm to switch on
#     MORININGTIME = const(6) # 6am to switch off

    def __init__(self, manualmode = MANUAL_SWITCH_OFF, bulbflag = BULB_OFF):
        self.MANUAL_SWITCH_FLAG = manualmode
        self.bulb_FLAG = bulbflag
        self.SSID_PASS_FLAG = False
        self.sunrise_h = 0
        self.sunrise_m = 0
        self.sunset_h = 0
        self.sunset_m = 0
        if bulbflag == BULB_OFF:
            self.relaysoff(D1=D1,D2=D2)
        if bulbflag == BULB_ON:
            self.relayson(D1=D1,D2=D2)
    def _refreshbulb(self):
        if self.MANUAL_SWITCH_FLAG:
            # In manual mode if Permanently button is clicked
            if self.bulb_FLAG:
                self.relayson(D1=D1,D2=D2)
            else:
                self.relaysoff(D1=D1,D2=D2)
    def setmanualyswitchbulb(self,manualmode = MANUAL_SWITCH_OFF, bulbflag = BULB_OFF):
        self.MANUAL_SWITCH_FLAG = manualmode
        self.bulb_FLAG = bulbflag
        self._refreshbulb()
    def getmode(self):
        return self.MANUAL_SWITCH_FLAG
    def getbulb(self):
        return self.bulb_FLAG
    def _setmode(self,manualmode = MANUAL_SWITCH_OFF):
        self.MANUAL_SWITCH_FLAG = manualmode
        self._refreshbulb()
    def _setbulb(self,bulbflag = BULB_OFF):
        self.bulb_FLAG = bulbflag
        self._refreshbulb()
    def manualmodeon(self):
        self._setmode(MANUAL_SWITCH_ON)
        return self.MANUAL_SWITCH_FLAG
    def manualmodeoff(self):
        self._setmode(MANUAL_SWITCH_OFF)
        return self.MANUAL_SWITCH_FLAG
    def bulbon(self):
        self._setbulb(BULB_ON)
        return self.bulb_FLAG
    def bulboff(self):
        self._setbulb(BULB_OFF)
        return self.bulb_FLAG
    def _turnoff(self,D1,D2):
        if D1.value():
            D1.off()
        if D2.value():
            D2.off()
    def _turnon(self,D1,D2):
        if not D1.value():
            D1.on()
        if not D2.value():
            D2.on()
    def relayson(self,D1,D2):
        self._turnoff(D1=D1,D2=D2)
        self.bulb_FLAG = BULB_ON
    def relaysoff(self,D1,D2):
        self._turnon(D1=D1,D2=D2)
        self.bulb_FLAG = BULB_OFF
    def isblubon(self):
        return self.getbulb()
    def ssidpasswordchanged(self):
        self.SSID_PASS_FLAG = True
    def is_ssidpasswordchanged(self):
        return self.SSID_PASS_FLAG
##
    def _checkclockandupdaterelayssunriseandsunset(self,rtc_initlized):
        # update sunrise and sunset variables
        dt = list(rtc_initlized.datetime())
        month = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec",][dt[DATETIME_ELEMENTS["month"]] - 1]
        self.sunrise_h = sunrise[month]['h']
        self.sunrise_m = sunrise[month]['m']
        self.sunset_h = sunset[month]['h']
        self.sunset_m = sunset[month]['m']
    def timestring(self,rtc_initlized):
        date = list(rtc_initlized.datetime())
        return "%s, %02d %s %04d, %02d:%02d:%02d, %s" % (
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][date[DATETIME_ELEMENTS["day_of_week"]]],
        date[DATETIME_ELEMENTS["day"]],
        ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec",][date[DATETIME_ELEMENTS["month"]] - 1],
        date[DATETIME_ELEMENTS["year"]],
        date[DATETIME_ELEMENTS["hour"]],
        date[DATETIME_ELEMENTS["minute"]],
        date[DATETIME_ELEMENTS["second"]],
        "calcutta +5:30",)
    def isevening(self,rtc_initlized):
        self._checkclockandupdaterelayssunriseandsunset(rtc_initlized)
        date = list(rtc_initlized.datetime())
        if date[DATETIME_ELEMENTS["hour"]] == self.sunset_h: #check evening boundary condition
            if date[DATETIME_ELEMENTS["minute"]] == self.sunset_m:
                return True
            else:
                if date[DATETIME_ELEMENTS["minute"]] < self.sunset_m:
                    return False
                else:
                    return True
        else:
            if date[DATETIME_ELEMENTS["hour"]] > self.sunset_h:
                return True
            else: # current hour is less than or equal to sunset hour
                if date[DATETIME_ELEMENTS["hour"]] == self.sunrise_h: #check mornig boundary condition
                    if date[DATETIME_ELEMENTS["minute"]] == self.sunrise_m:
                        return False
                    else:
                        if date[DATETIME_ELEMENTS["minute"]] < self.sunrise_m:
                            return True
                        else:
                            return False
                else:
                    if date[DATETIME_ELEMENTS["hour"]] < self.sunrise_h:
                        return True
                    else:
                        return False
    def ismorning(self,rtc_initlized):
        self._checkclockandupdaterelayssunriseandsunset(rtc_initlized)
        date = list(rtc_initlized.datetime())
        if date[DATETIME_ELEMENTS["hour"]] == self.sunrise_h: #check morning boundary condition
            if date[DATETIME_ELEMENTS["minute"]] == self.sunrise_m:
                return True
            else:
                if date[DATETIME_ELEMENTS["minute"]] < self.sunrise_m:
                    return False
                else:
                    return True
        else:
            if date[DATETIME_ELEMENTS["hour"]] < self.sunrise_h:
                return False
            else: # current hour is grater than or equal to sunrise hour
                if date[DATETIME_ELEMENTS["hour"]] == self.sunset_h: #check evening boundary condition
                    if date[DATETIME_ELEMENTS["minute"]] == self.sunset_m:
                        return False
                    else:
                        if date[DATETIME_ELEMENTS["minute"]] < self.sunset_m:
                            return True
                        else:
                            return False
                else:
                    if date[DATETIME_ELEMENTS["hour"]] < self.sunset_h:
                        return True
                    else:
                        return False
    def checkclockandupdaterelays(self,rtc_initlized,D1,D2):
        # update sunrise and sunset variables
        self._checkclockandupdaterelayssunriseandsunset(rtc_initlized)
        if not self.MANUAL_SWITCH_FLAG: #self.MANUAL_SWITCH_FLAG == bulb.MANUAL_SWITCH_OFF:
            if self.ismorning(rtc_initlized):
                self.relaysoff(D1=D1,D2=D2)
            if self.isevening(rtc_initlized):
                self.relayson(D1=D1,D2=D2)
##  
    def parse_params(self,part):
        parameters = {}
        for piece in part.split(" "):
            if "/?" in piece:
                piece = piece.replace("/?", "")
                amp_split = piece.split("&")
                for param_set in amp_split:
                    eq_split = param_set.split("=")
                    parameters[eq_split[0]] = eq_split[1]
        return parameters
    def web_page(self,rtc_initlized,memstr):
        timestr = self.timestring(rtc_initlized)
        if self.isblubon():
            bulbstatus = '<h3>Current Status : Bulb is ON</h3>'
        else:
            bulbstatus = '<h3>Current Status : Bulb is OFF</h3>'
        if self.ismorning(rtc_initlized):
            bulbgreetings = '<h3>Good Morning from Bulb Logic. It should be off</h3>'
        else:
            bulbgreetings = '<h3>Good Evening from Bulb Logic. It should be on</h3>'
            
        manual_mode_button_on = """<a href="/?manual=on"><button class="button"> Manual Mode ON</button></a>"""
        manual_mode_button_off = """<a href="/?manual=off"><button class="button button2"> Manual Mode OFF</button></a>"""
        bulbon = """<a href="/?bulb=on"><button class="button"> Permanently ON</button></a>"""
        bulboff = """<a href="/?bulb=off"><button class="button button2"> Permanently OFF</button></a>"""
        html = """<!DOCTYPE html><html><head> <title>Blub ESP Web Server</title> <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="icon" href="data:,"> <style>html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
      h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none; 
      border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
      .button2{background-color: #4286f4;}</style></head><body> <h1>ESP Web Server</h1>"""
        html = html + "<p>" + bulbgreetings + "</p>"
        html = html + "<p>" + bulbstatus + "</p>"
        html = html + "<p><h3>" + timestr + "</h3></p>"
        html = html + "<p><h3>Memory(Rom) :" + memstr + "</h3></p>"
        if self.MANUAL_SWITCH_FLAG:
            html = html + "<p>" + manual_mode_button_off + "</p>"
            # In manual mode if Permanently button is clicked
            if self.bulb_FLAG:
                html = html + "<p>" + bulboff + "</p>"
            else:
                html = html + "<p>" + bulbon + "</p>"
        else:
            html = html + "<p>" + manual_mode_button_on + "</p>"
        html = html + "<script>setTimeout(() => {{document.location.reload();}}, 30000);</script>" + "</body></html>"
        return html
    def web_page_password(self):
        html = """<!DOCTYPE html><html><head> <title>Bulb ESP Web Server</title> <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="icon" href="data:,"> <style>*, *:before, *:after {
-moz-box-sizing: border-box;
-webkit-box-sizing: border-box; box-sizing: border-box; } body {
font-family: 'Nunito', sans-serif; color: #384047; } form {
max-width: 300px; margin: 10px auto; padding: 10px 20px; background: #f4f7f8; border-radius: 8px; } h1 { margin: 0 0 30px 0; text-align: center; } input[type="text"], input[type="password"], input[type="date"], input[type="datetime"], input[type="email"], input[type="number"], input[type="search"], input[type="tel"], input[type="time"], input[type="url"], textarea, select { background: rgba(255,255,255,0.1); border: none; font-size: 16px; height: auto; margin: 0; outline: 0; padding: 15px; width: 100%; background-color: #e8eeef; color: #8a97a0; box-shadow: 0 1px 0 rgba(0,0,0,0.03) inset; margin-bottom: 30px; } input[type="radio"], input[type="checkbox"] { margin: 0 4px 8px 0; } select { padding: 6px; height: 32px; border-radius: 2px; } button { padding: 19px 39px 18px 39px; color: #FFF; background-color: #4bc970; font-size: 18px; text-align: center; font-style: normal; border-radius: 5px; width: 100%; border: 1px solid #3ac162; border-width: 1px 1px 3px; box-shadow: 0 -1px 0 rgba(255,255,255,0.1) inset; margin-bottom: 10px; } fieldset { margin-bottom: 30px; border: none; } legend { font-size: 1.4em; margin-bottom: 10px; } label { display: block; margin-bottom: 8px; } label.light { font-weight: 300; display: inline; } .number { background-color: #5fcf80; color: #fff; height: 30px; width: 30px; display: inline-block; font-size: 0.8em; margin-right: 4px; line-height: 30px; text-align: center; text-shadow: 0 1px 0 rgba(255,255,255,0.2); border-radius: 100%; } @media screen and (min-width: 480px) { form { max-width: 480px; } }</style></head><body> <h1>ESP Web Server Change Wifi SSID and Password</h1><br>
<div class="row"><div class="col-md-12"><form action="/" method="get" target="_self"><fieldset><label for="ssid">New Wifi SSID:</label><input type="text" id="ssid" name="ssid"><br><label for="paswd">New Wifi Password:</label><input type="text" id="paswd" name="paswd"></fieldset><button type="submit">Set New Wifi SSID and Password</button></form></div></div>
</body></html>"""
        return html
    def web_page_ssid(self, sleepfn, wlan):
        try:
            html = """<!DOCTYPE html><html><head> <title>Bulb ESP Web Server</title><style>strong { color: blue; font-family: verdana; font-size: 100%; } p { color: green; font-family: courier; font-size: 100%; border: 2px solid black; padding: 5px; margin: 10px 10px 5px 25px; background-color: lightyellow;} </style></head><body> <h1><center>Bulb ESP Web Server SSID</center></h1><br>"""
            ssids = wlan.scan()
            sleepfn(950)
            for x in ssids:
                if x[5] == 0:
                    html = html + "<p>ssid = <strong>%s</strong></p>" % (str(x[0], 'ascii'))
            for x in ssids:
                if x[5] == 1:
                    html = html + "<p>ssid = %s</p>" % (str(x[0], 'ascii'))
            return html + "</body></html>"
        except MemoryError as er:
            print(f"MemoryError : {er}")
            del html
            gc.collect()
            return """<!DOCTYPE html><html><head> <title>Bulb ESP Web Server</title><style>strong { color: blue; font-family: verdana; font-size: 150%; } p { color: red; font-family: courier; font-size: 100%; border: 2px solid black; padding: 10px; margin: 10px 10px 5px 25px; background-color: lightyellow;} </style></head><body> <h1><center>Bulb ESP Web Server SSID</center></h1><br><p>MemoryError</p></body></html>"""