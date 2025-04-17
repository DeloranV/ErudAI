import pyautogui
from io import BytesIO

class Snapshotter():

    def snapshot(self) -> BytesIO:
        """
        Method for taking a screenshot from the user screen and saving it into a BytesIO buffer

        Returns the buffer containing the screenshot
        """
        screenshot = pyautogui.screenshot()
        snapshot = BytesIO()
        screenshot.save(snapshot, format="PNG")
        return snapshot
