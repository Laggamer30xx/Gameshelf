import os
print(f"Loading GameManager from: {os.path.abspath(__file__)}")
class GameManager:
    def __init__(self):
        self.games = []

    def add_game(self, title, executable_path="", launch_arguments=""):
        game = {
            "title": title,
            "executable_path": executable_path,
            "launch_arguments": launch_arguments,
            "iso_paths": [] # New field for ISO paths
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

    def edit_game(self, index, new_title, new_platform, new_genre, new_executable_path, new_launch_arguments, iso_paths):
        if 0 <= index < len(self.games):
            self.games[index]["title"] = new_title
            self.games[index]["platform"] = new_platform
            self.games[index]["genre"] = new_genre
            self.games[index]["launch_arguments"] = new_launch_arguments
            self.games[index]["executable_path"] = new_executable_path
            self.games[index]["iso_paths"] = iso_paths
            print(f"Edited game at index {index}")
            return True
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