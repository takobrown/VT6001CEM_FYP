#include <SPI.h>
#include <MFRC522.h>

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

#define maxPet       50
#define HSPI_SS_PIN  14
#define VSPI_SS_PIN  5
#define HSPI_RST_PIN 33
#define VSPI_RST_PIN 32
#define resetIDtime  2000 //reset nuidPICC array every 2000ms
SPIClass hspi(HSPI);
SPIClass vspi(VSPI);

MFRC522 mfrc522_hspi(HSPI_SS_PIN, HSPI_RST_PIN,&hspi);
MFRC522 mfrc522_vspi(VSPI_SS_PIN, VSPI_RST_PIN,&vspi);
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
byte nuidPICC_hspi[4]; 
byte nuidPICC_vspi[4];
unsigned long resetTimer = 0;
String petName[maxPet] = {"Cotton","Lucy","Dummy","Jerry","Tim"};
String tagID[maxPet] = {"9b f4 20 c3","9b 5c 20 c3","1b 58 20 c3","db cb 1f c3","5b c7 1f c3"};
int8_t petState[maxPet] = {0,0,0,0,0};
//Publish Former: RFID,Server
const char* ssid = "Tako Brown iphone";
const char* password = "user1256";
const char* mqtt_server = "175.178.10.95";
const char* mqtt_username = "RFID";
const char* mqtt_password = "RFID";
const char* pub_topic = "RFID";
const char* init_topic = "Init";
const char* sub_topic = "Server";
WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("WiFi and MQTT Init");
  display.display();
  Serial.println(F("WiFi and MQTT Init"));
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  reconnect();
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("RFID Init");
  display.display();
  Serial.println(F("RFID Init"));
  hspi.begin(27, 25, 26, HSPI_SS_PIN); //SCLK, MISO, MOSI, SS
  mfrc522_hspi.PCD_Init();
  vspi.begin(18, 19, 23, VSPI_SS_PIN); //SCLK, MISO, MOSI, SS
  mfrc522_vspi.PCD_Init();
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("System Init Success");
  display.display();
  Serial.println(F("System Init Success"));
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  readTag(); 
}
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  String res = "";
  for (int i = 0; i < length; i++) {
    res += (char)payload[i];
  }
  Serial.println(res);
  
  DynamicJsonDocument doc(10240);
  DeserializationError error = deserializeJson(doc, payload, length);
  if(error){
    doc.clear();
  } else {
    if(doc.containsKey("length")){
      int petNums = int(doc["length"]);
      petNums = min(petNums,maxPet);
      JsonObject Data;
      String Name,ID;
      for(int i = 0;i<petNums;i++){
        Data = doc["Data"][i];
        Name = Data["Name"].as<String>();
        ID = Data["RFID"].as<String>();
        Serial.print(ID);
        Serial.print("\t");
        Serial.println(Name);
        petName[i] = Name;
        tagID[i] = ID;
      }    
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32Client", mqtt_username, mqtt_password)) {
      Serial.println("connected");
      client.subscribe(sub_topic);
      prepareInit();
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 1 seconds");
      delay(1000);
    }
  }
}
void readTag(){
  if(millis() - resetTimer >= resetIDtime){
    resetTimer = millis();
    for (byte i = 0; i < 4; i++) {
      nuidPICC_hspi[i] = 0;
    }
    for (byte i = 0; i < 4; i++) {
      nuidPICC_vspi[i] = 0;
    }
  }
  // Use HSPI to read the UID from the first module
  if (mfrc522_hspi.PICC_IsNewCardPresent() && mfrc522_hspi.PICC_ReadCardSerial()) {
      Serial.print(F("PICC type: "));
      MFRC522::PICC_Type piccType = mfrc522_hspi.PICC_GetType(mfrc522_hspi.uid.sak);
      Serial.println(mfrc522_hspi.PICC_GetTypeName(piccType));
    
      // Check is the PICC of Classic MIFARE type
      if (piccType != MFRC522::PICC_TYPE_MIFARE_MINI &&  
        piccType != MFRC522::PICC_TYPE_MIFARE_1K &&
        piccType != MFRC522::PICC_TYPE_MIFARE_4K) {
        Serial.println(F("Your tag is not of type MIFARE Classic."));
        return;
      }
      if (mfrc522_hspi.uid.uidByte[0] != nuidPICC_hspi[0] || 
        mfrc522_hspi.uid.uidByte[1] != nuidPICC_hspi[1] || 
        mfrc522_hspi.uid.uidByte[2] != nuidPICC_hspi[2] || 
        mfrc522_hspi.uid.uidByte[3] != nuidPICC_hspi[3] ) {
        Serial.println(F("A new card has been detected."));
    
        // Store NUID into nuidPICC array
        for (byte i = 0; i < 4; i++) {
          nuidPICC_hspi[i] = mfrc522_hspi.uid.uidByte[i];
        }
       
        Serial.println(F("The NUID tag is:"));
        Serial.print(F("In hex: "));
        String ID = transferHex(mfrc522_hspi.uid.uidByte, mfrc522_hspi.uid.size);
        int index = tagJudge(ID);
        Serial.println(ID);
        if(index == -1){
          Serial.println("Unknown Tag");
        } else {
          if(petState[index] == 0){
            petState[index] = -1;
          } 
          else if(petState[index] == 1){
            petState[index] = 2;
          }
          if (petState[index] == 2){
            //Publish Pet state change! In
            display.clearDisplay();
            display.setCursor(0, 0);
            display.println(String(petName[index])+" In!");
            display.display();
            Serial.println(String(petName[index])+" In!");
            petState[index] = 0;
            prepareMsg(tagID[index],petName[index],1);
          }
        }
      }
      else Serial.println(F("Card read previously."));
      // Halt PICC
      mfrc522_hspi.PICC_HaltA();
      // Stop encryption on PCD
      mfrc522_hspi.PCD_StopCrypto1();
  }
  
  // Use VSPI to read the UID from the first module
  if (mfrc522_vspi.PICC_IsNewCardPresent() && mfrc522_vspi.PICC_ReadCardSerial()) {
      Serial.print(F("PICC type: "));
      MFRC522::PICC_Type piccType = mfrc522_vspi.PICC_GetType(mfrc522_vspi.uid.sak);
      Serial.println(mfrc522_vspi.PICC_GetTypeName(piccType));
    
      // Check is the PICC of Classic MIFARE type
      if (piccType != MFRC522::PICC_TYPE_MIFARE_MINI &&  
        piccType != MFRC522::PICC_TYPE_MIFARE_1K &&
        piccType != MFRC522::PICC_TYPE_MIFARE_4K) {
        Serial.println(F("Your tag is not of type MIFARE Classic."));
        return;
      }
      if (mfrc522_vspi.uid.uidByte[0] != nuidPICC_vspi[0] || 
        mfrc522_vspi.uid.uidByte[1] != nuidPICC_vspi[1] || 
        mfrc522_vspi.uid.uidByte[2] != nuidPICC_vspi[2] || 
        mfrc522_vspi.uid.uidByte[3] != nuidPICC_vspi[3] ) {
        Serial.println(F("A new card has been detected."));
    
        // Store NUID into nuidPICC array
        for (byte i = 0; i < 4; i++) {
          nuidPICC_vspi[i] = mfrc522_vspi.uid.uidByte[i];
        }
       
        Serial.println(F("The NUID tag is:"));
        Serial.print(F("In hex: "));
        String ID = transferHex(mfrc522_vspi.uid.uidByte, mfrc522_vspi.uid.size);
        int index = tagJudge(ID);
        Serial.println(ID);
        if(petState[index] == 0){
          petState[index] = 1;
        } 
        else if(petState[index] == -1){
          petState[index] = -2;
        }
        if (petState[index] == -2){
          //Publish Pet state change! Out
          display.clearDisplay();
          display.setCursor(0, 0);
          display.println(String(petName[index])+" Out!");
          display.display();
          Serial.println(String(petName[index])+" Out!");
          petState[index] = 0;
          prepareMsg(tagID[index],petName[index],0);
        }
      }
      else Serial.println(F("Card read previously."));
      // Halt PICC
      mfrc522_vspi.PICC_HaltA();
      // Stop encryption on PCD
      mfrc522_vspi.PCD_StopCrypto1();
  }
}
String transferHex(byte *buffer, byte bufferSize) {
  String hex = "";
  for (byte i = 0; i < bufferSize; i++) {
    hex = hex + String(buffer[i] < 0x10 ? "0" : "")+String(buffer[i], HEX)+String(" ");
  }
  hex = hex.substring(0,hex.length()-1);//delete last space
  return hex;
}
int tagJudge(String ID){
  for(int i=0;i<maxPet;i++){
    String tag = String(tagID[i]);
    tag.toUpperCase();
    ID.toUpperCase();
    if(tag == ID){
      return i;
    }
  }
  return -1;
}
void prepareMsg(String ID,String Name,int state){
  StaticJsonDocument<128> doc;
  char msgJson[128];  
  String sendContent = "";
  doc["RFID"] = ID;
  doc["Name"] = Name;
  if (state == 1){
    doc["State"] = "In";
  } else {
    doc["State"] = "Out";
  }
  serializeJson(doc,sendContent);
  Serial.println(sendContent);
  client.publish(pub_topic,sendContent.c_str());
  doc.clear();
}
void prepareInit(){
  StaticJsonDocument<128> doc;
  char msgJson[128];  
  String sendContent = "";
  doc["Init"] = "Success";
  serializeJson(doc,sendContent);
  Serial.println(sendContent);
  client.publish(init_topic,sendContent.c_str());
  doc.clear();
}
