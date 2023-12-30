import config as c
from frontgateblub import bulb
from env import env
PASSWORD = '/password'
EVENODDALL ='/evenodd'
def WDTtick(p_en=""):
    c.WDTcon+=1
    if p_en!="": print("WDT: "+str(c.WDTcon)+" WDTtrigger: "+str(c.WDTtrigger))
    if c.WDTcon>(c.WDTtrigger-1):
        import machine
        WDTkill(p_en)
        if p_en!="": print("############ WDT RESET! #############")
        utime.sleep_ms(900) # So you have time to see on screen why it is resetting...
        machine.reset()
def WDTfeed(p_en=""):
    if c.WDT_enable==0:
        c.WDTobj.deinit()
        return
    if p_en!="": print("WDT fed!")
    c.WDTobj.deinit()
    c.WDTcon=0
    c.WDTobj.init(period=c.WDTtimval, mode=Timer.PERIODIC, callback=lambda x: WDTtick(p_en))
def WDTkill(p_en=""):
    c.WDTobj.deinit()
    c.WDT_enable=0
    if p_en!="": print ("WDT dead!!")
def wlandisconnect(fb):
    fb.relaysoff()
    utime.sleep_ms(200)
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
def espweserver(poller, frontbulb: bulb, vne: env):
    try:
        response = ""
        res = poller.poll(3000)  # time in milliseconds
        if res:
            #print(f"res = {res} type = {type(res)}")
            for sock, ev in res:
                #print(f"sock = {sock} type = {type(sock)} id = {id(sock)}")
                if ev & (uselect.POLLHUP | uselect.POLLERR):
                    print(f"error uselect.POLLHUP | uselect.POLLERR")
                    return
                conn, addr = sock.accept()
                conn.settimeout(3)
                request = conn.recv(1024)
                request = str(request)
                if request.find(PASSWORD) == 6:
                    from pages import web_page_password
                    response = web_page_password()
                if request.find(EVENODDALL) == 6:
                    from pages import web_page_evanoddall
                    response = web_page_evanoddall()
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
                    if 'manual'in params:
                        if params['manual'] == 'on':
                            frontbulb.manualmodeon(is_bulbturnday = vne.is_bulbturn_day(),is_morning = vne.ismorning(),is_evening = vne.isevening())
                        if params['manual'] == 'off':
                            frontbulb.manualmodeoff(is_bulbturnday = vne.is_bulbturn_day(),is_morning = vne.ismorning(),is_evening = vne.isevening())
                    if 'bulb'in params:
                        if params['bulb'] == 'on':
                            frontbulb.bulbon()
                        if params['bulb'] == 'off':
                            frontbulb.bulboff()
                    if 'ssid' in params and 'paswd' in params:
                        from env_static import u_sidpaswd
                        u_sidpaswd(params)
                        vne.pass_ch = 1
                    if 'w' in params:
                        from env_static import updatedays_selection
                        updatedays_selection(params, vne.week)
                if response == "":
                    from pages import web_page
                    response = web_page(vne = vne, bb = frontbulb, rtc = rtc,sleepnap = str(vne.sleepornap()))
                conn.send('HTTP/1.1 200 OK\n')
                conn.send('Content-Type: text/html\n')
                conn.send('Connection: close\n\n')
                conn.sendall(response)
                #print(f"sock = {sock} type = {type(sock)} id = {id(sock)}")
                #print(f"conn = {conn} type = {type(conn)} id = {id(conn)}")
                conn.close()
                if vne.pass_ch == 1:
                    vne.pass_ch = 0
                    print('Password Rest')
                    utime.sleep_ms(400)
                    machine.reset()
    except Exception as e:
            import sys
            sys.print_exception(e)
            print(f"OSError : {e}")
            conn.close()
            utime.sleep_ms(200)
##
if machine.reset_cause() != machine.SOFT_RESET:
    wlan = network.WLAN(network.STA_IF)
vne = env(rtc=rtc,STA_AP='STA_IF')
frontbulb = bulb()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#print(f"s = {s} id = {id(s)}")
poller = uselect.poll()
poller.register(s, uselect.POLLIN)
tim = Timer(-1) # Create Timer instance
c.WDTobj=tim # Give it a 'c. reference'
try:
    s.bind(('', 80))
    s.listen(5)
except Exception as e:
    import sys
    sys.print_exception(e)
utime.sleep_ms(1000)
while True:
    if vne.STA_AP == 'AP_IF':
        espweserver(poller, frontbulb=frontbulb, vne=vne)
    else:
        if not wlan.isconnected():
            print('\nBlub is not Conneted to Wifi')
            if not vne.w_notconnected(wlan,rtc,frontbulb,vne):
                continue
        else:
            gc.collect()
            #WDTfeed(p_en="p")
            WDTfeed()
            try:
                if vne.STA_AP == 'STA_IF':
                    frontbulb.updaterelays(is_bulbturnday = vne.is_bulbturn_day(),is_morning = vne.ismorning(),is_evening = vne.isevening())
                    vne.clocksync(wlan=wlan)
                    utime.sleep(vne.sleepornap())
                espweserver(poller, frontbulb=frontbulb, vne=vne)
            except Exception as e:
                import sys
                sys.print_exception(e)
                print(f"OSError : {e}")
                conn.close()
                utime.sleep_ms(200)