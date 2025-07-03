import pyautogui
from io import BytesIO

class Snapshotter:
    @staticmethod
    def snapshot(logger = None) -> BytesIO:
        """
        Takes a screenshot in .png format and saves it as a BytesIO object

        :param logger: Optional logger object to pass
        :return: BytesIO object containing the taken screenshot in a .png format
        """
        screenshot = pyautogui.screenshot()
        snapshot = BytesIO()
        screenshot.save(snapshot, format="PNG")

        if logger and logger.log_snapshot is True:
            logger.log_img_data(screenshot)

        return snapshot
