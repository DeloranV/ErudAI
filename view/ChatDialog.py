import threading
from agent import Query
from graph import Pathfinder
from pyautogui import size, sleep
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QPushButton, QHBoxLayout, \
QGraphicsOpacityEffect
from PySide6.QtCore import QThread, QPropertyAnimation, QEasingCurve, Signal
from util import Logger
from .SettingsDialog import SettingsDialog
from kg.KnowledgeBuilder import KgExtractor
from util import Snapshotter, ImageEncoder
from autonomous_scanner import AutonomyEmulator

class AutonomyEmulatorThread(QThread):
    def __init__(self,
                 autonomous_mode,
                 auth):
        super().__init__()
        self.emulator = AutonomyEmulator(autonomous_mode, auth)

    def run(self):
        self.emulator.execute()

class KGInitThread(QThread):
    error_occurred = Signal(str)

    def __init__(self, kg_builder, image):
        super().__init__()
        self.kg_builder = kg_builder
        self.image = image

    def run(self):
        try:
            self.kg_builder.initialize_cache(self.image)
        except Exception as e:
            self.error_occurred.emit(str(e))

class ScanThread(QThread):
    error_occurred = Signal(str)

    def __init__(self, kg_builder, clicked_button, encoded_image):
        super().__init__()
        self.kg_builder = kg_builder
        self.clicked_button = clicked_button
        self.encoded_image = encoded_image

    def run(self):
        try:
            self.kg_builder.extract_gui_schema(self.clicked_button, self.encoded_image)
        except Exception as e:
            self.error_occurred.emit(str(e))

class QueryThread(QThread):
    error_occurred = Signal(str)

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
        self.context_var = pathfinder.get_ui_path(self.user_input)

    def run(self):
        try:
            query = Query(api_key=self.endpoint_api_key,
                          base_url=self.endpoint_url,
                          logger=self.logger)

            prompt = f"{self.user_input}. This map of UI elements specifies what view has what button and what the buttons are leading to: [{self.context_var}]"

            query.execute(
                prompt=prompt)
        except Exception as e:
            self.error_occurred.emit(str(e))

