#include <Adafruit_NeoPixel.h>

#define MESSAGE_BUFFER_SIZE 100

#define LED_PIN_NO 10

// This initializes a "strip" of exactly 1 LED (so not a strip...)
Adafruit_NeoPixel led = Adafruit_NeoPixel(1, LED_PIN_NO, NEO_GRB + NEO_KHZ800);

char msgBuf[MESSAGE_BUFFER_SIZE];
int msgLen;
boolean msgExists = false;

void setup() {
  Serial.begin(9600);
  led.begin();
  led.show();
}

void loop() {
  checkSerialPort();
  if (msgExists) {
    handleMsg();
  }
}

void handleMsg() {
  if (strcmp(msgBuf,"Hello") == 0) {
    // The message was "Hello"
    Serial.print("Hey there handsome!");
  } else if (strcmp(msgBuf, "HALT") == 0) {
    // We need to stop everything we're doing!
    handleHaltMsg();
    Serial.print("HAMMERZEIT");
  } else if (msgLen >= 4 && strncmp(msgBuf, "LED:", 4) == 0) {
    // The message beegins with "LED:"
    // This message should be on the form "LED:r:g:b"
    handleLEDMsg();
    Serial.print("OK");
  } else {
    Serial.print("Ohai");
  }
  byte stopByte = 0;
  Serial.write(stopByte);

  msgLen = 0; // reset the message length counter
  msgExists = false;
}

// This function stops everything the bot is doing right now
void handleHaltMsg() {
  // TODO: This function should do more things when we have more functionality.
  led.setPixelColor(0, 0, 0, 0);
  led.show();
}

// We got a LED message. Handle it!
void handleLEDMsg() {
  char *p;
  p = strtok(msgBuf, ":"); // This will just say "LED"
  // We expect 3 more delimited values (R, G, and B)
  // Note that strtok "remembers" the result of the last call.
  int r = atoi(strtok(NULL, ":"));
  int g = atoi(strtok(NULL, ":"));
  int b = atoi(strtok(NULL, ":"));

  led.setPixelColor(0, r, g, b);
  led.show();
}

void checkSerialPort() {
  while (Serial.available()) {
    char inChar = (char) Serial.read();
    if (inChar == 0) {
      msgBuf[msgLen] = 0; // terminating character
      msgExists = true;
    } else {
      msgBuf[msgLen] = inChar;
      msgLen++;
    }
  }
}
