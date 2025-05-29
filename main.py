import os
from PySide6.QtWidgets import QApplication
from view import ChatDialog

if __name__ == "__main__":
    directory = "logs"

    os.makedirs(directory, exist_ok=True)

    stylesheet_path = os.path.join('view', 'static', 'style.qss')

    app = QApplication()

    chat_dialog = ChatDialog()

    chat_dialog.show()

    with open(stylesheet_path, 'r') as stylesheet_file:
        _style = stylesheet_file.read()
        chat_dialog.setStyleSheet(_style)

    app.exec()