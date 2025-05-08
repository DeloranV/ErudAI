import pyautogui

from agent import Query
from graph import Pathfinder

from pyautogui import size

from PySide6.QtWidgets import QDialog, QComboBox, QVBoxLayout, QLineEdit, QLabel, QListWidget, QPushButton, QHBoxLayout, QRadioButton
from PySide6.QtCore import Qt, QThread

class QueryThread(QThread):
    def __init__(self, endpoint_api_key, endpoint_url, user_input, context_var):
        super().__init__()
        self.endpoint_api_key = endpoint_api_key
        self.endpoint_url = endpoint_url
        self.user_input = user_input
        self.context_var = context_var

    def run(self):
        query = Query(api_key=self.endpoint_api_key,
                      base_url=self.endpoint_url,
                      debug=True)

        query.execute(
            prompt=f"{self.user_input}. This map of UI elements specifies what view has what button and what the buttons are leading to: [{self.context_var}]")

class ChatDialog(QDialog):

    def __init__(self, n4j_uri: str, n4j_auth: tuple[str, str], n4j_db_name: str, endpoint_url: str, endpoint_api_key: str, parent=None):
        super(ChatDialog, self).__init__(parent)

        self.program_option_mode = None

        self.pathfinder = Pathfinder(n4j_uri, n4j_auth, n4j_db_name, "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")
        self.pathfinder.test_connectivity()

        self.endpoint_url = endpoint_url
        self.endpoint_api_key = endpoint_api_key

        # THREAD NEEDS TO BE IN A CONTAINER OR AS A CLASS MEMBER TO NOT GO OUT OF SCOPE
        self.temp_thread_container = [] # TODO MAKE IT NICER - CLASS VARIABLE INSTEAD OF CONTAINER

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
                context_var = self.pathfinder.get_ui_path(user_input)
                query_thread = QueryThread(endpoint_api_key=self.endpoint_api_key,
                                           endpoint_url=self.endpoint_url,
                                           user_input=user_input,
                                           context_var=context_var)

                query_thread.start()
                self.temp_thread_container.append(query_thread)
                self.showMinimized()

                query_thread.finished.connect(self.thread_callback)

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

    def thread_callback(self):
        self.showMaximized()
        centerX = size()[0]/2.5
        centerY = size()[1]/3
        self.move(centerX, centerY)