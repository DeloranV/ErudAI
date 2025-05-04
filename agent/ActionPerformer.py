import pyautogui

class ActionPerformer:

    def perform_movement(self, coordinates: list) -> None:
        """
        Moves a user mouse to the specified coordinates

        Args:
            coordinates - List of coordinates in the form of [x: int, y: int]
        """
        pyautogui.moveTo(*coordinates)

    def perform_click(self, coordinates: list) -> None:
        pyautogui.click(*coordinates)

    def perform_input(self, content: str):
        pyautogui.write(content)