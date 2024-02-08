#include <Arduino.h>
#ifdef ESP32
    #include <WiFi.h>
#else
    #include <ESP8266WiFi.h>
#endif
#include <EEPROM.h>
#include <Hash.h>
#include <ESP8266WebServer.h>
#include "fauxmoESP.h"
#include "FS.h"

// Rename the credentials.sample.h file to credentials.h and 
// edit it according to your router configuration

fauxmoESP fauxmo;
// Create ESP8266WebServer object on port 80
ESP8266WebServer server(80);
String dev1, dev2;
// -----------------------------------------------------------------------------

#define SERIAL_BAUDRATE     115200
#define EEPROM_SIZE_T       512


#define D1_GPIO5            5
#define D2_GPIO4            4
#define D5_GPIO14           14
#define D6_GPIO12           12
#define D7_GPIO13           13
// pins sutable for output only
#define D3_GPIO0            0
#define D4_GPIO2            2

// #define LED_YELLOW          4
// #define LED_GREEN           5
// #define LED_BLUE            0
// #define LED_PINK            2
// #define LED_WHITE           15

// #define ID_YELLOW           "yellow lamp"
// #define ID_GREEN            "green lamp"
// #define ID_BLUE             "blue lamp"
// #define ID_PINK             "pink lamp"
// #define ID_WHITE            "white lamp"
uint8_t tmo = 100;
const char header_html[] PROGMEM = R"rawliteral(
  <!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Lucida Console;background-color:lightblue;color:#871F78;}h1{padding:2vh;text-align:center;}div{margin:70px;border:1px solid #4CAF50;font-size:1.5rem;} button{background-color: #FFFF00;font-size:1.5rem;width:100%;padding:12px 20px;margin:8px 0;} button:hover {opacity: 0.8;} .button2{background-color: #FFFF00;font-size:1.5rem;}
@media screen and (max-width: 300px)}form {border:3px solid #f1f1f1;} input[type=text], input[type=password],input[type=button]{width:100%;padding:12px 20px;margin:8px 0;display:inline-block;border: 1px solid #ccc;box-sizing: border-box;} .container{padding:16px;}</style></head>
)rawliteral";

const char sidpas_body_html[] PROGMEM = R"rawliteral(
  <body> <h2>IoT Web Server : Change Wifi SSID and Password</h2><form action="/defWebPage" method="get" target="_self"><fieldset><div class="container" style="background-color:#f1f1f1"><label for="ssid">New Wifi SSID:</label><input type="text" id="ssid" name="ssid" required><br><label for="paswd">New Wifi Password:</label><input type="password" id="paswd" name="paswd" required></div></fieldset><button type="submit">Set New Wifi SSID and Password</button></form></body></html>
  )rawliteral";
