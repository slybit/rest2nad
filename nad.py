import yaml
import logging
import sys
import serial
import serial.threaded
from flask import Flask, request
import paho.mqtt.client as mqtt
from Queue import Queue

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
        # publish on the MQTT
        try:
            command = text.split('=')[0]
            value = text.split('=')[1]
            client.publish("nad/status/" + str(command), str(value))
        except:
            logging.error("Could not publish MQTT message")



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
# MQTT
# ----------------------------------------------------------------------------------------------------------------------------------------

def mqtt_on_connect(client, userdata, flags, rc):
    logging.info("[MQTT] Connected to broker (result code " + str(rc) + ")")
    client.subscribe("nad/#")

def mqtt_on_message(client, userdata, msg):
    global nad_serial
    logging.debug("[MQTT] Message on '" + msg.topic + "': " + str(msg.payload))
    command = msg.topic.split('/')[len(msg.topic.split('/')) - 1]
    if msg.topic.startswith("nad/get") or msg.topic.startswith("nad/read"):
        command = command + '?'
    elif msg.topic.startswith("nad/set") or msg.topic.startswith("nad/write"):
        command = command + str(msg.payload)
    else:
        logging.debug("Not a valid nad command msg")
        return

    try:
        logging.debug("sending to serial: " + command)
        nad_serial.write(str(command) + '\r')
    except serial.SerialTimeoutException:
        return "RS232 Time out"
    except:
        return "RS232 Unknown error"
    

try:
    client = mqtt.Client()
    client.on_connect = mqtt_on_connect
    client.on_message = mqtt_on_message
    client.connect(config["mqtt"]["host"], config["mqtt"]["port"], 60)
    client.loop_start()
except:
    logging.critical("Could not setup mqtt session. Bye")
    sys.exit(1)



# ----------------------------------------------------------------------------------------------------------------------------------------
# SERIAL
# ----------------------------------------------------------------------------------------------------------------------------------------

try:
    nad_serial = serial.Serial(port=config['serial']['port'], baudrate=115200, xonxoff=False, rtscts=False, dsrdtr=False, timeout=0.5)
    #nad_serial = serial.serial_for_url('loop://', baudrate=115200, timeout=1)
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