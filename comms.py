from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import socket
import serial
import time
import datetime
import threading
import math
import queue

startTime = datetime.datetime.now()

# Driving states:
DRIVING_NOWHERE   = 100
DRIVING_FORWARDS  = 101
DRIVING_BACKWARDS = 102

# Turning states:
TURNING_NOWHERE   = 200
TURNING_LEFT      = 201
TURNING_RIGHT     = 202

# States
IDLE              = 100
LEFT              = 101
RIGHT             = 102
FORWARDS          = 103
FORWARDS_LEFT     = 104
FORWARDS_RIGHT    = 105
BACKWARDS         = 106
BACKWARDS_LEFT    = 107
BACKWARDS_RIGHT   = 108

# Actions
DRIVE_FORWARDS  = 200
DRIVE_BACKWARDS = 201
STOP_DRIVING    = 202
TURN_LEFT       = 203
TURN_RIGHT      = 204
STOP_TURNING    = 205

# This dictionary maps a state-action tuple to the resulting state.
stateProgressChart = {}

# Progress for the IDLE state
stateProgressChart[IDLE, DRIVE_FORWARDS]  = FORWARDS
stateProgressChart[IDLE, DRIVE_BACKWARDS] = BACKWARDS
stateProgressChart[IDLE, STOP_DRIVING]    = IDLE
stateProgressChart[IDLE, TURN_LEFT]       = LEFT
stateProgressChart[IDLE, TURN_RIGHT]      = RIGHT
stateProgressChart[IDLE, STOP_TURNING]    = IDLE

# Progress for the LEFT state
stateProgressChart[LEFT, DRIVE_FORWARDS]  = FORWARDS_LEFT
stateProgressChart[LEFT, DRIVE_BACKWARDS] = BACKWARDS_LEFT
stateProgressChart[LEFT, STOP_DRIVING]    = LEFT
stateProgressChart[LEFT, TURN_LEFT]       = LEFT
stateProgressChart[LEFT, TURN_RIGHT]      = LEFT
stateProgressChart[LEFT, STOP_TURNING]    = IDLE

# Progress for the RIGHT state
stateProgressChart[RIGHT, DRIVE_FORWARDS]  = FORWARDS_RIGHT
stateProgressChart[RIGHT, DRIVE_BACKWARDS] = BACKWARDS_RIGHT
stateProgressChart[RIGHT, STOP_DRIVING]    = RIGHT
stateProgressChart[RIGHT, TURN_LEFT]       = RIGHT
stateProgressChart[RIGHT, TURN_RIGHT]      = RIGHT
stateProgressChart[RIGHT, STOP_TURNING]    = IDLE

# Progress for the FORWARDS state
stateProgressChart[FORWARDS, DRIVE_FORWARDS]  = FORWARDS
stateProgressChart[FORWARDS, DRIVE_BACKWARDS] = FORWARDS
stateProgressChart[FORWARDS, STOP_DRIVING]    = IDLE
stateProgressChart[FORWARDS, TURN_LEFT]       = FORWARDS_LEFT
stateProgressChart[FORWARDS, TURN_RIGHT]      = FORWARDS_RIGHT
stateProgressChart[FORWARDS, STOP_TURNING]    = FORWARDS

# Progress for the BACKWARDS state
stateProgressChart[BACKWARDS, DRIVE_FORWARDS]  = BACKWARDS
stateProgressChart[BACKWARDS, DRIVE_BACKWARDS] = BACKWARDS
stateProgressChart[BACKWARDS, STOP_DRIVING]    = IDLE
stateProgressChart[BACKWARDS, TURN_LEFT]       = BACKWARDS_LEFT
stateProgressChart[BACKWARDS, TURN_RIGHT]      = BACKWARDS_RIGHT
stateProgressChart[BACKWARDS, STOP_TURNING]    = BACKWARDS