const char devices_body_html[] PROGMEM = R"rawliteral(
  <body> <h2>IoT Web Server : Change Devices Name</h2><form action="/PageDeviesName" method="get" target="_self"><fieldset><div class="container" style="background-color:#f1f1f1"><label for="div1">Device 1 Name :</label><input type="text" id="div1" name="div1" required><br><label for="div2">Device 2 Name:</label><input type="text" id="div2" name="div2" required></div></fieldset><button type="submit">Set Devices Name</button></form></body></html>
  )rawliteral";
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// Wifi
// -----------------------------------------------------------------------------
class wifieeprom {
  // 512 = 16 * 32;  dev(1) 0 to 15 dev(2) 16 to 31 dev(3) 32 to 47 dev(n) LB =16*(n-1) , UB = (16*n) - 1
    // ssid is n = 32 i.e. LB = 16*(32-1) to UB = 16*32 - 1
    // pass is n = 31 i.e. LB = 16*(31-1) to UB = 16*31 - 1
    // n(0 to 31) is block number in EEPROM; first byte in block contains length of string which should less than equal to 15(block size LEN 16 - 1)
    // Device number is block number
    // nlen is number of char in davice name <= LEN-1; 
    static const uint16_t SIZE = 512;
    static const uint8_t LEN = 16; //max length in char
  private:
    char *blockdata;
    uint8_t nblock;
    // void readSsidlen(uint8_t n_for_s = 31){len_sid = (uint8_t)EEPROM.read(LEN*n_for_s);}
    // void readPasslen(uint8_t n_for_p = 30){len_pas = (uint8_t)EEPROM.read(LEN*n_for_p);}
    // void readDevlen(uint8_t n){return (uint8_t)EEPROM.read(LEN*n);}
    void write(const char * name, uint8_t namelen, uint8_t n){//nlen is number of char in Device Name;  n is block/device number in EEPROM
      if(n > 0 and n < 32 and namelen <= (LEN - 1)){ // MAX DEVICES is 30 = (32 -2) = 512/16 - 2; two blocks for ssid and password
        EEPROM.begin(EEPROM_SIZE_T);
        EEPROM.write(LEN*(n-1), namelen);
        for(int iadr = LEN*(n-1) + 1, iname = 0; iadr < LEN*n and iname < namelen;iadr++,iname++)
          EEPROM.write(iadr, (byte)name[iname]);
        EEPROM.end();
      }
    }
    void read(uint8_t n){
      if(n > 0 and n < 32){ // MAX DEVICES is 30 = (32 -2) = 512/16 - 2; two blocks for ssid and password
        EEPROM.begin(EEPROM_SIZE_T);
        uint8_t namelen = (uint8_t)EEPROM.read(LEN*(n-1));//LB = LEN*(n-1) first byte of nth block UB = (LEN*16) -1 last byte nth block
        if(namelen <= (LEN - 1)){
          free(blockdata);
          nblock = n;
          blockdata = (char*)malloc((namelen + 1) * sizeof(char));
          for(int iadr = LEN*(n-1) + 1, iname = 0; iadr < LEN*n and iname < namelen;iadr++,iname++)
            blockdata[iname] = (char)EEPROM.read(iadr);
          blockdata[namelen] = '\0';
        }
        else{
          free(blockdata);
          nblock = -1;
          blockdata = NULL;
        }
        EEPROM.end();
      }
      ESP.getFreeHeap();
    }
  public:
    wifieeprom() {
      blockdata = NULL;
      nblock = -1;
    }
    ~wifieeprom(){
      free(blockdata);
      ESP.getFreeHeap();
    }
    String GetSsid(){read(31); return blockdata != NULL ? String(blockdata) : "";} //if(blockdata != NULL) return String(blockdata); else return "";
    String GetPass(){read(30); return blockdata != NULL ? String(blockdata) : "";}
    void SaveSsid(String s){ write(s.c_str(),(uint8_t)s.length(),31);}
    void SavePass(String s){ write(s.c_str(),(uint8_t)s.length(),30);}
    String GetDevice(uint8_t dev_num){read(dev_num); return blockdata != NULL ? String(blockdata) : "";}
    void SaveDevice(String dev_name, uint8_t dev_num){ if(dev_num > 0){write(dev_name.c_str(),(uint8_t)dev_name.length(),dev_num);}}
};

// class wifieeprom {
//     static const int SIZE = 512;
//     static const uint8_t LEN = 255;
//   private:
//     uint16_t addr;
//     char *sid;
//     char *pas;
//     uint8_t len_sid, len_pas;
//     void restaddr(){addr=1;}
//     bool storelengths(uint8_t lensid, uint8_t lenpas){
//       if(len_sid <= LEN && len_pas <= LEN){
//         len_sid = lensid;
//         len_pas = lenpas;
//         EEPROM.write(0, len_sid);
//         EEPROM.write(1, len_pas);
//         return true;
//       }
//       else
//         return false;
//     }
//     void readSsidlen(){len_sid = (uint8_t)EEPROM.read(0);}
//     void readPasslen(){len_pas = (uint8_t)EEPROM.read(1);}
//   public:
//     ~wifieeprom(){
//       free(sid);
//       free(pas);
//       ESP.getFreeHeap();
//     }
//     wifieeprom() {
//       addr = 1;
//       len_sid = 0;
//       len_pas = 0;
//       sid = NULL;
//       pas = NULL;
//     }
    
