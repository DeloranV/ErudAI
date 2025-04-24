from agent import Query
from rag import GraphRetriever

from PySide6.QtWidgets import QDialog, QComboBox, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QTableWidget, QListWidget, QPushButton, QHBoxLayout, QRadioButton, QButtonGroup
from PySide6.QtCore import Qt

class ChatDialog(QDialog):

    def __init__(self, n4j_uri: str, n4j_auth: tuple[str, str], n4j_db_name: str, endpoint_url: str, endpoint_api_key: str, parent=None):
        super(ChatDialog, self).__init__(parent)

        self.program_option_mode = None

        self.graph = GraphRetriever(n4j_uri, n4j_auth, n4j_db_name)
        self.graph.test_connectivity()

        self.endpoint_url = endpoint_url
        self.endpoint_api_key = endpoint_api_key

        #LAYOUT DECLARATION
        root_layout = QVBoxLayout(self)
        program_name_layout = QHBoxLayout()
        chat_box_layout = QHBoxLayout()
        bottom_layout = QVBoxLayout()
        bottom_upper_layout = QHBoxLayout()
        bottom_lower_layout = QHBoxLayout()


        # PROGRAM NAME LABEL
        program_name = QLabel("ErudAI")
        program_name.setAlignment(Qt.AlignCenter)
        program_name_layout.addWidget(program_name, alignment=Qt.AlignCenter)


        # CHAT BOX
        chat_box = QListWidget()
        chat_box_layout.addWidget(chat_box)


        # USER INPUT
        user_input_widget = QLineEdit()


        # LIST
        program_option_list = QComboBox()
        program_option_list.addItems(["Message", "Action"])



        #RADIO BUTTONS
        program_option_layout = QHBoxLayout()
        program_option_button_message = QRadioButton("Message")
        program_option_button_action = QRadioButton("Action")
        program_option_layout.addWidget(program_option_button_message)
        program_option_layout.addWidget(program_option_button_action)


        #USER INPUT ADD
        bottom_upper_layout.addWidget(user_input_widget)
        bottom_upper_layout.addSpacing(10)

        """
        # LIST ADD
        bottom_upper_layout.addWidget(program_option_list)
        """

        # RADIO BUTTONS ADD
        bottom_upper_layout.addLayout(program_option_layout)



        #SEND BUTTON
        send_button = QPushButton("Send")
        bottom_lower_layout.addWidget(send_button)

        #BOTTOM LAYOUT MERGE
        bottom_layout.addLayout(bottom_upper_layout)
        bottom_layout.addLayout(bottom_lower_layout)


        #ROOT LAYOUT
        root_layout.addLayout(program_name_layout)
        root_layout.addLayout(chat_box_layout)
        root_layout.addSpacing(10)
        root_layout.addLayout(bottom_layout)

        def on_submit():
            if self.program_option_mode == "Action":
                user_input = user_input_widget.text()
                context_var = self.graph.get_ui_context()

                query = Query(api_key=self.endpoint_api_key,
                              base_url=self.endpoint_url,
                              debug=True)

                query.execute(
                    prompt=f"{user_input}. This map of UI elements specifies what view has what button and what the buttons are leading to: [{context_var}]")

        send_button.clicked.connect(on_submit)

        """
        #RETURN LIST OPTION
        def update_selection_list(index):
            global program_option_mode
            selected_option = program_option_list.currentText()
            print(selected_option)
        program_option_list.currentIndexChanged.connect(update_selection_list)
        """

        #RETURN CHECKED RADIO BUTTON OPTION
        def update_selection_buttons():
            if program_option_button_message.isChecked():
                self.program_option_mode = "Message"

            elif program_option_button_action.isChecked():
                self.program_option_mode = "Action"

        program_option_button_message.toggled.connect(update_selection_buttons)
        program_option_button_action.toggled.connect(update_selection_buttons)