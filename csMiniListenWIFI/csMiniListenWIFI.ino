#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include "Adafruit_MCP9601.h"

#define SDA_PIN 18
#define SCL_PIN 19
#define I2C_ADDRESS (0x67)
#define PRESSURE_PIN 2
#define OUTPUT_PIN 4
#define INPUT_PIN 5

// WiFi Credentials
const char* ssid = "engtech-ThinkPad-X270";
const char* password = "Franco123";
const char* serverAddress = "http://10.10.100.132:5001/data";

Adafruit_MCP9601 mcp;
WiFiClient client;

bool thermocoupleConnected = true;  // Assume thermocouple is connected initially

void setup() {
    Serial.begin(115200);
    while (!Serial) {
      delay(10);
    }

    connectToWiFi();  // Function to handle WiFi connection

    // Initialize the I2C bus
    Wire.begin(SDA_PIN, SCL_PIN);
    if (! mcp.begin(I2C_ADDRESS)) {
        Serial.println("Failed to initialize MCP9601");
    }

    uint8_t status = mcp.getStatus();
    if (status & MCP9601_STATUS_OPENCIRCUIT || status & MCP9601_STATUS_SHORTCIRCUIT) {
        Serial.println("Thermocouple not detected or short-circuited. Proceeding with other sensors.");
        thermocoupleConnected = false;
    } else {
        Serial.println("Thermocouple detected. Proceeding with all sensors.");
    }

    mcp.setADCresolution(MCP9600_ADCRESOLUTION_18);
    mcp.setThermocoupleType(MCP9600_TYPE_K);
    mcp.setFilterCoefficient(3);
    mcp.setAlertTemperature(1, 30);
    mcp.configureAlert(1, true, true);
    mcp.enable(true);

    // Setup analog read resolution for pressure sensor
    analogReadResolution(12); 

    // Initialize pins for pressure switch
    pinMode(OUTPUT_PIN, OUTPUT);
    pinMode(INPUT_PIN, INPUT_PULLDOWN);
    digitalWrite(OUTPUT_PIN, HIGH);

    // Send handshake to server
    sendHandshake();
}

void connectToWiFi() {
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("Connected to WiFi!");
}

void sendHandshake() {
    HTTPClient http;
    http.begin(serverAddress);
    http.addHeader("Content-Type", "application/json");

    String macAddress = WiFi.macAddress();
    String handshakeJson = "{\"type\": \"handshake\", \"mac_address\": \"" + macAddress + "\"}";

    int httpResponseCode = http.POST(handshakeJson);
    if (httpResponseCode > 0) {
        Serial.printf("Handshake sent! Response code: %d\n", httpResponseCode);
    } else {
        Serial.printf("Handshake failed! Error: %s\n", http.errorToString(httpResponseCode).c_str());
    }
    http.end();
}

void sendData(float hotJunctionTemp, float coldJunctionTemp, int pressureValue, bool pressureSwitchState) {
    HTTPClient http;
    http.begin(serverAddress);
    http.addHeader("Content-Type", "application/json");
    String postData = "{\"Hot Junction\": " + String(hotJunctionTemp) + ", \"Cold Junction\": " + String(coldJunctionTemp) + ", \"Pressure (RAW ADC)\": " + String(pressureValue) + ", \"Pressure Switch State\": \"" + (pressureSwitchState ? "Closed" : "Open") + "\"}";
    int httpResponseCode = http.POST(postData);
    if (httpResponseCode > 0) {
        Serial.printf("Data sent! Response code: %d\n", httpResponseCode);
    } else {
        Serial.printf("Data send failed! Error: %s\n", http.errorToString(httpResponseCode).c_str());
    }
    http.end();
}

void loop() {
    if (WiFi.status() != WL_CONNECTED) {
        connectToWiFi();
    }

    float hotJunctionTemp = 0;
    float coldJunctionTemp = 0;

    if (thermocoupleConnected) {
        hotJunctionTemp = mcp.readThermocouple();
        coldJunctionTemp = mcp.readAmbient();
    }

    int pressureValue = analogRead(PRESSURE_PIN);
    bool pressureSwitchState = digitalRead(INPUT_PIN);

    sendData(hotJunctionTemp, coldJunctionTemp, pressureValue, pressureSwitchState);

    delay(100);
}