//     void write(const char *ssid, uint8_t lensid, const char *pass, uint8_t lenpas) {
//       EEPROM.begin(EEPROM_SIZE_T);
//       if(!storelengths(lensid,lenpas))
//         return;
//       // ASCII encoding
//       byte bbuf;
//       restaddr();
//       for (int i = 0; i < lensid && addr < len_sid + 2; i++) {
//         //Serial.printf("char = %c \n", ssid[i];
//         addr = addr + 1;
//         bbuf = (byte)ssid[i];
//         EEPROM.write(addr, bbuf);
//         // Serial.print(bbuf);// Serial.println();// Serial.printf("Byte = %d \n", bbuf);// Serial.println();
//       }
//       for (int i = 0; i < lenpas && addr < len_sid + len_pas + 2; i++) {
//         addr = addr + 1;
//         bbuf = (byte)pass[i];
//         EEPROM.write(addr, bbuf);
//       }
//       EEPROM.end();
//     }
//     void read() { // 
//       free(sid);
//       free(pas);
//       EEPROM.begin(EEPROM_SIZE_T);
//       len_sid = (uint8_t)EEPROM.read(0);
//       sid = (char*)malloc((len_sid + 1) * sizeof(char));
//       sid[len_sid + 1] ='\0';
//       len_pas = (uint8_t)EEPROM.read(1);
//       pas = (char*)malloc((len_pas + 1) * sizeof(char));
//       pas[len_pas + 1] = '\0';
//       restaddr();
//       for (int i = 0; i < len_sid && addr < len_sid + 2; i++) {
//         //ssid.append((char)EEPROM.read(addr));
//         addr = addr + 1;
//         sid[i] = (char)EEPROM.read(addr);
        
//       }
//       for (int i = 0; i < len_pas && addr < len_sid +len_pas + 2; i++) {
//         //pass.append((char)EEPROM.read(addr));
//         addr = addr + 1;
//         pas[i] = (char)EEPROM.read(addr);
//       }
//       EEPROM.end();
//       ESP.getFreeHeap();
//     }
//     void writestr(String ssid,String pass) {
//       if(ssid.length() < LEN && pass.length() < LEN){
//         len_sid = (uint8_t)ssid.length();
//         len_pas = (uint8_t)pass.length();
//         char sd[len_sid + 1];
//         char ps[len_pas + 1];
//         ssid.toCharArray(sd,len_sid + 1);
//         pass.toCharArray(ps,len_pas + 1);
//         write(sd, len_sid + 1, ps, len_pas + 1);
//       }
//     }
//     String readSsid(){
//       free(sid);
//       sid = NULL;
//       ESP.getFreeHeap();
//       EEPROM.begin(EEPROM_SIZE_T);
//       readSsidlen();
//       restaddr();
//       sid = (char*)malloc((len_sid + 1) * sizeof(char));
//       sid[len_sid + 1] ='\0';
//       for (int i = 0; i < len_sid && addr < len_sid + 2; i++) {
//         //ssid.append((char)EEPROM.read(addr));
//         addr = addr + 1;
//         sid[i] = (char)EEPROM.read(addr);
//       }
//       EEPROM.end();
//       return String(sid);
//     }
//     String readPass(){
//       free(pas);
//       pas = NULL;
//       ESP.getFreeHeap();
//       EEPROM.begin(EEPROM_SIZE_T);
//       readSsidlen();
//       readPasslen();
//       addr = (uint16_t)len_sid + (2-1); // last eeprom address of ssid
//       pas = (char*)malloc((len_pas + 1) * sizeof(char));
//       pas[len_pas + 1] = '\0';
//       for (int i = 0; i < len_pas && addr < len_sid + len_pas + 2; i++) {
//         //pass.append((char)EEPROM.read(addr));
//         addr = addr + 1;
//         pas[i] = (char)EEPROM.read(addr);
//       }
//       EEPROM.end();
//       return String(pas);
//     }
    
    
//     String GetSsid(){ if(sid != NULL) return String(sid); else return readSsid();}
//     String GetPass(){ if(pas != NULL) return String(pas); else return readPass();}
// };