class ChatDialog(QDialog):

    def __init__(self, parent=None):
        super(ChatDialog, self).__init__(parent)
        self.setWindowTitle("ErudAI")
        self.setObjectName("ChatDialog")
        self.setMinimumSize(500, 600)
        self.program_option_mode = None

        self.settings_dialog = SettingsDialog(self)

        self.autonomous_scanning_in_progress = False
        self.emulator_thread = None  # To store the running thread
        self.query_thread = None

        self.endpoint_url = self.settings_dialog.gui_model_endpoint.text().strip()
        self.endpoint_api_key = self.settings_dialog.gui_api_key.text().strip() or None

        self.gui_model_deployment = "cloud" if self.settings_dialog.gui_cloud.isChecked() else "local"

        self.n4j_uri = self.settings_dialog.neo4j_endpoint.text().strip()
        self.n4j_db_name = self.settings_dialog.neo4j_db.text().strip()
        self.n4j_auth = (
            self.settings_dialog.local_username.text().strip(),
            self.settings_dialog.local_password.text().strip()
        )

        self.aura_username = self.settings_dialog.aura_username.text().strip()
        self.aura_api_key = self.settings_dialog.aura_api_key.text().strip()

        self.openai_api_key = self.settings_dialog.openai_api_key.text().strip()

        if self.settings_dialog.autonomous_scanning_endpoint.isChecked():
            self.autonomous_mode = "endpoint"
            self.autonomous_endpoint_url = self.settings_dialog.endpoint_url_input.text().strip()
            self.autonomous_endpoint_api_key = self.settings_dialog.endpoint_api_key_input.text().strip()
            self.autonomous_model_name = self.settings_dialog.endpoint_model_name_input.text().strip()
        elif self.settings_dialog.autonomous_scanning_gpt.isChecked():
            self.autonomous_mode = "gpt"
            self.autonomous_gpt_api_key = self.settings_dialog.gpt_api_key_input.text().strip()
        else:
            self.autonomous_mode = "off"
            self.autonomous_endpoint_url = None
            self.autonomous_endpoint_api_key = None
            self.autonomous_model_name = None
            self.autonomous_gpt_api_key = None

        self.debug_mode = "on" if self.settings_dialog.debug_on.isChecked() else "off"
        self.log_snapshots = self.settings_dialog.log_snapshots.isChecked()
        self.log_encoded = self.settings_dialog.log_encoded.isChecked()

        self.logger = Logger(
            log_snapshot=self.log_snapshots,
            log_encoded_image=self.log_encoded
        )

        self.threads = [] # switch to concurrent.futures.ThreadPoolExecutor?
        self._lock = threading.Lock() # TODO - threads held in their respective instance variables

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(15)

        self.chat_box = QListWidget()
        self.chat_box.setObjectName("ChatBox")
        root_layout.addWidget(self.chat_box)

        input_layout = QHBoxLayout()
        self.user_input_widget = QLineEdit()
        self.user_input_widget.setPlaceholderText("Type your message...")
        self.user_input_widget.setObjectName("UserInput")
        input_layout.addWidget(self.user_input_widget)

        root_layout.addLayout(input_layout)

        buttons_layout = QHBoxLayout()

        buttons_layout.addStretch()

        button_group = QHBoxLayout()

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

    def load_settings(self) -> None:
        """
        Method responsible for loading configuration parameters into the program
        """
        self.endpoint_url = self.settings_dialog.gui_model_endpoint.text().strip()
        self.endpoint_api_key = self.settings_dialog.gui_api_key.text().strip() or None

        self.gui_model_deployment = "cloud" if self.settings_dialog.gui_cloud.isChecked() else "local"

        self.n4j_uri = self.settings_dialog.neo4j_endpoint.text().strip()
        self.n4j_db_name = self.settings_dialog.neo4j_db.text().strip()
        self.n4j_auth = (
            self.settings_dialog.local_username.text().strip(),
            self.settings_dialog.local_password.text().strip()
        )

        self.aura_username = self.settings_dialog.aura_username.text().strip()
        self.aura_api_key = self.settings_dialog.aura_api_key.text().strip()

        self.openai_api_key = self.settings_dialog.openai_api_key.text().strip()

        if self.settings_dialog.autonomous_scanning_endpoint.isChecked():
            self.autonomous_mode = "endpoint"
            self.autonomous_endpoint_url = self.settings_dialog.endpoint_url_input.text().strip()
            self.autonomous_endpoint_api_key = self.settings_dialog.endpoint_api_key_input.text().strip()
            self.autonomous_model_name = self.settings_dialog.endpoint_model_name_input.text().strip()
            self.autonomous_gpt_api_key = None
        elif self.settings_dialog.autonomous_scanning_gpt.isChecked():
            self.autonomous_mode = "gpt"
            self.autonomous_gpt_api_key = self.settings_dialog.gpt_api_key_input.text().strip()
            self.autonomous_endpoint_url = None
            self.autonomous_endpoint_api_key = None
            self.autonomous_model_name = None
        else:
            self.autonomous_mode = "off"
            self.autonomous_endpoint_url = None
            self.autonomous_endpoint_api_key = None
            self.autonomous_model_name = None
            self.autonomous_gpt_api_key = None

        self.debug_mode = "on" if self.settings_dialog.debug_on.isChecked() else "off"
        self.log_snapshots = self.settings_dialog.log_snapshots.isChecked()
        self.log_encoded = self.settings_dialog.log_encoded.isChecked()

        self.logger = Logger(
            log_snapshot=self.log_snapshots,
            log_encoded_image=self.log_encoded
        )

    def open_settings(self) -> None:
        self.settings_dialog.exec()

    def update_selection_buttons(self) -> None:
        if self.radio_message.isChecked():
            self.program_option_mode = "Message"
        elif self.radio_action.isChecked():
            self.program_option_mode = "Action"

    def add_chat_message(self, sender: str, message: str) -> None:
        item_text = f"{sender}: {message}"
        self.chat_box.addItem(item_text)
        self.chat_box.scrollToBottom()

        item = self.chat_box.item(self.chat_box.count() - 1)
        item_widget = self.chat_box.itemWidget(item)
        if item_widget:
            opacity_effect = QGraphicsOpacityEffect()
            item_widget.setGraphicsEffect(opacity_effect)
            fade = QPropertyAnimation(opacity_effect, b"opacity")
            fade.setDuration(400)
            fade.setStartValue(0)
            fade.setEndValue(1)
            fade.setEasingCurve(QEasingCurve.Type.OutQuad)
            fade.start()

    def extract_view(self) -> None:
        self.load_settings()
        try:
            clicked_button = self.user_input_widget.text().strip()
            self.showMinimized()
            sleep(2)
            encoded_img = ImageEncoder.encode(Snapshotter.snapshot())
            scan_thread = ScanThread(self.kg_builder ,clicked_button, encoded_img)
            self.threads.append(scan_thread)
            scan_thread.start()
            scan_thread.error_occurred.connect(lambda msg: self.add_chat_message("SYSTEM", f"Error during view extraction thread: {msg}"))
            scan_thread.finished.connect(self.scan_callback)
        except Exception as e:
            self.add_chat_message("SYSTEM", f"There was an error during view extraction: {str(e)}")

    def on_scan_toggle(self) -> None:
        try:
            self.load_settings()

            if self.autonomous_scanning_in_progress:
                if self.emulator_thread and self.emulator_thread.isRunning():
                    self.emulator_thread.terminate()
                    self.emulator_thread.wait()
                self.autonomous_scanning_in_progress = False
                self.scan_button.setText("Begin Scan")
                self.add_chat_message("SYSTEM", "Scan aborted")
                return

            if self.autonomous_mode in ['endpoint', 'gpt']:
                if self.autonomous_mode == 'endpoint':
                    auth = [self.autonomous_endpoint_url,
                            self.autonomous_endpoint_api_key,
                            self.autonomous_model_name]
                else:
                    auth = [self.autonomous_gpt_api_key]

                self.emulator_thread = AutonomyEmulatorThread(self.autonomous_mode, auth)
                self.showMinimized()
                self.threads.append(self.emulator_thread)
                self.emulator_thread.start()

                self.autonomous_scanning_in_progress = True
                self.scan_button.setText("Stop")
            else:
                self.kg_builder = KgExtractor(self.openai_api_key, self.n4j_uri, self.n4j_auth)
                self.showMinimized()
                sleep(2)
                encoded_image = ImageEncoder.encode(Snapshotter.snapshot())
                self.kg_init_thread = KGInitThread(self.kg_builder, encoded_image)
                self.kg_init_thread.start()
                self.kg_init_thread.error_occurred.connect(
                    lambda msg: self.add_chat_message("SYSTEM", f"Error during view caching thread: {msg}"))
                self.kg_init_thread.finished.connect(self.cache_callback)

        except Exception as e:
            self.add_chat_message("SYSTEM", f"There was an error during scanning: {str(e)}")

    def on_submit(self) -> None:
        try:
            self.load_settings()
            if self.query_thread is not None:
                if self.query_thread.isRunning():
                    self.query_thread.terminate()
                    self.query_thread.wait()
                    self.add_chat_message("SYSTEM", "Action stopped.")
                else:
                    self.add_chat_message("SYSTEM", "No action is currently running.")
                self.query_thread = None
                self.send_button.setText("Send")
                return

            user_input = self.user_input_widget.text().strip()
            self.add_chat_message("You", user_input)
            self.pathfinder = Pathfinder(self.n4j_uri, self.n4j_auth, self.n4j_db_name, self.openai_api_key)

            self.query_thread = QueryThread(
                endpoint_api_key=self.endpoint_api_key,
                endpoint_url=self.endpoint_url,
                user_input=user_input,
                logger=self.logger,
                pathfinder=self.pathfinder
            )

            self.query_thread.error_occurred.connect(
                lambda msg: self.add_chat_message("SYSTEM", f"Error during query thread: {msg}")
            )
            self.query_thread.finished.connect(self.thread_callback)
            self.query_thread.start()
            self.threads.append(self.query_thread)
            self.showMinimized()
            self.send_button.setText("Stop")

        except Exception as e:
            self.add_chat_message("SYSTEM", f"There was an error during action submit: {str(e)}")

    def maximize_callback(self) -> None:
        self.showMaximized()
        center_x = size()[0] / 5
        center_y = size()[1] / 8
        self.move(center_x, center_y)

    def cache_callback(self) -> None:
        self.add_chat_message("SYSTEM",
                              "Click a button leading to the next view, then input its label and press 'Extract view'")
        self.user_input_widget.setPlaceholderText("Type the label of the clicked button")
        self.scan_button.setText("Extract view")
        self.maximize_callback()
        self.scan_button.clicked.disconnect()
        self.scan_button.clicked.connect(self.extract_view)
        self.autonomous_scanning_in_progress = False

    def scan_callback(self) -> None:
        self.scan_button.clicked.disconnect()
        self.scan_button.clicked.connect(self.on_scan_toggle)
        self.maximize_callback()
        self.user_input_widget.setPlaceholderText("Type your message...")
        self.user_input_widget.setText("")
        self.scan_button.setText("Begin Scan")
        self.add_chat_message("SYSTEM", "View extraction complete")
        self.autonomous_scanning_in_progress = False

    def thread_callback(self) -> None:
        self.maximize_callback()
        self.send_button.setText("Send")
        self.query_thread = None
        self.add_chat_message("SYSTEM", "Action complete")
