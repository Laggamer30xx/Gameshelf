import winreg
import os
import psutil
import re
import vdf # Added import for vdf
import requests

def find_steam_install_path():
    try:
        # Try 64-bit registry path first
        hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\Valve\\Steam")
    except FileNotFoundError:
        try:
            # Fallback to 32-bit registry path
            hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Valve\\Steam")
        except FileNotFoundError:
            # Fallback to common installation paths if registry lookup fails
            common_paths = [
                "C:\\Program Files (x86)\\Steam",
                "C:\\Program Files\\Steam",
                os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"), "Steam"),
                os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), "Steam")
            ]
            for path in common_paths:
                if os.path.exists(path) and os.path.isdir(path):
                    return path
            return None

    try:
        steam_path, _ = winreg.QueryValueEx(hkey, "InstallPath")
        return steam_path
    except Exception as e:
        print(f"Error reading Steam InstallPath from registry: {e}")
        return None
    finally:
        if hkey:
            winreg.CloseKey(hkey)

def find_steam_userdata_path(steam_install_path):
    """
    Finds the Steam 'userdata' directory.
    """
    userdata_path = os.path.join(steam_install_path, "userdata")
    if os.path.exists(userdata_path) and os.path.isdir(userdata_path):
        return userdata_path
    return None

# For testing purposes
import re

