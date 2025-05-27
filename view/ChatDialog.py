from pynput import mouse
from agent import Query
from graph import Pathfinder
from pyautogui import size
from PySide6.QtWidgets import QDialog, QComboBox, QVBoxLayout, QLineEdit, QLabel, QListWidget, QPushButton, QHBoxLayout, \
    QRadioButton, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QThread, QPropertyAnimation, QEasingCurve
from util import Logger
from .SettingsDialog import SettingsDialog
from kg.KnowledgeBuilder import kg_extractor
from util import Snapshotter, ImageEncoder

class KGInitThread(QThread):
    def __init__(self, kg_builder, image):
        super().__init__()
        self.kg_builder = kg_builder
        self.image = image

    def run(self):
        self.kg_builder.initialize_cache(self.image)

class ScanThread(QThread):
    def __init__(self, kg_builder, clicked_button, encoded_image):
        super().__init__()
        self.kg_builder = kg_builder
        self.clicked_button = clicked_button
        self.encoded_image = encoded_image

    def run(self):
        self.kg_builder.extract_GUI_schema(self.clicked_button, self.encoded_image)

class QueryThread(QThread):
    def __init__(self,
                 endpoint_api_key,
                 endpoint_url,
                 user_input,
                 pathfinder,
                 logger = None):
        super().__init__()
        self.endpoint_api_key = endpoint_api_key
        self.endpoint_url = endpoint_url
        self.user_input = user_input
        self.logger = logger
        self.pathfinder = pathfinder

    def run(self):
        self.context_var = self.pathfinder.get_ui_path(self.user_input)
        query = Query(api_key=self.endpoint_api_key,
                      base_url=self.endpoint_url,
                      logger=self.logger)
        # if self.scan:
        #     prompt = f"""
        #     Navigate through the entire website starting from the homepage. Explore all accessible pages by following the available links and clicking on buttons with icons.
        #     If you get lost or stuck, click the 'Comarch BSS' button in the top left corner to return to the homepage. Do not click the links which you've already explored
        #     """
        # else:
        prompt = f"{self.user_input}. This map of UI elements specifies what view has what button and what the buttons are leading to: [{self.context_var}]"

        query.execute(
            prompt=prompt)

