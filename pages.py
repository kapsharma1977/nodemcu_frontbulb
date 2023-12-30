def free(full=False):
    import gc
    gc.collect()
    F = gc.mem_free()
    A = gc.mem_alloc()
    T = F+A
    P = '{0:.2f}%'.format(F/T*100)
    if not full: return P
    else : return ('Total:{0} Free:{1} ({2})'.format(T,F,P))
def timestring(rtc, sleepnap):
    date = list(rtc.datetime())
    return "%s, %02d %s %04d, %02d:%02d:%02d, %s" % (
    ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][date[3]],date[2],
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec",][date[1] - 1],
    date[0],date[4],date[5],date[6],"sleep:" + sleepnap)
def daysstr_turn(envweek):
    wk = []
    for key in envweek:
        wk.append(int(key))
    wk.sort()
    dstr = ''
    for ikey in wk:
        if envweek[str(ikey)] != '':
            dstr = dstr + envweek[str(ikey)] + ' '
    return dstr
def web_page(vne,bb, rtc, sleepnap):
    html_style = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Lucida Console;background-color:lightblue;color:#871F78;}h1{padding:2vh;text-align:center;}div{margin:70px;border:1px solid #4CAF50;font-size:1.5rem;} button{background-color: #871F78;font-size:1.5rem;width:100%;padding:12px 20px;margin:8px 0;} button:hover {opacity: 0.8;} .button2{background-color: #FFFF00;font-size:1.5rem;}
@media screen and (max-width: 300px)}"""
    style_end = "</style></head>"
    if vne.ismorning():
        b_g = 'Good Morning'
    else:
        b_g = 'Good Evening'
    if bb.bulb_FLAG:
        b_s = '<br>Status: <strong>ON</strong>' + '. It will off at ' + str(vne.sr_h) + ':' + str(vne.sr_m) + 'am and on at ' +  str(int(vne.ss_h) - 12) + ':' + str(vne.ss_m) + 'pm'
    else:
        b_s = '<br>Status: <strong>OFF</strong>' + '. It will on at ' + str(int(vne.ss_h) - 12) + ':' + str(vne.ss_m) + 'pm and off at ' +  str(vne.sr_h) + ':' + str(vne.sr_m) + 'am'
    manual_mode_button_on = """<a href="/?manual=on"><button class="button">Manual Mode ON</button></a>"""
    manual_mode_button_off = """<a href="/?manual=off"><button class="button button2">Manual Mode OFF</button></a>"""
    bulbon = """<a href="/?bulb=on"><button class="button">Permanently ON</button></a>"""
    bulboff = """<a href="/?bulb=off"><button class="button button2">Permanently OFF</button></a>""" 
    h_b = """<body><h1>ESP Web Server</h1><div>""" + b_g + "<br>" + b_s + "<br>" + timestring(rtc, sleepnap) + "<br>Memory(Rom):" + free(full=True) + "<br>Bulb will be On Days:" + daysstr_turn(vne.week) + """<br><a target="_self" href="/evenodd">"Change Days"</a>""" + """<br><a target="_self" href="/password">"Change Wifi SSID & Password"</a></div>"""
    if bb.MANUAL_SWITCH_FLAG:
        h_b = h_b + "<p>" + manual_mode_button_off + "</p>"
        if bb.bulb_FLAG:
            h_b = h_b + "<p>" + bulboff + "</p>"
        else:
            h_b = h_b + "<p>" + bulbon + "</p>"
    else:
        h_b = h_b + "<p>" + manual_mode_button_on + "</p>"
    h_b = h_b + "</body></html>"
    return html_style + style_end + h_b + "</body></html>"
def web_page_password():
    html_style = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Lucida Console;background-color:lightblue;color:#871F78;}h1{padding:2vh;text-align:center;}div{margin:70px;border:1px solid #4CAF50;font-size:1.5rem;} button{background-color: #FFFF00;font-size:1.5rem;width:100%;padding:12px 20px;margin:8px 0;} button:hover {opacity: 0.8;} .button2{background-color: #FFFF00;font-size:1.5rem;}
@media screen and (max-width: 300px)}"""
    style_end = """form {border:3px solid #f1f1f1;} input[type=text], input[type=password],input[type=button]{width:100%;padding:12px 20px;margin:8px 0;display:inline-block;border: 1px solid #ccc;box-sizing: border-box;} .container{padding:16px;}</style></head>"""
    return html_style + style_end +"""<body> <h2>Blub ESP Web Server : Change Wifi SSID and Password</h2><form action="/" method="get" target="_self"><fieldset><div class="container" style="background-color:#f1f1f1"><label for="ssid">New Wifi SSID:</label><input type="text" id="ssid" name="ssid" required><br><label for="paswd">New Wifi Password:</label><input type="password" id="paswd" name="paswd" required></div></fieldset><button type="submit">Set New Wifi SSID and Password</button></form></body></html>"""
def web_page_evanoddall():
    html_style = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Lucida Console;background-color:lightblue;color:#871F78;}h1{padding:2vh;text-align:center;}div{margin:50px;border:1px solid #4CAF50;font-size:2rem;padding: 20px;} button{background-color: #FFFF00;font-size:1.5rem;width:100%;padding:12px 20px;margin:8px 0;} button:hover {opacity: 0.8;} .button2{background-color: #FFFF00;font-size:1.5rem;}
@media screen and (max-width: 300px)}"""
    style_end = """</style></head>"""
    return html_style + style_end + """<body> <h1>Select days</h1>
<form action="/" method="get" target="_self"><div><fieldset><input type="checkbox"  name="w" value="1" checked hidden><input type="checkbox"  name="0" value="Mon">Mon<br><input type="checkbox" name="1" value="Tue">Tue<br><input type="checkbox" name="2" value="Wed">Wed<br><input type="checkbox" name="3" value="Thu">Thur<br><input type="checkbox" name="4" value="Fri">Fri<br> <input type="checkbox" name="5" value="Sat">Sat<br><input type="checkbox" name="6" value="Sun">Sun<br><button type="submit" value="Submit">Submit</button></fieldset></div></form>
</body></html>"""