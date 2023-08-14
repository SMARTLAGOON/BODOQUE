import os
import time
from configparser import ConfigParser
from utils.utils import logger_info, logger_error
import threading

from video_downloader import VideoDownloader
from video_processor import VideoProcessor
from results_sender import ResultsSender


class BodoqueSystem:
    def __init__(self):
        self.config = ConfigParser()
        self.config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

        # Create directories if they don't exist
        for directory in [self.config.get('general', 'DOWNLOAD_VIDEOS_DIR'), 
                            self.config.get('general', 'PROCESSING_VIDEOS_DIR'), 
                            self.config.get('general', 'PROCESSED_VIDEOS_DIR'), 
                            self.config.get('general', 'RESULTS_DIR')]:
            os.makedirs(directory, exist_ok=True)

        self.condition = threading.Condition()
        self.video_downloader = VideoDownloader(self.config, self.condition)
        self.video_processor = VideoProcessor(self.config, self.condition)
        self.results_sender = ResultsSender(self.config)

    def run(self):
        # Start threads for downloading and processing videos before trying to open the serial port
        threading.Thread(target=self.video_downloader.download_videos).start()
        threading.Thread(target=self.video_processor.process_videos).start()
        threading.Thread(target=self.results_sender.send_results).start()

        # Attempt to open the serial port
        self.results_sender.open_serial_port()
        if self.results_sender.ser is None:
            logger_error.error("Could not open serial port.")
        else:
            logger_info.info("Serial port opened successfully.")

        # Wait for the shutdown signal from the video processor
        self.video_processor.shutdown_event.wait()

        # Wait for all results to be sent
        while len(os.listdir(self.config.get('general', 'RESULTS_DIR'))) > 0:
            time.sleep(60)

        # Send shutdown signal to ESP32 if serial port is available
        if self.results_sender.ser is not None:
            self.results_sender.ser.write(b'SHUTDOWN\n')
            logger_info.info("Shutdown signal sent to ESP32.")

            # Wait for the ESP32 to acknowledge the shutdown signal
            self.results_sender.wait_for_shutdown_ack()
            logger_info.info("Shutdown signal acknowledged by ESP32.")

            # Shut down the Raspberry Pi
            os.system('sudo shutdown -h now')


if __name__ == "__main__":
    BodoqueSystem().run()
