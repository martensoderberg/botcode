import serial
import time
import thread

def defineArduinoConnection(portNumber):
  portName = "/dev/ttyACM" + str(portNumber)
  ser = serial.Serial(
    port = portName
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
  for portNumber in [1, 2, 3, 4]:
    try:
      ser = defineArduinoConnection(portNumber)
      return (True, ser) # success
    except:
      continue
  return (False, None) # nothing found


# This class handles communications with the arduino controller
# over an already-established serial port (ser)
class ArduinoCommsThread:
  def __init__(self, ser):
    self.ser = ser

  def run(self):
    while i < 100:
      command = bytes([1])
      print("Sent: 1")
      ser.write(command)
      time.sleep(0.05)
      returnedBytes = ser.read(ser.inWaiting())
      resultString = returnedBytes.decode("utf-8")
      print("Rcvd: " + str(resultString))
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