// class sipffsdevice{
//   const String fdevices = "devices.txt";
//   uint8_t len[2];
//   char *dev1;
//   char *dev2;
//   void devicenames_len(){
//     char ch; uint8_t line = 0, count = 0;
//     free(dev1);
//     free(dev2);
//     dev1 = NULL;
//     dev2 = NULL;
//     ESP.getFreeHeap();
//     bool res = SPIFFS.begin();
//     if (res) {
//       File f = SPIFFS.open(fdevices, "r");
//       if (!f)
//         Serial.println("File 'example.txt' open failed.");
//       else {
//         while (f.available()){
//           ch = f.read();     
//           if(ch == '\n')
//           {
//             len[line] = count;
//             line = line + 1;
//             count = 0;
//           }
//           else
//             count = count + 1;
//         }
//         f.close();
//       }
//     }
//     dev1 = (char*)malloc((len[0] + 1) * sizeof(char));
//     dev2 = (char*)malloc((len[1] + 1) * sizeof(char));
//     dev1[len[0] + 1] = '\0';
//     dev1[len[1] + 1] = '\0';
//   }
//   public:
//   sipffsdevice(){len[0] -1;len[1]=-1;dev1=NULL;dev2=NULL;}
//   ~sipffsdevice(){free(dev1);free(dev2);ESP.getFreeHeap();}
//   void info(){
//     bool res = SPIFFS.begin();
//     Serial.print("SPIFFS.begin() = ");
//     Serial.println(res);

//     if (res) {
//       FSInfo fs_info;
//       SPIFFS.info(fs_info);

//       Serial.print("fs_info.totalBytes = ");
//       Serial.println(fs_info.totalBytes);
//       Serial.print("fs_info.usedBytes = ");
//       Serial.println(fs_info.usedBytes);
//       Serial.print("fs_info.blockSize = ");
//       Serial.println(fs_info.blockSize);
//       Serial.print("fs_info.pageSize = ");
//       Serial.println(fs_info.pageSize);
//       Serial.print("fs_info.maxOpenFiles = ");
//       Serial.println(fs_info.maxOpenFiles);
//       Serial.print("fs_info.maxPathLength = ");
//       Serial.println(fs_info.maxPathLength);
//     }
//   }
//   void writedevicenames(String d1, String d2){
//     bool res = SPIFFS.begin();
//     if (res) {
//       SPIFFS.remove(fdevices.c_str());
//       delay(100);
//       File f = SPIFFS.open(fdevices, "w");
//       if (!f)
//         Serial.println("File 'example.txt' open failed.");
//       else {
//         f.println(d1);
//         f.println(d2);
//         f.close();
//       }
//     }
//   }
//   void readdevicenames(){
//     devicenames_len();
//     char ch; uint8_t line = 0, count = 0;
//     bool res = SPIFFS.begin();
//     if (res) {
//       File f = SPIFFS.open(fdevices, "r");
//       if (!f)
//         Serial.println("File 'example.txt' open failed.");
//       else {
//         while (f.available()){
//           ch = f.read();     
//           if(ch == '\n')
//           {
//             //Serial.write(" NewLine ");
//             Serial.printf("Line : %d Count : %d\n", line, count);
//             line = line + 1;
//             count = 0;
//           }
//           else
//           {
//           //Serial.write(ch);
//           if(line == 0){dev1[count] = (char)ch;}
//           if(line == 1){dev2[count] = (char)ch;}
//           count = count + 1;
//           }
//         }
//         f.close();
//       }
//     }
//   }
//   String Device1name(){
//     if(dev1 == NULL){readdevicenames();}
//     return String(dev1);
//   }
//   String Device2name(){
//     if(dev2 == NULL){readdevicenames();}
//     return String(dev2);
//   }
// };


