import serial
import time
import datetime
import threading

startTime = datetime.datetime.now()
connected = False

def getTimestamp():
  timeNow = datetime.datetime.now()
  return str(timeNow - startTime)

# This class handles communications with the arduino controller
# over an already-established serial port (ser)
class ArduinoCommsThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)

  def defineArduinoConnection(self, portName):
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

  def tryArduinoConnection(self):
    for portNumber in [0, 1, 2, 3]:
      try:
        portName = "/dev/ttyACM" + str(portNumber)
        print(getTimestamp() + ": Attempting to connect to arduino on " + portName + "... ",end="")
        ser = self.defineArduinoConnection(portName)
        print("succeded")
        return (True, ser) # success
      except serial.SerialException:
        print("failed")
        continue
      except Exception as exception:
        print("failed for an unknown reason!")
        print(type(exception))
    return (False, None) # nothing found

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
    # Establish connection
    (success, ser) = self.tryArduinoConnection()
    while not success:
      time.sleep(1)
      (success, ser) = self.tryArduinoConnection()
    self.ser = ser

    i = 0
    while i < 10000:
      if (i % 2) == 1:
        command = "LED:0:0:0"
      else:
        command = "LED:15:105:255"
      print(getTimestamp() + ": Sent: " + command)
      self.sendMessage(command)
      reply = self.receiveMessage()
      print(getTimestamp() + ": Rcvd: " + reply)
      i = i + 1
    ser.close()

def main():
  commsThread = ArduinoCommsThread()
  commsThread.start()

main()
