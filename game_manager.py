import os
import json
class GameManager:
    def __init__(self):
        self.games = []
        self.games_file = os.path.join(os.path.dirname(__file__), "games.json")
        self.load_games()

    def save_games(self):
        with open(self.games_file, "w", encoding="utf-8") as f:
            json.dump(self.games, f, indent=4)
        print(f"Games saved to {self.games_file}")

    def load_games(self):
        if os.path.exists(self.games_file):
            with open(self.games_file, "r", encoding="utf-8") as f:
                self.games = json.load(f)
            # Ensure new fields exist for old game entries
            for game in self.games:
                if "workshop_content_paths" not in game:
                    game["workshop_content_paths"] = []
                if "developer" not in game:
                    game["developer"] = ""
                if "publisher" not in game:
                    game["publisher"] = ""
                if "game_type" not in game:
                    game["game_type"] = ""
                if "os_list" not in game:
                    game["os_list"] = ""
                if "release_state" not in game:
                    game["release_state"] = ""
                if "description" not in game:
                    game["description"] = ""
            print(f"Games loaded from {self.games_file}")
        else:
            self.games = []
            print("No games.json found, starting with empty game list.")

    def add_game(self, title, platform, genre, executable_path="", launch_arguments="", iso_paths=None, artwork=None,
                 cloud_save_path="", workshop_content_paths=None, steam_app_id="",
                 developer="", publisher="", game_type="", os_list="", release_state="", description=""):
        if iso_paths is None:
            iso_paths = []
        if artwork is None:
            artwork = {}
        if workshop_content_paths is None:
            workshop_content_paths = []
        game = {
            "title": title,
            "platform": platform,
            "genre": genre,
            "executable_path": executable_path,
            "launch_arguments": launch_arguments,
            "iso_paths": iso_paths,
            "artwork": artwork,
            "cloud_save_path": cloud_save_path,
            "steam_app_id": steam_app_id,
            "workshop_content_paths": workshop_content_paths,
            "developer": developer,
            "publisher": publisher,
            "game_type": game_type,
            "os_list": os_list,
            "release_state": release_state,
            "description": description
        }
        self.games.append(game)
        print(f"Added game: {title}")

    def get_all_games(self):
        return self.games

    def search_games(self, query, search_by="title"):
        results = []
        for game in self.games:
            if search_by == "title" and query.lower() in game["title"].lower():
                results.append(game)
            elif search_by == "platform" and query.lower() in game["platform"].lower():
                results.append(game)
            elif search_by == "genre" and query.lower() in game["genre"].lower():
                results.append(game)
        return results

    def edit_game(self, index, new_title, new_platform, new_genre, new_executable_path, new_launch_arguments, new_iso_paths, new_artwork, new_cloud_save_path, new_steam_app_id, new_workshop_content_paths,
                  new_developer, new_publisher, new_game_type, new_os_list, new_release_state, new_description):
        if 0 <= index < len(self.games):
            game = self.games[index]
            game["title"] = new_title
            game["platform"] = new_platform
            game["genre"] = new_genre
            game["executable_path"] = new_executable_path
            game["launch_arguments"] = new_launch_arguments
            game["iso_paths"] = new_iso_paths
            game["artwork"] = new_artwork
            game["cloud_save_path"] = new_cloud_save_path
            game["steam_app_id"] = new_steam_app_id
            game["workshop_content_paths"] = new_workshop_content_paths
            game["developer"] = new_developer
            game["publisher"] = new_publisher
            game["game_type"] = new_game_type
            game["os_list"] = new_os_list
            game["release_state"] = new_release_state
            game["description"] = new_description
            print(f"Edited game at index {index}: {new_title}")
            return True
        else:
            print(f"Error: Index {index} out of bounds for editing.")
            return False

    def delete_game(self, index):
        if 0 <= index < len(self.games):
            deleted_game = self.games.pop(index)
            print(f"Deleted game: {deleted_game['title']}")
            return True
        return False

    def save_games(self, filename="games.json"):
        import json
        with open(filename, "w") as f:
            json.dump(self.games, f, indent=4)
        print(f"Game data saved to {filename}")

    def load_games(self, filename="games.json"):
        import json
        import os
        if os.path.exists(filename):
            with open(filename, "r") as f:
                self.games = json.load(f)
            print(f"Game data loaded from {filename}")
        else:
            print(f"No game data file found at {filename}")