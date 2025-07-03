import pyautogui

class ActionPerformer:
    @staticmethod
    def perform_click(coordinates: list) -> None:
        """
        Performs a mouse-click at given coordinates

        :param coordinates: Coordinates of the click, given as a list of two ints x,y
        """
        pyautogui.moveTo(*coordinates, duration=0.25)
        pyautogui.click()

    @staticmethod
    def perform_input(content: str) -> None:
        """
        Performs input of specified text by emulating keyboard usage.

        :param content: Input text given in the form of a string
        """
        pyautogui.write(content)

    @staticmethod
    def perform_scroll(clicks, x, y):
        pyautogui.scroll(clicks, x, y)