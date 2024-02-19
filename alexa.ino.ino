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
//#include <SPI.h>  // not used here, but needed to prevent a RTClib compile error
#include "fauxmoESP.h"
#include "RTClib.h"

fauxmoESP fauxmo;
ESP8266WebServer server(80);

Ticker secondTick;
volatile int watchdogCount = 0;


//String dev1, dev2;
uint8_t tmo = 100;
uint32_t Chipid;
uint32_t flashid;
// -----------------------------------------------------------------------------
#define debug 1

#define SERIAL_BAUDRATE     115200
#define EEPROM_SIZE_T       512

const char header_html[] PROGMEM = R"rawliteral(
  <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Lucida Console;background-color:lightblue;color:#871F78;}h1{padding:2vh;text-align:center;}div{margin:70px;border:1px solid #4CAF50;font-size:1.5rem;} button{background-color: #FFFF00;font-size:1.5rem;width:100%;padding:12px 20px;margin:8px 0;} button:hover {opacity: 0.8;} .button2{background-color: #FFFF00;font-size:1.5rem;}
@media screen and (max-width: 300px)}form {border:3px solid #f1f1f1;} input[type=text], input[type=password],input[type=button]{width:100%;padding:12px 20px;margin:8px 0;display:inline-block;border: 1px solid #ccc;box-sizing: border-box;} .container{padding:16px;}</style></head>
)rawliteral";

const char sidpas_body_html[] PROGMEM = R"rawliteral(
  <body> <h2>IoT Web Server : Change Wifi SSID and Password</h2><form action="/wifi" method="get" target="_self"><fieldset><div class="container" style="background-color:#f1f1f1"><label for="ssid">New Wifi SSID:</label><input type="text" id="ssid" name="ssid" required><br><label for="paswd">New Wifi Password:</label><input type="password" id="paswd" name="paswd" required></div></fieldset><button type="submit">Set New Wifi SSID and Password</button></form></body></html>
  )rawliteral";
const char devices_body_html[] PROGMEM = R"rawliteral(
  <body> <h2>IoT Web Server : Change Devices Name</h2><form action="/devices" method="get" target="_self"><fieldset><div class="container" style="background-color:#f1f1f1"><label for="div1">Device 1 Name :</label><input type="text" id="div1" name="div1" required><br><label for="div2">Device 2 Name:</label><input type="text" id="div2" name="div2" required></div></fieldset><button type="submit">Set Devices Name</button></form></body></html>
  )rawliteral";
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// Wifi
// -----------------------------------------------------------------------------


class encryp {
  static const uint8_t KEYLEN = 16;
  char *key;
  uint8_t len;
  char *str; // encrypted
  char *dstr;// decrypted
  
