// https://randomnerdtutorials.com/esp8266-pinout-reference-gpios/
#include <Arduino.h>
#ifdef ESP32
    #include <WiFi.h>
#else
    #include <ESP8266WiFi.h>
#endif
#include <EEPROM.h>
#include <Hash.h>
#include <ESP8266WebServer.h>
#include <Ticker.h>
#include <Wire.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
//#include <SPI.h>  // not used here, but needed to prevent a RTClib compile error
#include "fauxmoESP.h"
#include "RTClib.h"
#define debug 1

#define SERIAL_BAUDRATE     115200
#define EEPROM_SIZE_T       512
#define LEN                 16
#define KEYLEN              16
#define MAX_DEVS            4

#define MON                 0x01 //1;   00000001
#define TUS                 0x02 //2;   00000010
#define WED                 0x04 //4;   00000100
#define THU                 0x08 //8;   00001000
#define FRI                 0x10 //16;  00010000
#define SAT                 0x20 //32;  00100000
#define SUN                 0x40 //64;  01000000
#define ALLDAYS             0x7F //01111111     //////0x80 //128; 10000000
#define UNMON               0xFE //254 bitwise &; 11111110
#define UNTUS               0xFD // 253 11111101
#define UNWED               0xFB // 11111011
#define UNTHU               0xF7 // 11110111
#define UNFRI               0xEF // 11101111
#define UNSAT               0xDF // 11011111
#define UNSUN               0x8F //10111111
///////////#define UNDAYS              0x7F //01111111

#define D5_GPIO14           14
#define D6_GPIO12           12
#define D7_GPIO13           13
// pins sutable for output only
#define D3_GPIO0            0
#define D4_GPIO2            2

#define D5_GPIO14block      1 // device number
#define D6_GPIO12block      2
/////#define D7_GPIO13block          5
// pins sutable for output only
#define D3_GPIO0block       3
#define D4_GPIO2block       4
Ticker secondTick;
volatile int watchdogCount = 0;

fauxmoESP fauxmo;
ESP8266WebServer server(80);
//ESP8266WebServer *server = (ESP8266WebServer*)malloc(sizeof(ESP8266WebServer));
char D_5[(LEN-2)+1],D_6[14+1],D_3[14+1],D_4[14+1];// last char is '\0'
bool D5onof,D6onof,D3onof,D4onof; // bool &presentState
uint8_t tmo = 100;
uint32_t Chipid;
uint32_t flashid;
// -----------------------------------------------------------------------------


const char header_html[] PROGMEM = R"rawliteral(
  <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Lucida Console;background-color:lightblue;color:#871F78;}h1{padding:2vh;text-align:center;}div{margin:70px;border:1px solid #4CAF50;font-size:1.5rem;} button{background-color: #FFFF00;font-size:1.5rem;width:100%;padding:12px 20px;margin:8px 0;} button:hover {opacity: 0.8;} .button2{background-color: #FFFF00;font-size:1.5rem;}
@media screen and (max-width: 300px)}form {border:3px solid #f1f1f1;} input[type=text], input[type=password],input[type=button]{width:100%;padding:12px 20px;margin:8px 0;display:inline-block;border: 1px solid #ccc;box-sizing: border-box;} .container{padding:16px;}</style></head>
)rawliteral";

const char sidpas_body_html[] PROGMEM = R"rawliteral(
  <body> <h2>IoT Web Server : Change Wifi SSID and Password</h2><form action="/wifi" method="get" target="_self"><fieldset><div class="container" style="background-color:#f1f1f1"><label for="ssid">New Wifi SSID:</label><input type="text" id="ssid" name="ssid" required><br><label for="paswd">New Wifi Password:</label><input type="password" id="paswd" name="paswd" required></div></fieldset><button type="submit">Set New Wifi SSID and Password</button></form></body></html>
  )rawliteral";
const char devices_body_html[] PROGMEM = R"rawliteral(
  <body> <h2>IoT Web Server : Change Devices Name</h2><form action="/devices" method="get" target="_self"><fieldset><div class="container" style="background-color:#f1f1f1"><label for="div1">Device 1 Name :</label><input type="text" id="div1" name="div1" required><br><label for="div2">Device 2 Name:</label><input type="text" id="div2" name="div2" required></div><br><label for="div3">Device 3 Name:</label><input type="text" id="div3" name="div3" required></div><br><label for="div4">Device 4 Name:</label><input type="text" id="div4" name="div4" required></div></fieldset><button type="submit">Set Devices Name</button></form></body></html>
  )rawliteral";
const char week_body_html[] PROGMEM = R"rawliteral(
  <body> <h2>IoT Web Server : Change Week Days On/Off</h2><form action="/week" method="get" target="_self"><fieldset><div class="container" style="background-color:#f1f1f1"><label for="dn">Device Number(1|2|3|4) :</label><input type="text" id="dn" name="dn" required><br><input type="checkbox" name="0" value="Mon">Mon<br><input type="checkbox" name="1" value="Tue">Tue<br><input type="checkbox" name="2" value="Wed">Wed<br><input type="checkbox" name="3" value="Thu">Thur<br><input type="checkbox" name="4" value="Fri">Fri<br> <input type="checkbox" name="5" value="Sat">Sat<br><input type="checkbox" name="6" value="Sun">Sun<br><button type="submit" value="Submit">Submit</button></div></fieldset></form></body></html>
  )rawliteral";
