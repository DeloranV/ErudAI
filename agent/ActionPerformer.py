import pyautogui

class ActionPerformer:

    def performMovement(self, coordinates: list) -> None:
        """
        Moves a user mouse to the specified coordinates

        Args:
            coordinates - List of coordinates in the form of [x: int, y: int]
        """
        pyautogui.moveTo(*coordinates)

    def performClick(self, coordinates: list) -> None:
        pyautogui.click(*coordinates)