import serial

def loop():
  ser = serial.Serial('/dev/ttyACM0', 9600)
  i = 0

  while i < 100:
    outString = b"Hello"
    print("Sent: " + outString)
    ser.write(outString)
    result = ser.read()
    print("Rcvd: " + result)
    i++
    ser.close()

loop()