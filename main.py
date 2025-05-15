import os
from PySide6.QtWidgets import QApplication
from view import ChatDialog

if __name__ == "__main__":

    stylesheet_path = os.path.join('view', 'static', 'style.qss')

    app = QApplication()

    n4j_auth_data = open("api_keys/n4j_auth_data", "r").read().split("\n")
    hf_auth_data = open("api_keys/hf_auth_data", "r").read().split("\n")
    hf_aws_endpoint = hf_auth_data[0]
    hf_api_key = hf_auth_data[1]
    openai_api_key = open("api_keys/openai_api_key", "r").read()

    chat_dialog = ChatDialog(n4j_uri=n4j_auth_data[0],
                             n4j_auth=(n4j_auth_data[1], n4j_auth_data[2]),
                             n4j_db_name="neo4j",
                             endpoint_url=hf_aws_endpoint,
                             endpoint_api_key=hf_api_key,
                             openai_api_key=openai_api_key
                             )

    chat_dialog.show()

    with open(stylesheet_path, 'r') as stylesheet_file:
        _style = stylesheet_file.read()
        chat_dialog.setStyleSheet(_style)

    app.exec()