byte count;
byte incomingByte;

void setup() {
  count = 0;
  Serial.begin(9600);
}

void loop() {
   // check if data has been sent from the computer
  if (Serial.available()) {
    incomingByte = Serial.read(); // Read input
    count++;
    byte reply;
    switch (incomingByte) {
      case 1:
        reply = 0;
        break;
      default:
        reply = 1;
        break;
    }
    Serial.write(reply);
  }
}
