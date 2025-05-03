import os
from PySide6.QtWidgets import QApplication
from view import ChatDialog
from agent import ActionPerformer, Query
from rag import GraphRetriever

if __name__ == "__main__":

    stylesheet_path = os.path.join('view', 'static', 'style.qss')

    app = QApplication()

    n4j_auth_data = open("n4j_auth_data", "r").read().split("\n")
    hf_api_key = open("hf_api_key", "r").read()

    chat_dialog = ChatDialog(n4j_uri=n4j_auth_data[0],
                             n4j_auth=(n4j_auth_data[1], n4j_auth_data[2]),
                             n4j_db_name="neo4j",
                             endpoint_url="https://fn7lxcome3tixe20.us-east-1.aws.endpoints.huggingface.cloud/v1/",
                             endpoint_api_key=hf_api_key
                             )

    chat_dialog.show()

    with open(stylesheet_path, 'r') as stylesheet_file:
        _style = stylesheet_file.read()
        chat_dialog.setStyleSheet(_style)

    app.exec()