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

# States
IDLE            = 0
LEFT            = 1
RIGHT           = 2
FORWARDS        = 3
FORWARDS_LEFT   = 4
FORWARDS_RIGHT  = 5
BACKWARDS       = 6
BACKWARDS_LEFT  = 7
BACKWARDS_RIGHT = 8

# Message types
LED_MSG    = 0x11
STATE_MSG  = 0x22
HALT_MSG   = 0x33
STATUS_REQ = 0x44
STATUS_MSG = 0x55
ACK        = 0xEE
SAY_AGAIN  = 0xFF

# Actions
DRIVE_FORWARDS  = "driveForwards"
DRIVE_BACKWARDS = "driveBackwards"
STOP_DRIVING    = "stopDriving"
TURN_LEFT       = "turnLeft"
TURN_RIGHT      = "turnRight"
STOP_TURNING    = "stopTurning"

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


# Color chart for the LED, (r, g, b)
ledColorChart = {}
ledColorChart[IDLE]            = (  0,   0,   0)
ledColorChart[LEFT]            = (  0,   0, 100)
ledColorChart[RIGHT]           = (  0, 100,   0)
ledColorChart[FORWARDS]        = (100,   0,   0)
ledColorChart[FORWARDS_LEFT]   = (100,   0, 100)
ledColorChart[FORWARDS_RIGHT]  = (100, 100,   0)
ledColorChart[BACKWARDS]       = ( 50,  50,  50)
ledColorChart[BACKWARDS_LEFT]  = ( 50,  50, 150)
ledColorChart[BACKWARDS_RIGHT] = ( 50, 150,  50)

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
    self.messagesSent = 0
    self.lastLEDMsgTime   = time.time()
    self.lastStateMsgTime = time.time()

  def shouldIKeepGoing(self):
    self.keepGoingLock.acquire()
    wellShouldI = self.keepGoing
    self.keepGoingLock.release()
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
        ser = self.defineArduinoConnection(portName)
        return (True, ser) # success
      except serial.SerialException:
        continue
      except Exception as exception:
        print("failed for an unknown reason!")
        print(type(exception))
    return (False, None) # nothing found

  def sendMessage(self, message):
    self.ser.write(message)
    self.messagesSent += 1
    print(getTimestamp() + ": Sent: " + str(message))

  def receiveMessage(self):
    frame = bytearray()
    commandByte = self.ser.read(1)
    if commandByte[0] == SAY_AGAIN:
      pass
      # we should handle this somehow
      print(getTimestamp() + ": Rcvd: SAY_AGAIN")
    elif commandByte[0] == ACK:
      pass
      print(getTimestamp() + ": Rcvd: ACK")
    elif commandByte[0] == STATUS_MSG:
      # we expect 10 more bytes!
      status = self.ser.read(10)
      # do nothing with them...
      print(getTimestamp() + ": Rcvd: STATUS_MSG")
    self.messagesReceived += 1
    return

  def establishConnection(self):
    (success, ser) = self.tryArduinoConnection()
    counter = 0
    while not success:
      if self.shouldIKeepGoing():
        time.sleep(0.2)
        (success, ser) = self.tryArduinoConnection()
        counter += 1
        if counter > 10:
          print(getTimestamp() + ": Can't connect to arduino, retrying...")
          counter = 0
      else:
        exit(0)
    print(getTimestamp() + ": Connected to arduino")
    self.ser = ser
    self.connected = True

  def run(self):
    global stateLock, state

    self.establishConnection()
    i = 0
    while self.shouldIKeepGoing():
      command = []

      # Build some kind of message!
      timeNow = time.time()
      # Has it been more than 0.1 seconds since the last LED message?
      if (timeNow > self.lastLEDMsgTime + 0.1):
        # Build a LED message! This gives us a LED update frequency of < 10 Hz
        command.append(LED_MSG)
        stateLock.acquire()
        (r, g, b) = ledColorChart[state]
        stateLock.release()
        command.append(r)
        command.append(g)
        command.append(b)
        self.lastLEDMsgTime = timeNow
      else:
        # Build a state message (default)
        stateLock.acquire()
        command.append(STATE_MSG)
        command.append(state)
        stateLock.release()
        self.lastStateMsgTime = timeNow

      try:
        self.sendMessage(bytes(command))
        self.receiveMessage()
      except serial.SerialException:
        self.connected = False
        self.establishConnection()
      i = i + 1
    if self.connected:
      self.sendMessage(bytes([HALT_MSG]))
      self.receiveMessage()
      self.ser.close()

class HTTPHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    global stateLock, state, stateProgressChart
    action = self.path[1:]
    stateLock.acquire()
    try:
      newState = stateProgressChart[state, action]
      if (newState == state):
        message = "NO CAN DO"
      else:
        message = "COPY THAT"
        state = newState
    except KeyError:
      message = "SAY AGAIN, HOUSTON"
    finally:
      stateLock.release()

    # Respond by describing the (new) state of the machine
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
    msgPerSecond = msgsRcvd / (secondsPassed + (microseconds / 1000000))
    print("")
    print("Session terminated")
    print("Received " + str(msgsRcvd) + " messages in " + str(secondsPassed) + "." + str(microseconds)[:2] + " seconds.")
    print("Avg. messages per second: " + str(math.ceil(msgPerSecond)))

main()
