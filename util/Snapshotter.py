import pyautogui
from io import BytesIO

class Snapshotter():
# NO STATE - STATIC METHOD
    def snapshot(self, logger = None) -> BytesIO:
        """
        Method for taking a screenshot from the user screen and saving it into a BytesIO buffer

        Returns the buffer containing the screenshot
        """
        screenshot = pyautogui.screenshot()
        snapshot = BytesIO()
        screenshot.save(snapshot, format="PNG")

        if logger and logger.log_snapshot is True:
            logger.log_img_data(screenshot)

        return snapshot
