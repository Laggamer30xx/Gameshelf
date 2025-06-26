from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QListWidgetItem
from PyQt5.QtCore import Qt

class ScanResultsDialog(QDialog):
    def __init__(self, found_executables, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scan Results - Select Games")
        self.setGeometry(100, 100, 600, 400)

        self.found_executables = found_executables
        self.selected_executables = []

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()

        self.list_widget = QListWidget()
        for exe_path in self.found_executables:
            item = QListWidgetItem(exe_path)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Unchecked)
            self.list_widget.addItem(item)
        main_layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()

        self.add_selected_button = QPushButton("Add Selected Games")
        self.add_selected_button.clicked.connect(self._add_selected_games)
        button_layout.addWidget(self.add_selected_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def _add_selected_games(self):
        print("DEBUG: _add_selected_games called")
        self.selected_executables = [] # Clear previous selections
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            print(f"DEBUG: Item '{item.text()}' checkState: {item.checkState()}")
            if item.checkState() == Qt.Checked:
                self.selected_executables.append(item.text())
        self.accept()

    def get_selected_executables(self):
        return self.selected_executables
