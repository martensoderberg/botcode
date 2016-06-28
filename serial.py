import serial

def loop():
  serial = serial.Serial('/dev/ttyACM0', 9600)

  while True:
    outString = b"Hello"
    print("Sent: " + outString)
    serial.write(outString)
    result = serial.read()
    print("Rcvd: " + result)

loop()