void setupfauxmo() {
    // LEDs
    
    
    // pinMode(LED_BLUE, OUTPUT);
    // pinMode(LED_PINK, OUTPUT);
    // pinMode(LED_WHITE, OUTPUT);
    // digitalWrite(LED_YELLOW, LOW);
    
    // digitalWrite(LED_BLUE, LOW);
    // digitalWrite(LED_PINK, LOW);
    // digitalWrite(LED_WHITE, LOW);

    

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
    fauxmo.addDevice(dev1.c_str());
    fauxmo.addDevice(dev2.c_str());
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

        if (strcmp(device_name, dev1.c_str())==0) {
            digitalWrite(D1_GPIO5, state ? HIGH : LOW);
        } else if (strcmp(device_name, dev2.c_str())==0) {
            digitalWrite(D2_GPIO4, state ? HIGH : LOW);
        // } else if (strcmp(device_name, ID_BLUE)==0) {
        //     digitalWrite(LED_BLUE, state ? HIGH : LOW);
        // } else if (strcmp(device_name, ID_PINK)==0) {
        //     digitalWrite(LED_PINK, state ? HIGH : LOW);
        // } else if (strcmp(device_name, ID_WHITE)==0) {
        //     digitalWrite(LED_WHITE, state ? HIGH : LOW);
        }

    });

}

void defWebPage(){
  //Serial.println("defWebPage called");
  //Serial.println((server.method() == HTTP_GET) ? "GET" : "POST");
  //server.send(200, "text/html", index_html);
  // for (uint8_t i = 0; i < server.args(); i++)
  // {
  //   if (server.argName(i) == "ssid"){ss_id = server.arg(i)}
  //   // {
  //   //   Serial.println(server.arg(i));
  //   // }
  //   else if (server.argName(i) == "paswd")
  //   {
  //     Serial.println(server.arg(i));
  //   }
  //   else
  //   {
  //     Serial.println("unknown argument! ");
  //   }
  //   // Serial.print(server.argName(i));
  //   // Serial.print(": ");
  //   // Serial.print(server.arg(i));
  //   // Serial.printn();
  // }
  if(server.args() == 0)
    server.send(200, "text/html", String(header_html) + String(sidpas_body_html));
  else
  { // Write ssid and paswd to eeprom
    if(server.argName(0) == "ssid" && server.argName(1) == "paswd"){
      //Serial.printf("server.arg(0) = %s; server.arg(1) = %s\n", server.arg(0),server.arg(1));
      
      wifieeprom wp;
      String newsid(server.arg(0)), newpass(server.arg(1));
      wp.SaveSsid(newsid);
      wp.SavePass(newpass);
      
      //Serial.printf("Web SSID from eeprom is : %s\n", wp.GetSsid());
      //Serial.printf("Web PASS from eeprom is : %s\n", wp.GetPass());
      server.send(200, "text/html", "<!DOCTYPE html><html><head></head><body>Done:" + wp.GetSsid() + ":" + wp.GetPass() + "</body></html>");
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
void setup(){
  // Init serial port and clean garbage
    Serial.begin(SERIAL_BAUDRATE);
    Serial.println();
    Serial.println();

    pinMode(D1_GPIO5, OUTPUT);
    digitalWrite(D1_GPIO5, LOW);
    pinMode(D2_GPIO4, OUTPUT);
    digitalWrite(D2_GPIO4, LOW);
    
    // Wifi
    // Set WIFI module to STA mode
    WiFi.mode(WIFI_STA);

    wifieeprom wp;
    dev1 = wp.GetDevice(1);
    dev2 = wp.GetDevice(2);
    //Serial.printf("Device 1 eeprom is : %s\n", wp.GetDevice(1));
    //Serial.printf("Device 2 eeprom is : %s\n", wp.GetDevice(2));
    // Connect
    WiFi.begin(wp.GetSsid(), wp.GetPass());
    //Serial.printf("SSID from eeprom is : %s\n", wp.GetSsid());
    //Serial.printf("PASS from eeprom is : %s\n", wp.GetPass());
    
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
      server.on("/defWebPage",defWebPage);
      server.on("/PageDeviesName",PageDeviesName);
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

    // If your device state is changed by any other means (MQTT, physical button,...)
    // you can instruct the library to report the new state to Alexa on next request:
    // fauxmo.setState(ID_YELLOW, true, 255);
    }
    else{
      server.handleClient();
      
    }
}
