from PySide6.QtWidgets import QApplication
from view import ChatDialog


if __name__ == "__main__":
    app = QApplication()
    chat_dialog = ChatDialog()
    chat_dialog.show()
    app.exec()