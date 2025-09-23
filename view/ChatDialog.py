from agent import Query
from graph import Pathfinder
from pyautogui import sleep
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QPushButton, QHBoxLayout, \
QGraphicsOpacityEffect, QApplication
from PySide6.QtCore import QThread, QPropertyAnimation, QEasingCurve
from util import Logger
from .SettingsDialog import SettingsDialog
from kg.KnowledgeBuilder import KgExtractor
from util import Snapshotter, ImageEncoder
from autonomous_scanner import AutonomyEmulator
import asyncio

# TODO CHANGE THREAD FOR ASYNC ?
class AutonomyEmulatorThread(QThread):
    def __init__(self,
                 autonomous_mode,
                 auth,
                 connect_kg = False,
                 kg_openai_api = None,
                 kg_n4j_uri = None,
                 kg_n4j_auth = None):
        super().__init__()
        self.emulator = AutonomyEmulator(autonomous_mode, auth, connect_kg, kg_openai_api, kg_n4j_uri, kg_n4j_auth)

    def run(self):
        self.emulator.execute()

class ChatDialog(QDialog):

    def __init__(self, parent=None):
        super(ChatDialog, self).__init__(parent)
        self.setWindowTitle("ErudAI")
        self.setObjectName("ChatDialog")
        self.setMinimumSize(500, 600)
        self.program_option_mode = None

        self.settings_dialog = SettingsDialog(self)

        self.autonomous_scanning_in_progress = False
        self.autonomy_emulator_thread = None  # To store the running thread

        self.query_task = None
        self.kg_init_task = None

        self.autonomy_kg = None
        self.kg_builder = None
        self.pathfinder = None

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
        self.send_button.clicked.connect(lambda: asyncio.ensure_future(self.on_submit()))
        button_group.addWidget(self.send_button)

        self.scan_button = QPushButton("Begin Scan")
        self.scan_button.setObjectName("ScanButton")
        self.scan_button.clicked.connect(lambda: asyncio.ensure_future(self.on_scan_toggle()))
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
        """
        Method responsible for opening the settings dialog
        """
        self.settings_dialog.exec()

    def add_chat_message(self, sender: str, message: str) -> None:
        """
        Method responsible for rendering a sent message inside of chat history

        :param sender: Name of the sender to be displayed e.g. SYSTEM or user
        :param message: Message to be displayed
        """
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

    async def extract_view(self) -> None:
        """
        Method responsible for initiating the process of a view extraction
        """
        self.load_settings()
        try:
            clicked_button = self.user_input_widget.text().strip()
            self.showMinimized()
            sleep(2)
            encoded_img = ImageEncoder.encode(Snapshotter.snapshot())

            scanTask = asyncio.create_task(self.kg_builder.extract_gui_schema(clicked_button, encoded_img))
            await scanTask
            self.scan_callback()

        except Exception as e:
            self.add_chat_message("SYSTEM", f"There was an error during view extraction: {str(e)}")

    async def on_scan_toggle(self) -> None:
        """
        Method responsible for initiating program scanning mode
        """
        try:
            self.load_settings()
            if self.autonomous_scanning_in_progress:
                if self.autonomy_emulator_thread and self.autonomy_emulator_thread.isRunning():
                    self.autonomy_emulator_thread.terminate()
                    self.autonomy_emulator_thread.wait()
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

                self.autonomy_kg = self.settings_dialog.knowledge_on.isChecked()

                if self.autonomy_kg:
                    self.autonomy_emulator_thread = AutonomyEmulatorThread(self.autonomous_mode,
                                                                           auth,
                                                                           self.autonomy_kg,
                                                                           self.openai_api_key,
                                                                           self.n4j_uri,
                                                                           self.n4j_auth)
                else:
                    self.autonomy_emulator_thread = AutonomyEmulatorThread(self.autonomous_mode, auth, self.autonomy_kg)

                self.showMinimized()
                self.autonomy_emulator_thread.start()

                self.autonomous_scanning_in_progress = True
                self.scan_button.setText("Stop")
            else:
                self.kg_builder = KgExtractor(self.openai_api_key, self.n4j_uri, self.n4j_auth)
                self.showMinimized()
                sleep(2)
                encoded_image = ImageEncoder.encode(Snapshotter.snapshot())

                kgInitTask = asyncio.create_task(self.kg_builder.initialize_cache(encoded_image))
                await kgInitTask
                self.cache_callback()

        except Exception as e:
            self.add_chat_message("SYSTEM", f"There was an error during scanning: {str(e)}")

    async def on_submit(self) -> None:
        """
        Method responsible for initiating an action-type query
        """
        try:
            self.load_settings()
            if self.query_task:
                self.query_task.cancel()
                self.add_chat_message("SYSTEM", "Action stopped.")
                self.query_task = None
                self.send_button.setText("Send")
                return

            user_input = self.user_input_widget.text().strip()
            self.add_chat_message("You", user_input)
            self.pathfinder = Pathfinder(self.n4j_uri, self.n4j_auth, self.n4j_db_name, self.openai_api_key)
            self.showMinimized()
            context_var = await self.pathfinder.get_ui_path(user_input) # TODO ADDITIONAL TASKS CAN BE LAUNCHED WHILE THIS IS BEING DONE - FIX
            query = Query(api_key=self.endpoint_api_key,
                          base_url=self.endpoint_url,
                          logger=self.logger)

            prompt = f"{user_input}. This map of UI elements specifies what view has what button and what the buttons are leading to: [{context_var}]"
            self.query_task = asyncio.create_task(query.execute(prompt=prompt))

            self.send_button.setText("Stop")

            await self.query_task

        except Exception as e:
            self.add_chat_message("SYSTEM", f"There was an error during action submit: {str(e)}")

    def maximize_callback(self) -> None:
        """
        Callback method which maximizes back the window in center of the screen
        """
        self.showNormal()
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        window_size = self.frameGeometry()
        center_point = screen_rect.center()
        window_size.moveCenter(center_point)
        self.move(window_size.topLeft())

    def cache_callback(self) -> None:
        """
        Callback method which prepares the program for the second-stage of scanning
        """
        self.add_chat_message("SYSTEM",
                              "Click a button leading to the next view, then input its label and press 'Extract view'")
        self.user_input_widget.setPlaceholderText("Type the label of the clicked button")
        self.scan_button.setText("Extract view")
        self.maximize_callback()
        self.scan_button.clicked.disconnect()
        self.scan_button.clicked.connect(lambda: asyncio.ensure_future(self.extract_view()))
        self.autonomous_scanning_in_progress = False

    def scan_callback(self) -> None:
        """
        Callback method which reverts the program back from scanning mode to default state
        """
        self.scan_button.clicked.disconnect()
        self.scan_button.clicked.connect(lambda: asyncio.ensure_future(self.on_scan_toggle()))
        self.maximize_callback()
        self.user_input_widget.setPlaceholderText("Type your message...")
        self.user_input_widget.setText("")
        self.scan_button.setText("Begin Scan")
        self.add_chat_message("SYSTEM", "View extraction complete")
        self.autonomous_scanning_in_progress = False

    def thread_callback(self) -> None:
        """
        Callback method for finished threads
        """
        self.maximize_callback()
        self.send_button.setText("Send")
        self.query_thread = None
        self.add_chat_message("SYSTEM", "Action complete")