  public:
    encryp(){
      len=0;
      str = NULL;
      dstr = NULL;
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
    ~encryp(){free(key);free(str);free(dstr);ESP.getFreeHeap();}
    void clear(){free(str);free(dstr);ESP.getFreeHeap();str = NULL;dstr = NULL;len=0;}
    //char xor_encrypt(char c, uint8_t at_i_key){return (at_i_key >= 0 && at_i_key < KEYLEN && c != '\0') ? c^key[at_i_key] : '\0';}
    char xor_encrypt(char c, uint8_t at_i_key){return c^key[at_i_key];}
    char * xor_encrypt(String s){//char *string, uint8_t slen)
      if(s.length() <= KEYLEN && s.length() > 0){
        clear();
        len = s.length();
        str = (char *)malloc(len*sizeof(char));
        //Serial.printf("Length %d\n",len);
        for(uint8_t i = 0; i < len; i++){
          str[i] = xor_encrypt(s.charAt(i),i);
          //Serial.printf("Char at xor_encrypt(String s) = %c \tstr = %c\n",s.charAt(i),str[i]^key[i]);
          // if(tmp != '\0')
          //   str[i] = tmp;
          // else{
          //   Serial.printf(" char = %c Loop Break %d tmp = %c \n",s.charAt(i), i, tmp);
          //   break;
          // }
        }
        //Serial.printf("len %d\n",len);
        return str;
      }
      else
        {return NULL;}
    }
    String xor_decrypt(){// member *str is decrypted by this fn, so do not call clear()
      if(str != NULL and len > 0){
        if(dstr != NULL){free(dstr);ESP.getFreeHeap();}
        dstr = (char *)malloc((len + 1)*sizeof(char));
        for(uint8_t i = 0; i < len; i++){
          dstr[i] = xor_decrypt(str[i],i);
        }
        dstr[len] = '\0';
        //Serial.printf("string =%s;len =%d\n",dstr,len);
        //Serial.println(String(dstr));
        return String(dstr);
      }
      else
        return "";
    }
    //char xor_decrypt(char encrypted_c, uint8_t at_i_key){return (at_i_key >= 0 && at_i_key < KEYLEN) ? encrypted_c^key[at_i_key] : '\0';}
    char xor_decrypt(char encrypted_c, uint8_t at_i_key){return encrypted_c^key[at_i_key];}
    String xor_decrypt(char *str, uint8_t len){
      if(str != NULL and len > 0){
        clear();
        this->str = str;
        this->len = len;
        return this->xor_decrypt();
      }
      else
        return "";

    }
    uint8_t length(){return (len > 0 && len < KEYLEN) ? len : 0;}
    String Key(){return String(key);}
    char keycharat(uint8_t i){return (i >= 0 && i < KEYLEN) ? key[i] : '\0';}
    char strcharat(uint8_t i){return (i >= 0 && i < KEYLEN && str != NULL) ? str[i] : '\0';}
    char dstrcharat(uint8_t i){return (i >= 0 && i < KEYLEN && dstr != NULL) ? dstr[i] : '\0';}
};
class wifieeprom {
  // 512 = 16 * 32;  dev(1) 0 to 15 dev(2) 16 to 31 dev(3) 32 to 47 dev(n) LB =16*(n-1) , UB = (16*n) - 1 for 1 <= n <= 32
    // ssid is n = 32 i.e. LB = 16*(32-1) = 496 to UB = 16*32 - 1 = 511
    // pass is n = 31 i.e. LB = 16*(31-1) = 480 to UB = 16*31 - 1 = 495
    // n(1 to 32) is block number in EEPROM; first byte LEN*(n-1) in block contains length of string which should less than equal to 15(block size LEN 16 - 1)
    //last byte(LEN*n-1) stores state onof (LEN - 1)
    // Device number is block number
    // nlen is number of char in davice name <= LEN-2(14); 
    static const uint16_t SIZE = 512;
    static const uint8_t LEN = 16; //length of block in char
  private:
    char *blockdata;
    uint8_t len; // number of char(MAX 14(LEN-2)) in blockdata
    uint8_t nblock; // is n
    //LEN*(n-1)0 to (LEN*n)15 bytes are avalable; 
    //first byte LEN*(n-1) store length of name(namelen);
    //last byte(LEN*n-1) stores state onof (LEN - 1)
    // so only 14(LEN-2) can be stored
    void write(const char * name, uint8_t namelen, uint8_t n){//nlen(MAX 14) is number of char in Device Name;  n is block/device number in EEPROM
      if(checkboundaries(n,namelen)){  
        EEPROM.begin(EEPROM_SIZE_T);
        EEPROM.write(LEN*(n-1), namelen);// LB =16*(n-1)
        for(int iadr = LEN*(n-1) + 1, iname = 0; iadr <= (LEN*n-1)-1 and iname < namelen;iadr++,iname++)// UB = (16*n) - 1
          EEPROM.write(iadr, (byte)name[iname]);
        ////////EEPROM.write(LEN*n-1, onof); // last byte for state
        EEPROM.end();
      }
    }
    void write(encryp &cryp, uint8_t n){
      if(checkboundaries(n,cryp.length())){
        EEPROM.begin(EEPROM_SIZE_T);
        EEPROM.write(LEN*(n-1), cryp.length());
        for(int iadr = LEN*(n-1) + 1, iname = 0; iadr <= (LEN*n-1)-1 and iname < cryp.length();iadr++,iname++)//{
          EEPROM.write(iadr, (byte)cryp.strcharat(iname));
          //Serial.printf("Char at write encryp \tstr = %c\n",cryp.strcharat(iname)^cryp.keycharat(iname));
        //}
        EEPROM.end();
      }
      //Serial.printf("Write encrypt string = %s\n",cryp.xor_decrypt());
    }
    void read(uint8_t n){
      if(checkBlockNumber(n)){ 
        EEPROM.begin(EEPROM_SIZE_T);
        len = (uint8_t)EEPROM.read(LEN*(n-1));//LB = LEN*(n-1) first byte of nth block UB = (LEN*16) -1 last byte nth block
        //Serial.printf("wifi read N = %d\n",len);
        if(checkBlockDataLen(len)){ // number of char(MAX 14(LEN-2)) in blockdata
          free(blockdata);
          nblock = n;
          blockdata = (char*)malloc((len + 1) * sizeof(char));
          for(int iadr = LEN*(n-1) + 1, iname = 0; iadr <= (LEN*n-1)-1 and iname < len;iadr++,iname++)
            blockdata[iname] = (char)EEPROM.read(iadr);
          blockdata[len] = '\0';
        }
        else{
          free(blockdata);
          nblock = 0;
          blockdata = NULL;
          len=0;
        }
        EEPROM.end();
      }
      ESP.getFreeHeap();
    }
    void read(encryp &cryp, uint8_t n){
      if(checkBlockNumber(n)){ // MAX DEVICES is 30 = (32 -2) = 512/16 - 2; two blocks for ssid and password
        EEPROM.begin(EEPROM_SIZE_T);
        len = (uint8_t)EEPROM.read(LEN*(n-1));//LB = LEN*(n-1) first byte of nth block UB = (LEN*16) -1 last byte nth block
        //Serial.printf("wifi read N = %d\n",len);
        if(checkBlockDataLen(len)){ // number of char(MAX 14(LEN-2)) in blockdata
          free(blockdata);
          nblock = n;
          blockdata = (char*)malloc((len + 1) * sizeof(char));
          for(int iadr = LEN*(n-1) + 1, iname = 0; iadr <= (LEN*n-1)-1 and iname < len;iadr++,iname++)//{
            blockdata[iname] = cryp.xor_decrypt((char)EEPROM.read(iadr),iname);
          //}
          blockdata[len] = '\0';
          //Serial.printf("Crypt Read = %s\n",blockdata);
        }
        else{
          free(blockdata);
          nblock = 0;
          blockdata = NULL;
          len=0;
        }
        EEPROM.end();
      }
      ESP.getFreeHeap();
    }
  public:
    wifieeprom() {blockdata = NULL;nblock = 0;len=0;}
    ~wifieeprom(){free(blockdata);ESP.getFreeHeap();}
    //String GetSsid(){read(32); return blockdata != NULL ? String(blockdata) : "";}
    //String GetPass(){read(31); return blockdata != NULL ? String(blockdata) : "";}
    void clearblockdata(){free(blockdata);ESP.getFreeHeap();blockdata = NULL;nblock = 0;len=0;}
    uint8_t length(uint8_t n){EEPROM.begin(EEPROM_SIZE_T);uint8_t l = (uint8_t)EEPROM.read(LEN*(n-1));EEPROM.end();return l;}
    bool checkboundaries(uint8_t n,uint8_t l){if(n >= 1 and n <= 32 and l <= (LEN - 2)){return 1;}else{return 0;}}
    bool checkBlockNumber(uint8_t n){if(n >= 1 and n <= 32){return 1;}else{return 0;}}
    bool checkBlockDataLen(uint8_t l){if(l >= 1 and l <= LEN-2){return 1;}else{return 0;}}
    uint8_t GetSsidlen(){return length(32);}
    uint8_t GetPasslen(){return length(31);}
    char* GetSsid(){read(32); return blockdata != NULL ? blockdata : NULL;}
    char* GetSsid(encryp &cryp){read(cryp,32); return blockdata != NULL ? blockdata : NULL;}
    char* GetPass(){read(31); return blockdata != NULL ? blockdata : NULL;}
    char* GetPass(encryp &cryp){read(cryp,31); return blockdata != NULL ? blockdata : NULL;}

