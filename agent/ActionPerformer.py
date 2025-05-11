import pyautogui

class ActionPerformer:

    def perform_movement(self, coordinates: list, logger = None) -> None:
        """
        Moves a user mouse to the specified coordinates

        Args:
            coordinates - List of coordinates in the form of [x: int, y: int]
        """
        pyautogui.moveTo(*coordinates)

    def perform_click(self, coordinates: list) -> None:
        pyautogui.moveTo(*coordinates, duration=0.25)
        pyautogui.click()

    def perform_input(self, content: str):
        pyautogui.write(content)