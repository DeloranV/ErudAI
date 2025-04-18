from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel
from util.ImageEncoder import ImageEncoder

class ChatDialog(QDialog):

    def __init__(self, parent=None):
        super(ChatDialog, self).__init__(parent)
        root_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        text1 = QLabel("zmienna1")
        text2 = QLabel("zmienna2")

        left_layout.addWidget(text1)

        left_layout.addWidget(text2)

        input1 = QLineEdit()
        input2 = QLineEdit()

        right_layout.addWidget(input1)

        right_layout.addWidget(input2)

        root_layout.addLayout(left_layout)
        root_layout.addSpacing(100)
        root_layout.addLayout(right_layout)
