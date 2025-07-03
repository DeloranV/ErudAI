from pathlib import Path
import time, datetime
import os
from PIL.Image import Image

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

        if not self.log_file.exists():
            open(self.log_file, 'x').close()

    def log_text_data(self, label: str, data: str) -> None:
        """
        Method responsible for logging textual data inside the log file in the format <label>:<data>

        :param label: Label which describes the type of logged data e.g. "message"
        :param data: Data which will be logged
        """
        with open(self.log_file, 'a', encoding='utf-16') as log_file:
            log_contents = f"""<{label}>:{data}\n"""
            log_file.write(log_contents)

    def log_img_data(self, img: Image) -> None:
        """
        Method responsible for logging an image in a .png file named with the timestamp of logging

        :param img: An image to save of type PIL.Image
        """
        img.save(self.log_directory.joinpath("IMG_" + str(time.time()) + ".png"), format="PNG")

    def log_encoded_img_data(self, data: str) -> None:
        """
        Method responsible for logging base64 encoded image data inside of a .txt file named with the timestamp of logging

        :param data: Image data encoded in a base64 string
        """
        filename = "LOG_ENCODED_IMG_" + str(time.time())
        with open(self.log_directory.joinpath(filename), 'w') as encoded_img_log:
            encoded_img_log.write(data)