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
    if (inputString.equals("Hello")) {
      Serial.print("Hey there handsome!");
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