def get_steam_library_folders(steam_install_path):
    library_folders = []
    library_folders_vdf_path = os.path.join(steam_install_path, "steamapps", "libraryfolders.vdf")

    if not os.path.exists(library_folders_vdf_path):
        print(f"Error: libraryfolders.vdf not found at {library_folders_vdf_path}")
        return [steam_install_path] # Fallback to default if not found

    try:
        with open(library_folders_vdf_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Regex to find paths within "path" keys
        # This regex looks for lines like "\"1\"\t\t\"E:\\SteamLibrary\""
        # and extracts the path. It handles escaped backslashes.
        # It specifically targets numeric keys for library folders.
        paths = re.findall(r'"\d+"\s+"(.+?)"', content)
        
        for path in paths:
            # Ensure the path ends with 'steamapps'
            steamapps_path = os.path.join(path, 'steamapps')
            if os.path.exists(steamapps_path):
                library_folders.append(steamapps_path)

    except Exception as e:
        print(f"Error reading libraryfolders.vdf: {e}")
        # Fallback to default if error occurs during parsing
        default_steamapps_path = os.path.join(steam_install_path, "steamapps")
        if os.path.exists(default_steamapps_path):
            return [default_steamapps_path]
        return [] # Return empty if default also doesn't exist

    # Always include the default steamapps folder from the main Steam installation
    default_steamapps_path = os.path.join(steam_install_path, "steamapps")
    if default_steamapps_path not in library_folders and os.path.exists(default_steamapps_path):
        library_folders.insert(0, default_steamapps_path)

    return library_folders


def get_installed_steam_games(library_folders):
    steam_games = {}
    for lib_folder in library_folders:
        steamapps_path = lib_folder # lib_folder already points to steamapps
        for filename in os.listdir(steamapps_path):
            if filename.startswith("appmanifest_") and filename.endswith(".acf"):
                acf_path = os.path.join(steamapps_path, filename)
                game_info = parse_acf_file(acf_path)
                if game_info and "appid" in game_info and "name" in game_info and "installdir" in game_info:
                    game_info['full_install_path'] = os.path.join(lib_folder.replace('steamapps', ''), 'common', game_info['installdir'])
                    steam_games[game_info["appid"]] = game_info
    return steam_games

def parse_acf_file(acf_path):
    game_info = {}
    try:
        with open(acf_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Simple regex to extract appid, name, and installdir
        appid_match = re.search(r'"appid"\s+"(\d+)"', content)
        name_match = re.search(r'"name"\s+"(.+?)"', content)
        installdir_match = re.search(r'"installdir"\s+"(.+?)"', content)

        if appid_match: game_info["appid"] = appid_match.group(1)
        if name_match: game_info["name"] = name_match.group(1)
        if installdir_match: game_info["installdir"] = installdir_match.group(1)

    except Exception as e:
        print(f"Error parsing ACF file {acf_path}: {e}")
    return game_info

def get_steam_artwork_paths(steam_install_path, appid):
    artwork_paths = {}
    base_artwork_path = os.path.join(steam_install_path, "appcache", "librarycache", str(appid))

    if os.path.exists(base_artwork_path):
        # These are the specific filenames you provided
        artwork_paths["hero"] = os.path.join(base_artwork_path, "library_hero.jpg")
        artwork_paths["grid"] = os.path.join(base_artwork_path, "library_600x900.jpg")
        artwork_paths["header"] = os.path.join(base_artwork_path, "library_header.jpg")
        artwork_paths["logo"] = os.path.join(base_artwork_path, "logo.png")
        # The icon path provided was a hash, which might be dynamic. Let's include it as an example.
        artwork_paths["icon"] = os.path.join(base_artwork_path, "82afae56cfd88514886adb316b6d0f672dcbfaea.jpg")
    
    # Filter out paths that don't actually exist
    return {k: v for k, v in artwork_paths.items() if os.path.exists(v)}

def get_steam_cloud_save_paths(userdata_path, appid):
    """
    Finds the Steam cloud save path for a given app ID.
    Assumes a single user for simplicity, or takes the first user ID found.
    """
    if not userdata_path or not appid:
        return None

    # Steam cloud saves are typically in userdata/<userid>/<appid>/remote/
    # We need to find the user ID first
    user_ids = [d for d in os.listdir(userdata_path) if os.path.isdir(os.path.join(userdata_path, d)) and d.isdigit()]

    if not user_ids:
        return None

    # For simplicity, take the first user ID found
    user_id = user_ids[0]
    cloud_save_path = os.path.join(userdata_path, user_id, appid, "remote")

    if os.path.exists(cloud_save_path) and os.path.isdir(cloud_save_path):
        return cloud_save_path
    return None

def get_steam_workshop_content_paths(steam_path, appid):
    """
    Finds the local Steam Workshop content paths for a given app ID.
    """
    workshop_paths = []
    if not steam_path or not appid:
        return workshop_paths

    # The workshop content is typically in steam_path/steamapps/workshop/content/<appid>
    workshop_content_base_path = os.path.join(steam_path, "steamapps", "workshop", "content", str(appid))

    if os.path.exists(workshop_content_base_path) and os.path.isdir(workshop_content_base_path):
        for item_id in os.listdir(workshop_content_base_path):
            item_path = os.path.join(workshop_content_base_path, item_id)
            if os.path.isdir(item_path):
                workshop_paths.append(item_path)
    return workshop_paths

def is_steam_running():
    """
    Checks if the Steam client is currently running.
    """
    return is_process_running("steam.exe")

def is_steam_game_running(game_executable_path):
    """
    Checks if a specific Steam game's executable is currently running.
    """
    print(f"[DEBUG] is_steam_game_running: Checking for executable path: {game_executable_path}")
    if not game_executable_path:
        print("[DEBUG] is_steam_game_running: No executable path provided.")
        return False
    # Extract the executable name from the full path
    executable_name = os.path.basename(game_executable_path)
    print(f"[DEBUG] is_steam_game_running: Extracted executable name: {executable_name}")
    return is_process_running(executable_name)

def is_process_running(process_name):
    """
    Checks if a process with the given name is currently running.
    """
    print(f"[DEBUG] is_process_running: Looking for process: {process_name}")
    for process in psutil.process_iter(['name']):
        current_process_name = process.info['name']
        print(f"[DEBUG] is_process_running: Found process: {current_process_name}")
        if current_process_name.lower() == process_name.lower():
            print(f"[DEBUG] is_process_running: Match found for {process_name}")
            return True
    print(f"[DEBUG] is_process_running: No match found for {process_name}")
    return False


def find_game_executable(game_install_path, game_name):
    # Common executable names/patterns to look for
    potential_executables = [
        f"{game_name}.exe",
        f"{game_name.replace(' ', '')}.exe", # Remove spaces
        f"{game_name.replace(' ', '_')}.exe", # Replace spaces with underscores
        f"{game_name.split(' ')[0]}.exe", # First word
        "launcher.exe",
        "game.exe",
        "steam.exe" # Fallback, though unlikely to be the actual game
    ]

    # Common subdirectories to search
    search_dirs = [
        game_install_path,
        os.path.join(game_install_path, "Binaries", "Win64"),
        os.path.join(game_install_path, "Binaries", "Win32"),
        os.path.join(game_install_path, "x64"),
        os.path.join(game_install_path, "x86"),
        os.path.join(game_install_path, "bin"),
    ]

    for directory in search_dirs:
        if os.path.exists(directory):
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(".exe"):
                        # Check if the executable name is in our list of potentials
                        for potential_name in potential_executables:
                            if file.lower() == potential_name.lower():
                                return os.path.join(root, file)
                        
                        # Heuristic: if the file name contains the game name, consider it
                        if game_name.lower() in file.lower():
                            return os.path.join(root, file)

    # If no specific executable is found, return None
    return None

def get_game_details_from_appinfo_vdf(steam_path, appids):
    """
    Parses appinfo.vdf to get richer metadata for given app IDs.
    """
    appinfo_vdf_path = os.path.join(steam_path, "appcache", "appinfo.vdf")
    game_details = {}

    if not os.path.exists(appinfo_vdf_path):
        print(f"Warning: appinfo.vdf not found at {appinfo_vdf_path}")
        return game_details

    try:
        with open(appinfo_vdf_path, "rb") as f:
            appinfo_data = vdf.binary_load(f)

        for appid in appids:
            if str(appid) in appinfo_data:
                app_data = appinfo_data[str(appid)]
                details = {
                    "type": app_data.get("common", {}).get("type"),
                    "developer": app_data.get("extended", {}).get("developer"),
                    "publisher": app_data.get("extended", {}).get("publisher"),
                    "genres": app_data.get("extended", {}).get("genres"),
                    "gamedescription": app_data.get("extended", {}).get("gamedescription"),
                    "oslist": app_data.get("common", {}).get("oslist"),
                    "releasestate": app_data.get("common", {}).get("releasestate"),
                }
                game_details[str(appid)] = details
    except Exception as e:
        print(f"Error parsing appinfo.vdf: {e}")

    return game_details

# For testing purposes
if __name__ == "__main__":
    steam_path = find_steam_install_path()
    if steam_path:
        print(f"Steam installation path: {steam_path}")
        library_folders = get_steam_library_folders(steam_path)
        print("Steam Library Folders:")
        for folder in library_folders:
            print(f"- {folder}")
        
        steam_games = get_installed_steam_games(library_folders)
        print("\nInstalled Steam Games:")
        if steam_games:
            for appid, game_info in steam_games.items():
                print(f"  AppID: {appid}")
                print(f"    Name: {game_info['name']}")
                print(f"    Install Dir: {game_info['installdir']}")
                print(f"    Full Install Path: {game_info['full_install_path']}")
                
                artwork = get_steam_artwork_paths(steam_path, appid)
                if artwork:
                    print("    Artwork:")
                    for art_type, art_path in artwork.items():
                        print(f"      {art_type.capitalize()}: {art_path}")
                else:
                    print("    No artwork found.")

                game_executable_path = find_game_executable(game_info['full_install_path'], game_info['name'])
                game_info['executable_path'] = game_executable_path if game_executable_path else 'Not found'
                print(f"    Executable Path: {game_info['executable_path']}")
        else:
            print("  No Steam games found.")
    else:
        print("Steam installation path not found.")

def get_current_steam_user_id(steam_userdata_path):
    """
    Attempts to find the SteamID64 of the currently logged-in user.
    This is typically found by looking for subdirectories in the userdata folder
    that correspond to SteamID64s.
    """
    if not steam_userdata_path or not os.path.isdir(steam_userdata_path):
        print(f"Invalid Steam userdata path: {steam_userdata_path}")
        return None

    # SteamID64s are usually 17 digits long and start with 7656
    steam_id_pattern = re.compile(r'^7656\d{13}$')

    for entry in os.listdir(steam_userdata_path):
        full_path = os.path.join(steam_userdata_path, entry)
        if os.path.isdir(full_path) and steam_id_pattern.match(entry):
            # This is likely a SteamID folder.
            # We can try to confirm by looking for a localconfig.vdf or similar
            # For simplicity, we'll assume the first valid SteamID folder is the active one.
            # A more robust solution might involve parsing localconfig.vdf for the actual user ID.
            return entry
    return None

def get_steam_friends_list(steam_api_key, steam_id):
    """
    Fetches the friend list for a given SteamID using the Steam Web API.
    Requires a valid Steam Web API key.
    """
    if not steam_api_key or not steam_id:
        print("Steam API Key or SteamID is missing. Cannot fetch friends list.")
        return None

    # Steam Web API endpoint for GetFriendList
    url = f"http://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={steam_api_key}&steamid={steam_id}&relationship=friend"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()

        if "friendslist" in data and "friends" in data["friendslist"]:
            return data["friendslist"]["friends"]
        else:
            print(f"Unexpected response format for friends list: {data}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Steam friends list: {e}")
        return None
    except ValueError as e:
        print(f"Error parsing JSON response for friends list: {e}")
        return None

def get_steam_player_summaries(steam_api_key, steam_ids):
    """
    Fetches player summaries for a list of SteamIDs using the Steam Web API.
    Requires a valid Steam Web API key.
    """
    if not steam_api_key or not steam_ids:
        print("Steam API Key or SteamIDs are missing. Cannot fetch player summaries.")
        return None

    # Steam Web API endpoint for GetPlayerSummaries
    # steam_ids should be a comma-separated string of SteamIDs
    steam_ids_str = ",".join(steam_ids)
    url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={steam_api_key}&steamids={steam_ids_str}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()

        if "response" in data and "players" in data["response"]:
            return data["response"]["players"]
        else:
            print(f"Unexpected response format for player summaries: {data}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Steam player summaries: {e}")
        return None
    except ValueError as e:
        print(f"Error parsing JSON response for player summaries: {e}")
        return None

def check_steamworks_sdk_installed(steam_path):
    """
    Checks if Steamworks SDK related files are present, first by registry, then by heuristic file check.
    """
    import winreg # Import winreg here as it's Windows-specific

    # Try checking registry first
    try:
        # HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Valve\Steam\Apps\CommonRedis
        key_path = r"SOFTWARE\Wow6432Node\Valve\Steam\Apps\CommonRedis"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            # If the key exists, it suggests the SDK might be registered
            # You might want to check a specific value here if one exists,
            # but for now, just the presence of the key is a strong indicator.
            return True
    except OSError:
        # Registry key not found, fall back to file-based check
        pass

    if not steam_path:
        return False

    # Common Steamworks SDK files to look for
    sdk_files = [
        "sdk/redist/steam_api.dll",
        "sdk/redist/steam_api64.dll",
        "sdk/public/steam/steam_api.h" # A header file, indicating dev files
    ]

    for sdk_file in sdk_files:
        full_path = os.path.join(steam_path, sdk_file)
        if os.path.exists(full_path):
            return True
    return False


