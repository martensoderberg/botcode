import serial
import time

def loop():
  ser = serial.Serial(
    port = '/dev/ttyACM0',
    baudrate = 9600,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = 2,
    xonxoff = False,
    rtscts = False,
    writeTimeout = 2
  )
  i = 0

  while i < 100:
    command = bytes([1])
    print("Sent: 1")
    ser.write(command)
    time.sleep(0.05)
    returnedBytes = ser.read(ser.inWaiting())
    resultString = returnedBytes.decode("utf-8")
    #result = int.from_bytes(returnedBytes, byteorder='big')
    print("Rcvd: " + str(resultString))
    i = i + 1
  ser.close()

loop()
