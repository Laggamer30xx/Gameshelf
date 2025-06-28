from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QLabel, QCheckBox, QSizePolicy, QWidget, QComboBox # Added QComboBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QSize
import os

class SteamImportDialog(QDialog):
    def __init__(self, steam_games, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Steam Games")
        self.setGeometry(100, 100, 800, 600)

        self.steam_games = steam_games
        self.selected_games = []

        self.main_layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.main_layout.addWidget(self.list_widget)

        self.populate_list_widget()

        self.buttons_layout = QHBoxLayout()
        self.import_button = QPushButton("Import Selected Games")
        self.import_button.clicked.connect(self.accept)
        self.buttons_layout.addWidget(self.import_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.buttons_layout.addWidget(self.cancel_button)

        self.main_layout.addLayout(self.buttons_layout)

    def populate_list_widget(self):
        for game_info in self.steam_games:
            item = QListWidgetItem(self.list_widget)
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)

            checkbox = QCheckBox()
            checkbox.setChecked(True) # Default to checked
            checkbox.stateChanged.connect(lambda state, g=game_info: self.toggle_game_selection(state, g))
            item_layout.addWidget(checkbox)

            # Game Title
            title_label = QLabel(game_info['name'])
            title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            item_layout.addWidget(title_label)

            # Executable Path (optional)
            exe_path = game_info.get('executable_path', 'Not found')
            exe_label = QLabel(f"Exe: {os.path.basename(exe_path)}")
            exe_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            item_layout.addWidget(exe_label)

            # Artwork display
            artwork_label = QLabel()
            item_layout.addWidget(artwork_label)
            
            # Artwork selection combo box
            artwork_combo = QComboBox()
            artwork_combo.addItems([art_type.capitalize() for art_type in game_info.get('artwork', {}).keys() if art_type.lower() in ['grid', 'logo'] and game_info.get('artwork', {}).get(art_type) and os.path.exists(game_info['artwork'][art_type])])
            artwork_combo.setCurrentText("Grid") # Default to Grid
            artwork_combo.currentIndexChanged.connect(lambda index, al=artwork_label, gc=game_info: self.update_artwork_display(al, gc, artwork_combo.currentText()))
            item_layout.addWidget(artwork_combo)

            # Initial artwork display
            self.update_artwork_display(artwork_label, game_info, artwork_combo.currentText() if artwork_combo.currentText() else "Grid")

            item_widget.setLayout(item_layout)
            item.setSizeHint(item_widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, item_widget)

            # Add to selected games by default
            self.selected_games.append(game_info)

    def update_artwork_display(self, artwork_label, game_info, artwork_type):
        artwork_path = game_info.get('artwork', {}).get(artwork_type.lower())
        if artwork_path and os.path.exists(artwork_path):
            if artwork_type.lower() == 'hero':
                pixmap = QPixmap(artwork_path).scaled(184, 69, Qt.KeepAspectRatio, Qt.SmoothTransformation) # Steam hero image size
            elif artwork_type.lower() == 'grid':
                pixmap = QPixmap(artwork_path).scaled(460, 215, Qt.KeepAspectRatio, Qt.SmoothTransformation) # Steam grid image size
            elif artwork_type.lower() == 'logo':
                pixmap = QPixmap(artwork_path).scaled(300, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation) # Example size for logo
            else:
                pixmap = QPixmap(artwork_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation) # Default size
            artwork_label.setPixmap(pixmap)
        else:
            artwork_label.setText("No Artwork")
            artwork_label.clear()

    def toggle_game_selection(self, state, game_info):
        if state == Qt.Checked:
            if game_info not in self.selected_games:
                self.selected_games.append(game_info)
        else:
            if game_info in self.selected_games:
                self.selected_games.remove(game_info)

    def get_selected_games(self):
        return self.selected_games
