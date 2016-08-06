#include <Adafruit_NeoPixel.h>

// There are 5 analog line sensors in the front of the bot
#define LINE_SENSOR_PIN_L  0
#define LINE_SENSOR_PIN_CL 1
#define LINE_SENSOR_PIN_C  2
#define LINE_SENSOR_PIN_CR 3
#define LINE_SENSOR_PIN_R  4

// Each pin here controls two of the four motors on the bot
#define MOTOR_SPD_PIN_L    5
#define MOTOR_SPD_PIN_R    6
#define MOTOR_DIR_PIN_R    7
#define MOTOR_DIR_PIN_L    12

// The led can do fancy things like glow
#define LED_PIN            10

// The buzzer can play songs!
#define BUZZER_PIN         16

// Two IR transmitters and an IR receiver let us ping the environment
#define IR_TX_PIN_L        13
#define IR_TX_PIN_R        8
#define IR_RX_PIN          17

#define MESSAGE_BUFFER_SIZE 100

// This initializes a "strip" of exactly 1 LED (so not a strip...)
Adafruit_NeoPixel led = Adafruit_NeoPixel(1, LED_PIN, NEO_GRB + NEO_KHZ800);

char msgBuf[MESSAGE_BUFFER_SIZE];
int msgLen;
boolean msgExists = false;

void setup() {
  Serial.begin(9600);
  led.begin();
  led.show();

  pinMode(MOTOR_SPD_PIN_L, OUTPUT);
  pinMode(MOTOR_SPD_PIN_R, OUTPUT);
  pinMode(MOTOR_DIR_PIN_L, OUTPUT);
  pinMode(MOTOR_DIR_PIN_R, OUTPUT);
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
