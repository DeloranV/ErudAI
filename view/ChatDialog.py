from PySide6.QtWidgets import QDialog
from util.ImageEncoder import ImageEncoder

class ChatDialog(QDialog):

    def __init__(self, parent=None):
        super(ChatDialog, self).__init__(parent)
