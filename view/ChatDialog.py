from urllib.response import addbase

from PySide6.QtWidgets import QDialog, QComboBox, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QTableWidget, QListWidget, QPushButton, QHBoxLayout, QRadioButton, QButtonGroup
from util.ImageEncoder import ImageEncoder
from PySide6.QtCore import Qt

class ChatDialog(QDialog):

    def __init__(self, parent=None):
        super(ChatDialog, self).__init__(parent)

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



        #PROGRAM MODE AND USER INPUT VARIABLES
        program_option_mode = None
        user_input = None

        # RETURN USER INPUT
        def on_submit():
            user_input = user_input_widget.text()
            print(user_input)

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
            global program_option_mode
            if program_option_button_message.isChecked():
                program_option_mode = "Message"
                print(program_option_mode)
            elif program_option_button_action.isChecked():
                program_option_mode = "Action"
                print(program_option_mode)
        program_option_button_message.toggled.connect(update_selection_buttons)
        program_option_button_action.toggled.connect(update_selection_buttons)