from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QRadioButton, QPushButton, QButtonGroup, QWidget
import os
import json

SETTINGS_FILE = os.path.join(".erudai_settings.json")

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # GUI model endpoint
        layout.addWidget(QLabel("Address of GUI model endpoint:"))
        self.gui_model_endpoint = QLineEdit()
        layout.addWidget(self.gui_model_endpoint)

        # GUI model deployment toggle
        layout.addWidget(QLabel("GUI model deployed on:"))
        self.gui_local = QRadioButton("Local")
        self.gui_cloud = QRadioButton("Cloud")
        self.gui_radio_group = QButtonGroup()
        self.gui_radio_group.addButton(self.gui_local)
        self.gui_radio_group.addButton(self.gui_cloud)
        gui_radio_layout = QHBoxLayout()
        gui_radio_layout.addWidget(self.gui_local)
        gui_radio_layout.addWidget(self.gui_cloud)
        layout.addLayout(gui_radio_layout)

        # GUI model API key
        self.gui_api_key_label = QLabel("GUI model API key:")
        self.gui_api_key = QLineEdit()
        layout.addWidget(self.gui_api_key_label)
        layout.addWidget(self.gui_api_key)

        # Neo4j endpoint
        layout.addWidget(QLabel("Address of Neo4j endpoint:"))
        self.neo4j_endpoint = QLineEdit()
        layout.addWidget(self.neo4j_endpoint)

        # Neo4j DB name
        layout.addWidget(QLabel("Neo4j database name:"))
        self.neo4j_db = QLineEdit()
        layout.addWidget(self.neo4j_db)

        # Neo4j deployment toggle
        layout.addWidget(QLabel("Neo4j deployed on:"))
        self.neo4j_local = QRadioButton("Local")
        self.neo4j_aura = QRadioButton("Aura Instance")
        self.neo4j_radio_group = QButtonGroup()
        self.neo4j_radio_group.addButton(self.neo4j_local)
        self.neo4j_radio_group.addButton(self.neo4j_aura)
        neo4j_radio_layout = QHBoxLayout()
        neo4j_radio_layout.addWidget(self.neo4j_local)
        neo4j_radio_layout.addWidget(self.neo4j_aura)
        layout.addLayout(neo4j_radio_layout)

        # Aura credentials
        self.aura_username_label = QLabel("Aura username:")
        self.aura_username = QLineEdit()
        layout.addWidget(self.aura_username_label)
        layout.addWidget(self.aura_username)

        self.aura_api_key_label = QLabel("Aura API key:")
        self.aura_api_key = QLineEdit()
        layout.addWidget(self.aura_api_key_label)
        layout.addWidget(self.aura_api_key)

        # OpenAI API key
        layout.addWidget(QLabel("OpenAI API key:"))
        self.openai_api_key = QLineEdit()
        layout.addWidget(self.openai_api_key)

        # Debug mode toggle
        layout.addWidget(QLabel("Debug mode:"))
        self.debug_on = QRadioButton("On")
        self.debug_off = QRadioButton("Off")
        self.debug_radio_group = QButtonGroup()
        self.debug_radio_group.addButton(self.debug_on)
        self.debug_radio_group.addButton(self.debug_off)
        debug_layout = QHBoxLayout()
        debug_layout.addWidget(self.debug_on)
        debug_layout.addWidget(self.debug_off)
        layout.addLayout(debug_layout)

        # Debug options
        self.log_snapshots_label = QLabel("Log taken snapshots:")
        self.log_snapshots = QRadioButton("On")
        self.log_snapshots_off = QRadioButton("Off")
        self.log_snapshots_group = QButtonGroup()
        self.log_snapshots_group.addButton(self.log_snapshots)
        self.log_snapshots_group.addButton(self.log_snapshots_off)
        layout.addWidget(self.log_snapshots_label)
        snapshots_layout = QHBoxLayout()
        snapshots_layout.addWidget(self.log_snapshots)
        snapshots_layout.addWidget(self.log_snapshots_off)
        layout.addLayout(snapshots_layout)

        self.log_encoded_label = QLabel("Log encoded snapshots:")
        self.log_encoded = QRadioButton("On")
        self.log_encoded_off = QRadioButton("Off")
        self.log_encoded_group = QButtonGroup()
        self.log_encoded_group.addButton(self.log_encoded)
        self.log_encoded_group.addButton(self.log_encoded_off)
        layout.addWidget(self.log_encoded_label)
        encoded_layout = QHBoxLayout()
        encoded_layout.addWidget(self.log_encoded)
        encoded_layout.addWidget(self.log_encoded_off)
        layout.addLayout(encoded_layout)

        # Save/Close buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect radio logic
        self.gui_cloud.toggled.connect(self.toggle_gui_api_key)
        self.neo4j_aura.toggled.connect(self.toggle_aura_fields)
        self.debug_on.toggled.connect(self.toggle_debug_fields)

        self.toggle_gui_api_key()
        self.toggle_aura_fields()
        self.toggle_debug_fields()

        self.load_settings()
        self.save_button.clicked.connect(self.save_settings)

    def toggle_gui_api_key(self):
        visible = self.gui_cloud.isChecked()
        self.gui_api_key.setVisible(visible)
        self.gui_api_key_label.setVisible(visible)

    def toggle_aura_fields(self):
        visible = self.neo4j_aura.isChecked()
        self.aura_username.setVisible(visible)
        self.aura_username_label.setVisible(visible)
        self.aura_api_key.setVisible(visible)
        self.aura_api_key_label.setVisible(visible)

    def toggle_debug_fields(self):
        visible = self.debug_on.isChecked()
        self.log_snapshots.setVisible(visible)
        self.log_snapshots_off.setVisible(visible)
        self.log_snapshots_label.setVisible(visible)
        self.log_encoded.setVisible(visible)
        self.log_encoded_off.setVisible(visible)
        self.log_encoded_label.setVisible(visible)

    def save_settings(self):
        data = {
            "gui_model_endpoint": self.gui_model_endpoint.text(),
            "gui_model_deployment": "cloud" if self.gui_cloud.isChecked() else "local",
            "gui_model_api_key": self.gui_api_key.text(),

            "neo4j_endpoint": self.neo4j_endpoint.text(),
            "neo4j_db": self.neo4j_db.text(),
            "neo4j_deployment": "aura" if self.neo4j_aura.isChecked() else "local",
            "aura_username": self.aura_username.text(),
            "aura_api_key": self.aura_api_key.text(),

            "openai_api_key": self.openai_api_key.text(),

            "debug": "on" if self.debug_on.isChecked() else "off",
            "log_snapshots": "on" if self.log_snapshots.isChecked() else "off",
            "log_encoded": "on" if self.log_encoded.isChecked() else "off",
        }

        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return

        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)

        self.gui_model_endpoint.setText(data.get("gui_model_endpoint", ""))
        (self.gui_cloud if data.get("gui_model_deployment") == "cloud" else self.gui_local).setChecked(True)
        self.gui_api_key.setText(data.get("gui_model_api_key", ""))

        self.neo4j_endpoint.setText(data.get("neo4j_endpoint", ""))
        self.neo4j_db.setText(data.get("neo4j_db", ""))
        (self.neo4j_aura if data.get("neo4j_deployment") == "aura" else self.neo4j_local).setChecked(True)
        self.aura_username.setText(data.get("aura_username", ""))
        self.aura_api_key.setText(data.get("aura_api_key", ""))

        self.openai_api_key.setText(data.get("openai_api_key", ""))

        (self.debug_on if data.get("debug") == "on" else self.debug_off).setChecked(True)
        (self.log_snapshots if data.get("log_snapshots") == "on" else self.log_snapshots_off).setChecked(True)
        (self.log_encoded if data.get("log_encoded") == "on" else self.log_encoded_off).setChecked(True)

        # Re-apply visibility logic
        self.toggle_gui_api_key()
        self.toggle_aura_fields()
        self.toggle_debug_fields()

