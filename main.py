#import frontgateblub
from frontgateblub import bulb
# #Manualy Switch off Front Gate Blub, it will supress time based operation of Blub
# _MANUAL_SWITCH_FLAG = 0
# _BLUB_FLAG = 0

frontbulb = bulb()
frontbulb.relaysoff(D1=D1,D2=D2)
###frontgateblub.relaysoff(D1=D1,D2=D2)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)
while True:    
    gc.collect()
    if not wlan.isconnected():
        if wlanconnect(wlan=wlan):
            initializeRTC(rtc=rtc)
            set_datetime_element(rtc) # RTC initlized and time zone applied
            print("!!! connected to WiFi")
        else:
            print("!!! Not able to connect to WiFi")
            # You are not conneted to internet so turn off D1 and D2
            frontbulb.relaysoff(D1=D1,D2=D2)
            print("led D1={0} D2={1}".format(D1.value(),D2.value()))
            pass
    #print(rtc.datetime()) # print the updated RTC time
    frontbulb.checkclockandupdaterelays(rtc=rtc,D1=D1,D2=D2)
    #print("led D1={0} D2={1}".format(D1.value(),D2.value()))
    conn, addr = s.accept()
    print('Got a connection from %s' % str(addr))
    request = conn.recv(1024)
    request = str(request)
    #print('Content = %s' % request)
    manual_on = request.find('/?manual=on')
    manual_off = request.find('/?manual=off')
    bulb_on = request.find('/?bulb=on')
    bulb_off = request.find('/?bulb=off')
    if manual_on == 6:
        #print('manual ON {0}'.format(frontgateblub.setmanualyswitchblub(manualmode = 1)))
        #frontgateblub.manualyswitchblub(manualmode = 1)
        #MANUAL_SWITCH_FLAG = frontgateblub.setmanualyswitchblub(manualmode = 1)
        #print("Loop MANUAL_SWITCH_FLAG = {0}".format(MANUAL_SWITCH_FLAG))
        frontbulb.manualmodeon()
        #response = frontgateblub.web_page()
    if manual_off == 6:
        #print('manual OFF')
        #frontgateblub.setmanualyswitchblub(manualmode = 0)
        frontbulb.manualmodeoff()
        #response = frontgateblub.web_page()
    if bulb_on == 6:
        frontbulb.bulbon()
    if bulb_off == 6:
        frontbulb.bulboff()
    
    response = frontbulb.web_page()
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: text/html\n')
    conn.send('Connection: close\n\n')
    conn.sendall(response)
    conn.close()
    #sleep(SLEEPSECONDS)