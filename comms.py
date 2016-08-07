from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import socket
import serial
import time
import datetime
import threading
import math

startTime = datetime.datetime.now()

def getTimestamp():
  timeNow = datetime.datetime.now()
  return str(timeNow - startTime)

# This class handles communications with the arduino controller
# over an already-established serial port (ser)
class ArduinoCommsThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.connected = False
    self.keepGoing = True
    self.keepGoingLock = threading.Lock()
    self.messagesReceived = 0

  def shouldIKeepGoing(self):
    self.keepGoingLock.acquire() # begin mutex zone
    wellShouldI = self.keepGoing
    self.keepGoingLock.release() # stop mutex zone
    return wellShouldI

  def halt(self):
    self.keepGoingLock.acquire()
    self.keepGoing = False
    self.keepGoingLock.release()

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
    self.messagesReceived += 1
    return reply

  def establishConnection(self):
    (success, ser) = self.tryArduinoConnection()
    while not success:
      if self.shouldIKeepGoing():
        time.sleep(0.2)
        (success, ser) = self.tryArduinoConnection()
      else:
        exit(0)
    self.ser = ser
    self.connected = True

  def run(self):
    self.establishConnection()
    i = 0
    while self.shouldIKeepGoing():
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

class HTTPHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    # Depending on the path requested in the GET, take a different action.
    parsed_path = urlparse(self.path)
    if   (self.path == "/driveForwards"):
      pass
    elif (self.path == "/driveBackwards"):
      pass
    elif (self.path == "/turnLeft"):
      pass
    elif (self.path == "/turnRight"):
      pass
    elif (self.path == "/stopDriving"):
      pass
    elif (self.path == "/stopTurning"):
      pass

    # Respond by describing the (new) state of the machine
    message = "COPY THAT"
    self.send_response(200)
    self.end_headers()
    self.wfile.write(bytes(message, 'UTF-8'))
    return

def getNetworkIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('192.168.1.1', 80))
    return s.getsockname()[0]

def main():
  # Start arduino comms thread
  commsThread = ArduinoCommsThread()
  commsThread.daemon = True
  commsThread.start()

  # Start HTTP server thread
  myip = getNetworkIP()
  server = HTTPServer((myip, 8080), HTTPHandler)
  httpThread = threading.Thread(target = server.serve_forever)
  httpThread.daemon = True
  httpThread.start()

  try:
    # wait indefinitely
    commsThread.join()
  except KeyboardInterrupt:
    commsThread.halt() # ask to die
    server.shutdown() # ask to die
    commsThread.join()
    httpThread.join()

    # Print pretty things when session is over
    msgsRcvd = commsThread.messagesReceived
    timePassed = (datetime.datetime.now() - startTime)
    secondsPassed = timePassed.seconds
    microseconds = timePassed.microseconds
    msgPerSecond = msgsRcvd / (secondsPassed + (1000000 / microseconds))
    print("")
    print("Session terminated")
    print("Received " + str(msgsRcvd) + " messages in " + str(secondsPassed) + "." + str(microseconds)[:2] + " seconds.")
    print("Avg. messages per second: " + str(math.ceil(msgPerSecond)))

main()
