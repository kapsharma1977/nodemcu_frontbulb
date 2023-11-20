
from boot import DATETIME_ELEMENTS, D1, D2 
 
# #################### Bulb State Module veriables
MANUAL_SWITCH_ON = 1
MANUAL_SWITCH_OFF = 0
BULB_ON = 1
BULB_OFF = 0


###############

class bulb:
    EVENINGTIME = const(19) # 7pm to switch on
    MORININGTIME = const(6) # 6am to switch off

    def __init__(self,manualmode = MANUAL_SWITCH_OFF, bulbflag = BULB_OFF):
        self.MANUAL_SWITCH_FLAG = manualmode
        self.bulb_FLAG = bulbflag
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
    def isevening(self,rtc_initlized):
        date = list(rtc_initlized.datetime())
        if date[DATETIME_ELEMENTS["hour"]] >= bulb.EVENINGTIME or date[DATETIME_ELEMENTS["hour"]] < bulb.MORININGTIME:
            del date
            return True
        else:
            del date
            return False
    def ismorning(self,rtc_initlized):
        date = list(rtc_initlized.datetime())
        if date[DATETIME_ELEMENTS["hour"]] >= bulb.MORININGTIME and date[DATETIME_ELEMENTS["hour"]] < bulb.EVENINGTIME:
            del date
            return True
        else:
            del date
            return False
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
    def checkclockandupdaterelays(self,rtc,D1,D2):
        if not self.MANUAL_SWITCH_FLAG: #self.MANUAL_SWITCH_FLAG == bulb.MANUAL_SWITCH_OFF:
            if self.ismorning(rtc):
                self.relaysoff(D1=D1,D2=D2)
                #print("Good Morinig")
                #print("led D1={0} D2={1}".format(D1.value(),D2.value()))
                #print(rtc.datetime()) # print the updated RTC time
            if self.isevening(rtc):
                self.relayson(D1=D1,D2=D2)
                #print("Good Evening")
                #print("led D1={0} D2={1}".format(D1.value(),D2.value()))
    def web_page(self):
        # Button HTML Code
        manual_mode_button_on = """<a href="/?manual=on"><button class="button"> Manual Mode ON</button></a>"""
        manual_mode_button_off = """<a href="/?manual=off"><button class="button button2"> Manual Mode OFF</button></a>"""
        bulbon = """<a href="/?bulb=on"><button class="button"> Permanently ON</button></a>"""
        bulboff = """<a href="/?bulb=off"><button class="button button2"> Permanently OFF</button></a>"""
        html = """<html><head> <title>ESP Web Server</title> <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="icon" href="data:,"> <style>html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
      h1{color: #0F3376; padding: 2vh;}p{font-size: 1.5rem;}.button{display: inline-block; background-color: #e7bd3b; border: none; 
      border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
      .button2{background-color: #4286f4;}</style></head><body> <h1>ESP Web Server</h1>"""
        
        #+ gpio_state + """</strong></p><p><a href="/?led=on"><button class="button">ON</button></a></p>
      #<p><a href="/?led=off"><button class="button button2">OFF</button></a></p></body></html>"""
      
        if self.MANUAL_SWITCH_FLAG:
            html = html + "<p>" + manual_mode_button_off + "</p>"
            # In manual mode if Permanently button is clicked
            if self.bulb_FLAG:
                html = html + "<p>" + bulboff + "</p>"
            else:
                html = html + "<p>" + bulbon + "</p>"
        else:
            html = html + "<p>" + manual_mode_button_on + "</p>"
        #print("_MANUAL_SWITCH_FLAG = {0}".format(_MANUAL_SWITCH_FLAG))
        html = html + "</body></html>"
        return html

