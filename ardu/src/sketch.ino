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

// These constants defines the column order for the pinValues matrix
#define IDX_DIR_R 0
#define IDX_DIR_L 1
#define IDX_SPD_R 2
#define IDX_SPD_L 3

// Motor constants
#define FORWARDS  0
#define BACKWARDS 1

// Message types
#define LED_MSG    0x11
#define STATE_MSG  0x22
#define HALT_MSG   0x33
#define STATUS_REQ 0x44
#define STATUS_MSG 0x55
#define ACK        0xEE
#define SAY_AGAIN  0xFF

#define MESSAGE_BUFFER_SIZE 100

// This initializes a "strip" of exactly 1 LED (so not a strip...)
Adafruit_NeoPixel led = Adafruit_NeoPixel(1, LED_PIN, NEO_GRB + NEO_KHZ800);

char state;
char ledValues[3];
int statusValues[5];
char statusMsgBuf[10];

// DIR_R, DIR_L, SPD_R, SPD_L
int pinValues [9][7] = {
  { FORWARDS,  FORWARDS,   0,   0}, // IDLE            (0)
  { FORWARDS, BACKWARDS, 100, 100}, // LEFT            (1)
  {BACKWARDS,  FORWARDS, 100, 100}, // RIGHT           (2)
  { FORWARDS,  FORWARDS, 250, 250}, // FORWARDS        (3)
  { FORWARDS,  FORWARDS, 250,  50}, // FORWARDS_LEFT   (4)
  { FORWARDS,  FORWARDS,  50, 250}, // FORWARDS_RIGHT  (5)
  {BACKWARDS, BACKWARDS, 250, 250}, // BACKWARDS       (6)
  {BACKWARDS, BACKWARDS, 250,  50}, // BACKWARDS_LEFT  (7)
  {BACKWARDS, BACKWARDS,  50, 250}  // BACKWARDS_RIGHT (8)
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
  readStatus();
  checkSerialPort();
}

void readStatus() {
  statusValues[0] = analogRead(LINE_SENSOR_PIN_L);
  statusValues[1] = analogRead(LINE_SENSOR_PIN_CL);
  statusValues[2] = analogRead(LINE_SENSOR_PIN_C);
  statusValues[3] = analogRead(LINE_SENSOR_PIN_CR);
  statusValues[4] = analogRead(LINE_SENSOR_PIN_R);
}

void prepareStatusMsg() {
  // Prepare high/low bytes of the statusMsgBuf array
  for (int i = 0; i < 5; i++) {
    statusMsgBuf[(i * 2)]     = statusValues[i] / 0xFF;
    statusMsgBuf[(i * 2) + 1] = statusValues[i] % 0xFF;
  }
}

void handleStateChange() {
  // The pin values are stored in the pinValues matrix
  digitalWrite(MOTOR_DIR_PIN_L, pinValues[state][IDX_DIR_L]);
  digitalWrite(MOTOR_DIR_PIN_R, pinValues[state][IDX_DIR_R]);
  analogWrite (MOTOR_SPD_PIN_L, pinValues[state][IDX_SPD_L]);
  analogWrite (MOTOR_SPD_PIN_R, pinValues[state][IDX_SPD_R]);
}

void handleLedChange() {
  led.setPixelColor(
    0,
    ledValues[0],
    ledValues[1],
    ledValues[2]
  );
  led.show();
}

void checkSerialPort() {
  if (Serial.available() == 0) {
    return;
  }

  char commandByte = Serial.read();
  switch (commandByte) {
    case STATE_MSG:
      state = Serial.read();
      Serial.write(ACK);
      handleStateChange();
      break;
    case LED_MSG:
      ledValues[0] = Serial.read();
      ledValues[1] = Serial.read();
      ledValues[2] = Serial.read();
      Serial.write(ACK);
      handleLedChange();
      break;
    case HALT_MSG:
      state = 0; // IDLE
      Serial.write(ACK);
      handleStateChange();
    case STATUS_REQ:
      prepareStatusMsg();
      Serial.write(STATUS_MSG);
      Serial.write(statusMsgBuf);
      break;
    default:
      flushSerialInput();
      Serial.write(SAY_AGAIN);
      break;
  }
}

void flushSerialInput() {
  while(Serial.available() > 0) {
    char t = Serial.read();
  }
}
