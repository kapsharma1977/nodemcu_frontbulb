import ujson
def set_datetime_element(rtc, h=5, m=30):
    date = list(rtc.datetime())
    date[4] = date[4] + h
    date[5] = date[5] + m
    rtc.datetime(date)
def initializeRTC(wlan, rtc):
    import ntptime
    try:
        if wlan.isconnected():
            ntptime.settime()
            set_datetime_element(rtc)
            return True
        else:
            return False
    except Exception as e:
        import sys
        sys.print_exception(e)
        print('ntptime out')
        return False
def json_savetofile(fname,jsondata):
    with open(fname, 'w') as fd:
        ujson.dump(jsondata, fd)
def json_getfromfile(fname):
    try:
        with open(fname, 'r') as fd:
            return ujson.load(fd)
    except Exception as e:
        import sys
        sys.print_exception(e)
        print('read error')
        return False
def getsidpaswd():
    try:
        _jsonstr = json_getfromfile('paswd.json')
        return ujson.loads(_jsonstr)
    except:
        u_sidpaswd({"ssid":"Jiya","paswd":"9971989772"})
        return {"ssid":"Jiya","paswd":"9971989772"}
def u_sidpaswd(params):
    _jsonstr = ujson.dumps(params)
    json_savetofile('paswd.json',jsondata=_jsonstr)
def getlasttime():
    try:
        _jsonstr = json_getfromfile('time.json')
        return ujson.loads(_jsonstr)
    except Exception as e:
        import sys
        sys.print_exception(e)
def loadweek(envweek):
    try:
        _jsonstr = json_getfromfile('week.json')
        _json = ujson.loads(_jsonstr)
        envweek.clear()
        envweek.update(_json)
    except Exception as e:
        import sys
        sys.print_exception(e)
        week = {'0':'Mon', '1':'Tue', '2':'Wed', '3':'Thu', '4':'Fri', '5':'Sat', '6':'Sun'}
        envweek.clear()
        envweek.update(week)
        _jsonstr = ujson.dumps(week)
        json_savetofile('week.json',jsondata=_jsonstr)
        print(f"envweek={envweek}")
        print(f"week={week}")
def updatedays_selection(params, envweek):
    for key in envweek:
        envweek[key] = ''
    for key in params:
        if key in envweek:
            envweek[key] = params[key]
    _jsonstr = ujson.dumps(envweek)
    json_savetofile('week.json',jsondata=_jsonstr)
def sunrise(month):
    try:
        _jsonstr = json_getfromfile('sunrise.json')
        _json = ujson.loads(_jsonstr)
        return _json[month]
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
        _jsonstr = ujson.dumps(sunrise)
        json_savetofile('sunrise.json',_jsonstr)
        return _json[month]
def sunset(month):
    try:
        _jsonstr = json_getfromfile('sunset.json')
        _json = ujson.loads(_jsonstr)
        return _json[month]
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
        _jsonstr = ujson.dumps(sunset)
        json_savetofile('sunset.json',_jsonstr)
        return _json[month]