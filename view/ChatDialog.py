from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel
from util.ImageEncoder import ImageEncoder

class ChatDialog(QDialog):

    def __init__(self, parent=None):
        super(ChatDialog, self).__init__(parent)
        root_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()

        text1 = QLabel("zmienna1")

        top_layout.addWidget(text1)

        input1 = QLineEdit()
        sendButton = QPushButton(self)

        bottom_layout.addWidget(input1)

        bottom_layout.addWidget(sendButton)

        root_layout.addLayout(top_layout)
        root_layout.addSpacing(100)
        root_layout.addLayout(bottom_layout)

        print("test")