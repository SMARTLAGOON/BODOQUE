import os
import subprocess
import time
from configparser import ConfigParser
from utils.utils import logger_info, logger_error
import logging

class VideoDownloader:
    def __init__(self, config, condition):
        self.config = config
        self.condition = condition
        self.downloaded_videos_file = 'downloaded_videos.txt'
        if not os.path.exists(self.downloaded_videos_file):
            with open(self.downloaded_videos_file, 'w'):
                pass

    def check_if_downloaded(self, file_name):
        with open(self.downloaded_videos_file, 'r') as f:
            downloaded_videos = f.read().splitlines()
        return file_name in downloaded_videos

    def mark_as_downloaded(self, file_name):
        with open(self.downloaded_videos_file, 'a') as f:
            f.write(file_name + '\n')

    def notify_video_downloaded(self):
        with self.condition:
                self.condition.notify_all()  # notify the processing thread that a video has been downloaded
            

    def download_videos(self):
        print("Downloading videos...")
        while True:
            try:
                # List all directories under SOURCE_DIR
                command_list_dir = f"lftp -u {self.config.get('camera_ftp', 'USER')},{self.config.get('camera_ftp', 'PASSWD')} {self.config.get('camera_ftp', 'HOST')} -e 'ls {self.config.get('camera_ftp', 'SOURCE_DIR')}; quit'"
                res_list_dir = subprocess.check_output(command_list_dir, shell=True, universal_newlines=True)
                # Extract directory names (dates)
                date_dirs = [l.split()[-1] for l in res_list_dir.split("\n") if l]

                for date_dir in date_dirs:
                    command_list_hour_dirs = f"lftp -u {self.config.get('camera_ftp', 'USER')},{self.config.get('camera_ftp', 'PASSWD')} {self.config.get('camera_ftp', 'HOST')} -e 'ls {self.config.get('camera_ftp', 'SOURCE_DIR')}/{date_dir}; quit'"
                    res_list_hour_dirs = subprocess.check_output(command_list_hour_dirs, shell=True, universal_newlines=True)
                    hour_dirs = [l.split()[-1] for l in res_list_hour_dirs.split("\n") if l]

                    for hour_dir in hour_dirs:
                        # List all files under each hour directory
                        command_list_files = f"lftp -u {self.config.get('camera_ftp', 'USER')},{self.config.get('camera_ftp', 'PASSWD')} {self.config.get('camera_ftp', 'HOST')} -e 'ls {self.config.get('camera_ftp', 'SOURCE_DIR')}/{date_dir}/{hour_dir}; quit'"
                        res_list_files = subprocess.check_output(command_list_files, shell=True, universal_newlines=True)

                        # Extract filenames (videos)
                        file_names = [l.split()[-1] for l in res_list_files.split("\n") if '.mp4' in l]

                        for file_name in file_names:
                            # Only download the file if it has not been downloaded before
                            if not self.check_if_downloaded(file_name):
                                print(f"Downloading {file_name}...")
                                source_file = f"{self.config.get('camera_ftp', 'SOURCE_DIR')}/{date_dir}/{hour_dir}/{file_name}"
                                target_directory = f"{self.config.get('general', 'DOWNLOAD_VIDEOS_DIR')}"
                                os.makedirs(target_directory, exist_ok=True)
                                command_download = f"lftp -u {self.config.get('camera_ftp', 'USER')},{self.config.get('camera_ftp', 'PASSWD')} {self.config.get('camera_ftp', 'HOST')} -e 'get {source_file} -o {target_directory}/{file_name}; quit'"
                                try:
                                    res_download = subprocess.check_output(command_download, shell=True, universal_newlines=True)
                                    if res_download:
                                        logger_info.info(res_download)
                                        self.mark_as_downloaded(file_name)  # Mark the file as downloaded
                                        self.notify_video_downloaded()  # Notify the processing thread that a video has been downloaded
                                    else:
                                        print(f"No new files downloaded from {source_file}")
                                except subprocess.CalledProcessError as e:
                                    print(f"Error in command: {command_download}")
                                    print(e.output)

                logging.info('Sleeping until next download interval...')
                time.sleep(self.config.getint('general', 'DOWNLOAD_INTERVAL_MINUTES') * 60)
                logging.info('Waking up to start next download...')

            except Exception as e:
                logger_error.error(e)