// -----------------------------------------------------------------------------
class wifieeprom {
  // 512 = 16 * 32;  dev(1) 0 to 15 dev(2) 16 to 31 dev(3) 32 to 47 dev(n) LB =16*(n-1) , UB = (16*n) - 1 for 1 <= n <= 32
    // ssid is n = 32 i.e. LB = 16*(32-1) = 496 to UB = 16*32 - 1 = 511
    // pass is n = 31 i.e. LB = 16*(31-1) = 480 to UB = 16*31 - 1 = 495
    // n(1 to 32) is block number in EEPROM; first byte LEN*(n-1) in block contains length of string which should less than equal to 15(block size LEN 16 - 1)
    //last byte(LEN*n-1) stores state onof (LEN - 1)
    // Device number is block number
    // nlen is number of char in davice name <= LEN-2(14); 
    ////static const uint16_t SIZE = 512;
    ////static const uint8_t LEN = 16; //length of block in char
    //LEN*(n-1)0 to (LEN*n)15 bytes are avalable; 
    //first byte LEN*(n-1) store length of name(namelen);
    //last byte(LEN*n-1) stores state onof (LEN - 1) in case of device name
    // so only 14(LEN-2) can be stored
  public:
    //uint8_t len; // number of char(MAX 14(LEN-2)) in blockdata
    //uint8_t nblock; // is n; invalid n is 0
    wifieeprom(){} //{datablock = NULL;nblock = 0;len=0;}
    ~wifieeprom(){}//{free(datablock);ESP.getFreeHeap();}
    
