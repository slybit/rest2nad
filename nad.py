import yaml
import logging
import sys
import serial
from flask import Flask, request

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
        nad_serial.write('\n' + command + '\n')
        res = nad_serial.read_until()
        return res
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
        nad_serial.write('\n' + command + '\n')
        res = nad_serial.read_until()
        return res
    except serial.SerialTimeoutException:
        return "RS232 Time out"
    except:
        return "RS232 Unknown error"

# ----------------------------------------------------------------------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host=config['rest']['bindIP'], port=config['rest']['port'])