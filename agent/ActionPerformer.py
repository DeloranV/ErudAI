import pyautogui

class ActionPerformer:
    @staticmethod
    def perform_click(coordinates: list) -> None:
        pyautogui.moveTo(*coordinates, duration=0.25)
        pyautogui.click()

    @staticmethod
    def perform_input(content: str) -> None:
        pyautogui.write(content)

    @staticmethod
    def perform_scroll(clicks, x, y):
        pyautogui.scroll(clicks, x, y)