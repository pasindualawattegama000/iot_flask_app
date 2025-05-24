#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_FLASK_SERVER_IP:5000";

const int buttonPin = 4;  // D4
const int ledPin = 5;     // D5

String deviceId = "ESP123";  // Change this to your device ID

bool lastButtonState = false;
bool currentLedState = false;

void setup() {
  Serial.begin(115200);
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(ledPin, OUTPUT);
  
  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi...");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    // Check button state
    bool currentButtonState = !digitalRead(buttonPin);  // Inverted because of PULLUP
    
    if (currentButtonState != lastButtonState) {
      sendButtonState(currentButtonState);
      lastButtonState = currentButtonState;
    }
    
    // Get LED state from server
    getLedState();
    
    delay(5000);  // Wait 5 seconds between checks
  } else {
    Serial.println("WiFi Disconnected");
    WiFi.begin(ssid, password);
    delay(5000);
  }
}

void sendButtonState(bool state) {
  HTTPClient http;
  
  String url = String(serverUrl) + "/api/device_data";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  DynamicJsonDocument doc(1024);
  doc["device_id"] = deviceId;
  doc["button_state"] = state;
  
  String requestBody;
  serializeJson(doc, requestBody);
  
  int httpResponseCode = http.POST(requestBody);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println(httpResponseCode);
    Serial.println(response);
  } else {
    Serial.print("Error on sending POST: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

void getLedState() {
  HTTPClient http;
  
  String url = String(serverUrl) + "/api/get_led_state?device_id=" + deviceId;
  
  http.begin(url);
  
  int httpResponseCode = http.GET();
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, response);
    
    String ledState = doc["led_state"];
    bool newLedState = (ledState == "on");
    
    if (newLedState != currentLedState) {
      digitalWrite(ledPin, newLedState ? HIGH : LOW);
      currentLedState = newLedState;
      Serial.println("LED state changed to: " + ledState);
    }
  } else {
    Serial.print("Error on sending GET: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}