    static uint8_t length(uint8_t n){EEPROM.begin(EEPROM_SIZE_T);uint8_t l = (uint8_t)EEPROM.read(LEN*(n-1));EEPROM.end();return l;}
    static bool checkboundaries(uint8_t n,uint8_t l){return (n >= 1 and n <= 32) and (l <= (LEN - 2) and l > 0) ? true : false;}
    static bool checkBlockNumber(uint8_t n){return n >= 1 and n <= 32 ? true : false;}
    static bool checkBlockDataLen(uint8_t l){return l >= 1 and l <= LEN-2 ? true:false;}
    static void writebytes(const uint8_t * rawbytes, uint8_t rawbyteslen, uint8_t n);//16 bytes or namelen(first byte is count/number/length; so only 15 bytes contains data) number of bytes write;  n is block number in EEPROM
    static void writechar(const char * name, uint8_t namelen, uint8_t n);
    static uint8_t readbytes(uint8_t n,uint8_t *buff);
    static uint8_t readchar(uint8_t n, char *buff);
    static bool getDeviceState(uint8_t nblock){if(checkBlockNumber(nblock) && nblock <= 30){uint8_t n = nblock;EEPROM.begin(EEPROM_SIZE_T);bool onof = (bool)EEPROM.read(LEN*n-1);EEPROM.end();return onof;}else{return false;}}
    static void setDeviceState(uint8_t nblock, bool onof){if(nblock >= 1 && nblock <= 30){uint8_t n = nblock;EEPROM.begin(EEPROM_SIZE_T);EEPROM.write(LEN*n-1, onof);EEPROM.end();}}
};
void wifieeprom::writebytes(const uint8_t *rawbytes, uint8_t rawbyteslen, uint8_t n){
  if(checkBlockNumber(n) and checkBlockDataLen(rawbyteslen)){  
        EEPROM.begin(EEPROM_SIZE_T);
        EEPROM.write(LEN*(n-1), rawbyteslen);// LB =16*(n-1); it store count/number of bytes written
        for(int iadr = LEN*(n-1) + 1, irawbytes = 0; iadr <= (LEN*n-1)-1 and irawbytes < rawbyteslen;iadr++,irawbytes++)// UB = (16*n) - 1
          EEPROM.write(iadr, rawbytes[irawbytes]);
        ////////EEPROM.write(LEN*n-1, onof); // last byte for state
        EEPROM.end();
      }
}
void wifieeprom::writechar(const char * name, uint8_t namelen, uint8_t n){//nlen(MAX 14) is number of char in Device Name;  n is block/device number in EEPROM
  if(checkboundaries(n,namelen)){  
    EEPROM.begin(EEPROM_SIZE_T);
    EEPROM.write(LEN*(n-1), namelen);// LB =16*(n-1)
    for(int iadr = LEN*(n-1) + 1, iname = 0; iadr <= (LEN*n-1)-1 and iname < namelen;iadr++,iname++)// UB = (16*n) - 1
      EEPROM.write(iadr, (byte)name[iname]);
    ////////EEPROM.write(LEN*n-1, onof); // last byte for state
    EEPROM.end();
  }
}
uint8_t wifieeprom::readbytes(uint8_t n,uint8_t *buff){ 
  uint8_t l = 255;
  if(checkBlockNumber(n)){ 
    EEPROM.begin(EEPROM_SIZE_T);
    l = (uint8_t)EEPROM.read(LEN*(n-1));//LB = LEN*(n-1) first byte of nth block UB = (LEN*n) -1 last byte nth block
    //Serial.printf("wifi read N = %d\n",l);
    if(checkBlockDataLen(l)){
      for(int iadr = LEN*(n-1) + 1, irawbytes = 0; iadr <= (LEN*n-1)-1 and irawbytes < l;iadr++,irawbytes++)
        buff[irawbytes] = EEPROM.read(iadr);
    }
    EEPROM.end();
  }
  if(l <= LEN-2)
    return l;
  else
    return 0;
}
uint8_t wifieeprom::readchar(uint8_t n, char *buff){ // Device Name 
  uint8_t lenn = 255;
  if(checkBlockNumber(n)){ 
    EEPROM.begin(EEPROM_SIZE_T);
    lenn = (uint8_t)EEPROM.read(LEN*(n-1));//LB = LEN*(n-1) first byte of nth block UB = (LEN*16) -1 last byte nth block
    //Serial.printf("wifi read N = %d\n",lenn);
    if(checkBlockDataLen(lenn)){ // number of char(MAX 14(LEN-2)) in blockdata
      for(int iadr = LEN*(n-1) + 1, iname = 0; iadr <= (LEN*n-1)-1 and iname < lenn;iadr++,iname++)
        buff[iname] = (char)EEPROM.read(iadr);
      buff[lenn] = '\0';
    }
    EEPROM.end();
  }
  if(lenn <= LEN-2)
    return lenn;
  else
    return 0;
}
class encryp {
  char *key;
  public:
    encryp();
    ~encryp(){free(key);ESP.getFreeHeap();}//free(str);free(dstr);}
    char xor_encrypt(char c, uint8_t at_i_key){return c^key[at_i_key];}
    char xor_decrypt(char encrypted_c, uint8_t at_i_key){return encrypted_c^key[at_i_key];}
    bool xor_encrypt(char *s, uint8_t l);// char *s is plain text
    bool xor_decrypt(char *crypted, uint8_t l);
    String Key(){return String(key);}
};
encryp::encryp(){
  //len = 0;
  //str = NULL;
  //dstr = NULL;
  key= (char *)malloc((KEYLEN+1)*sizeof(char)); // one for null char
  String m = WiFi.macAddress();
  char tmp[7];
  itoa(ESP.getChipId(),tmp,16);
  key[0] = tmp[0];
  key[1] = tmp[1];
  uint8_t ik = 2;
  for(uint8_t i = 0; i < m.length() && ik < (2 + 12); i++){
    if(m.charAt(i) != ':'){
      key[ik] = m.charAt(i);
      ik++;
    }
  }
  key[14] = tmp[2];
  key[15] = tmp[3];
  //free(tmp);
  key[KEYLEN] = '\0';
  ESP.getFreeHeap();
}
bool encryp::xor_encrypt(char *s, uint8_t len){
  if(s != NULL && len <= KEYLEN && len > 0){
    ////str = (char *)malloc(len*sizeof(char));
    //Serial.printf("Length %d\n",len);
    for(uint8_t i = 0; i < len; i++){
      s[i] = xor_encrypt(s[i],i);
    }
    //Serial.printf("len %d\n",len);
    return true;
  }
  else
    return false;
}
bool encryp::xor_decrypt(char *crypted, uint8_t len){// member *crypted will be decrypted by this fn, so do not call clear()
  if(crypted != NULL and len <= KEYLEN && len > 0){
    //free(dstr);ESP.getFreeHeap();
    //dstr = (char *)malloc((len + 1)*sizeof(char));
    for(uint8_t i = 0; i < len; i++){
      crypted[i] = xor_decrypt(crypted[i],i);
    }
    //dstr[len] = '\0';
    //Serial.printf("string =%s;len =%d\n",dstr,len);
    //Serial.println(String(dstr));
    return true;
  }
  else
    return false;
}
class DevPinOut{
  public:
    static bool getDevName(char *dev_name,uint8_t devno_nblock,bool &presentState){presentState=wifieeprom::getDeviceState(devno_nblock);return wifieeprom::readchar(devno_nblock, dev_name) != 0 ? true : false;}
    static void saveDevName(String dev_name,uint8_t devno_nblock){wifieeprom::writechar(dev_name.c_str(),dev_name.length(), devno_nblock);wifieeprom::setDeviceState(devno_nblock, true);}
    static void PinOutPutMode(uint8_t p){pinMode(p, OUTPUT);}
    static void On(uint8_t p,uint8_t nblock, bool &presentState);
    static void Off(uint8_t p,uint8_t nblock, bool &presentState);
};
void DevPinOut::On(uint8_t p,uint8_t nblock, bool &presentState){
  if(!presentState){
    digitalWrite(p, HIGH);
    presentState = true;
    wifieeprom::setDeviceState(nblock, true);
  }
}
void DevPinOut::Off(uint8_t p,uint8_t nblock, bool &presentState){
  if(presentState){
    digitalWrite(p, LOW);
    presentState = false;
    wifieeprom::setDeviceState(nblock, false);
  }
}
class encrpeeprom{
  public:
    encryp cryp;
    //wifieeprom rom;
    encrpeeprom():cryp(){}
    void savessidpass(uint8_t sid_pass_nblock, String s){
      //Serial.printf("encrpeeprom SSID = %s\n",s);
      char sid_pas[s.length()];
      for(uint8_t i = 0; i < s.length();i++)
        sid_pas[i] = s.charAt(i);
      cryp.xor_encrypt(sid_pas,s.length());
      wifieeprom::writechar(sid_pas, s.length(), sid_pass_nblock);
    }
    void savessid(String s){savessidpass(32,s);}
    void savepass(String s){savessidpass(31,s);}
    String getssidpass(uint8_t sid_pass_nblock){
      char buff[14+1];
      uint8_t len = wifieeprom::readchar(sid_pass_nblock, buff);
      if(len != 0){
        cryp.xor_decrypt(buff,len);
        buff[len] = '\0';
        return String(buff);
      }
      return "";
    }
    String getssid(){return getssidpass(32);}
    String getpass(){return getssidpass(31);}
    // void readDevname(char *dev_name,uint8_t devno_nblock){
    //   uint8_t len = wifieeprom::readchar(devno_nblock, dev_name);
    //   Serial.printf("Device name in eeprom is : %s\n", dev_name);
    // }
    // void AllDevNames(){
    //   readDevname(D_5,D5_GPIO14block);
    //   readDevname(D_6,D6_GPIO12block);
    //   //readDevname(D_3,D3_GPIO0block);
    //   //readDevname(D_4,D4_GPIO2block);
    // }
};
class ds1307rtc{
  uint8_t uday; // day of ntp time from internet and adjusted RTC
  public:
    RTC_DS1307 RTC;
    ds1307rtc(){
    }
    void initRTC(){
      Wire.begin();
      RTC.begin();
      if (! RTC.isrunning()) {
        Serial.println("RTC is NOT running!");
        // following line sets the RTC to the date & time this sketch was compiled
        RTC.adjust(DateTime(__DATE__, __TIME__));
      }
      uday = RTC.now().day();
    }
    bool ntpadjustRTC(){
      WiFiUDP ntpUDP;
      NTPClient ntpClient = NTPClient(ntpUDP, "pool.ntp.org");
      ntpClient.begin();
      ntpClient.setTimeOffset(3600*5+1800);
      unsigned long rlast = millis();
      bool flag = ntpClient.update();
      while(!flag) {
        flag = ntpClient.forceUpdate();
        if ((millis() - rlast > 2000) && !flag){rlast = millis();} else {break;}
        flag = ntpClient.update();
      }
      if(flag){// Serial.println("ntp fail");return !flag;
        //String formattedDate = ntpClient.getFormattedTime();//.getFormattedDate();
        //Serial.printf("ntp time :%s\n",ntpClient.getFormattedTime());
        //Week Days
        //String weekDays[7]={"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"};

        //Month names
        //String months[12]={"January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"};
        //Serial.println(ntpClient.getEpochTime());
        time_t epochTime = ntpClient.getEpochTime();
        //Serial.print("Epoch Time: ");
        //Serial.println(epochTime);
        
        String formattedTime = ntpClient.getFormattedTime();
        // Serial.print("Formatted Time: ");
        // Serial.println(formattedTime);  

        
        int currentHour = ntpClient.getHours();
        // Serial.print("Hour: ");
        // Serial.println(currentHour);  

        int currentMinute = ntpClient.getMinutes();
        // Serial.print("Minutes: ");
        // Serial.println(currentMinute); 
        
        int currentSecond = ntpClient.getSeconds();
        // Serial.print("Seconds: ");
        // Serial.println(currentSecond);  

        // String weekDay = weekDays[ntpClient.getDay()];
        // Serial.print("Week Day: ");
        // Serial.println(weekDay);    
        delay(1000);
        //Get a time structure
        struct tm *ptm = gmtime((time_t *)&epochTime);
        
        // int monthDay = ptm->tm_mday;
        // Serial.print("Month day: ");
        // Serial.println(monthDay);

        // int currentMonth = ptm->tm_mon+1;
        // Serial.print("Month: ");
        // Serial.println(currentMonth);

        // String currentMonthName = months[currentMonth-1];
        // Serial.print("Month name: ");
        // Serial.println(currentMonthName);

        //int currentYear = ptm->tm_year+1900;
        // Serial.print("Year: ");
        // Serial.println(currentYear);
        // Serial.print("tm_year: ");
        // Serial.println(ptm->tm_year);

        //Print complete date:
        // String currentDate = String(currentYear) + "-" + String(currentMonth) + "-" + String(monthDay);
        // Serial.print("Current date: ");
        // Serial.println(currentDate);

        DateTime dt = DateTime(ptm->tm_year+1900,ptm->tm_mon,ptm->tm_mday,currentHour,currentMinute,currentSecond); //(year, month, day, hour, min, sec);
        RTC.adjust(dt);
      }
      else
        Serial.println("ntp fail");
      ntpClient.end();
      return flag;
    }
    void checkandupdateRTC(){ // once in a day
      if(uday < RTC.now().day()){
        if(ntpadjustRTC())
          uday = RTC.now().day();
      }
    }
    String date(char seaprator = ':'){//dd:mm:yyyy
      DateTime now = RTC.now();
      char d[11];
      d[10] = '\0';
      sprintf(&d[0],"%d%c",now.day(),seaprator);
      sprintf(&d[3],"%d%c",now.month(),seaprator);
      sprintf(&d[6],"%d",now.year());
      return String(d);
    }
    void printRTC(){
      DateTime now = RTC.now();
      Serial.print(now.year(), DEC);
      Serial.print('/');
      Serial.print(now.month(), DEC);
      Serial.print('/');
      Serial.print(now.day(), DEC);
      Serial.print(' ');
      Serial.print(now.hour(), DEC);
      Serial.print(':');
      Serial.print(now.minute(), DEC);
      Serial.print(':');
      Serial.print(now.second(), DEC);
      Serial.println();
      
      Serial.print(" since midnight 1/1/1970 = ");
      Serial.print(now.unixtime());
      Serial.print("s = ");
      Serial.print(now.unixtime() / 86400L);
      Serial.println("d");
    
      // calculate a date which is 7 days and 30 seconds into the future
      DateTime future (now.unixtime() + 7 * 86400L + 30);
      
      Serial.print(" now + 7d + 30s: ");
      Serial.print(future.year(), DEC);
      Serial.print('/');
      Serial.print(future.month(), DEC);
      Serial.print('/');
      Serial.print(future.day(), DEC);
      Serial.print(' ');
      Serial.print(future.hour(), DEC);
      Serial.print(':');
      Serial.print(future.minute(), DEC);
      Serial.print(':');
      Serial.print(future.second(), DEC);
      Serial.println();
      
      Serial.println();
    } 
};
class DevTime{
  // Time Schedule
  //uint8_t week; // 00000000(0)(None) 00000001(1)(Mon) 00000010(2)(Tus) 00000100(4)(Wed) 00001000(8)(Thr) 00010000(16)(Fri) 00100000(32)(Sat) 01000000(64)(Sun) 10000000(128)(All)
  //uint8_t on_h,on_m,on_s;
  //uint8_t of_h,of_m,of_s;
  //uint8_t nblock;
  bool isweekofday(uint8_t weekofday);
  bool _midnighttosunrise(ds1307rtc & rtc);
  bool is_bulbturn_day(ds1307rtc & rtc);
  public:
    DevTime(uint8_t nblock){this->nblock = nblock;}
    uint8_t nblock;
    uint8_t week_on_of[7];// week 0 
    //on_h 1,on_m 2,on_s 3, on in evening eg. 20H:30M
    //of_h 4,of_m 5,of_s 6;  off in morning 07H:30M
    bool enable; // ON OFF time schedule for pin is enable/disable
    void reset(){
      week_on_of[0] = ALLDAYS;
      week_on_of[1] = 20; // H
      week_on_of[2] = 30; // M
      week_on_of[3] = 0; // S
      week_on_of[4] = 7; // H
      week_on_of[5] = 30; // M
      week_on_of[6] = 0; // S
      enable = 1;
      save();
    }
    void setDay(uint8_t set){week_on_of[0] = week_on_of[0] | set;}// to set Monday setDay(MON); to unset Monday
    void unsetDay(uint8_t unset){week_on_of[0] = week_on_of[0] & unset;}// to unset Monday setDay(UNMON);
    bool isday(uint8_t day){return week_on_of[0] & day ? 1 : 0;} //to check isDay(MON)
    
