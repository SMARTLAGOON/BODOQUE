import os
import subprocess
import time
import shutil
from utils.utils import logger_info, logger_error
import json
import threading

class VideoProcessor:
    def __init__(self, config, condition):
        self.config = config
        self.condition = condition
        self.last_discharge_values = []
        self.shutdown_event = threading.Event()

    def process_videos(self):
        while True:
            # Check if there is a video in the processing directory
            processing_videos = os.listdir(self.config.get('general', 'PROCESSING_VIDEOS_DIR'))

            # If no video is currently being processed, check the downloaded videos directory
            if not processing_videos:
                downloaded_videos = os.listdir(self.config.get('general', 'DOWNLOAD_VIDEOS_DIR'))
                if downloaded_videos:
                    for filename in downloaded_videos:
                        video_path = os.path.join(self.config.get('general', 'DOWNLOAD_VIDEOS_DIR'), filename)
                        processing_video_path = shutil.move(video_path, self.config.get('general', 'PROCESSING_VIDEOS_DIR'))
                else:
                    with self.condition:
                        self.condition.wait()  # wait for a video to be downloaded
                    continue  # start from the beginning of the loop after a video has been downloaded
            else:
                filename = processing_videos[0]
                processing_video_path = os.path.join(self.config.get('general', 'PROCESSING_VIDEOS_DIR'), filename)

            # Process the video
            pathsfile_content = "{}\n{}\n".format(self.config.get('general', 'SITE_CONFIG_PATH'), 
                                                  self.config.get('general', 'TMP_DIR_PATH')) + processing_video_path
            with open(self.config.get('general', 'PATHSFILE_PATH'), "w") as pathsfile:
                pathsfile.write(pathsfile_content)
            command2 = '{} {}'.format(self.config.get('general', 'PTK_OPENCHANNEL_RUN_PATH'), 
                                      self.config.get('general', 'PATHSFILE_PATH'))
            try:
                res2 = subprocess.check_output(command2, shell=True, universal_newlines=True)
                logger_info.info(res2)
            except Exception as e:
                logger_error.error(e)
                continue

            # Parse results
            result_path = os.path.join(self.config.get('general', 'TMP_DIR_PATH'), 
                                       os.path.basename(processing_video_path).replace('.mp4', '_run.json'))
            with open(result_path, 'r') as f:
                results = json.load(f)

            # Add the new discharge value to the list of last N discharge values
            self.last_discharge_values.append(results['openchannelFlow']['total']['discharge']['value'])
            if len(self.last_discharge_values) > self.config.getint('general', 'DISCHARGE_VALUES_TO_CONSIDER'):
                self.last_discharge_values.pop(0)

            # Check if the average of the last N discharge values is below the threshold
            if sum(self.last_discharge_values) / len(self.last_discharge_values) < self.config.getfloat('general', 'DISCHARGE_THRESHOLD'):
                self.shutdown_event.set()  # Set the event to signal shutdown
                return  # Exit the method

            # Check if there's still water flow
            if results['openchannelFlow']['total']['discharge']['value'] <= 0:
                return False

            # Move processed video to the processed videos directory
            shutil.move(processing_video_path, os.path.join(self.config.get('general', 'PROCESSED_VIDEOS_DIR'), filename))

            time.sleep(self.config.getint('general', 'PROCESS_INTERVAL_MINUTES') * 60)
