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

// State constants
#define IDLE            100
#define LEFT            101
#define RIGHT           102
#define FORWARDS        103
#define FORWARDS_LEFT   104
#define FORWARDS_RIGHT  105
#define BACKWARDS       106
#define BACKWARDS_LEFT  107
#define BACKWARDS_RIGHT 108

// Motor constants
#define FORWARDS  0
#define BACKWARDS 1

#define MESSAGE_BUFFER_SIZE 100

// This initializes a "strip" of exactly 1 LED (so not a strip...)
Adafruit_NeoPixel led = Adafruit_NeoPixel(1, LED_PIN, NEO_GRB + NEO_KHZ800);

char sendBuf[MESSAGE_BUFFER_SIZE];
char msgBuf[MESSAGE_BUFFER_SIZE];
int msgLen;
boolean msgExists = false;
boolean stateChanged = true;

int state = IDLE;

int pinValues [9][7] = {
  { FORWARDS,  FORWARDS,   0,   0,   0,   0,   0},
  { FORWARDS, BACKWARDS, 100, 100,   0,   0, 100},
  {BACKWARDS,  FORWARDS, 100, 100,   0, 100,   0},
  { FORWARDS,  FORWARDS, 250, 250, 100,   0,   0},
  { FORWARDS,  FORWARDS, 250,  50, 100,   0, 100},
  { FORWARDS,  FORWARDS,  50, 250, 100, 100,   0},
  {BACKWARDS, BACKWARDS, 250, 250,  50,  50,  50},
  {BACKWARDS, BACKWARDS, 250,  50,  50,  50, 150},
  {BACKWARDS, BACKWARDS,  50, 250,  50, 150,  50}
};

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
  if (stateChanged) {
    updatePins();
  }

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
    stateChanged = true;
    sprintf(sendBuf, "HAMMERZEIT");
  } else if (msgLen >= 6 && strncmp(msgBuf, "STATE:", 6) == 0) {
    // This message begins with "STATE:"
    // This message should be on the form "STATE:xxx:yyy"
    handleStateMsg();
    stateChanged = true;
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
  led.setPixelColor(0, 0, 0, 0);
  led.show();

  state = IDLE;
  stateChanged = true;
}

// This function handles a state message
void handleStateMsg() {
  char *p;
  p = strtok(msgBuf, ":"); // This will just say "STATE"
  // We expect 1 more delimited values (state)
  // note that strtok "remembers" the result of the last call.
  state = atoi(strtok(NULL, ":"));
}

void updatePins() {
  // The pin values are stored in the pinValues matrix
  // The index for this matrix is derived from the state value...
  int pinIndex = (state - 100);
  int rightSideDir = pinValues[pinIndex][0];
  int leftSideDir  = pinValues[pinIndex][1];
  int rightSideSpd = pinValues[pinIndex][2];
  int leftSideSpd  = pinValues[pinIndex][3];
  int r = pinValues[pinIndex][4];
  int g = pinValues[pinIndex][5];
  int b = pinValues[pinIndex][6];

  digitalWrite(MOTOR_DIR_PIN_L, leftSideDir);
  digitalWrite(MOTOR_DIR_PIN_R, rightSideDir);
  analogWrite (MOTOR_SPD_PIN_L, leftSideSpd);
  analogWrite (MOTOR_SPD_PIN_R, rightSideSpd);

  led.setPixelColor(0, r, g, b);
  led.show();
  stateChanged = false;
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
