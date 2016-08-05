import serial
import time
import datetime
import threading

startTime = datetime.datetime.now()
keepGoing = True
keepGoingLock = threading.Lock()

def getTimestamp():
  timeNow = datetime.datetime.now()
  return str(timeNow - startTime)

def shouldIKeepGoing():
  global keepGoingLock, keepGoing
  wellShouldI = True
  keepGoingLock.acquire() # begin mutex zone
  wellShouldI = keepGoing
  keepGoingLock.release() # stop mutex zone
  return wellShouldI

def halt():
  global keepGoingLock, keepGoing
  keepGoingLock.acquire()
  keepGoing = False
  keepGoingLock.release()

# This class handles communications with the arduino controller
# over an already-established serial port (ser)
class ArduinoCommsThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.connected = False

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
    print(getTimestamp() + ": Sent: " + message)

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
    reply = frame.decode("utf-8")
    print(getTimestamp() + ": Rcvd: " + reply)
    return reply

  def establishConnection(self):
    (success, ser) = self.tryArduinoConnection()
    while not success:
      if shouldIKeepGoing():
        time.sleep(0.2)
        (success, ser) = self.tryArduinoConnection()
      else:
        exit(0)
    self.ser = ser
    self.connected = True

  def run(self):
    self.establishConnection()
    i = 0
    while shouldIKeepGoing():
      hectoseconds = int(round(time.time() * 100))
      r = (hectoseconds + 50) % 255
      g = (hectoseconds - 50) % 255
      b =  hectoseconds       % 255
      command = "LED:" + str(r) + ":" + str(g) + ":" + str(b)
      try:
        self.sendMessage(command)
        self.receiveMessage()
      except serial.SerialException:
        self.connected = False
        self.establishConnection()
      i = i + 1
    if self.connected:
      self.sendMessage("HALT")
      self.receiveMessage()
      self.ser.close()

def main():
  commsThread = ArduinoCommsThread()
  commsThread.daemon = True
  commsThread.start()
  try:
    commsThread.join()
  except KeyboardInterrupt:
    halt()
  finally:
    commsThread.join()

main()