# Progress for the FORWARDS_LEFT state
stateProgressChart[FORWARDS_LEFT, DRIVE_FORWARDS]  = FORWARDS_LEFT
stateProgressChart[FORWARDS_LEFT, DRIVE_BACKWARDS] = FORWARDS_LEFT
stateProgressChart[FORWARDS_LEFT, STOP_DRIVING]    = LEFT
stateProgressChart[FORWARDS_LEFT, TURN_LEFT]       = FORWARDS_LEFT
stateProgressChart[FORWARDS_LEFT, TURN_RIGHT]      = FORWARDS_LEFT
stateProgressChart[FORWARDS_LEFT, STOP_TURNING]    = FORWARDS

# Progress for the FORWARDS_RIGHT state
stateProgressChart[FORWARDS_RIGHT, DRIVE_FORWARDS]  = FORWARDS_RIGHT
stateProgressChart[FORWARDS_RIGHT, DRIVE_BACKWARDS] = FORWARDS_RIGHT
stateProgressChart[FORWARDS_RIGHT, STOP_DRIVING]    = RIGHT
stateProgressChart[FORWARDS_RIGHT, TURN_LEFT]       = FORWARDS_RIGHT
stateProgressChart[FORWARDS_RIGHT, TURN_RIGHT]      = FORWARDS_RIGHT
stateProgressChart[FORWARDS_RIGHT, STOP_TURNING]    = FORWARDS

# Progress for the BACKWARDS_LEFT state
stateProgressChart[BACKWARDS_LEFT, DRIVE_FORWARDS]  = BACKWARDS_LEFT
stateProgressChart[BACKWARDS_LEFT, DRIVE_BACKWARDS] = BACKWARDS_LEFT
stateProgressChart[BACKWARDS_LEFT, STOP_DRIVING]    = LEFT
stateProgressChart[BACKWARDS_LEFT, TURN_LEFT]       = BACKWARDS_LEFT
stateProgressChart[BACKWARDS_LEFT, TURN_RIGHT]      = BACKWARDS_LEFT
stateProgressChart[BACKWARDS_LEFT, STOP_TURNING]    = BACKWARDS

# Progress for the BACKWARDS_RIGHT state
stateProgressChart[BACKWARDS_RIGHT, DRIVE_FORWARDS]  = BACKWARDS_RIGHT
stateProgressChart[BACKWARDS_RIGHT, DRIVE_BACKWARDS] = BACKWARDS_RIGHT
stateProgressChart[BACKWARDS_RIGHT, STOP_DRIVING]    = RIGHT
stateProgressChart[BACKWARDS_RIGHT, TURN_LEFT]       = BACKWARDS_RIGHT
stateProgressChart[BACKWARDS_RIGHT, TURN_RIGHT]      = BACKWARDS_RIGHT
stateProgressChart[BACKWARDS_RIGHT, STOP_TURNING]    = FORWARDS

state = IDLE
stateLock = threading.Lock()

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
    global stateLock, state

    self.establishConnection()
    i = 0
    while self.shouldIKeepGoing():
      #hectoseconds = int(round(time.time() * 100))
      #r = (hectoseconds + 50) % 255
      #g = (hectoseconds - 50) % 255
      #b =  hectoseconds       % 255
      #command = "LED:" + str(r) + ":" + str(g) + ":" + str(b)

      stateLock.acquire()
      command = "STATE:" + str(state)
      stateLock.release()

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
    global stateLock, state, stateProgressChart
    # Depending on the path requested in the GET, take a different action.
    parsed_path = urlparse(self.path)
    if   (self.path == "/driveForwards"):
      action = DRIVE_FORWARDS
    elif (self.path == "/driveBackwards"):
      action = DRIVE_BACKWARDS
    elif (self.path == "/turnLeft"):
      action = TURN_LEFT
    elif (self.path == "/turnRight"):
      action = TURN_RIGHT
    elif (self.path == "/stopDriving"):
      action = STOP_DRIVING
    elif (self.path == "/stopTurning"):
      action = STOP_TURNING

    stateLock.acquire()
    state = stateProgressChart[state, action]
    stateLock.release()

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
    # wait indefinitely (commsThread won't quit on its own)
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
