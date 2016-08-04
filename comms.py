import serial
import time
import threading

def defineArduinoConnection(portName):
  ser = serial.Serial(
    port = portName,
    baudrate = 9600,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = 2,
    xonxoff = False,
    rtscts = False,
    writeTimeout = 2
  )
  return ser

def tryArduinoConnection():
  for portNumber in [0, 1, 2, 3]:
    try:
      portName = "/dev/ttyACM" + str(portNumber)
      print("Attempting to connect to arduino on " + portName + "... ",end="")
      ser = defineArduinoConnection(portName)
      print("succeded")
      return (True, ser) # success
    except:
      print("failed")
      continue
  return (False, None) # nothing found

# This class handles communications with the arduino controller
# over an already-established serial port (ser)
class ArduinoCommsThread(threading.Thread):
  def __init__(self, ser):
    threading.Thread.__init__(self)
    self.ser = ser

  def run(self):
    ser = self.ser
    i = 0
    while i < 100:
      command = "Hello"
      print("Sent: " + command)
      ser.write(str.encode(command)) # send a bytes object of the string
      ser.write(bytes([0]))
      time.sleep(0.05)
      returnedBytes = ser.read(1)
      print("Rcvd: " + str(returnedBytes))
      i = i + 1
    ser.close()

def main():
  (success, ser) = tryArduinoConnection()
  if success:
    commsThread = ArduinoCommsThread(ser)
    commsThread.start()
  else:
    print("Could not connect to Arduino, exiting")
    exit(1)
main()
