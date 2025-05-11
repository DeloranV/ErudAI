import pyautogui

class ActionPerformer:
    @staticmethod
    def perform_click(coordinates: list) -> None:
        pyautogui.moveTo(*coordinates, duration=0.25)
        pyautogui.click()

    @staticmethod
    def perform_input(content: str):
        pyautogui.write(content)