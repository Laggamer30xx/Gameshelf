from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, QComboBox, QMessageBox, QLabel, QStackedWidget, QFormLayout, QFileDialog, QAction, QMenu, QProgressDialog, QDialog, QStackedLayout, QTextEdit
from scan_results_dialog import ScanResultsDialog
from PyQt5.QtCore import Qt, QTimer, QSettings
from styles import Style
from game_manager import GameManager
from iso_manager import IsoManager
from steam_integrator import find_steam_install_path, get_steam_library_folders, get_installed_steam_games, get_steam_artwork_paths, find_game_executable, find_steam_userdata_path, get_steam_cloud_save_paths, is_steam_game_running, get_steam_workshop_content_paths, check_steamworks_sdk_installed, get_game_details_from_appinfo_vdf
from steam_import_dialog import SteamImportDialog
from settings_dialog import SettingsDialog
from steam_workshop_integrator import SteamWorkshopIntegrator
from PyQt5.QtGui import QPixmap, QIcon

import os
import pygame
import subprocess
from PyQt5.QtWidgets import QMessageBox

class GameshelfUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gameshelf")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Enable key press events for Konami Code
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        self.game_manager = GameManager()
        self.game_manager.load_games()
        self.iso_manager = IsoManager()

        # Determine the path for QSettings
        # First, try to load from a temporary default QSettings instance
        temp_settings = QSettings("Gameshelf", "Settings")
        config_path = temp_settings.value("config_file_location", "")

        if config_path and os.path.isdir(config_path):
            # If a custom path is set and valid, use it
            self.settings = QSettings(os.path.join(config_path, "Gameshelf.ini"), QSettings.IniFormat)
        else:
            # Otherwise, use the default (application's data location)
            self.settings = QSettings("Gameshelf", "Settings")
            # Ensure the default path is saved if not already
            if not temp_settings.contains("config_file_location"):
                temp_settings.setValue("config_file_location", self.settings.fileName())
        self.steam_path = find_steam_install_path()
        self.steam_userdata_path = find_steam_userdata_path(self.steam_path)

        # Initialize SteamWorkshopIntegrator with API key from settings
        steam_api_key = self.settings.value("steam_web_api_key", "")
        if not steam_api_key:
            QMessageBox.warning(self, "Steam API Key Missing",
                                "Some Steam-related features (like Friends/Presence) "
                                "will be unavailable because no Steam Web API Key "
                                "is configured. Please go to Settings to add your API key.")
        self.steam_workshop_integrator = SteamWorkshopIntegrator(api_key=steam_api_key)

        # Konami Code setup
        self.konami_code_sequence = [
            Qt.Key_Up, Qt.Key_Up, Qt.Key_Down, Qt.Key_Down,
            Qt.Key_Left, Qt.Key_Right, Qt.Key_Left, Qt.Key_Right,
            Qt.Key_B, Qt.Key_A, Qt.Key_Return # Using Qt.Key_Return for Enter
        ]
        self.konami_code_index = 0

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # Main game table page
        self.main_page = QWidget()
        self.main_page_layout = QVBoxLayout(self.main_page)
        # Existing widgets will be added to main_page_layout later
        self.stacked_widget.addWidget(self.main_page)

        # Steam Workshop placeholder page
        self.workshop_page = QWidget()
        self.workshop_layout = QVBoxLayout(self.workshop_page)

        self.back_to_main_button = QPushButton("Back to Main")
        self.back_to_main_button.clicked.connect(self._show_main_page)
        self.workshop_layout.addWidget(self.back_to_main_button)

        self.workshop_search_input = QLineEdit(self.workshop_page)
        self.workshop_search_input.setPlaceholderText("Search workshop items...")
        self.workshop_layout.addWidget(self.workshop_search_input)

        self.workshop_search_button = QPushButton("Search Workshop")
        self.workshop_search_button.clicked.connect(self._perform_workshop_search)
        self.workshop_layout.addWidget(self.workshop_search_button)

        self.workshop_results_table = QTableWidget(self.workshop_page)
        self.workshop_results_table.setColumnCount(2) # Title, Description
        self.workshop_results_table.setHorizontalHeaderLabels(["Title", "Description"])
        self.workshop_layout.addWidget(self.workshop_results_table)

        self.stacked_widget.addWidget(self.workshop_page)

        self.gamepad_status_label = QLabel("Gamepad: Not Connected")
        self.main_page_layout.addWidget(self.gamepad_status_label)

        self.steam_cloud_status_label = QLabel("Steam Cloud Sync: Checking...")
        self.main_page_layout.addWidget(self.steam_cloud_status_label)

        # Game input fields
        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Game Title")
        self.main_page_layout.addWidget(self.title_input)

        self.platform_input = QLineEdit(self)
        self.main_page_layout.addWidget(self.platform_input)

        add_game_layout = QHBoxLayout()
        self.add_game_button = QPushButton("Add New Game")
        self.add_game_button.clicked.connect(self._show_add_game_form)
        add_game_layout.addWidget(self.add_game_button)

        self.scan_games_button = QPushButton("Scan for Games")
        self.scan_games_button.clicked.connect(self._scan_for_games)
        add_game_layout.addWidget(self.scan_games_button)

        self.import_steam_button = QPushButton("Import from Steam")
        self.import_steam_button.clicked.connect(self._import_from_steam)
        add_game_layout.addWidget(self.import_steam_button)

        self.import_arc_button = QPushButton("Import from Arc")
        self.import_arc_button.clicked.connect(self._import_from_arc)
        add_game_layout.addWidget(self.import_arc_button)

        self.steam_friends_button = QPushButton("Steam Friends")
        self.steam_friends_button.clicked.connect(self._load_steam_friends)
        add_game_layout.addWidget(self.steam_friends_button)

        self.main_page_layout.addLayout(add_game_layout)

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

        self.main_page_layout.addLayout(search_layout)

        self.game_table = QTableWidget()
        self.game_table.setColumnCount(8) # Title, Platform, Genre, Artwork, Status, Edit, Delete, Launch
        self.game_table.setHorizontalHeaderLabels(["Title", "Platform", "Genre", "Artwork", "Status", "Edit", "Delete", "Launch"])
        self.game_table.setColumnWidth(3, 150) # Set a reasonable width for the artwork column
        self.game_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.game_table.customContextMenuRequested.connect(self._show_game_table_context_menu)
        self.main_page_layout.addWidget(self.game_table)

        # Add/Edit Game Form
        self.edit_form_widget = QWidget()
        self.edit_form_layout = QFormLayout(self.edit_form_widget)
        self.stacked_widget.addWidget(self.edit_form_widget) # Add edit_form_widget to the stacked widget

        # Steam Friends/Presence placeholder page
        self.steam_friends_page = QWidget()
        self.steam_friends_layout = QVBoxLayout(self.steam_friends_page)
        self.steam_friends_label = QLabel("Steam Friends/Presence features will appear here.")
        self.steam_friends_label.setAlignment(Qt.AlignCenter)
        self.steam_friends_layout.addWidget(self.steam_friends_label)
        self.stacked_widget.addWidget(self.steam_friends_page)

        # Artwork display for game info page
        self.artwork_display_widget = QWidget()
        self.artwork_layout = QStackedLayout(self.artwork_display_widget)

        self._update_steam_cloud_status() # Call to update initial status

        self.hero_artwork_label = QLabel()
        self.hero_artwork_label.setAlignment(Qt.AlignCenter)
        self.hero_artwork_label.setScaledContents(True)
        self.artwork_layout.addWidget(self.hero_artwork_label)

        self.logo_artwork_label = QLabel()
        self.logo_artwork_label.setAlignment(Qt.AlignCenter)
        self.logo_artwork_label.setScaledContents(True)
        self.artwork_layout.addWidget(self.logo_artwork_label)

        self.edit_form_layout.addRow(self.artwork_display_widget)

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

        self.iso_paths_edit_input = QLineEdit()
        self.browse_iso_button = QPushButton("Browse ISOs")
        self.browse_iso_button.clicked.connect(self._browse_iso_path)
        iso_path_layout = QHBoxLayout()
        iso_path_layout.addWidget(self.iso_paths_edit_input)
        iso_path_layout.addWidget(self.browse_iso_button)
        self.edit_form_layout.addRow("ISO Paths (comma-separated):", iso_path_layout)

        self.launch_arguments_edit_input = QLineEdit()
        self.edit_form_layout.addRow("Launch Arguments:", self.launch_arguments_edit_input)

        self.cloud_save_path_edit_input = QLineEdit()
        self.cloud_save_path_edit_input.setReadOnly(True)
        self.browse_cloud_save_button = QPushButton("Open Folder")
        self.browse_cloud_save_button.clicked.connect(self._open_cloud_save_folder)
        cloud_save_layout = QHBoxLayout()
        cloud_save_layout.addWidget(self.cloud_save_path_edit_input)
        cloud_save_layout.addWidget(self.browse_cloud_save_button)
        self.edit_form_layout.addRow("Cloud Save Path:", cloud_save_layout)

        # Informational label about Steam Cloud Sync limitations
        self.cloud_sync_info_label = QLabel("<i>Steam Cloud sync status and force sync require Steamworks API integration.</i>")
        self.cloud_sync_info_label.setStyleSheet("font-size: 10px; color: gray;")
        self.edit_form_layout.addRow("", self.cloud_sync_info_label)

        # New fields for richer metadata
        self.developer_edit_input = QLineEdit()
        self.edit_form_layout.addRow("Developer:", self.developer_edit_input)

        self.publisher_edit_input = QLineEdit()
        self.edit_form_layout.addRow("Publisher:", self.publisher_edit_input)

        self.game_type_edit_input = QLineEdit()
        self.edit_form_layout.addRow("Game Type:", self.game_type_edit_input)

        self.os_list_edit_input = QLineEdit()
        self.edit_form_layout.addRow("OS List:", self.os_list_edit_input)

        self.release_state_edit_input = QLineEdit()
        self.edit_form_layout.addRow("Release State:", self.release_state_edit_input)

        self.description_edit_input = QTextEdit() # Use QTextEdit for multi-line description
        self.description_edit_input.setPlaceholderText("Enter game description...")
        self.edit_form_layout.addRow("Description:", self.description_edit_input)

        self.save_edit_button = QPushButton("Save Game")
        self.save_edit_button.clicked.connect(self._save_edited_game)
        self.cancel_edit_button = QPushButton("Cancel")
        self.cancel_edit_button.clicked.connect(self._cancel_edit)

        edit_buttons_layout = QHBoxLayout()
        edit_buttons_layout.addWidget(self.save_edit_button)
        edit_buttons_layout.addWidget(self.cancel_edit_button)
        self.edit_form_layout.addRow(edit_buttons_layout)

        self.layout.addWidget(self.edit_form_widget)
        self.edit_form_widget.hide()

        self._create_menu_bar()
        self._init_gamepad()
        self._update_game_table()

    def _import_from_steam(self):
        # This method will contain the logic for importing Steam games.
        # The code previously causing SyntaxError will be moved here.
        # This assumes 'library_folders', 'get_installed_steam_games', 'find_steam_userdata_path' are defined or imported elsewhere.

        # Placeholder for steam_path, library_folders, etc. - these need to be properly defined or passed.
        # For now, I'll assume they are accessible or will be defined globally/within the class scope.
        steam_path = None # You'll need to define how steam_path is obtained
        library_folders = [] # You'll need to define how library_folders are obtained

        if not library_folders:
            QMessageBox.warning(self, "Steam Import", "No Steam library folders found.")

            steam_games = get_installed_steam_games(library_folders)
            if not steam_games:
                QMessageBox.information(self, "Steam Import", "No installed Steam games found.")
                return

            steam_userdata_path = find_steam_userdata_path(steam_path)

        # Collect all appids to query appinfo.vdf once
        all_appids = [appid for appid in steam_games.keys()]
        appinfo_details = get_game_details_from_appinfo_vdf(steam_path, all_appids)

        found_steam_games_list = []
        for appid, game_info in steam_games.items():
            artwork = get_steam_artwork_paths(steam_path, appid)
            game_executable_path = find_game_executable(game_info['full_install_path'], game_info['name'])
            cloud_save_path = get_steam_cloud_save_paths(steam_userdata_path, appid) if steam_userdata_path else ""
            print(f"DEBUG: AppID: {appid}, Userdata Path: {steam_userdata_path}, Calculated Cloud Save Path: {cloud_save_path}")

            game_info['executable_path'] = game_executable_path if game_executable_path else 'Not found'
            game_info['artwork'] = artwork
            game_info['cloud_save_path'] = cloud_save_path
            found_steam_games_list.append(game_info)

        if found_steam_games_list:
            dialog = SteamImportDialog(found_steam_games_list, self)
            if dialog.exec_() == QDialog.Accepted:
                selected_games = dialog.get_selected_games()
                if selected_games:
                    for game_data in selected_games:
                        appid = game_data['appid']
                        
                        # Merge richer metadata from appinfo.vdf
                        if str(appid) in appinfo_details:
                            game_data.update(appinfo_details[str(appid)])

                        cloud_save_path = get_steam_cloud_save_paths(self.steam_userdata_path, appid)
                        workshop_content_paths = get_steam_workshop_content_paths(self.steam_path, appid)

                        self.game_manager.add_game(
                            title=game_data["name"],
                            platform="PC (Steam)",
                            genre=game_data.get("genres", ""), # Use genre from appinfo.vdf if available
                            executable_path=game_data['executable_path'],
                            launch_arguments=f"steam://rungameid/{appid}",
                            artwork=game_data['artwork'],
                            cloud_save_path=cloud_save_path,
                            steam_app_id=appid,
                            workshop_content_paths=workshop_content_paths,
                            developer=game_data.get("developer", ""),
                            publisher=game_data.get("publisher", ""),
                            game_type=game_data.get("type", ""),
                            os_list=game_data.get("oslist", ""),
                            release_state=game_data.get("releasestate", ""),
                            description=game_data.get("gamedescription", "")
                        )
                    self._update_game_table()
                    QMessageBox.information(self, "Games Added", f"Successfully added {len(selected_games)} Steam games.")
                else:
                    QMessageBox.information(self, "No Games Selected", "No Steam games were selected to add.")
        else:
            QMessageBox.information(self, "Steam Import", "No potential Steam games found.")

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
        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self._show_settings_dialog)
        view_menu.addAction(settings_action)

        # Steam Menu
        steam_menu = menubar.addMenu("&Steam")
        workshop_action = QAction("&Workshop", self)
        workshop_action.triggered.connect(lambda: self.stacked_widget.setCurrentWidget(self.workshop_page))
        steam_menu.addAction(workshop_action)

        # Help Menu
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _show_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Settings saved, re-apply if necessary
            updated_api_key = dialog.get_steam_api_key()
            self.steam_workshop_integrator = SteamWorkshopIntegrator(api_key=updated_api_key)
            self._update_game_table() # Re-update game table in case artwork preference changed
            new_theme = self.settings.value("theme_preference", "Dark").lower()
            self.apply_theme(new_theme)

    def _show_about_dialog(self):
        QMessageBox.about(self, "About Gameshelf",
                          "Gameshelf\n\nVersion 1.0\n\nDeveloped by Laggamer30xx")

    def _perform_workshop_search(self):
        search_query = self.workshop_search_input.text()
        if not search_query:
            QMessageBox.information(self, "Workshop Search", "Please enter a search query.")
            return

        try:
            # Assuming self.steam_workshop_integrator is initialized elsewhere
            # For now, just a placeholder
            print(f"Searching workshop for: {search_query}")
            # results = self.steam_workshop_integrator.search_items(search_query)
            # self.workshop_results_table.setRowCount(0)
            # for row, item in enumerate(results):
            #     self.workshop_results_table.insertRow(row)
            #     self.workshop_results_table.setItem(row, 0, QTableWidgetItem(item.get('title', '')))
            #     self.workshop_results_table.setItem(row, 1, QTableWidgetItem(item.get('description', '')))
        except Exception as e:
            QMessageBox.critical(self, "Workshop Search Error", f"An error occurred during search: {e}")

    def _show_main_page(self):
        self.stacked_widget.setCurrentWidget(self.main_page)

    def _update_game_table(self):
        # Placeholder for now, will implement game table population here
        print("Updating game table...")
        self.game_table.setRowCount(0) # Clear existing rows
        games = self.game_manager.get_all_games() # Assuming this method exists and returns a list of game objects/dicts
        for row, game in enumerate(games):
            self.game_table.insertRow(row)
            self.game_table.setItem(row, 0, QTableWidgetItem(game.get('title', '')))
            self.game_table.setItem(row, 1, QTableWidgetItem(game.get('platform', '')))
            self.game_table.setItem(row, 2, QTableWidgetItem(game.get('genre', '')))
            # Add other columns as needed

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
            self.gamepad_timer.start(10)
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
        self.current_edit_game_index = -1
        self.title_input.clear()
        self.platform_input.clear()
        self.genre_edit_input.clear()
        self.executable_path_edit_input.clear()
        self.launch_arguments_edit_input.clear()
        self.iso_paths_edit_input.clear()

        self.edit_form_widget.show()
        self.game_table.hide()
        self.search_input.hide()
        self.search_by_combo.hide()
        self.search_button.hide()
        self.clear_search_button.hide()
        self.add_game_button.hide()
        self.scan_games_button.hide()

    def _save_new_game(self):
        title = self.title_input.text().strip()
        platform = self.platform_input.text().strip()
        genre = self.genre_input.text().strip()
        executable_path = self.executable_path_input.text().strip()
        launch_arguments = self.launch_arguments_input.text()
        iso_paths_text = self.iso_paths_input.text()
        iso_paths = [path.strip() for path in iso_paths_text.split(',') if path.strip()]

        if not title or not platform or not genre:
            QMessageBox.warning(self, "Input Error", "Title, Platform, and Genre cannot be empty.")
            return

        self.game_manager.add_game(title, platform, genre, executable_path, launch_arguments, iso_paths)
        self.game_manager.save_games()
        QMessageBox.information(self, "Game Added", f"Game '{title}' has been added.")
        self._update_game_table()
        self._update_game_table()
        self._clear_add_game_form()

    def _save_edited_game(self):
        title = self.title_edit_input.text().strip()
        platform = self.platform_edit_input.text().strip()
        genre = self.genre_edit_input.text().strip()
        executable_path = self.executable_path_edit_input.text().strip()
        launch_arguments = self.launch_arguments_edit_input.text()
        iso_paths_text = self.iso_paths_edit_input.text()
        iso_paths = [path.strip() for path in iso_paths_text.split(',') if path.strip()]
        cloud_save_path = self.cloud_save_path_edit_input.text().strip()

        if not title or not platform or not genre:
            QMessageBox.warning(self, "Input Error", "Title, Platform, and Genre cannot be empty.")
            return

        original_game = self.game_manager.get_all_games()[self.current_edit_game_index]
        steam_app_id = original_game.get("steam_app_id")
        artwork = original_game.get("artwork")
        workshop_content_paths = original_game.get("workshop_content_paths", []) # Preserve existing if not Steam game

        if steam_app_id:
            # If it's a Steam game, re-fetch workshop content paths
            workshop_content_paths = get_steam_workshop_content_paths(self.steam_path, steam_app_id)

        # Read new fields from UI (assuming they exist)
        developer = self.developer_edit_input.text().strip()
        publisher = self.publisher_edit_input.text().strip()
        game_type = self.game_type_edit_input.text().strip()
        os_list = self.os_list_edit_input.text().strip()
        release_state = self.release_state_edit_input.text().strip()
        description = self.description_edit_input.toPlainText().strip() # Assuming QTextEdit for description

        self.game_manager.edit_game(
            self.current_edit_game_index,
            title,
            platform,
            genre,
            executable_path,
            launch_arguments,
            iso_paths,
            artwork,
            cloud_save_path,
            steam_app_id,
            new_workshop_content_paths=workshop_content_paths,
            new_developer=developer,
            new_publisher=publisher,
            new_game_type=game_type,
            new_os_list=os_list,
            new_release_state=release_state,
            new_description=description
        )
        self.game_manager.save_games()
        QMessageBox.information(self, "Game Saved", f"Game '{title}' has been updated.")
        self._update_game_table()
        self._update_game_table()

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

    def _perform_search(self):
        query = self.search_input.text()
        category = self.search_by_combo.currentText().lower()
        results = self.game_manager.search_games(query, category)
        self._update_game_table(results)

    def _clear_search(self):
        self.search_input.clear()
        self._update_game_table()

    def _update_game_table(self, games=None):
        self.game_table.setRowCount(0)
        if games is None:
            games = self.game_manager.get_all_games()

        for game in games:
            row_position = self.game_table.rowCount()
            self.game_table.insertRow(row_position)

            self.game_table.setItem(row_position, 0, QTableWidgetItem(game["title"]))
            self.game_table.setItem(row_position, 1, QTableWidgetItem(game["platform"]))
            self.game_table.setItem(row_position, 2, QTableWidgetItem(game["genre"]))

            artwork_label = QLabel()
            artwork_type = self.settings.value("artwork_display_preference", "Header").lower()
            artwork_paths = game.get('artwork', {})
            artwork_path = artwork_paths.get(artwork_type)

            if artwork_path and os.path.exists(artwork_path):
                if artwork_type == 'grid':
                    pixmap = QPixmap(artwork_path).scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                elif artwork_type == 'logo':
                    pixmap = QPixmap(artwork_path).scaled(150, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                else:
                    pixmap = QPixmap(artwork_path).scaled(150, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                artwork_label.setPixmap(pixmap)
                artwork_label.setAlignment(Qt.AlignCenter)
            else:
                artwork_label.setText("No Artwork")
                artwork_label.setAlignment(Qt.AlignCenter)
            self.game_table.setCellWidget(row_position, 3, artwork_label)

            status = ""
            if game.get("steam_app_id"):
                game_executable_path = game.get("executable_path")
                if game_executable_path and is_steam_game_running(game_executable_path):
                    status = "Running"
                else:
                    status = "Installed"
            else:
                status = "N/A"
            self.game_table.setItem(row_position, 4, QTableWidgetItem(status))

            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(lambda _, r=row_position: self._edit_game_from_ui(r))
            self.game_table.setCellWidget(row_position, 5, edit_button)

            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(lambda _, r=row_position: self._delete_game_from_ui(r))
            self.game_table.setCellWidget(row_position, 6, delete_button)

            launch_button = QPushButton("Launch")
            launch_button.clicked.connect(lambda _, r=row_position: self._launch_game(r))
            self.game_table.setCellWidget(row_position, 7, launch_button)

    def _edit_game_from_ui(self, row):
        self.current_edit_game_index = row
        game_to_edit = self.game_manager.get_all_games()[row]

        self.title_edit_input.setText(game_to_edit.get("title", ""))
        self.platform_edit_input.setText(game_to_edit.get("platform", ""))
        self.genre_edit_input.setText(game_to_edit.get("genre", ""))
        self.executable_path_edit_input.setText(game_to_edit.get("executable_path", ""))
        self.launch_arguments_edit_input.setText(game_to_edit.get("launch_arguments", ""))
        self.iso_paths_edit_input.setText(",".join(game_to_edit.get("iso_paths", [])))
        self.cloud_save_path_edit_input.setText(game_to_edit.get("cloud_save_path", ""))

        # Load and display Hero and Logo artwork
        app_id = game_to_edit.get("steam_app_id")
        if app_id:
            artwork_paths = get_steam_artwork_paths(self.steam_path, app_id)
            hero_path = artwork_paths.get("hero")
            logo_path = artwork_paths.get("logo")

            if hero_path and os.path.exists(hero_path):
                hero_pixmap = QPixmap(hero_path)
                self.hero_artwork_label.setPixmap(hero_pixmap)
            else:
                self.hero_artwork_label.clear()

            if logo_path and os.path.exists(logo_path):
                logo_pixmap = QPixmap(logo_path)
                self.logo_artwork_label.setPixmap(logo_pixmap)
            else:
                self.logo_artwork_label.clear()
        else:
            self.hero_artwork_label.clear()
            self.logo_artwork_label.clear()

        self.stacked_widget.setCurrentWidget(self.edit_form_widget)

    def _delete_game_from_ui(self, row):
        # Get the game from the game manager based on the row
        # Assuming game_manager has a way to get games by index or ID
        # For now, let's assume we can get the game's title from the table
        # Get the game title for the confirmation message
        game_title = self.game_table.item(row, 0).text()
        reply = QMessageBox.question(self, 'Delete Game', f"Are you sure you want to delete '{game_title}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.game_manager.delete_game(row) # Pass the row (index) directly
            self._update_game_table()
            QMessageBox.information(self, "Game Deleted", f"'{game_title}' has been deleted.")

    def _browse_executable_edit(self):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, "Select Executable", "", "All Files (*)")
        if file_path:
            self.executable_path_edit_input.setText(file_path)

    def _browse_iso_path(self):
        file_dialog = QFileDialog(self)
        file_paths, _ = file_dialog.getOpenFileNames(self, "Select ISO Files", "", "ISO Files (*.iso);;All Files (*)")
        if file_paths:
            self.iso_paths_edit_input.setText(",".join(file_paths))

    def _open_cloud_save_folder(self):
        if self.current_edit_game_index != -1:
            game = self.game_manager.get_all_games()[self.current_edit_game_index]
            cloud_save_path = game.get("cloud_save_path")

            if cloud_save_path and os.path.exists(cloud_save_path):
                try:
                    subprocess.Popen(f'explorer "{cloud_save_path}"')
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not open folder: {e}")
    def _scan_for_games(self):
        scan_directory = QFileDialog.getExistingDirectory(self, "Select Directory to Scan", "")
        if not scan_directory:
            return

        found_executables = []
        for root, _, files in os.walk(scan_directory):
            for file in files:
                if file.lower().endswith(".exe"):
                    full_path = os.path.join(root, file)
                    found_executables.append(full_path)

        if not found_executables:
            QMessageBox.information(self, "Scan Results", "No executable files found in the selected directory.")
            return

        dialog = ScanResultsDialog(found_executables, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_executables = dialog.get_selected_executables()
            if selected_executables:
                for exe_path in selected_executables:
                    # Derive title from filename, remove .exe extension
                    title = os.path.splitext(os.path.basename(exe_path))[0]
                    self.game_manager.add_game(
                        title=title,
                        platform="PC", # Assuming PC for .exe files
                        genre="Unknown", # Can be updated later
                        executable_path=exe_path,
                        launch_arguments="",
                        iso_paths=[]
                    )
                self._update_game_table()
                QMessageBox.information(self, "Games Added", f"Successfully added {len(selected_executables)} games.")
            else:
                QMessageBox.information(self, "No Games Selected", "No games were selected to add.")

    def _launch_game(self, row):
        game_to_launch = self.game_manager.get_all_games()[row]
        game_title = game_to_launch.get("title", "Unknown Game")
        steam_app_id = game_to_launch.get("steam_app_id")
        executable_path = game_to_launch.get("executable_path", "")
        launch_args = game_to_launch.get("launch_arguments", "").split()
        iso_paths = game_to_launch.get("iso_paths", [])

        mounted_iso = False
        if iso_paths:
            if self.iso_manager.mount_iso(iso_paths[0]):
                mounted_iso = True
            else:
                QMessageBox.critical(self, "Launch Error", f"Failed to mount ISO for {game_title}.")
                return

        if steam_app_id:
            try:
                steam_url = f"steam://rungameid/{steam_app_id}"
                os.startfile(steam_url)
                QMessageBox.information(self, "Launch Game", f"Successfully launched {game_title} via Steam.")
            except Exception as e:
                QMessageBox.critical(self, "Launch Error", f"An error occurred while launching {game_title} via Steam: {e}")
            finally:
                if mounted_iso:
                    self.iso_manager.dismount_iso(iso_paths[0])
            return

        if not executable_path:
            QMessageBox.warning(self, "Launch Error", f"No executable path specified for {game_title}.")
            return

        try:
            command = [executable_path] + launch_args
            subprocess.Popen(command)
            QMessageBox.information(self, "Launch Game", f"Successfully launched {game_title}.")
        except FileNotFoundError:
            QMessageBox.critical(self, "Launch Error", f"Executable not found at: {executable_path}")
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"An error occurred while launching {game_title}: {e}")
        finally:
            if mounted_iso:
                self.iso_manager.dismount_iso(iso_paths[0])

    def _show_game_table_context_menu(self, pos):
        index = self.game_table.indexAt(pos)
        if not index.isValid():
            return

        row = index.row()
        game = self.game_manager.get_all_games()[row]

        context_menu = QMenu(self)

        launch_action = context_menu.addAction("Launch Game")
        launch_action.triggered.connect(lambda: self._launch_game(row))

        show_info_action = context_menu.addAction("Show Game Info")
        show_info_action.triggered.connect(lambda: self._edit_game_from_ui(row))

        icon_pixmap = None
        app_id = game.get("steam_app_id")
        if app_id:
            artwork_paths = get_steam_artwork_paths(self.steam_path, app_id)
            icon_path = artwork_paths.get("icon")
            if icon_path and os.path.exists(icon_path):
                icon_pixmap = QPixmap(icon_path).scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        if icon_pixmap:
            launch_action.setIcon(QIcon(icon_pixmap))
            show_info_action.setIcon(QIcon(icon_pixmap))

        context_menu.exec_(self.game_table.mapToGlobal(pos))

    def keyPressEvent(self, event):
        if event.key() == self.konami_code_sequence[self.konami_code_index]:
            self.konami_code_index += 1
            if self.konami_code_index == len(self.konami_code_sequence):
                print("Konami Code Activated!")
                self._trigger_dummy_workshop_search()
                self.konami_code_index = 0 # Reset for next time
        else:
            self.konami_code_index = 0 # Reset if sequence is broken
        super().keyPressEvent(event)

    def _trigger_dummy_workshop_search(self):
        self.stacked_widget.setCurrentWidget(self.workshop_page)
        self._perform_workshop_search()

    def _perform_workshop_search(self):
        search_text = self.workshop_search_input.text()
        # Using a common appid for testing, e.g., 440 for Team Fortress 2
        # In a real application, this appid might come from the selected game
        # or be configurable.
        appid = 440 # Example: Team Fortress 2 AppID

        results = self.steam_workshop_integrator.search_workshop_items(
            appid=appid,
            search_text=search_text
        )

        self.workshop_results_table.setColumnCount(4) # Title, Description, PublishedFileId, Creator
        self.workshop_results_table.setHorizontalHeaderLabels(["Title", "Description", "File ID", "Creator"])
        self.workshop_results_table.setRowCount(0)

        for row_num, item in enumerate(results.get("items", [])):
            self.workshop_results_table.insertRow(row_num)
            self.workshop_results_table.setItem(row_num, 0, QTableWidgetItem(item.get("title", "")))
            self.workshop_results_table.setItem(row_num, 1, QTableWidgetItem(item.get("description", "")))
            self.workshop_results_table.setItem(row_num, 2, QTableWidgetItem(item.get("publishedfileid", "")))
            self.workshop_results_table.setItem(row_num, 3, QTableWidgetItem(item.get("creator", "")))
        self.workshop_results_table.resizeColumnsToContents()

    def _load_steam_friends(self):
        steam_api_key = self.settings.value("steam_web_api_key", "")
        if not steam_api_key:
            QMessageBox.warning(self, "API Key Missing", "Please set your Steam Web API Key in settings to use this feature.")
            return

        steam_userdata_path = find_steam_userdata_path(self.steam_path)
        if not steam_userdata_path:
            QMessageBox.warning(self, "Steam Userdata Not Found", "Could not find Steam userdata path.")
            return

        current_steam_id = get_current_steam_user_id(steam_userdata_path)
        if not current_steam_id:
            QMessageBox.warning(self, "SteamID Not Found", "Could not determine current Steam user ID.")
            return

        # Fetch friends list
        friends_list = get_steam_friends_list(steam_api_key, current_steam_id)

        if friends_list:
            # Extract SteamIDs of friends to get their summaries
            friend_steam_ids = [friend['steamid'] for friend in friends_list]
            player_summaries = get_steam_player_summaries(steam_api_key, friend_steam_ids)

            if player_summaries:
                # Update the UI with friends' information
                friends_info = []
                for player in player_summaries:
                    persona_name = player.get('personaname', 'Unknown')
                    persona_state = player.get('personastate', 0) # 0 = Offline, 1 = Online, etc.
                    game_extra_info = player.get('gameextrainfo', '')
                    
                    status = "Offline"
                    if persona_state == 1:
                        status = "Online"
                    elif persona_state == 2:
                        status = "Busy"
                    elif persona_state == 3:
                        status = "Away"
                    elif persona_state == 4:
                        status = "Snooze"
                    elif persona_state == 5:
                        status = "Looking to Trade"
                    elif persona_state == 6:
                        status = "Looking to Play"
                    
                    if game_extra_info:
                        status += f" (Playing: {game_extra_info})"
                    
                    friends_info.append(f"{persona_name}: {status}")
                
                self.steam_friends_label.setText("\n".join(friends_info))
            else:
                self.steam_friends_label.setText("Could not retrieve player summaries for friends.")
        else:
            self.steam_friends_label.setText("Could not retrieve Steam friends list.")
        
        self.stacked_widget.setCurrentWidget(self.steam_friends_page)
    def _import_from_arc(self):
        ARC_GAMES_PATH = "C:\\Program Files (x86)\\Arc"
        if not os.path.exists(ARC_GAMES_PATH):
            QMessageBox.warning(self, "Arc Games Import", f"Arc Games directory not found at {ARC_GAMES_PATH}")
            return

        found_executables = []
        for root, _, files in os.walk(ARC_GAMES_PATH):
            for file in files:
                if file.lower().endswith(".exe"):
                    full_path = os.path.join(root, file)
                    found_executables.append(full_path)

        if not found_executables:
            QMessageBox.information(self, "Arc Games Import", "No executable files found in Arc Games directory.")
            return

        dialog = ScanResultsDialog(found_executables, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_executables = dialog.get_selected_executables()
            if selected_executables:
                for exe_path in selected_executables:
                    title = os.path.splitext(os.path.basename(exe_path))[0]
                    self.game_manager.add_game(
                        title=title,
                        platform="PC",
                        genre="Unknown",
                        executable_path=exe_path,
                        launch_arguments="",
                        iso_paths=[]
                    )
                self._update_game_table()
                QMessageBox.information(self, "Arc Games Import", f"Successfully added {len(selected_executables)} games from Arc.")
            else:
                QMessageBox.information(self, "Arc Games Import", "No games were selected to add from Arc.")

    def _update_steam_cloud_status(self):
        if self.steam_path and check_steamworks_sdk_installed(self.steam_path):
            self.steam_cloud_status_label.setText("Steam Cloud Sync: Steamworks SDK detected. (Further integration needed for detailed status)")
            # Here, you would integrate with a Steamworks Python wrapper
            # to get actual cloud sync status for specific games.
            # For now, this is a placeholder.
        else:
            self.steam_cloud_status_label.setText("Steam Cloud Sync: Steamworks SDK not detected. Features unavailable.")

    def closeEvent(self, event):
        self.game_manager.save_games()
        if self.iso_manager.get_mounted_drive_letter():
            self.iso_manager.dismount_iso()
        pygame.quit()
        super().closeEvent(event)
