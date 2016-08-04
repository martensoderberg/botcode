#include <Adafruit_NeoPixel.h>

#define LED_PIN_NO 10

// This initializes a "strip" of exactly 1 LED (so not a strip...)
Adafruit_NeoPixel led = Adafruit_NeoPixel(1, LED_PIN_NO, NEO_GRB + NEO_KHZ800);

String inputString = "";
boolean stringComplete = false;

void setup() {
  Serial.begin(9600);
  inputString.reserve(200); // reserves space
  led.begin();
  led.show();
}

void loop() {
  checkSerialPort();

  // check if data has been sent from the computer
  if (stringComplete) {
    stringComplete = false;
    if (inputString.equals("Hello")) {
      Serial.print("Hey there handsome!");
    } else if (inputString.startsWith("LED:")) {
      // This message should be on the form "LED:r:g:b"

    } else {
      Serial.print("Ohai");
    }
    byte stopByte = 0;
    Serial.write(stopByte);
    inputString = "";
  }
}

void checkSerialPort() {
  while (Serial.available()) {
    char inChar = (char) Serial.read();
    if (inChar == 0) {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}
