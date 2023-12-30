from machine import Pin
class bulb:
    D1 = Pin(5, Pin.OUT, value=1)
    D2 = Pin(4, Pin.OUT, value=1)
    MANUAL_SWITCH_ON = 1
    MANUAL_SWITCH_OFF = 0
    BULB_ON = 1
    BULB_OFF = 0
    def __init__(self, manualmode = 0, bulbflag = 0):
        self.MANUAL_SWITCH_FLAG = manualmode
        self.bulb_FLAG = bulbflag
        if bulbflag == bulb.BULB_OFF:
            self.relaysoff()
        if bulbflag == bulb.BULB_ON:
            self.relayson()
    def _refreshbulb(self):
        if self.MANUAL_SWITCH_FLAG:
            if self.bulb_FLAG:
                self.relayson()
            else:
                self.relaysoff()
    def setmanualyswitchbulb(self,manualmode = 0, bulbflag = 0):
        self.MANUAL_SWITCH_FLAG = manualmode
        self.bulb_FLAG = bulbflag
        self._refreshbulb()
    def _setmode(self,manualmode = 0):
        self.MANUAL_SWITCH_FLAG = manualmode
        self._refreshbulb()
    def _setbulb(self,bulbflag = 0):
        self.bulb_FLAG = bulbflag
        self._refreshbulb()
    def manualmodeon(self, is_bulbturnday,is_morning,is_evening):
        self._setmode(bulb.MANUAL_SWITCH_ON)
        self.updaterelays(is_bulbturnday,is_morning,is_evening)
        return self.MANUAL_SWITCH_FLAG
    def manualmodeoff(self, is_bulbturnday,is_morning,is_evening):
        self._setmode(bulb.MANUAL_SWITCH_OFF)
        self.updaterelays(is_bulbturnday,is_morning,is_evening)
        return self.MANUAL_SWITCH_FLAG
    def bulbon(self):
        self._setbulb(bulb.BULB_ON)
        return self.bulb_FLAG
    def bulboff(self):
        self._setbulb(bulb.BULB_OFF)
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
        self.bulb_FLAG = bulb.BULB_ON
    def relaysoff(self):
        self._turnon()
        self.bulb_FLAG = bulb.BULB_OFF
    def updaterelays(self,is_bulbturnday,is_morning,is_evening):
        if not self.MANUAL_SWITCH_FLAG:
            if not is_bulbturnday:
                self.relaysoff()
            else:
                if is_morning:
                    self.relaysoff()
                if is_evening:
                    self.relayson()