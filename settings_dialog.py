from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel, QLineEdit, QFileDialog
from PyQt5.QtCore import QSettings, Qt
import os

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 400, 200)

        self.settings = QSettings("Gameshelf", "Settings")

        self.main_layout = QVBoxLayout(self)

        # Artwork Display Preference
        artwork_layout = QHBoxLayout()
        artwork_label = QLabel("Default Artwork for Game Listings:")
        self.artwork_combo = QComboBox()
        self.artwork_combo.addItems(["Grid", "Logo"])
        
        # Load saved artwork preference
        saved_artwork_pref = self.settings.value("artwork_display_preference", "Grid")
        self.artwork_combo.setCurrentText(saved_artwork_pref)

        artwork_layout.addWidget(artwork_label)
        artwork_layout.addWidget(self.artwork_combo)
        self.main_layout.addLayout(artwork_layout)

        # Theme Preference
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])

        # Load saved theme preference
        saved_theme_pref = self.settings.value("theme_preference", "Dark")
        self.theme_combo.setCurrentText(saved_theme_pref)

        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        self.main_layout.addLayout(theme_layout)

        # Steam Web API Key
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("Steam Web API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your Steam Web API Key")

        # Load saved API key
        saved_api_key = self.settings.value("steam_web_api_key", "")
        self.api_key_input.setText(saved_api_key)

        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_input)
        self.main_layout.addLayout(api_key_layout)

        # Config File Location
        config_path_layout = QHBoxLayout()
        config_path_label = QLabel("Config File Location:")
        self.config_path_input = QLineEdit()
        self.config_path_input.setPlaceholderText("Select directory for config files")
        self.config_browse_button = QPushButton("Browse")
        self.config_browse_button.clicked.connect(self._browse_config_path)

        config_path_layout.addWidget(config_path_label)
        config_path_layout.addWidget(self.config_path_input)
        config_path_layout.addWidget(self.config_browse_button)
        self.main_layout.addLayout(config_path_layout)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        self.main_layout.addLayout(buttons_layout)
        # Load saved config path
        saved_config_path = self.settings.value("config_file_location", "")
        if not saved_config_path:
            # Set default to current working directory if not set
            saved_config_path = os.getcwd()
        self.config_path_input.setText(saved_config_path)

    def save_settings(self):
        self.settings.setValue("artwork_display_preference", self.artwork_combo.currentText())
        self.settings.setValue("theme_preference", self.theme_combo.currentText())
        self.settings.setValue("steam_web_api_key", self.api_key_input.text())
        self.settings.setValue("config_file_location", self.config_path_input.text())
        self.accept()

    def _browse_config_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Config File Location", self.config_path_input.text())
        if directory:
            self.config_path_input.setText(directory)

    def get_artwork_display_preference(self):
        return self.artwork_combo.currentText()

    def get_theme_preference(self):
        return self.theme_combo.currentText()

    def get_steam_api_key(self):
        return self.api_key_input.text()
