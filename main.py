import os
from PySide6.QtWidgets import QApplication
from view import ChatDialog

if __name__ == "__main__":

    stylesheet_path = os.path.join('view', 'static', 'style.qss')

    app = QApplication()
    openai_api_key = open("api_keys/openai_api_key", "r").read()
    localhost = True

    n4j_auth_data = open("api_keys/n4j_auth_data", "r").read().split("\n")
    hf_auth_data = open("api_keys/hf_auth_data", "r").read().split("\n")
    hf_aws_endpoint = hf_auth_data[0]
    hf_api_key = hf_auth_data[1]

    chat_dialog = ChatDialog()

    chat_dialog.show()

    with open(stylesheet_path, 'r') as stylesheet_file:
        _style = stylesheet_file.read()
        chat_dialog.setStyleSheet(_style)

    app.exec()