String inputString = "";
boolean stringComplete = false;

void setup() {
  Serial.begin(9600);
  inputString.reserve(200); // reserves space
}

void loop() {
  checkSerialPort();

  // check if data has been sent from the computer
  if (stringComplete) {
    stringComplete = false;
    byte reply = 0;
    if (inputString.equals("Hello")) {
      Serial.print("A");
      //reply = 1;
    } else {
      Serial.print("B");
      //reply = 2;
    }
    // Serial.write(reply);
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
