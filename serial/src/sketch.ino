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
    switch (incomingByte) {
      case 1:
        Serial.write("Go forth!");
        break;
      default:
        Serial.write("What?");
        break;
    }
  }
}
