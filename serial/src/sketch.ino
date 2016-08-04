#include <Adafruit_NeoPixel.h>

#define MESSAGE_BUFFER_SIZE 100

#define LED_PIN_NO 10

// This initializes a "strip" of exactly 1 LED (so not a strip...)
Adafruit_NeoPixel led = Adafruit_NeoPixel(1, LED_PIN_NO, NEO_GRB + NEO_KHZ800);

char msgBuf[MESSAGE_BUFFER_SIZE];
int msgLen;
boolean stringComplete = false;

void setup() {
  Serial.begin(9600);
  led.begin();
  led.show();
}

void loop() {
  checkSerialPort();

  // check if data has been sent from the computer
  if (stringComplete) {
    stringComplete = false;
    if (strcmp(msgBuf,"Hello") == 0) {
      // The message was "Hello"
      Serial.print("Hey there handsome!");
    } else if (msgLen >= 4 && strncmp(msgBuf, "LED:", 4) == 0) {
      // The message beegins with "LED:"
      // This message should be on the form "LED:r:g:b"

    } else {
      Serial.print("Ohai");
    }
    byte stopByte = 0;
    Serial.write(stopByte);
    msgLen = 0; // reset the message length counter
  }
}

void checkSerialPort() {
  while (Serial.available()) {
    char inChar = (char) Serial.read();
    if (inChar == 0) {
      msgBuf[msgLen] = 0; // terminating character
      stringComplete = true;
    } else {
      msgBuf[msgLen] = inChar;
      msgLen++;
    }
  }
}
