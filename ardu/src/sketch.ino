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

// State constants -- driving states
#define DRIVING_NOWHERE   100
#define DRIVING_FORWARDS  110
#define DRIVING_BACKWARDS 120

// State constants -- turning states
#define TURNING_NOWHERE   200
#define TURNING_LEFT      210
#define TURNING_RIGHT     220

#define MESSAGE_BUFFER_SIZE 100

// This initializes a "strip" of exactly 1 LED (so not a strip...)
Adafruit_NeoPixel led = Adafruit_NeoPixel(1, LED_PIN, NEO_GRB + NEO_KHZ800);

char sendBuf[MESSAGE_BUFFER_SIZE];
char msgBuf[MESSAGE_BUFFER_SIZE];
int msgLen;
boolean msgExists = false;

void setup() {
  Serial.begin(9600);
  led.begin();
  led.show();

  pinMode(LINE_SENSOR_PIN_L,  INPUT);
  pinMode(LINE_SENSOR_PIN_CL, INPUT);
  pinMode(LINE_SENSOR_PIN_C,  INPUT);
  pinMode(LINE_SENSOR_PIN_CR, INPUT);
  pinMode(LINE_SENSOR_PIN_R,  INPUT);

  pinMode(MOTOR_SPD_PIN_L, OUTPUT);
  pinMode(MOTOR_SPD_PIN_R, OUTPUT);
  pinMode(MOTOR_DIR_PIN_L, OUTPUT);
  pinMode(MOTOR_DIR_PIN_R, OUTPUT);

  pinMode(LED_PIN, OUTPUT);

  pinMode(IR_TX_PIN_L, OUTPUT);
  pinMode(IR_TX_PIN_R, OUTPUT);
  pinMode(IR_RX_PIN, INPUT);
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
    sprintf(sendBuf, "Hey there handsome!");
  } else if (strcmp(msgBuf, "HALT") == 0) {
    // We need to stop everything we're doing!
    handleHaltMsg();
    sprintf(sendBuf, "HAMMERZEIT");
  } else if (msgLen >= 6 && strncmp(msgBuf, "STATE:", 6) == 0) {
    // This message begins with "STATE:"
    // This message should be on the form "STATE:xxx:yyy"
    handleStateMsg();
    prepareStatusMsg();
  } else if (msgLen >= 4 && strncmp(msgBuf, "LED:", 4) == 0) {
    // The message begins with "LED:"
    // This message should be on the form "LED:r:g:b"
    handleLEDMsg();
    prepareStatusMsg();
  } else {
    sprintf(sendBuf, "I didn't quite get that");
  }
  Serial.write(sendBuf);
  byte stopByte = 0;
  Serial.write(stopByte);

  msgLen = 0; // reset the message length counter
  msgExists = false;
}

void prepareStatusMsg() {
  int analogL  = analogRead(LINE_SENSOR_PIN_L);
  int analogCL = analogRead(LINE_SENSOR_PIN_CL);
  int analogC  = analogRead(LINE_SENSOR_PIN_C);
  int analogCR = analogRead(LINE_SENSOR_PIN_CR);
  int analogR  = analogRead(LINE_SENSOR_PIN_R);

  sprintf(
    sendBuf,
    "OK:%d:%d:%d:%d:%d",
    analogL,
    analogCL,
    analogC,
    analogCR,
    analogR
  );
}

// This function stops everything the bot is doing right now
void handleHaltMsg() {
  // TODO: This function should do more things when we have more functionality.
  led.setPixelColor(0, 0, 0, 0);
  led.show();
}

// This function handles a state message
void handleStateMsg() {
  char *p;
  p = strtok(msgBuf, ":"); // This will just say "STATE"
  // We expect 2 more delimited values (drivingState and turningState)
  // note that strtok "remembers" the result of the last call.
  int drivingState = atoi(strtok(NULL, ":"));
  int turningState = atoi(strtok(NULL, ":"));

  int r = 0;
  int g = 0;
  int b = 0;

  int leftSideSpeed = 0;
  int rightSideSpeed = 0;

  switch (drivingState) {
    case DRIVING_NOWHERE:
      break;
    case DRIVING_FORWARDS:
      r += 25;
      g += 50;
      b += 75;
      leftSideSpeed += 100;
      rightSideSpeed += 100;
      break;
    case DRIVING_BACKWARDS:
      g += 100;
      leftSideSpeed -= 100;
      rightSideSpeed -= 100;
      break;
  }

  switch (turningState) {
    case TURNING_NOWHERE:
      break;
    case TURNING_LEFT:
      b += 100;
      leftSideSpeed -= 50;
      rightSideSpeed += 50;
      break;
    case TURNING_RIGHT:
      r += 100;
      leftSideSpeed += 50;
      rightSideSpeed -= 50;
      break;
  }

  led.setPixelColor(0, r, g, b);
  led.show();

  if (leftSideSpeed > 0) {
    // Go forward
    digitalWrite(MOTOR_DIR_PIN_L, 0);
  } else {
    // Go backward
    digitalWrite(MOTOR_DIR_PIN_L, 1);
    //leftSideSpeed = -leftSideSpeed; // we need positive values
  }

  if (rightSideSpeed > 0) {
    // Go forward
    digitalWrite(MOTOR_DIR_PIN_R, 0);
  } else {
    // Go backward
    digitalWrite(MOTOR_DIR_PIN_R, 1);
   // rightSideSpeed = -rightSideSpeed; // we need positive values
  }

  digitalWrite(MOTOR_SPD_PIN_L, leftSideSpeed);
  digitalWrite(MOTOR_SPD_PIN_R, rightSideSpeed);
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