    void ONOFF(ds1307rtc & rtc, uint8_t p, bool &presentState);
    
    // bool isMon(){return week_on_of[0] & (uint8_t)1u ? 1 : 0;}
    // bool isTus(){return week_on_of[0] & (uint8_t)2u ? 1 : 0;}
    // bool isWed(){return week_on_of[0] & (uint8_t)4u ? 1 : 0;}
    // bool isThr(){return week_on_of[0] & (uint8_t)8u ? 1 : 0;}
    // bool isFri(){return week_on_of[0] & (uint8_t)16u ? 1 : 0;}
    // bool isSat(){return week_on_of[0] & (uint8_t)32u ? 1 : 0;}
    // bool isSun(){return week_on_of[0] & (uint8_t)64u ? 1 : 0;}
    // bool isAll(){return week_on_of[0] & (uint8_t)128u ? 1 : 0;}
    // bool isNone(){return week_on_of[0] ? 1 : 0;}

    void save();
    void get();
    String print();
};
void DevTime::ONOFF(ds1307rtc & rtc, uint8_t p, bool &presentState){
  uint8_t h = rtc.RTC.now().hour();
  uint8_t m = rtc.RTC.now().minute();
      //uint8_t ofh = week_on_of[4]; // 07H:30M
      //uint8_t ofm = week_on_of[5];
  if(!is_bulbturn_day(rtc))
    DevPinOut::Off(p,nblock,presentState);
  else{
    if(h < week_on_of[4])
      DevPinOut::On(p,nblock,presentState);
    else 
      if(h == week_on_of[4]) // 07H:30M morning off
        if(m < week_on_of[5])
          DevPinOut::On(p,nblock,presentState); 
        else
          DevPinOut::Off(p,nblock,presentState);
      else //if(h > week_on_of[4]){ // 07H
        if(h < week_on_of[1]) // 20H on
          DevPinOut::Off(p,nblock,presentState);
        else 
          if(h == week_on_of[1]) // 20H
            if(m < week_on_of[2]) //30M
              DevPinOut::Off(p,nblock,presentState);
            else
              DevPinOut::On(p,nblock,presentState);
          else //if(h > week_on_of[1]){
            DevPinOut::On(p,nblock,presentState);
  }
}
void DevTime::save(){
  wifieeprom::setDeviceState(nblock,enable);
  wifieeprom::writebytes(week_on_of, 7, nblock);
}
void DevTime::get(){
  enable = wifieeprom::getDeviceState(nblock);
  wifieeprom::readbytes(nblock,week_on_of);
}
bool DevTime::is_bulbturn_day(ds1307rtc & rtc){
  uint8_t day = rtc.RTC.now().dayOfWeek();
  if(_midnighttosunrise(rtc))
    if(day == 0)
      return isweekofday(6);
    else
      return isweekofday(day - 1);
  else
    return isweekofday(day);
}
bool DevTime::_midnighttosunrise(ds1307rtc & rtc){
  uint8_t h = rtc.RTC.now().hour();
  uint8_t m = rtc.RTC.now().minute();
  if(h <= week_on_of[4])
    if(h == week_on_of[4])
      if(m < week_on_of[5])
        return true;
      else
        return false;
    else
      return true;
  else
    return false;
}
bool DevTime::isweekofday(uint8_t weekofday){
  if(weekofday == 0) {return isday(MON);}
  else if (weekofday == 1) {return isday(TUS);}
  else if (weekofday == 2) {return isday(WED);}
  else if (weekofday == 3) {return isday(THU);}
  else if (weekofday == 4) {return isday(FRI);}
  else if (weekofday == 5) {return isday(SAT);}
  else if (weekofday == 6) {return isday(SUN);}
  else {return 0;}
}
String DevTime::print(){
  //MTWTFSS
  char s[27];
  uint8_t i = 0;
  if(isday(MON)){s[i] = 'M';i++;}
  if(isday(TUS)){s[i] = 'T';i++;}
  if(isday(WED)){s[i] = 'W';i++;}
  if(isday(THU)){s[i] = 'T';i++;}
  if(isday(FRI)){s[i] = 'F';i++;}
  if(isday(SAT)){s[i] = 'S';i++;}
  if(isday(SUN)){s[i] = 'S';i++;}
  for(uint8_t z = 1; z <= 6; z++){
    sprintf(&s[i],"%2d:",week_on_of[z]);
    i = i + 3 + 1;
  }
  sprintf(&s[i],"%1d",enable);
  i = i + 1;
  s[i] = '\0';
  Serial.printf("DevTime = %s",s);
  return String(s);
}
ds1307rtc d1307rtc;
DevTime tD5(MAX_DEVS + 1), tD6(MAX_DEVS + 2), tD3(MAX_DEVS + 3), tD4(MAX_DEVS + 4);

