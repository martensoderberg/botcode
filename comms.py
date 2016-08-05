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

  def sendMessage(self, message):
    ser = self.ser
    ser.write(str.encode(message))
    ser.write(bytes([0])) # terminate message with zero-byte (0x00)

  def receiveMessage(self):
    ser = self.ser
    frame = bytearray()
    stopByteEncountered = False
    while not stopByteEncountered:
      byte = ser.read(1)
      if byte[0] == 0:
        stopByteEncountered = True
      else:
        frame += byte
    return frame.decode("utf-8")

  def run(self):
    ser = self.ser
    i = 0
    while i < 100:
      if (i % 2) == 1:
        command = "LED:0:0:0"
      else:
        command = "LED:15:105:255"
      print("Sent: " + command)
      self.sendMessage(command)
      reply = self.receiveMessage()
      print("Rcvd: " + reply)
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
