import yaml
import logging
import sys
import serial
from flask import Flask, request
import serial.threaded
from queue import Queue

# PySerial protocol class tailored to the NAD serial protocol
class NADProtocol(serial.threaded.Protocol):
    def __init__(self):
        self.buffer = bytearray()
        self.TERMINATOR = b'\r'

    def __call__(self):
        return self

    def data_received(self, data):
        self.buffer.extend(data)
        while self.TERMINATOR in self.buffer:
            packet, self.buffer = self.buffer.split(self.TERMINATOR, 1)
            self.handle_packet(packet)

    def handle_packet(self, packet):
        text = packet.decode('utf-8', 'replace')
        sys.stdout.write('line received: {}\n'.format(text))
        # we use the queue for just one item, so clear it first
        empty_queue()
        QUEUE.put(text)



# INIT LOGGING
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# SHARED QUEUE
QUEUE = Queue()

def empty_queue():
    while not QUEUE.empty():
        try:
            QUEUE.get(False)
        except Empty:
            continue
        QUEUE.task_done()

# ----------------------------------------------------------------------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------------------------------------------------------------------

if len(sys.argv) < 2:
    logging.critical("No config file provided.")
    sys.exit(1)
    
config_file = sys.argv[1]

try:
    with open(config_file) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
except:
    logging.critical("[CONFIG] Could not open file config.yaml")
    sys.exit(1) 
  

# ----------------------------------------------------------------------------------------------------------------------------------------
# SERIAL
# ----------------------------------------------------------------------------------------------------------------------------------------

try:
    nad_serial = serial.Serial(port=config['serial']['port'], baudrate=115200, xonxoff=False, rtscts=False, dsrdtr=False, timeout=0.5)
    logging.info("[SERIAL] Connected to " +  config['serial']['port'])
    nad_protocol = NADProtocol()
    serial_worker = serial.threaded.ReaderThread(nad_serial, nad_protocol)
    serial_worker.start()
except:
    logging.critical( "[SERIAL] Could not open " + config['serial']['port'])
    sys.exit(1)


# ----------------------------------------------------------------------------------------------------------------------------------------
# REST API
# ----------------------------------------------------------------------------------------------------------------------------------------
app = Flask(__name__)

@app.route('/nad/<command>', methods=['GET', 'POST'])
def getCommand(command):
    if request.method == 'POST':
        arg = request.data
        command = command + arg
    else:
        command = command + '?'
    command = command.encode('utf-8','ignore')
    logging.info("[SERIAL] Sending command " + command)
    try:
        # empty the queue first (it will normally contain a single old item)
        empty_queue()
        nad_serial.write('\n' + command + '\n')
        # retrieve data (blocking)
        data = QUEUE.get()
        # indicate data has been consumed
        QUEUE.task_done()
        return data
    except serial.SerialTimeoutException:
        return "RS232 Time out"
    except:
        return "RS232 Unknown error"

@app.route('/nad/', methods=['POST'])
def postCommand():
    command = request.data
    command = command.encode('utf-8','ignore')
    logging.info("[SERIAL] Sending command " + command)
    try:
        # empty the queue first (it will normally contain a single old item)
        empty_queue()
        nad_serial.write('\n' + command + '\n')
        # retrieve data (blocking)
        data = QUEUE.get()
        # indicate data has been consumed
        QUEUE.task_done()
        return data
    except serial.SerialTimeoutException:
        return "RS232 Time out"
    except:
        return "RS232 Unknown error"

# ----------------------------------------------------------------------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host=config['rest']['bindIP'], port=config['rest']['port'])