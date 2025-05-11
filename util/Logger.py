from pathlib import Path, PurePath
import time, datetime
import os
import pyautogui

class Logger:
    def __init__(self,
                 log_directory: Path = Path("logs", "LOG_" + str(datetime.date.today())),
                 log_filename: str = "LOG_" + str(time.time()) + ".txt",
                 log_snapshot: bool = False,
                 log_encoded_image: bool = False):
        self.log_directory = log_directory
        self.log_snapshot = log_snapshot
        self.log_encoded_image = log_encoded_image
        self.log_filename = log_filename
        self.log_file = self.log_directory.joinpath(self.log_filename)

        if not log_directory.exists():
            os.mkdir(log_directory)
            # log_directory.open('w').write(f"LOG FILE FROM {datetime.datetime.now().isoformat()}\n")

        if not self.log_file.exists():
            open(self.log_file, 'x').close()

    def log_text_data(self, label, data):
        with open(self.log_file, 'a', encoding='utf-16') as log_file:
            log_contents = f"""<{label}>:{data}\n"""
            log_file.write(log_contents)

    def log_img_data(self, img):
        img.save(self.log_directory.joinpath("IMG_" + str(time.time()) + ".png"), format="PNG")

    def log_encoded_img_data(self, data):
        filename = "LOG_ENCODED_IMG_" + str(time.time())
        with open(self.log_directory.joinpath(filename), 'w') as encoded_img_log:
            encoded_img_log.write(data)