class ChatDialog(QDialog):

    def __init__(self, parent=None):
        super(ChatDialog, self).__init__(parent)
        self.setWindowTitle("ErudAI")
        self.setObjectName("ChatDialog")
        self.setMinimumSize(500, 600)
        self.program_option_mode = None

        self.settings_dialog = SettingsDialog(self)
        self.endpoint_url = self.settings_dialog.gui_model_endpoint.text()
        self.endpoint_api_key = self.settings_dialog.gui_api_key.text()
        if self.endpoint_api_key == "": self.endpoint_api_key = None
        self.n4j_uri = self.settings_dialog.neo4j_endpoint.text()
        self.n4j_db_name = self.settings_dialog.neo4j_db.text()
        self.n4j_auth = (self.settings_dialog.aura_username.text(),
                    self.settings_dialog.aura_api_key.text())

        self.openai_api_key = self.settings_dialog.openai_api_key.text()

        self.logger = Logger(log_snapshot=True, log_encoded_image=True)

        # THREAD NEEDS TO BE IN A CONTAINER OR AS A CLASS MEMBER TO NOT GO OUT OF SCOPE
        self.temp_thread_container = [] # TODO
        self.kg_builder = kg_extractor()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(15)

        # Chat History
        self.chat_box = QListWidget()
        self.chat_box.setObjectName("ChatBox")
        root_layout.addWidget(self.chat_box)

        # Input Row
        input_layout = QHBoxLayout()
        self.user_input_widget = QLineEdit()
        self.user_input_widget.setPlaceholderText("Type your message...")
        self.user_input_widget.setObjectName("UserInput")
        input_layout.addWidget(self.user_input_widget)

        # Radio Buttons
        radio_layout = QVBoxLayout()
        self.radio_message = QRadioButton("Message")
        self.radio_action = QRadioButton("Action")
        self.radio_message.setChecked(True)
        self.program_option_mode = "Message"
        self.radio_message.toggled.connect(self.update_selection_buttons)
        self.radio_action.toggled.connect(self.update_selection_buttons)
        radio_layout.addWidget(self.radio_message)
        radio_layout.addWidget(self.radio_action)
        input_layout.addLayout(radio_layout)

        root_layout.addLayout(input_layout)

        # Buttons Row directly under input field (centered)
        buttons_layout = QHBoxLayout()

        # Add stretch on both sides to center the buttons
        buttons_layout.addStretch()

        button_group = QHBoxLayout()  # Nested layout to keep buttons together

        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("SettingsButton")
        self.settings_button.clicked.connect(self.open_settings)
        button_group.addWidget(self.settings_button)

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("SendButton")
        self.send_button.clicked.connect(self.on_submit)
        button_group.addWidget(self.send_button)

        self.scan_button = QPushButton("Begin Scan")
        self.scan_button.setObjectName("ScanButton")
        self.scan_button.clicked.connect(self.on_scan_toggle)
        button_group.addWidget(self.scan_button)

        buttons_layout.addLayout(button_group)
        buttons_layout.addStretch()

        root_layout.addLayout(buttons_layout)

    def open_settings(self):
        self.settings_dialog.exec()

    def update_selection_buttons(self):
        if self.radio_message.isChecked():
            self.program_option_mode = "Message"
        elif self.radio_action.isChecked():
            self.program_option_mode = "Action"

    def add_chat_message(self, sender, message):
        item_text = f"{sender}: {message}"
        self.chat_box.addItem(item_text)
        self.chat_box.scrollToBottom()

        # Animation effect
        item = self.chat_box.item(self.chat_box.count() - 1)
        item_widget = self.chat_box.itemWidget(item)
        if item_widget:
            opacity_effect = QGraphicsOpacityEffect()
            item_widget.setGraphicsEffect(opacity_effect)
            fade = QPropertyAnimation(opacity_effect, b"opacity")
            fade.setDuration(400)
            fade.setStartValue(0)
            fade.setEndValue(1)
            fade.setEasingCurve(QEasingCurve.OutQuad)
            fade.start()

    def extract_view(self):
        try:
            clicked_button = self.user_input_widget.text()
            self.showMinimized()
            encoded_img = ImageEncoder.encode(Snapshotter.snapshot())
            scan_thread = ScanThread(self.kg_builder ,clicked_button, encoded_img)
            self.temp_thread_container.append(scan_thread)
            scan_thread.start()
            scan_thread.finished.connect(self.scan_callback)
        except Exception as e:
            self.add_chat_message("SYSTEM", f"There was an error during view extraction: {str(e)}")

    def on_scan_toggle(self):
        try:
            self.showMinimized()
            encoded_image = ImageEncoder.encode(Snapshotter.snapshot())
            self.kg_init_thread = KGInitThread(self.kg_builder, encoded_image)
            self.kg_init_thread.start()
            self.kg_init_thread.finished.connect(self.cache_callback)
        except Exception as e:
            self.add_chat_message("SYSTEM", f"There was an error during view caching: {str(e)}")

    def on_submit(self):
        try:
            user_input = self.user_input_widget.text()
            self.add_chat_message("You", user_input)
            self.pathfinder = Pathfinder(self.n4j_uri, self.n4j_auth, self.n4j_db_name, self.openai_api_key)
            if self.program_option_mode == "Action":
                query_thread = QueryThread(endpoint_api_key=self.endpoint_api_key,
                                           endpoint_url=self.endpoint_url,
                                           user_input=user_input,
                                           logger=self.logger,
                                           pathfinder=self.pathfinder
                                           )

                query_thread.finished.connect(self.thread_callback)
                query_thread.start()
                self.temp_thread_container.append(query_thread)
                self.showMinimized()

        except Exception as e:
            self.add_chat_message("SYSTEM", str(e))

    def maximize_callback(self):
        self.showMaximized()
        center_x = size()[0] / 5
        center_y = size()[1] / 8
        self.move(center_x, center_y)

    def cache_callback(self):
        self.add_chat_message("SYSTEM",
                              "Click a button leading to the next view, then input its label and press 'Extract view'")
        self.user_input_widget.setPlaceholderText("Type the label of the clicked button")
        self.scan_button.setText("Extract view")
        self.maximize_callback()
        self.scan_button.clicked.disconnect()
        self.scan_button.clicked.connect(self.extract_view)

    def scan_callback(self):
        self.scan_button.clicked.disconnect()
        self.scan_button.clicked.connect(self.on_scan_toggle)
        self.maximize_callback()
        self.user_input_widget.setPlaceholderText("Type your message...")
        self.user_input_widget.setText("")
        self.scan_button.setText("Begin Scan")
        self.add_chat_message("SYSTEM", "View extraction complete")

    def thread_callback(self):
        self.maximize_callback()
        self.add_chat_message("SYSTEM", "Action complete")