import os
import time
import gzip
import json
import binascii
import shutil
from utils.utils import logger_info, logger_error
import serial


class ResultsSender:
    def __init__(self, config):
        self.config = config
        self.ser = None

    def open_serial_port(self):
        try:
            self.ser = serial.Serial(self.config.get('serial', 'PORT'), self.config.getint('serial', 'BAUD_RATE'))
        except serial.SerialException as e:
            logger_error.error(f"Could not open serial port {self.config.get('serial', 'PORT')}: {e}")

    def send_results(self):
        while True:
            # Open serial port
            self.open_serial_port()

            # Get the list of results
            results_files = os.listdir(self.config.get('general', 'RESULTS_DIR'))

            for filename in results_files:
                # Read results
                with open(os.path.join(self.config.get('general', 'RESULTS_DIR'), filename), 'r') as f:
                    results = json.load(f)

                # Compress results
                compressed_results = gzip.compress(json.dumps(results).encode())

                # Convert compressed results to hexadecimal
                hex_compressed_results = binascii.hexlify(compressed_results)

                # Send hexadecimal compressed results to ESP32
                if self.ser is not None:
                    self.ser.write(hex_compressed_results)
                else:
                    logger_error.error("Could not open serial port.")

                # Move results to the sent results directory
                shutil.move(os.path.join(self.config.get('general', 'RESULTS_DIR'), filename), 
                            os.path.join(self.config.get('general', 'SENT_RESULTS_DIR'), filename))

            # Sleep for the configured interval
            time.sleep(self.config.getint('general', 'SEND_INTERVAL_MINUTES') * 60)

    def wait_for_shutdown_ack(self):
        while True:
            line = self.ser.readline()
            if line == b'SHUTDOWN_ACK\n':
                return