void ISRwatchdog() {
  watchdogCount++;
  if ( watchdogCount == 20 ) {
     // Only print to serial when debugging
     (debug) && Serial.println("The dog bites!");
     ESP.reset();
  }
}
void setupfauxmo() {
    
    // By default, fauxmoESP creates it's own webserver on the defined port
    // The TCP port must be 80 for gen3 devices (default is 1901)
    // This has to be done before the call to enable()
    fauxmo.createServer(true); // not needed, this is the default value
    fauxmo.setPort(80); // This is required for gen3 devices

    // You have to call enable(true) once you have a WiFi connection
    // You can enable or disable the library at any moment
    // Disabling it will prevent the devices from being discovered and switched
    fauxmo.enable(true);

    // You can use different ways to invoke alexa to modify the devices state:
    // "Alexa, turn yellow lamp on"
    // "Alexa, turn on yellow lamp
    // "Alexa, set yellow lamp to fifty" (50 means 50% of brightness, note, this example does not use this functionality)
    
    // Add virtual devices
    //fauxmo.addDevice(dev1.c_str());
    //fauxmo.addDevice(dev2.c_str());
    // for(uint8_t i = 0; i < MAX_DEVS; i++)
    //   if(pnos.devs[i].getDeviceNum() > 0 && pnos.devs[i].getDevicename().length() > 0)
    //     fauxmo.addDevice(pnos.devs[i].getDevicename().c_str());
    fauxmo.addDevice(D_5);
    Serial.printf("Device D_5 in fauxmo : %s\n", D_5);
    fauxmo.addDevice(D_6);
    Serial.printf("Device D_6 in fauxmo : %s\n", D_6);
    // fauxmo.addDevice(D_5.getDevicename().c_str());
    // fauxmo.addDevice(D_6.getDevicename().c_str());
    //fauxmo.addDevice(D_3.getDevicename().c_str());
    //fauxmo.addDevice(D_4.getDevicename().c_str());
    //fauxmo.addDevice(pnos.devs[1].getname().c_str());
    // fauxmo.addDevice(ID_BLUE);
    // fauxmo.addDevice(ID_PINK);
    // fauxmo.addDevice(ID_WHITE);

    fauxmo.onSetState([](unsigned char device_id, const char * device_name, bool state, unsigned char value) {
        
        // Callback when a command from Alexa is received. 
        // You can use device_id or device_name to choose the element to perform an action onto (relay, LED,...)
        // State is a boolean (ON/OFF) and value a number from 0 to 255 (if you say "set kitchen light to 50%" you will receive a 128 here).
        // Just remember not to delay too much here, this is a callback, exit as soon as possible.
        // If you have to do something more involved here set a flag and process it in your main loop.
        
        Serial.printf("[MAIN] Device #%d (%s) state: %s value: %d\n", device_id, device_name, state ? "ON" : "OFF", value);

        // Checking for device_id is simpler if you are certain about the order they are loaded and it does not change.
        // Otherwise comparing the device_name is safer.
        if (strcmp(device_name, D_5)==0) {
          digitalWrite(D5_GPIO14, state ? HIGH : LOW);
          wifieeprom::setDeviceState(D5_GPIO14block, state);//EEPROM.begin(EEPROM_SIZE_T);EEPROM.write(LEN*D5_GPIO14block-1, state);EEPROM.end();
          return;
          }
        if (strcmp(device_name, D_6)==0) {
          digitalWrite(D6_GPIO12, state ? HIGH : LOW);
          wifieeprom::setDeviceState(D6_GPIO12block, state);//EEPROM.begin(EEPROM_SIZE_T);EEPROM.write(LEN*D6_GPIO12block-1, state);EEPROM.end();
          return;
        }
        //if (strcmp(device_name, D_6.getDevicename().c_str())==0) {D_6.toggal(state);return;}
        //if (strcmp(device_name, D_3.getDevicename().c_str())==0) {D_3.toggal(state);return;}
        //if (strcmp(device_name, D_4.getDevicename().c_str())==0) {D_4.toggal(state);return;}
        // if (strcmp(device_name, dev1.c_str())==0) {
        //     digitalWrite(D1_GPIO5, state ? HIGH : LOW);
        // } else if (strcmp(device_name, dev2.c_str())==0) {
        //     digitalWrite(D2_GPIO4, state ? HIGH : LOW);
        
        // } else if (strcmp(device_name, ID_BLUE)==0) {
        //     digitalWrite(LED_BLUE, state ? HIGH : LOW);
        // } else if (strcmp(device_name, ID_PINK)==0) {
        //     digitalWrite(LED_PINK, state ? HIGH : LOW);
        // } else if (strcmp(device_name, ID_WHITE)==0) {
        //     digitalWrite(LED_WHITE, state ? HIGH : LOW);
        //}

    });
}
void defWebPage(){
  if(server.args() == 0)
    server.send(200, "text/html", String(header_html) + String(sidpas_body_html));
  else
  { // Write ssid and paswd to eeprom
    if(server.argName(0) == "ssid" && server.argName(1) == "paswd"){
      //Serial.printf("server.arg(0) = %s; server.arg(1) = %s\n", server.arg(0),server.arg(1));
      String newsid(server.arg(0)), newpass(server.arg(1));
      encrpeeprom cryprom;
      cryprom.savessid(newsid);
      cryprom.savepass(newpass);
      
      //Serial.printf("Web SSID from eeprom is : %s\n", wp.GetSsid());
      //Serial.printf("Web PASS from eeprom is : %s\n", wp.GetPass());
      server.send(200, "text/html", "<!DOCTYPE html><html><head></head><body>Done:" + cryprom.getssid() + ":" + cryprom.getpass() + "</body></html>");
      delay(100);
      ESP.restart();
    }
    else
      server.send(200, "text/html", String(header_html) + String(sidpas_body_html));
  }
  ESP.getFreeHeap();
}
void PageDeviesName(){
  if(server.args() == 0)
    server.send(200, "text/html", String(header_html) + String(devices_body_html));
  else{ // Write ssid and paswd to eeprom
    wifieeprom wp;
    if(server.argName(0) == "div1"){
      String newdev1(server.arg(0));
      wp.writechar(newdev1.c_str(), newdev1.length(), D5_GPIO14block);
      wp.readchar(D5_GPIO14block, D_5);
    }
    if(server.argName(1) == "div2"){
      //Serial.printf("server.arg(0) = %s; server.arg(1) = %s\n", server.arg(0),server.arg(1));
      String newdev2(server.arg(1));
      wp.writechar(newdev2.c_str(), newdev2.length(), D6_GPIO12block);
      wp.readchar(D6_GPIO12block, D_6);
    }
    if(server.argName(2) == "div3"){
      //Serial.printf("server.arg(0) = %s; server.arg(1) = %s\n", server.arg(0),server.arg(1));
      String newdev3(server.arg(2));
      wp.writechar(newdev3.c_str(), newdev3.length(), D3_GPIO0block);
      wp.readchar(D3_GPIO0block, D_3);
    }
    if(server.argName(3) == "div4"){
      //Serial.printf("server.arg(0) = %s; server.arg(1) = %s\n", server.arg(0),server.arg(1));
      String newdev4(server.arg(3));
      wp.writechar(newdev4.c_str(), newdev4.length(), D4_GPIO2block);
      wp.readchar(D4_GPIO2block, D_4);
    }
  }
  if(server.args() > 3)
    server.send(200, "text/html", String(header_html) + String(sidpas_body_html));
  else{
    server.send(200, "text/html", "<!DOCTYPE html><html><head></head><body>Done:" + String(D_5) + ":" + String(D_6) + ":" + String(D_3) + ":" + String(D_4)+ "</body></html>");
    delay(100);
    ESP.restart();
  }
  ESP.getFreeHeap();
}
void weekpage(){
  if(server.args() == 0)
    server.send(200, "text/html", String(header_html) + String(week_body_html));
  else{ // Write ssid and paswd to eeprom
        uint8_t week = 0x00;
        if(server.argName(1) == "0"){
            String MoN(server.arg(1));
            if(MoN == "Mon"){week = week | MON;}
        }
        String TuE(server.arg(2));
        if(TuE == "Tue"){week = week | TUS;}
        String WeD(server.arg(3));
        if(WeD == "Wed"){week = week | WED;}
        String ThU(server.arg(4));
        if(ThU == "Thu"){week = week | THU;}
        String FrI(server.arg(5));
        if(FrI == "Fri"){week = week | FRI;}
        String SaT(server.arg(6));
        if(SaT == "Sat"){week = week | SAT;}
        String SuN(server.arg(7));
        if(SuN == "Sun"){week = week | SUN;}
        if(server.argName(0) == "dn"){
          String dev(server.arg(0));
          if(dev == "1"){tD5.get(); tD5.week_on_of[0] = week; tD5.save();}
          if(dev == "2"){tD6.get(); tD6.week_on_of[0] = week; tD6.save();}
          if(dev == "3"){tD3.get(); tD3.week_on_of[0] = week; tD3.save();}
          if(dev == "4"){tD4.get(); tD4.week_on_of[0] = week; tD4.save();}
        }
      }
}

