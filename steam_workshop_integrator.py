import requests

class SteamWorkshopIntegrator:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://api.steampowered.com/IPublishedFileService/"

    def search_workshop_items(self, appid, search_text="", page=1, num_per_page=10):
        """
        Searches Steam Workshop items using the Steam Web API.
        """
        if not self.api_key:
            print("Steam Web API Key not provided. Cannot search workshop items.")
            return {"items": [], "total_results": 0}

        endpoint = "QueryFiles/v1/"
        url = f"{self.base_url}{endpoint}"

        params = {
            "key": self.api_key,
            "appid": appid,
            "search_text": search_text,
            "page": page,
            "numperpage": num_per_page,
            "querytype": 9,  # 9 for rankedByVote, 0 for rankedByPublicationDate
            "return_metadata": 1,
            "return_tags": 1,
            "return_for_sharing": 1,
            "return_kv_tags": 1,
            "return_children": 1,
            "return_previews": 1,
            "return_walkthrough": 1,
            "return_vote_data": 1,
            "return_playtime_stats": 1,
            "return_details": 1,
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "response" in data and "publishedfiledetails" in data["response"]:
                items = []
                for item_data in data["response"]["publishedfiledetails"]:
                    items.append({
                        "title": item_data.get("title", "N/A"),
                        "description": item_data.get("description", "N/A"),
                        "publishedfileid": item_data.get("publishedfileid", "N/A"),
                        "creator": item_data.get("creator", "N/A"),
                        "preview_url": item_data.get("preview_url", ""),
                        "tags": [tag["tag"] for tag in item_data.get("tags", [])],
                        "subscriptions": item_data.get("subscriptions", 0),
                        "favorited": item_data.get("favorited", 0),
                        "views": item_data.get("views", 0),
                        "kvtags": item_data.get("kvtags", [])
                    })
                total_results = data["response"].get("totalcount", 0)
                return {"items": items, "total_results": total_results}
            else:
                print(f"Unexpected response format for workshop search: {data}")
                return {"items": [], "total_results": 0}
        except requests.exceptions.RequestException as e:
            print(f"Error searching Steam Workshop: {e}")
            return {"items": [], "total_results": 0}
        except ValueError as e:
            print(f"Error parsing JSON response for workshop search: {e}")
            return {"items": [], "total_results": 0}

    def get_workshop_item_details(self, publishedfileids):
        """
        Gets details of Steam Workshop items using the Steam Web API.
        """
        if not self.api_key:
            print("Steam Web API Key not provided. Cannot get workshop item details.")
            return {"items": []}

        endpoint = "GetDetails/v1/"
        url = f"{self.base_url}{endpoint}"

        params = {
            "key": self.api_key,
            "itemcount": len(publishedfileids)
        }
        for i, fileid in enumerate(publishedfileids):
            params[f"publishedfileids[{i}]"] = fileid

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "response" in data and "publishedfiledetails" in data["response"]:
                items = []
                for item_data in data["response"]["publishedfiledetails"]:
                    items.append({
                        "title": item_data.get("title", "N/A"),
                        "description": item_data.get("description", "N/A"),
                        "publishedfileid": item_data.get("publishedfileid", "N/A"),
                        "creator": item_data.get("creator", "N/A"),
                        "preview_url": item_data.get("preview_url", ""),
                        "tags": [tag["tag"] for tag in item_data.get("tags", [])],
                        "subscriptions": item_data.get("subscriptions", 0),
                        "favorited": item_data.get("favorited", 0),
                        "views": item_data.get("views", 0),
                        "kvtags": item_data.get("kvtags", [])
                    })
                return {"items": items}
            else:
                print(f"Unexpected response format for workshop item details: {data}")
                return {"items": []}
        except requests.exceptions.RequestException as e:
            print(f"Error getting Steam Workshop item details: {e}")
            return {"items": []}
        except ValueError as e:
            print(f"Error parsing JSON response for workshop item details: {e}")
            return {"items": []}
