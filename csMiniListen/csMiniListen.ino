#include "Adafruit_MCP9601.h"

#define SDA_PIN 18
#define SCL_PIN 19
#define I2C_ADDRESS (0x67)
#define PRESSURE_PIN 2
#define OUTPUT_PIN 4
#define INPUT_PIN 5

Adafruit_MCP9601 mcp;

void setup() {
    Serial.begin(115200);
    while (!Serial) {
      delay(10);
    }

    /* Initialize the I2C bus on pins 18 and 19. */
    Wire.begin(SDA_PIN, SCL_PIN);

    /* Initialise the driver with I2C_ADDRESS and the default I2C bus. */
    if (! mcp.begin(I2C_ADDRESS)) {
        while (1);
    }

    mcp.setADCresolution(MCP9600_ADCRESOLUTION_18);
    mcp.setThermocoupleType(MCP9600_TYPE_K);
    mcp.setFilterCoefficient(3);
    mcp.setAlertTemperature(1, 30);
    mcp.configureAlert(1, true, true);  // alert 1 enabled, rising temp
    mcp.enable(true);

    // Setup analog read resolution for pressure sensor
    analogReadResolution(12); // 12 bits resolution

    // Initialize pins for pressure switch
    pinMode(OUTPUT_PIN, OUTPUT);
    pinMode(INPUT_PIN, INPUT_PULLDOWN);
    digitalWrite(OUTPUT_PIN, HIGH);  // Set the output pin to HIGH initially
}

void loop() {
    uint8_t status = mcp.getStatus();

    if (status & MCP9601_STATUS_OPENCIRCUIT) { 
        return; // don't continue, since there's no thermocouple
    }
    if (status & MCP9601_STATUS_SHORTCIRCUIT) { 
        return; // don't continue, since the sensor is not working
    }

    float hotJunctionTemp = mcp.readThermocouple();
    float coldJunctionTemp = mcp.readAmbient();

    // Read pressure value from CJMCU-36
    int pressureValue = analogRead(PRESSURE_PIN);

    // Read the state of the INPUT pin
    bool pressureSwitchState = digitalRead(INPUT_PIN);  

    // Print all values on a single line
    Serial.print("Hot Junction: ");
    Serial.print(hotJunctionTemp);
    Serial.print(", Cold Junction: ");
    Serial.print(coldJunctionTemp);
    Serial.print(", Pressure (RAW ADC): ");
    Serial.print(pressureValue);
    Serial.print(", Pressure Switch State: ");
    Serial.println(pressureSwitchState ? "Closed" : "Open");  // Print the state of the switch

    delay(100);
}
