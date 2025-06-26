from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, QComboBox, QMessageBox, QLabel, QStackedWidget, QFormLayout, QFileDialog, QAction, QMenu, QProgressDialog, QDialog
from scan_results_dialog import ScanResultsDialog
from PyQt5.QtCore import Qt, QTimer
from styles import Style
import pygame
from game_manager import GameManager
from iso_manager import IsoManager

import subprocess

class GameshelfUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gameshelf")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.game_manager = GameManager()
        self.game_manager.load_games() # Force refresh
        self.iso_manager = IsoManager()

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        self.gamepad_status_label = QLabel("Gamepad: Not Connected")
        self.layout.addWidget(self.gamepad_status_label)

        # Game input fields
        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Game Title")
        self.layout.addWidget(self.title_input)

        self.platform_input = QLineEdit(self)
        self.layout.addWidget(self.platform_input)

        add_game_layout = QHBoxLayout()
        self.add_game_button = QPushButton("Add New Game")
        self.add_game_button.clicked.connect(self._show_add_game_form)
        add_game_layout.addWidget(self.add_game_button)

        self.scan_games_button = QPushButton("Scan for Games")
        self.scan_games_button.clicked.connect(self._scan_for_games)
        add_game_layout.addWidget(self.scan_games_button)

        self.layout.addLayout(add_game_layout)

        # Search fields
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search games...")
        search_layout.addWidget(self.search_input)

        self.search_by_combo = QComboBox(self)
        self.search_by_combo.addItems(["Title", "Platform", "Genre"])
        search_layout.addWidget(self.search_by_combo)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._perform_search)
        search_layout.addWidget(self.search_button)

        self.clear_search_button = QPushButton("Clear Search")
        self.clear_search_button.clicked.connect(self._clear_search)
        search_layout.addWidget(self.clear_search_button)

        self.layout.addLayout(search_layout)

        self.game_table = QTableWidget()
        self.game_table.setColumnCount(6) # Title, Platform, Genre, Edit, Delete, Launch
        self.game_table.setHorizontalHeaderLabels(["Title", "Platform", "Genre", "Edit", "Delete", "Launch"])
        self.layout.addWidget(self.game_table)

        # Add/Edit Game Form
        self.edit_form_widget = QWidget()
        self.edit_form_layout = QFormLayout(self.edit_form_widget)

        self.title_edit_input = QLineEdit()
        self.edit_form_layout.addRow("Title:", self.title_edit_input)

        self.platform_edit_input = QLineEdit()
        self.edit_form_layout.addRow("Platform:", self.platform_edit_input)

        self.genre_edit_input = QLineEdit()
        self.edit_form_layout.addRow("Genre:", self.genre_edit_input)

        self.executable_path_edit_input = QLineEdit()
        self.browse_executable_button = QPushButton("Browse")
        self.browse_executable_button.clicked.connect(self._browse_executable_edit)
        path_edit_layout = QHBoxLayout()
        path_edit_layout.addWidget(self.executable_path_edit_input)
        path_edit_layout.addWidget(self.browse_executable_button)
        self.edit_form_layout.addRow("Executable Path:", path_edit_layout)

        self.iso_paths_edit_input = QLineEdit() # New ISO paths input
        self.browse_iso_button = QPushButton("Browse ISOs") # New Browse ISOs button
        self.browse_iso_button.clicked.connect(self._browse_iso_path)
        iso_path_layout = QHBoxLayout()
        iso_path_layout.addWidget(self.iso_paths_edit_input)
        iso_path_layout.addWidget(self.browse_iso_button)
        self.edit_form_layout.addRow("ISO Paths (comma-separated):", iso_path_layout)

        self.launch_arguments_edit_input = QLineEdit()
        self.edit_form_layout.addRow("Launch Arguments:", self.launch_arguments_edit_input)

        self.save_edit_button = QPushButton("Save Game")
        self.save_edit_button.clicked.connect(self._save_edited_game)
        self.cancel_edit_button = QPushButton("Cancel")
        self.cancel_edit_button.clicked.connect(self._cancel_edit)

        edit_buttons_layout = QHBoxLayout()
        edit_buttons_layout.addWidget(self.save_edit_button)
        edit_buttons_layout.addWidget(self.cancel_edit_button)
        self.edit_form_layout.addRow(edit_buttons_layout)

        self.layout.addWidget(self.edit_form_widget)
        self.edit_form_widget.hide() # Hide by default

        self._create_menu_bar()
        self._init_gamepad()
        self._update_game_table() # Load games into table on startup

    def apply_theme(self, theme_name):
        if theme_name == "dark":
            QApplication.instance().setStyleSheet(Style.get_dark_stylesheet())
        elif theme_name == "light":
            QApplication.instance().setStyleSheet(Style.get_light_stylesheet())

    def _create_menu_bar(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menubar.addMenu("&View")
        light_mode_action = QAction("&Light Mode", self)
        light_mode_action.triggered.connect(lambda: self.apply_theme("light"))
        view_menu.addAction(light_mode_action)

        dark_mode_action = QAction("&Dark Mode", self)
        dark_mode_action.triggered.connect(lambda: self.apply_theme("dark"))
        view_menu.addAction(dark_mode_action)

        # Help Menu
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        # about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

        self.apply_theme("dark") # Default to dark mode

    def _init_gamepad(self):
        pygame.init()
        pygame.joystick.init()

        self.joysticks = []
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            self.joysticks.append(joystick)
            print(f"Detected Gamepad: {joystick.get_name()}")

        if self.joysticks:
            self.gamepad_status_label.setText("Gamepad: Connected")
            self.gamepad_timer = QTimer(self)
            self.gamepad_timer.timeout.connect(self._check_gamepad_input)
            self.gamepad_timer.start(10) # Check every 10ms
        else:
            self.gamepad_status_label.setText("Gamepad: No Gamepads Found")

    def _check_gamepad_input(self):
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                print(f"Button {event.button} pressed on joystick {event.joy}")
                self.gamepad_status_label.setText(f"Gamepad: Button {event.button} Pressed")
            elif event.type == pygame.JOYBUTTONUP:
                self.gamepad_status_label.setText("Gamepad: Connected")

    def _show_add_game_form(self):
        self.current_edit_game_index = -1 # Indicates adding a new game
        self.title_edit_input.clear()
        self.platform_edit_input.clear()
        self.genre_edit_input.clear()
        self.executable_path_edit_input.clear()
        self.launch_arguments_edit_input.clear()
        self.edit_form_widget.show()
        self.game_table.hide()
        self.search_input.hide()
        self.search_by_combo.hide()
        self.search_button.hide()
        self.clear_search_button.hide()
        self.add_game_button.hide()
        self.scan_games_button.hide() # Hide the scan games button when form is shown

    def _save_edited_game(self):
        title = self.title_edit_input.text().strip()
        platform = self.platform_edit_input.text().strip()
        genre = self.genre_edit_input.text().strip()
        executable_path = self.executable_path_edit_input.text().strip()
        launch_arguments = self.launch_arguments_edit_input.text()
        iso_paths_text = self.iso_paths_edit_input.text()
        iso_paths = [path.strip() for path in iso_paths_text.split(',') if path.strip()]

        if not title or not platform or not genre:
            QMessageBox.warning(self, "Input Error", "Title, Platform, and Genre cannot be empty.")
            return

        if self.current_edit_game_index == -1: # Adding a new game
            self.game_manager.add_game(title, platform, genre, executable_path, launch_arguments, iso_paths)
            QMessageBox.information(self, "Game Added", f"Game '{title}' has been added.")
        else: # Editing an existing game
            self.game_manager.edit_game(
                self.current_edit_game_index,
                title,
                platform,
                genre,
                executable_path,
                launch_arguments,
                iso_paths
            )
            QMessageBox.information(self, "Game Edited", f"Game '{title}' has been updated.")

        self._cancel_edit() # Hide form and refresh table

    def _cancel_edit(self):
        self.edit_form_widget.hide()
        self.game_table.show()
        self.search_input.show()
        self.search_by_combo.show()
        self.search_button.show()
        self.clear_search_button.show()
        self.add_game_button.show()
        self.scan_games_button.show()
        self._update_game_table()

    def _update_game_table(self, games=None):
        self.game_table.setRowCount(0) # Clear existing rows
        if games is None:
            games = self.game_manager.get_all_games()

        for game in games:
            row_position = self.game_table.rowCount()
            self.game_table.insertRow(row_position)
            print(f"DEBUG: Type of game: {type(game)}")
        print(f"DEBUG: Content of game: {game}")
        print(f"DEBUG: Type of game['title']: {type(game['title'])}")
        print(f"DEBUG: Content of game['title']: {game['title']}")
        self.game_table.setItem(row_position, 0, QTableWidgetItem(game["title"]))
        self.game_table.setItem(row_position, 1, QTableWidgetItem(game["platform"]))
            self.game_table.setItem(row_position, 2, QTableWidgetItem(game["genre"]))

            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(lambda _, r=row_position: self._edit_game_from_ui(r))
            self.game_table.setCellWidget(row_position, 3, edit_button)

            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, r=row_position: self._delete_game_from_ui(r))
            self.game_table.setCellWidget(row_position, 4, delete_button)

            launch_button = QPushButton("Launch")
            launch_button.clicked.connect(lambda _, r=row_position: self._launch_game(r))
            self.game_table.setCellWidget(row_position, 5, launch_button)

    def _edit_game_from_ui(self, row):
        self.current_edit_game_index = row
        game_to_edit = self.game_manager.get_all_games()[row]

        self.title_edit_input.setText(game_to_edit.get("title", ""))
        self.platform_edit_input.setText(game_to_edit.get("platform", ""))
        self.genre_edit_input.setText(game_to_edit.get("genre", ""))
        self.executable_path_edit_input.setText(game_to_edit.get("executable_path", ""))
        self.launch_arguments_edit_input.setText(game_to_edit.get("launch_arguments", ""))
        self.iso_paths_edit_input.setText(",".join(game_to_edit.get("iso_paths", [])))

        self.edit_form_widget.show()
        self.game_table.hide()
        self.search_input.hide()
        self.search_by_combo.hide()
        self.search_button.hide()
        self.clear_search_button.hide()
        self.add_game_button.hide()

    def _perform_search(self):
        query = self.search_input.text()
        search_by = self.search_by_combo.currentText()
        if query:
            results = self.game_manager.search_games(query, search_by)
            self._update_game_table(results)
        else:
            self._update_game_table()

    def _clear_search(self):
        self.search_input.clear()
        self._update_game_table()

    def _delete_game_from_ui(self, row):
        self.game_manager.delete_game(row)
        self._update_game_table()

    def _scan_for_games(self):
        import os

        # Concise blacklist of common non-game executables
        blacklist_executables = {
            "chrome.exe", "firefox.exe", "msedge.exe", "powerpnt.exe", "winword.exe",
            "excel.exe", "notepad.exe", "calc.exe", "explorer.exe", "cmd.exe",
            "python.exe", "py.exe", "code.exe", "steam.exe", "epicgameslauncher.exe",
            "goggalaxy.exe", "origin.exe", "uplay.exe", "battle.net.exe", "riotclientservices.exe",
            "install.exe", "setup.exe", "update.exe", "unins000.exe", "uninstall.exe"
        }

        # Blacklist of common system and application directories (case-insensitive)
        blacklist_directories = {
            "windows", "program files (x86)\\google", "program files\\microsoft office",
            "program files (x86)\\microsoft office", "program files\\common files",
            "program files (x86)\\common files", "users\\all users", "programdata",
            "appdata", "temp", "system32", "syswow64", "drivers", "driverstore",
            "winsxs", "logs", "cache", "temp", "downloads"
        }

        scan_paths = [
            os.environ.get("ProgramFiles", "C:\\Program Files"),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
            os.path.join(os.environ.get("APPDATA", "C:\\Users\\<username>\\AppData\\Roaming"), "Microsoft\\Windows\\Start Menu\\Programs"),
            os.path.join(os.environ.get("LOCALAPPDATA", "C:\\Users\\<username>\\AppData\\Local"), "Programs")
        ]

        found_executables = []
        total_dirs = 0
        for path in scan_paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    total_dirs += len(dirs)

        progress_dialog = QProgressDialog("Scanning for games...", "Cancel", 0, total_dirs, self)
        progress_dialog.setWindowTitle("Scan Progress")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setAutoClose(True)
        progress_dialog.show()

        current_dir_count = 0
        for path in scan_paths:
            if not os.path.exists(path):
                continue
            for root, dirs, files in os.walk(path):
                current_dir_count += 1
                progress_dialog.setValue(current_dir_count)
                QApplication.processEvents() # Allow UI to update

                if progress_dialog.wasCanceled():
                    break

                # Check if current directory or any of its parents are in blacklist
                skip_dir = False
                for black_dir in blacklist_directories:
                    if black_dir in root.lower():
                        skip_dir = True
                        break
                if skip_dir:
                    dirs[:] = [] # Skip subdirectories
                    continue

                for file in files:
                    if file.lower().endswith(".exe") and file.lower() not in blacklist_executables:
                        full_path = os.path.join(root, file)
                        found_executables.append(full_path)
            if progress_dialog.wasCanceled():
                break

        progress_dialog.close()

        if found_executables:
            dialog = ScanResultsDialog(found_executables, self)
            if dialog.exec_() == QDialog.Accepted:
                selected_games = dialog.get_selected_executables()
                if selected_games:
                    for exe_path in selected_games:
                        game_title = os.path.splitext(os.path.basename(exe_path))[0] # Suggest title from filename
                        # Add a placeholder for platform and genre, user can edit later
                        self.game_manager.add_game({
                            "title": game_title,
                            "executable_path": exe_path,
                            "launch_arguments": ""
                        })
                    self._update_game_table()
                    QMessageBox.information(self, "Games Added", f"Successfully added {len(selected_games)} games.")
                else:
                    QMessageBox.information(self, "No Games Selected", "No games were selected to add.")
        else:
            QMessageBox.information(self, "Scan Complete", "No potential game executables found.")

    def _browse_executable_edit(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Executables (*.exe)")
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            self.executable_path_edit_input.setText(selected_file)

    def _browse_iso_path(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles) # Allow multiple ISOs
        file_dialog.setNameFilter("ISO Files (*.iso *.cue *.bin)")
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            self.iso_paths_edit_input.setText(",".join(selected_files))

    def _launch_game(self, row):
        game_to_launch = self.game_manager.get_all_games()[row]
        game_title = game_to_launch.get("title", "Unknown Game")
        executable_path = game_to_launch.get("executable_path", "")
        launch_args = game_to_launch.get("launch_arguments", "").split()
        iso_paths = game_to_launch.get("iso_paths", [])

        mounted_iso = False
        if iso_paths:
            # For now, only mount the first ISO. Multi-disc handling can be added later.
            if self.iso_manager.mount_iso(iso_paths[0]):
                mounted_iso = True
            else:
                QMessageBox.critical(self, "Launch Error", f"Failed to mount ISO for {game_title}.")
                return

        if not executable_path:
            QMessageBox.warning(self, "Launch Error", f"No executable path specified for {game_title}.")
            return

        try:
            command = [executable_path] + launch_args
            # Using Popen without waiting, as the game might run for a long time.
            # ISO will be dismounted when the Gameshelf app closes.
            subprocess.Popen(command)
            QMessageBox.information(self, "Launch Game", f"Successfully launched {game_title}.")
        except FileNotFoundError:
            QMessageBox.critical(self, "Launch Error", f"Executable not found at: {executable_path}")
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"An error occurred while launching {game_title}: {e}")
        finally:
            # ISO will be dismounted when the Gameshelf app closes (in closeEvent)
            pass

    def closeEvent(self, event):
        self.game_manager.save_games()
        # Dismount any mounted ISO before closing
        if self.iso_manager.get_mounted_drive_letter():
            self.iso_manager.dismount_iso()
        pygame.quit()
        super().closeEvent(event)
