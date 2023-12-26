#include <TFT_eSPI.h> 
#include <SPI.h>
#include <WiFi.h>
#include <WiFiClient.h>
#include <HardwareSerial.h>
#include <TinyGPSPlus.h>
#include <Arduino.h>
#include <time.h>
#include <ESP32Time.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>


// WiFi credentials
const char* wifi_ssid = "SSID";           // Replace "SSID" with your WiFi network name
const char* wifi_password = "PASSWORD";   // Replace "PASSWORD" with your WiFi password

// MQTT server configuration
const char* mqtt_server = "SERVER-IP";    // Replace "SERVER-IP" with the IP address of your MQTT server
const char* mqtt_user = "mqttclient";     // Replace "mqttclient" with your MQTT username
const char* mqtt_password = "Kennwort1";  // Replace "Kennwort1" with your MQTT password



// constants for data transmission
const uint16_t mqtt_port = 1883;
const int JSON_BUFFER_SIZE = 128;
const char* topic_clients = "clients";
const char* topic_timestamp = "esp32/timestamp";

// name of the client, formatted as "ESP32-" + MAC
String clientName;

// time information
unsigned long mic = 0;       // variable for microseconds
time_t epochTime = 0;        // timestamp in seconds since 1970 (Epoch time)
bool marker_interrupt = LOW; // boolean variable for interrupt marker with low level


// declaration of the rtc & set offset for MESZ
ESP32Time rtc(3600);  

HardwareSerial gpsSerial(1); // Use UART1
TinyGPSPlus gps;

TFT_eSPI tft = TFT_eSPI(); // Invoke library, pins defined in User_Setup.h

WiFiClient espClient;
PubSubClient mqtt_client(espClient);



// interrrupt service routine
void ISR()
{
  epochTime = rtc.getLocalEpoch() + 3600; // get current epoch seconds without offset & add offset for MESZ
  mic = rtc.getMicros();                  // get micro seconds
  marker_interrupt = HIGH;                // set marker to indicate an interrupt that has been triggered
}

// function to set the rtc
void rtc_setup()
{
  bool marker_set = LOW;
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(2,2);
  tft.println("Waiting for GPS");
  Serial.println("Waiting for GPS");

  while (!marker_set)
  {
    if (gpsSerial.available() > 0)
    {  
      if (gps.encode(gpsSerial.read()))
      {
        if (gps.time.isValid() && gps.time.isUpdated() && gps.date.isValid() && gps.date.isUpdated() && gps.satellites.value() > 1) //gps.time.isValid() && gps.date.isValid() && gps.satellites.isValid() && gps.hdop.isValid() && gps.hdop.hdop() < 10
        {   
          rtc.setTime(gps.time.second(), gps.time.minute(), gps.time.hour(), gps.date.day(), gps.date.month(), gps.date.year(), gps.time.centisecond()*10);
          
          tft.fillScreen(TFT_BLACK);
          tft.setCursor(2,2);
          tft.setTextColor(TFT_GREEN);
          tft.println("Time set!");
          tft.setTextColor(TFT_WHITE);
          tft.println();
          tft.println(rtc.getTime("%H:%M:%S"));
          tft.setCursor(2,30);
          tft.println(rtc.getDate(false));
          tft.println();
          tft.setTextColor(TFT_GOLD);
          tft.println(clientName);

          marker_set = HIGH;
          delay(2000);
        }
      }
    }

    delay(50);
  }
}

// function to connect to the mqtt-server
void reconnect_mqtt() {
  if (mqtt_client.connect(clientName.c_str(), mqtt_user, mqtt_password,"will-topic",MQTTQOS2,false,(clientName+"-disconnected").c_str())) 
  {
    mqtt_client.publish(topic_clients, clientName.c_str());
  } 
}

void setup()
{
  gpsSerial.begin(9600, SERIAL_8N1, 3, 2);
  Serial.begin(115200);

  tft.init();
  tft.setRotation(1);
  
  pinMode(45, OUTPUT);
  digitalWrite(45, HIGH);
  pinMode(15, INPUT);

  WiFi.mode(WIFI_STA);
  WiFi.begin(wifi_ssid, wifi_password);

  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_GREEN);
  tft.setCursor(2,2);
  tft.println("Connecting to wifi...");

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println(".");
  }

  tft.fillScreen(TFT_BLACK);
  tft.setCursor(2,2);
  tft.println("Connected to wifi...");

  delay(2000);

  String mac_adr = WiFi.macAddress();
  clientName = "ESP32-" + mac_adr;

  mqtt_client.setServer(mqtt_server,mqtt_port);
  mqtt_client.setBufferSize(1024);
  mqtt_client.setSocketTimeout(20);

  reconnect_mqtt();
  delay(1000);
  rtc_setup();

  attachInterrupt(digitalPinToInterrupt(15), ISR, RISING);
}

void loop()
{
  if (marker_interrupt)  
  {
    struct tm timenow = *localtime(&epochTime);

    char isoTime[30];
    strftime(isoTime, sizeof(isoTime), "%Y-%m-%dT%H:%M:%S", &timenow);
    sprintf(isoTime + strlen(isoTime), ".%06lu", mic % 1000000);

    DynamicJsonDocument doc(JSON_BUFFER_SIZE);
    doc["esp_id"] = clientName;
    doc["timestamp"] = String(isoTime);
    
    String jsonStr;
    serializeJson(doc, jsonStr);

    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_GREEN);
    tft.setCursor(2,2);
    tft.println("Last:");
    tft.println();
    tft.setTextColor(TFT_WHITE);
    tft.println(String(isoTime).substring(0,String(isoTime).length() - 3));
    tft.println();
    tft.setTextColor(TFT_GOLD);
    tft.println(clientName);
    tft.println();
    tft.setTextColor(TFT_GREEN);
    tft.print("GPS:");
    tft.setTextColor(TFT_WHITE);
    tft.println(gps.satellites.value());

    marker_interrupt = LOW;

    mqtt_client.publish(topic_timestamp, jsonStr.c_str());
  }

  if (!mqtt_client.connected()) {
    reconnect_mqtt();
  }
  mqtt_client.loop();
}

