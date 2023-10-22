#include <Wire.h>
#include <BH1750.h>
#include <ArduinoBLE.h>
#include <WiFiNINA.h>
#include "ThingSpeak.h"

#define SECRET_SSID "vivo Y35" // replace MySSID with your WiFi network name
#define SECRET_PASS "12345678" // replace MyPassword with your WiFi password
#define SECRET_CH_ID 2299331 // replace with your channel number
#define SECRET_WRITE_APIKEY "EMJWA6XXCQA5JCAP" // replace with your channel write API Key

// Define the UUID for the service and characteristics
#define SERVICE_UUID "12345678-1234-5678-1234-56789abcdef0"
#define CHARACTERISTIC_UUID "12345678-1234-5678-1234-56789abcdef1"

char ssid[] = SECRET_SSID;  // your network SSID (name)
char pass[] = SECRET_PASS;  // your network password

int keyIndex = 0;  // your network key Index number (needed only for WEP)
WiFiClient client;

unsigned long myChannelNumber = SECRET_CH_ID;
const char* myWriteAPIKey = SECRET_WRITE_APIKEY;

// Create a BLE service and characteristic
BLEService bleService(SERVICE_UUID);

BLEIntCharacteristic lightCharacteristic(CHARACTERISTIC_UUID, BLERead | BLENotify);
BLEIntCharacteristic moistureCharacteristic("2A6E", BLERead | BLENotify);
BLEIntCharacteristic waterLevelCharacteristic("2A6F", BLERead | BLENotify);

BH1750 lightSensor;
int previousLightLevel = 0;
int previousMoistureLevel = 0;
int previousWaterLevel = 0;

void setup() {

  Serial.begin(9600);
  ThingSpeak.begin(client);  // Initialize ThingSpeak
  while (!Serial)
    ;
  Serial.println("Started");

  Wire.begin();

  if (!lightSensor.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println("Failed to initialize light sensor!");
    while (1)
      ;
  }

  pinMode(LED_BUILTIN, OUTPUT);  // Initialize the built-in LED pin

  if (!BLE.begin()) {  // Initialize NINA B306 BLE
    Serial.println("starting BLE failed!");
    while (1)
      ;
  }

  BLE.setLocalName("JH_ArduinoNano33BLESense_R2");  // Set name for connection
  BLE.setAdvertisedService(bleService);             // Advertise ble service

  bleService.addCharacteristic(lightCharacteristic);       // Add light level characteristic
  bleService.addCharacteristic(moistureCharacteristic);    // Add moisture level characteristic
  bleService.addCharacteristic(waterLevelCharacteristic);  // Add water level characteristic

  BLE.addService(bleService);  // Add environment service

  lightCharacteristic.setValue(0);       // Set initial light level value
  moistureCharacteristic.setValue(0);    // Set initial moisture level value
  waterLevelCharacteristic.setValue(0);  // Set initial water level value

  BLE.advertise();  // Start advertising
  Serial.print("Peripheral device MAC: ");
  Serial.println(BLE.address());
  Serial.println("Waiting for connections...");
}
void WiFi_connection() {
  // Connect or reconnect to WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(SECRET_SSID);
    while (WiFi.status() != WL_CONNECTED) {
      WiFi.begin(ssid, pass);  // Connect to WPA/WPA2 network. Change this line if using open or WEP network Serial.print(".");
      delay(5000);
    }
    Serial.println("\nConnected.");
  }
}

void loop() {

  BLEDevice central = BLE.central();  // Wait for a BLE central to connect

  // If central is connected to peripheral
  if (central) {
    Serial.print("Connected to central MAC: ");
    Serial.println(central.address());  // Central's BT address:

    digitalWrite(LED_BUILTIN, HIGH);  // Turn on the LED to indicate the connection

    while (central.connected()) {
      updateReadings();
      delay(100);
    }

    digitalWrite(LED_BUILTIN, LOW);  // When the central disconnects, turn off the LED
    Serial.print("Disconnected from central MAC: ");
    Serial.println(central.address());
  }
}

int getMoistureLevel() {
  // Read the moisture level from the soil moisture sensor
  int moisture = analogRead(A0);
  ThingSpeak.setField(1, moisture);
  return moisture;
}
int getLightLevel() {
  // Read the light level from the sensor
  int light = lightSensor.readLightLevel();
  ThingSpeak.setField(2, light);
  return light;
}
int getWaterLevel() {
  // Read the water level from the water level depth detection sensor
  int waterlevel = analogRead(A1);
  ThingSpeak.setField(3, waterlevel);
  return waterlevel;
}

void updateReadings() {

  WiFi_connection();
  int lightLevel = getLightLevel();
  int moistureLevel = getMoistureLevel();
  int waterLevel = getWaterLevel();
  // write to the ThingSpeak channel
  int x = ThingSpeak.writeFields(myChannelNumber, myWriteAPIKey);
  if (x == 200) {
    Serial.println("Channel update successful.");
  } else {
    Serial.println("Problem updating channel. HTTP error code " + String(x));
  }

  if (lightLevel != previousLightLevel) {
    Serial.print("Light Level: ");
    Serial.println(lightLevel);
    lightCharacteristic.writeValue(lightLevel);
    previousLightLevel = lightLevel;
  }

  if (moistureLevel != previousMoistureLevel) {
    Serial.print("Moisture Level: ");
    Serial.println(moistureLevel);
    moistureCharacteristic.writeValue(moistureLevel);
    previousMoistureLevel = moistureLevel;
  }

  if (waterLevel != previousWaterLevel) {
    Serial.print("Water Level: ");
    Serial.println(waterLevel);
    waterLevelCharacteristic.writeValue(waterLevel);
    previousWaterLevel = waterLevel;
  }
}
