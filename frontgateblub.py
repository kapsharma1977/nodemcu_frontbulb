from machine import Pin
MANUAL_SWITCH_ON = 1
MANUAL_SWITCH_OFF = 0
BULB_ON = 1
BULB_OFF = 0
class bulb:
    html_style = """<!DOCTYPE html><html><head> <title>Blub ESP Web Server</title><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"> <style> body {font-family: Arial, Helvetica, sans-serif;} h1{color: #871F78; padding: 2vh;}p{font-size: 1.5rem;} form {border: 3px solid #f1f1f1;} input[type=text], input[type=password]{width:100%;padding:12px 20px;margin:8px 0;display:inline-block;border: 1px solid #ccc;box-sizing: border-box; }
button {background-color: #871F78;color: white;padding: 14px 20px; margin: 8px 0;border: none;cursor: pointer;width: 100%;} button:hover {opacity: 0.8;} .button2{background-color: #4286f4;} .container {padding: 16px;} span.psw {float: right;padding-top: 16px; }
@media screen and (max-width: 300px) {span.psw {display: block;float: none;}}</style></head>"""
    D1 = Pin(5, Pin.OUT, value=1)
    D2 = Pin(4, Pin.OUT, value=1)
    def __init__(self, manualmode = MANUAL_SWITCH_OFF, bulbflag = BULB_OFF):
        self.MANUAL_SWITCH_FLAG = manualmode
        self.bulb_FLAG = bulbflag
        if bulbflag == BULB_OFF:
            self.relaysoff()
        if bulbflag == BULB_ON:
            self.relayson()
    def _refreshbulb(self):
        if self.MANUAL_SWITCH_FLAG:
            if self.bulb_FLAG:
                self.relayson()
            else:
                self.relaysoff()
    def setmanualyswitchbulb(self,manualmode = MANUAL_SWITCH_OFF, bulbflag = BULB_OFF):
        self.MANUAL_SWITCH_FLAG = manualmode
        self.bulb_FLAG = bulbflag
        self._refreshbulb()
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
    def _turnoff(self):
        if bulb.D1.value():
            bulb.D1.off()
        if bulb.D2.value():
            bulb.D2.off()
    def _turnon(self):
        if not bulb.D1.value():
            bulb.D1.on()
        if not bulb.D2.value():
            bulb.D2.on()
    def relayson(self):
        self._turnoff()
        self.bulb_FLAG = BULB_ON
    def relaysoff(self):
        self._turnon()
        self.bulb_FLAG = BULB_OFF
#     def _checkclockandupdaterelayssunriseandsunset(self,rtc):
#         dt = list(rtc.datetime())
#         bulb.month = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec",][dt[1] - 1]
#         bulb.today = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt[3]]
    def updaterelays(self,is_bulbturnday,is_morning,is_evening):
        if not self.MANUAL_SWITCH_FLAG:
            if not is_bulbturnday:
                self.relaysoff()
            else:
                if is_morning:
                    self.relaysoff()
                if is_evening:
                    self.relayson()
    def web_page(self,memstr,sunrise_h,sunrise_m,sunset_h,sunset_m,is_morning,daysstr,timestr):
        if self.bulb_FLAG:
            bulbstatus = '<h3>Status : <strong>ON</strong> ' + str(sunset_h) + ':' + str(sunset_m) + '</h3>'
        else:
            bulbstatus = '<h3>Status : <strong>OFF</strong> ' + str(sunrise_h) + ':' + str(sunrise_m) + '</h3>'
        if is_morning:
            bulbgreetings = '<h3>Good Morning. It should be off</h3>'
        else:
            bulbgreetings = '<h3>Good Evening. It should be on</h3>'
        manual_mode_button_on = """<a href="/?manual=on"><button class="button"> Manual Mode ON</button></a>"""
        manual_mode_button_off = """<a href="/?manual=off"><button class="button button2"> Manual Mode OFF</button></a>"""
        bulbon = """<a href="/?bulb=on"><button class="button"> Permanently ON</button></a>"""
        bulboff = """<a href="/?bulb=off"><button class="button button2"> Permanently OFF</button></a>""" 
        h_b = """<body> <h1>ESP Web Server</h1>""" + "<p>" + bulbgreetings + "</p>" + "<p>" + bulbstatus + "</p>" + "<p><h3>" + timestr + "</h3></p>" + "<p><h3>Memory(Rom) :" + memstr + "</h3></p>" + "<p><h3> Bulb will be On Days :" + daysstr + "</h3></p>"
        if self.MANUAL_SWITCH_FLAG:
            h_b = h_b + "<p>" + manual_mode_button_off + "</p>"
            if self.bulb_FLAG:
                h_b = h_b + "<p>" + bulboff + "</p>"
            else:
                h_b = h_b + "<p>" + bulbon + "</p>"
        else:
            h_b = h_b + "<p>" + manual_mode_button_on + "</p>"
        h_b = h_b + "<script>setTimeout(() => {{document.location.reload();}}, 30000);</script>" + "</body></html>"
        return bulb.html_style + h_b + "</body></html>" #"<script>setTimeout(() => {{document.location.reload();}}, 30000);</script>"
    def web_page_password(self):
        return bulb.html_style + """<body> <h2>Blub ESP Web Server : Change Wifi SSID and Password</h2><form action="/" method="get" target="_self"><fieldset><div class="container" style="background-color:#f1f1f1"><label for="ssid">New Wifi SSID:</label><input type="text" id="ssid" name="ssid" required><br><label for="paswd">New Wifi Password:</label><input type="text" id="paswd" name="paswd" required></div></fieldset><button type="submit">Set New Wifi SSID and Password</button></form></body></html>"""
    def web_page_evanoddall(self):
        return bulb.html_style + """<body> <h2>Blub ESP Web Server : Select days for which Bulb will be Switched On</h2>
<form action="/" method="get" target="_self"><fieldset><input type="checkbox"  name="w" value="Mon">Monday<br><input type="checkbox" name="w" value="Tue">Tuesday<br><input type="checkbox" name="W" value="Wed">Wednesday<br><input type="checkbox" name="w" value="Thu">Thursday<br><input type="checkbox" name="w" value="Fri">Friday<br> <input type="checkbox" name="w" value="Sat">Saturday<br><input type="checkbox" name="w" value="Sun">Sunday<br><br><input  type="button" onclick="Week()" value="Set Days for switching Bulb on"><input type="hidden" id="week" name="week" value=""></fieldset><input type="submit" id="bt" value="Submit" hidden></form>
<script>function Week(){var w = document.forms[0];var txt = "";var i;for (i = 0; i < w.length; i++) {if (w[i].checked){txt = txt + w[i].value + "-";}else {if (w[i].name == "w"){{txt = txt + "0" + "-";}}}}document.getElementById("week").value = txt;document.getElementById("bt").click();}</script>
</body></html>"""
