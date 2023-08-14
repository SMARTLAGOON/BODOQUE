import os
import subprocess
import time
import gzip
import json
import binascii
import shutil
from configparser import ConfigParser
from utils.utils import logger_info, logger_error
import serial
import threading

class VideoProcessor:
    def __init__(self):
        self.config = ConfigParser()
        self.config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

        self.downloaded_videos_dir = self.config.get('general', 'DOWNLOAD_VIDEOS_DIR')
        self.processing_videos_dir = self.config.get('general', 'PROCESSING_VIDEOS_DIR')
        self.processed_videos_dir = self.config.get('general', 'PROCESSED_VIDEOS_DIR')
        self.results_dir = self.config.get('general', 'RESULTS_DIR')
        self.sent_results_dir = self.config.get('general', 'SENT_RESULTS_DIR')
        
        self.process_interval_minutes = self.config.getint('general', 'PROCESS_INTERVAL_MINUTES')
        self.download_interval_minutes = self.config.getint('general', 'DOWNLOAD_INTERVAL_MINUTES')
        self.send_results_interval_minutes = self.config.getint('general', 'SEND_INTERVAL_MINUTES')

        self.ptk_openchannel_run_path = self.config.get('general', 'PTK_OPENCHANNEL_RUN_PATH')
        self.pathsfile_path = self.config.get('general', 'PATHSFILE_PATH')
        self.site_config_path = self.config.get('general', 'SITE_CONFIG_PATH')
        self.tmp_dir_path = self.config.get('general', 'TMP_DIR_PATH')

        self.discharge_values_to_consider = self.config.getint('general', 'DISCHARGE_VALUES_TO_CONSIDER')
        self.discharge_threshold = self.config.getfloat('general', 'DISCHARGE_THRESHOLD')
        self.last_discharge_values = []

        self.camera_ftp_host = self.config.get('camera_ftp', 'HOST')
        self.camera_ftp_user = self.config.get('camera_ftp', 'USER')
        self.camera_ftp_passwd = self.config.get('camera_ftp', 'PASSWD')
        self.camera_ftp_source_dir = self.config.get('camera_ftp', 'SOURCE_DIR')

        self.serial_port = self.config.get('serial', 'PORT')
        self.serial_baud_rate = self.config.getint('serial', 'BAUD_RATE')

        self.ser = None

    def run(self):
        threading.Thread(target=self.download_videos).start()
        threading.Thread(target=self.process_videos).start()
        threading.Thread(target=self.send_results).start()


    def open_serial_port(self):
        try:
            self.ser = serial.Serial(self.serial_port, self.serial_baud_rate)
        except serial.SerialException as e:
            logger_error.error(f"Could not open serial port {self.serial_port}: {e}")

    def download_videos(self):
        while True:
            # Create directories if they don't exist
            for directory in [self.downloaded_videos_dir, self.processing_videos_dir, self.processed_videos_dir, self.results_dir]:
                os.makedirs(directory, exist_ok=True)

            # Download videos from the camera
            command0 = "lftp -e 'mirror --verbose --file {} --target-directory {}' ftp://{}:{}@{} <<EOF".format(self.camera_ftp_source_dir,
                                                                                                                self.downloaded_videos_dir,
                                                                                                                self.camera_ftp_user,
                                                                                                                self.camera_ftp_passwd,
                                                                                                                self.camera_ftp_host)
            try:
                res0 = subprocess.check_output(command0, shell=True, universal_newlines=True)
                logger_info.info(res0)
            except Exception as e:
                logger_error.error(e)

    def process_videos(self):
        while True:
            # Get the list of downloaded videos
            downloaded_videos = os.listdir(self.downloaded_videos_dir)

            for filename in downloaded_videos:
                # Move the video to the processing directory
                video_path = os.path.join(self.downloaded_videos_dir, filename)
                processing_video_path = shutil.move(video_path, self.processing_videos_dir)

                # Process the video
                pathsfile_content = "{}\n{}\n".format(self.site_config_path, self.tmp_dir_path) + processing_video_path
                with open(self.pathsfile_path, "w") as pathsfile:
                    pathsfile.write(pathsfile_content)
                command2 = '{} {}'.format(self.ptk_openchannel_run_path, self.pathsfile_path)
                try:
                    res2 = subprocess.check_output(command2, shell=True, universal_newlines=True)
                    logger_info.info(res2)
                except Exception as e:
                    logger_error.error(e)
                    continue

                # Parse results
                result_path = os.path.join(self.tmp_dir_path, os.path.basename(processing_video_path).replace('.mp4', '_run.json'))
                with open(result_path, 'r') as f:
                    results = json.load(f)

                # Add the new discharge value to the list of last N discharge values
                self.last_discharge_values.append(results['openchannelFlow']['total']['discharge']['value'])
                if len(self.last_discharge_values) > self.discharge_values_to_consider:
                    self.last_discharge_values.pop(0)

                # Check if the average of the last N discharge values is below the threshold
                if sum(self.last_discharge_values) / len(self.last_discharge_values) < self.discharge_threshold:
                    # Send shutdown signal to ESP32 and shut down the Raspberry Pi
                    self.ser.write(b'SHUTDOWN\n')
                    os.system('sudo shutdown -h now')

                # Check if there's still water flow
                if results['openchannelFlow']['total']['discharge']['value'] <= 0:
                    return False

                # Move processed video to the processed videos directory
                shutil.move(processing_video_path, os.path.join(self.processed_videos_dir, filename))

    
    def send_results(self):
        while True:
            # Open serial port
            self.open_serial_port()

            # Get the list of results
            results_files = os.listdir(self.results_dir)

            for filename in results_files:
                # Read results
                with open(os.path.join(self.results_dir, filename), 'r') as f:
                    results = json.load(f)

                # Compress results
                compressed_results = gzip.compress(json.dumps(results).encode())

                # Convert compressed results to hexadecimal
                hex_compressed_results = binascii.hexlify(compressed_results)

                # Send hexadecimal compressed results to ESP32
                if self.ser is not None:
                    self.ser.write(hex_compressed_results)
                else:
                    print("Serial port not initialized.")

                # Move results to the sent results directory
                shutil.move(os.path.join(self.results_dir, filename), os.path.join(self.sent_results_dir, filename))

            # Sleep for the configured interval
            time.sleep(self.send_results_interval_minutes * 60)