void resetDevs(){
  DevPinOut::saveDevName("Device1", D5_GPIO14block);
  DevPinOut::saveDevName("Device2", D6_GPIO12block);
  DevPinOut::saveDevName("Device3", D3_GPIO0block);
  DevPinOut::saveDevName("Device4", D4_GPIO2block);
  tD5.reset(); // nblock
  tD6.reset();
  tD3.reset(); 
  tD4.reset();
}
void statusDevs(){

}
// void setup(){
//   resetDevs();
// }
// void loop(){}
void setup(){
  // Init serial port and clean garbage
  Serial.begin(SERIAL_BAUDRATE);
  secondTick.attach(1, ISRwatchdog);
  Serial.println();
  Serial.println();
  //resetDevs();
  // read devices names from eeprom
  DevPinOut::getDevName(D_5,D5_GPIO14block,D5onof);
  DevPinOut::getDevName(D_6,D6_GPIO12block,D6onof);
  DevPinOut::getDevName(D_3,D3_GPIO0block,D3onof);
  DevPinOut::getDevName(D_4,D4_GPIO2block,D4onof);
  tD5.get();
  tD6.get();
  tD3.get();
  tD4.get();
  tD5.print();
  tD6.print();
  tD3.print();
  tD4.print();
  // setup Pin Modes to OUTPUT
  DevPinOut::PinOutPutMode(D5_GPIO14);
  DevPinOut::PinOutPutMode(D6_GPIO12);
  DevPinOut::PinOutPutMode(D3_GPIO0);
  DevPinOut::PinOutPutMode(D4_GPIO2);
  //d1307rtc.initRTC();
  //d1307rtc.printRTC();
  
  Serial.println();
  encrpeeprom cryprom;
  Serial.println(cryprom.cryp.Key());
  //cryprom.savepass("99719897722");
  Serial.printf("ssid : %s; paswd : %s\n",cryprom.getssid(),cryprom.getpass());
  
  // Wifi
  // Set WIFI module to STA mode
  WiFi.mode(WIFI_STA);

  Serial.printf("getSketchSize : %d\n", ESP.getSketchSize());
  Serial.printf("getFreeSketchSpace : %d\n", ESP.getFreeSketchSpace());

  Serial.printf("getFlashChipSizeByChipId : %d\n", ESP.getFlashChipSizeByChipId());
  Serial.printf("getFlashChipSize : %d\n", ESP.getFlashChipSize());
  // Connect
  WiFi.begin(cryprom.getssid(),cryprom.getpass());
  // Wait
  while (WiFi.status() != WL_CONNECTED) {
      Serial.print(".");
      delay(100);
      tmo -= 1;
      if(tmo == 0)
        break;
  }
  if(tmo == 0){
    WiFi.disconnect();
    delay(100);
    WiFi.mode(WIFI_AP);
    WiFi.softAP("DeziWebApp","DeziWebApp",1,0,1);
    delay(100);
    Serial.println();
    Serial.printf("tmo = %d",tmo);
    Serial.println();
    Serial.print("Soft-AP IP address = ");
    Serial.println(WiFi.softAPIP());
    
    // Route for root / web page
    server.on("/wifi",defWebPage);
    server.on("/devices",PageDeviesName);
    server.on("/week",weekpage);
    server.begin();
    Serial.println();
    Serial.println("HTTP server started");
  }
  else{
    Serial.println();
    d1307rtc.ntpadjustRTC();
    d1307rtc.printRTC();
    // Connected!
    server.stop(); // Stop Webserver for ssid and paswd change
    Serial.printf("[WIFI] STATION Mode, SSID: %s, IP address: %s\n", WiFi.SSID().c_str(), WiFi.localIP().toString().c_str());
    setupfauxmo();
  }
}
//void loop() {}
void loop() {
  // Feeding the dog
  watchdogCount = 0;
  if(tmo != 0){
    // fauxmoESP uses an async TCP server but a sync UDP server
    // Therefore, we have to manually poll for UDP packets
    fauxmo.handle();

    // This is a sample code to output free heap every 5 seconds
    // This is a cheap way to detect memory leaks
    static unsigned long last = millis();
    if (millis() - last > 5000) {
        last = millis();
        ESP.getFreeHeap();
        d1307rtc.checkandupdateRTC();
        //Serial.printf("[MAIN] Free heap: %d bytes\n", ESP.getFreeHeap());
    }
  }
  else{
    //Serial.printf("[handleClient] tmo: %d\n", tmo);
    server.handleClient();
  }
}
