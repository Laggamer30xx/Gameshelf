import PyInstaller.__main__
import os

# Define the main script of your application
main_script = 'main.py'

# Define the name of your executable
app_name = 'Gameshelf'

# Define the path to your icon file (optional)
# icon_path = 'path/to/your/icon.ico'

# Define additional files to include (e.g., games.json, styles.py, etc.)
# PyInstaller expects a list of (source, destination_folder) tuples
data_files = [
    ('games.json', '.'), # Include games.json in the root directory of the executable
    ('styles.py', '.'), # Include styles.py
    ('game_manager.py', '.'), # Include game_manager.py
    ('edit_game_dialog.py', '.'), # Include edit_game_dialog.py
]

# Construct the PyInstaller command
pyinstaller_args = [
    main_script,
    '--name=%s' % app_name,
    '--onefile', # Create a single executable file
    '--windowed', # Prevent a console window from appearing
]

# Add icon if specified
# if 'icon_path' in locals() and os.path.exists(icon_path):
#     pyinstaller_args.append('--icon=%s' % icon_path)

# Add data files
for src, dest in data_files:
    if os.path.exists(src):
        pyinstaller_args.append('--add-data=%s%s%s' % (src, os.pathsep, dest))
    else:
        print(f"Warning: Data file not found - {src}")

# Run PyInstaller
print(f"Running PyInstaller with arguments: {pyinstaller_args}")
PyInstaller.__main__.run(pyinstaller_args)

print(f"\nPyInstaller build complete. Executable can be found in the 'dist' directory.")
