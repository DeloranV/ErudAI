import pyautogui
from io import BytesIO

class Snapshotter:
    @staticmethod
    def snapshot(logger = None) -> BytesIO:
        screenshot = pyautogui.screenshot()
        snapshot = BytesIO()
        screenshot.save(snapshot, format="PNG")

        if logger and logger.log_snapshot is True:
            logger.log_img_data(screenshot)

        return snapshot