    void SaveSsid(String s){ write(s.c_str(),(uint8_t)s.length(),32);}
    void SaveSsid(String s,encryp &cryp){cryp.xor_encrypt(s);write(cryp,32);}
    void SaveSsid(char *s,uint8_t len){ write(s,len,32);}
    void SavePass(String s){ write(s.c_str(),(uint8_t)s.length(),31);}
    void SavePass(String s,encryp &cryp){cryp.xor_encrypt(s);write(cryp,31);}
    void SavePass(char *s,uint8_t len){ write(s,len,31);}
    String GetDevice(uint8_t blocknum){if(checkBlockNumber(blocknum) && blocknum <= 30) {read(blocknum);return blockdata != NULL ? String(blockdata) : "";} else {return "";}}
    bool SaveDevice(String dev_name, uint8_t blocknum){if(checkBlockNumber(blocknum) && blocknum <= 30 && dev_name.length() > 0){write(dev_name.c_str(),(uint8_t)dev_name.length(),blocknum); return 1;}else{return 0;}}
    bool getDeviceState(uint8_t blocknum){if(checkBlockNumber(blocknum) && blocknum <= 30){uint8_t n = blocknum;EEPROM.begin(EEPROM_SIZE_T);bool onof = (bool)EEPROM.read(LEN*n-1);EEPROM.end();return onof;}else{return 0;}}
    void setDeviceState(uint8_t blocknum, bool onof){if(checkBlockNumber(blocknum) && blocknum <= 30){uint8_t n = blocknum;EEPROM.begin(EEPROM_SIZE_T);EEPROM.write(LEN*n-1, onof);;EEPROM.end();}}
};
class DevPinOut{
  uint8_t p;
  String name; // Devices Name(AlphaNumeric) given in Alexa
  bool onof;
  uint8_t nblock;
  void Pin(uint8_t p){if(isValidPin(p)){this->p = p;}}
  public:
    static const uint8_t D5_GPIO14 = 14;
    static const uint8_t D6_GPIO12 = 12;
    static const uint8_t D7_GPIO13 = 13;
    // pins sutable for output only
    static const uint8_t D3_GPIO0 = 0;
    static const uint8_t D4_GPIO2 = 2;
    DevPinOut(){p=255; name=""; onof=0;nblock=0;}
    //DevPinOut(uint8_t p){this->p=p; this->name=""; this->onof=0;pinMode(p, OUTPUT);digitalWrite(p, LOW);}
    //DevPinOut(uint8_t p,String name){this->p=p; this->name=name; this->onof=0;pinMode(p, OUTPUT);digitalWrite(p, LOW);}
    ~DevPinOut(){}
    bool isValidPin(){return isValidPin(this->p);}
    bool isValidPin(uint8_t p){if(D3_GPIO0 == p || D4_GPIO2 == p || D5_GPIO14 == p || D6_GPIO12 == p || D7_GPIO13 == p){return 1;}else{return 0;}}
    //void init(uint8_t p){Pin(p); this->name=""; this->onof=0;pinMode(p, OUTPUT);digitalWrite(p, LOW);}
    bool init(uint8_t p,String name,bool onof,uint8_t nblock){
      if(!setname(name)){return 0;}
      if(!isValidPin(p)){return 0;}
      Pin(p); 
      this->name=name; 
      this->onof=onof;
      this->nblock=nblock;
      pinMode(p, OUTPUT);
      if(onof)
        on();
      else
        off();
      return 1;
    }
    bool on(){
      if(!onof){
        digitalWrite(p, HIGH);
        onof=1;
        wifieeprom saveonof;
        saveonof.setDeviceState(nblock, onof);
      }
      return onof;
      }
    bool off(){
      if(onof){
        digitalWrite(p, LOW);
        onof=0;
        wifieeprom saveonof;
        saveonof.setDeviceState(nblock, onof);
      }
      return onof;
    }
    bool setname(String name){
      if(name.length() <= 0) {return 0;}
      for(uint8_t i = 0; i < name.length(); i++)
        if(!isAlphaNumeric(name.charAt(i)))
          return 0;
      this->name=name;
      return 1;
    }
    String getDevicename(){return name;}
    uint8_t getDeviceNum(){return nblock;}
    uint8_t getPinNum(){return p;}
    bool getStateonof(){return onof;}
};
class DevPinOuts{
  public:
    const static uint8_t MAX = 4;
    DevPinOut devs[MAX]; 
    DevPinOuts(){
      wifieeprom fetchdev;
      devs[0].init(DevPinOut::D3_GPIO0,fetchdev.GetDevice(1),fetchdev.getDeviceState(1),1);
      devs[1].init(DevPinOut::D4_GPIO2,fetchdev.GetDevice(2),fetchdev.getDeviceState(2),2);
      devs[2].init(DevPinOut::D5_GPIO14,fetchdev.GetDevice(3),fetchdev.getDeviceState(3),3);
      devs[3].init(DevPinOut::D6_GPIO12,fetchdev.GetDevice(4),fetchdev.getDeviceState(4),4);
    }
    //DevPinOuts(String s0,String s1,String s2,String s3){devs[0].init(DevPinOut::D3_GPIO0,s0);devs[1].init(DevPinOut::D4_GPIO2,s1);devs[2].init(DevPinOut::D5_GPIO14,s2);devs[3].init(DevPinOut::D6_GPIO12,s3);}
    ~DevPinOuts(){}
    // bool devon(String s){
    //   for(uint8_t i = 0; i < MAX; i++){
    //     if(devs[i].getname() == s)
    //       return devs[i].on();
    //   }
    //   return 0;
    // }
    void devtoggal(const char * device_name, bool state){
      for(uint8_t i = 0; i < MAX; i++){
        if(strcmp(device_name,devs[i].getDevicename().c_str()))
          if(state)
            devs[i].on();
          else
            devs[i].off();
      }
    }
    // bool setDeviceName(uint8_t dev_num0, String name){
    //   if(dev_num0 < MAX && dev_num0 >= 0)
    //     return devs[dev_num0].setname(name);
    //   return 0;
    // }
    // String getDeviceName(uint8_t dev_num0){if(dev_num0 < MAX && dev_num0 >= 0){return devs[dev_num0].getname();}else{return "";}}
    //DevPinOut& getDevPinOut(uint8_t dev_num0){if(dev_num0 < MAX && dev_num0 >= 0){return devs[dev_num0];}else{return NULL;}}
};
DevPinOuts pnos;
class encrpeeprom{
  public:
    encryp cryp;
    wifieeprom rom;
    encrpeeprom():cryp(),rom(){}
    void savessid(String s){
      //Serial.printf("encrpeeprom SSID = %s\n",s);
      rom.SaveSsid(s,cryp);
    }
    void savepass(String s){rom.SavePass(s,cryp);}
    String getssid(){return String(rom.GetSsid(cryp));}
    String getpass(){return String(rom.GetPass(cryp));}
};
class ds1307rtc{
  RTC_DS1307 RTC;
  public:
    ds1307rtc(){
    }
    void init(){Wire.begin();RTC.begin();}
    void printtest(){
      if (! RTC.isrunning()) {
        Serial.println("RTC is NOT running!");
        // following line sets the RTC to the date & time this sketch was compiled
        RTC.adjust(DateTime(__DATE__, __TIME__));
      }
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
    for(uint8_t i = 0; i < DevPinOuts::MAX; i++)
      if(pnos.devs[i].getDeviceNum() > 0 && pnos.devs[i].getDevicename().length() > 0)
        fauxmo.addDevice(pnos.devs[i].getDevicename().c_str());

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
        pnos.devtoggal(device_name,state);
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
  else
  { // Write ssid and paswd to eeprom
    if(server.argName(0) == "div1" && server.argName(1) == "div2"){
      //Serial.printf("server.arg(0) = %s; server.arg(1) = %s\n", server.arg(0),server.arg(1));
      wifieeprom wp;
      String newdev1(server.arg(0)), newdev2(server.arg(1));
      wp.SaveDevice(newdev1, 1);
      wp.SaveDevice(newdev2, 2);
      server.send(200, "text/html", "<!DOCTYPE html><html><head></head><body>Done:" + wp.GetDevice(1) + ":" + wp.GetDevice(2) + "</body></html>");
      delay(100);
      ESP.restart();
    }
    else
      server.send(200, "text/html", String(header_html) + String(sidpas_body_html));
  }
  ESP.getFreeHeap();
}


ds1307rtc d1307rtc;
void setup(){
  // Init serial port and clean garbage
    Serial.begin(SERIAL_BAUDRATE);
    secondTick.attach(1, ISRwatchdog);
    Serial.println();
    d1307rtc.init();
    d1307rtc.printtest();
    Serial.println();
    
    // Wifi
    // Set WIFI module to STA mode
    WiFi.mode(WIFI_STA);

    encrpeeprom cryprom;
    Serial.println(cryprom.cryp.Key());
    Serial.printf("ssid : %s; paswd : %s\n",cryprom.getssid(),cryprom.getpass());

    // pnos.setDeviceName(0, cryprom.rom.GetDevice(0));
    // pnos.setDeviceName(1, cryprom.rom.GetDevice(1));
    //dev1 = cryprom.rom.GetDevice(0);
    //dev2 = cryprom.rom.GetDevice(1);
    Serial.printf("Device 1 eeprom is : %s\n", pnos.devs[0].getDevicename());
    Serial.printf("Device 2 eeprom is : %s\n", pnos.devs[1].getDevicename());

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
      server.begin();
      Serial.println();
      Serial.println("HTTP server started");
      
    }
    else{
      Serial.println();
      // Connected!
      server.stop(); // Stop Webserver for ssid and paswd change
      Serial.printf("[WIFI] STATION Mode, SSID: %s, IP address: %s\n", WiFi.SSID().c_str(), WiFi.localIP().toString().c_str());
      setupfauxmo();
    }

}
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
          //Serial.printf("[MAIN] Free heap: %d bytes\n", ESP.getFreeHeap());
      }
    }
    else{
      server.handleClient();
      
    }
}
