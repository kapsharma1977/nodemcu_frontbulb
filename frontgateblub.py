from machine import Pin
MANUAL_SWITCH_ON = 1
MANUAL_SWITCH_OFF = 0
BULB_ON = 1
BULB_OFF = 0
class bulb:
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
    def updaterelays(self,is_bulbturnday,is_morning,is_evening):
        if not self.MANUAL_SWITCH_FLAG:
            if not is_bulbturnday:
                self.relaysoff()
            else:
                if is_morning:
                    self.relaysoff()
                if is_evening:
                    self.relayson()
    def web_page(self,memstr,sr_h,sr_m,ss_h,ss_m,is_morning,daysstr,timestr):
        html_style = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Lucida Console;background-color:lightblue;color:#871F78;}h1{padding:2vh;text-align:center;}div{margin:70px;border:1px solid #4CAF50;font-size:1.5rem;} button{background-color: #871F78;font-size:1.5rem;width:100%;padding:12px 20px;margin:8px 0;} button:hover {opacity: 0.8;} .button2{background-color: #FFFF00;font-size:1.5rem;}
@media screen and (max-width: 300px)}"""
        style_end = "</style></head>"
        if is_morning:
            b_g = 'Good Morning'
        else:
            b_g = 'Good Evening'
        if self.bulb_FLAG:
            b_s = '<br>Status: <strong>ON</strong>' + '. It will off at ' + str(sr_h) + ':' + str(sr_m) + 'am and on at ' +  str(int(ss_h) - 12) + ':' + str(ss_m) + 'pm'
        else:
            b_s = '<br>Status: <strong>OFF</strong>' + '. It will on at ' + str(int(ss_h) - 12) + ':' + str(ss_m) + 'pm and off at ' +  str(sr_h) + ':' + str(sr_m) + 'am'
        manual_mode_button_on = """<a href="/?manual=on"><button class="button">Manual Mode ON</button></a>"""
        manual_mode_button_off = """<a href="/?manual=off"><button class="button button2">Manual Mode OFF</button></a>"""
        bulbon = """<a href="/?bulb=on"><button class="button">Permanently ON</button></a>"""
        bulboff = """<a href="/?bulb=off"><button class="button button2">Permanently OFF</button></a>""" 
        h_b = """<body><h1>ESP Web Server</h1><div>""" + b_g + "<br>" + b_s + "<br>" + timestr + "<br>Memory(Rom):" + memstr + "<br>Bulb will be On Days:" + daysstr + """<br><a target="_self" href="/evenodd">"Change Days"</a>""" + """<br><a target="_self" href="/password">"Change Wifi SSID & Password"</a></div>"""
        if self.MANUAL_SWITCH_FLAG:
            h_b = h_b + "<p>" + manual_mode_button_off + "</p>"
            if self.bulb_FLAG:
                h_b = h_b + "<p>" + bulboff + "</p>"
            else:
                h_b = h_b + "<p>" + bulbon + "</p>"
        else:
            h_b = h_b + "<p>" + manual_mode_button_on + "</p>"
        h_b = h_b + "</body></html>" #"<script>setTimeout(() => {{document.location.reload();}}, 30000);</script>" + "</body></html>"
        return html_style + style_end + h_b + "</body></html>"
    def web_page_password(self):
        html_style = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Lucida Console;background-color:lightblue;color:#871F78;}h1{padding:2vh;text-align:center;}div{margin:70px;border:1px solid #4CAF50;font-size:1.5rem;} button{background-color: #FFFF00;font-size:1.5rem;width:100%;padding:12px 20px;margin:8px 0;} button:hover {opacity: 0.8;} .button2{background-color: #FFFF00;font-size:1.5rem;}
@media screen and (max-width: 300px)}"""
        style_end = """form {border:3px solid #f1f1f1;} input[type=text], input[type=password],input[type=button]{width:100%;padding:12px 20px;margin:8px 0;display:inline-block;border: 1px solid #ccc;box-sizing: border-box;} .container{padding:16px;}</style></head>"""
        return html_style + style_end +"""<body> <h2>Blub ESP Web Server : Change Wifi SSID and Password</h2><form action="/" method="get" target="_self"><fieldset><div class="container" style="background-color:#f1f1f1"><label for="ssid">New Wifi SSID:</label><input type="text" id="ssid" name="ssid" required><br><label for="paswd">New Wifi Password:</label><input type="password" id="paswd" name="paswd" required></div></fieldset><button type="submit">Set New Wifi SSID and Password</button></form></body></html>"""
    def web_page_evanoddall(self):
        html_style = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Lucida Console;background-color:lightblue;color:#871F78;}h1{padding:2vh;text-align:center;}div{margin:50px;border:1px solid #4CAF50;font-size:2rem;padding: 20px;} button{background-color: #FFFF00;font-size:1.5rem;width:100%;padding:12px 20px;margin:8px 0;} button:hover {opacity: 0.8;} .button2{background-color: #FFFF00;font-size:1.5rem;}
@media screen and (max-width: 300px)}"""
        style_end = """</style></head>"""
        return html_style + style_end + """<body> <h1>Select days</h1>
<form action="/" method="get" target="_self"><div><fieldset><input type="checkbox"  name="w" value="1" checked hidden><input type="checkbox"  name="1" value="Mon">Mon<br><input type="checkbox" name="2" value="Tue">Tue<br><input type="checkbox" name="3" value="Wed">Wed<br><input type="checkbox" name="4" value="Thu">Thur<br><input type="checkbox" name="5" value="Fri">Fri<br> <input type="checkbox" name="6" value="Sat">Sat<br><input type="checkbox" name="7" value="Sun">Sun<br><button type="submit" value="Submit">Submit</button></fieldset></div></form>
</body></html>"""