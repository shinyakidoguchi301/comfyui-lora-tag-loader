import requests
import json
import os

class EagleAPI:
    def __init__(self, config_path="config/config.json", ngrok_key="home"):
        self.base_url = self.load_ngrok_url(config_path, ngrok_key)

    def load_ngrok_url(self, config_path, key):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("ngrokUrls", {}).get(key, "")
        except Exception as e:
            print(f"Failed to load config: {e}")
            return ""

    def get_folder_id(self, folder_name="LoRA"):
        try:
            response = requests.get(f"{self.base_url}/api/folder/list")
            response.raise_for_status()
            folders = response.json()
            for folder in folders:
                if folder.get("name") == folder_name:
                    return folder.get("id")
        except Exception as e:
            print(f"Error getting folder ID: {e}")
        return None

    def get_item_id(self, folder_id, file_name):
        try:
            response = requests.get(f"{self.base_url}/api/item/list", params={"folderId": folder_id})
            response.raise_for_status()
            items = response.json()
            for item in items:
                if item.get("name") == file_name:
                    return item.get("id")
        except Exception as e:
            print(f"Error getting item ID: {e}")
        return None

    def get_memo(self, item_id):
        try:
            response = requests.get(f"{self.base_url}/api/item/info", params={"id": item_id})
            response.raise_for_status()
            return response.json().get("memo", "")
        except Exception as e:
            print(f"Error getting memo: {e}")
        return ""

    def update_memo(self, item_id, new_memo):
        try:
            response = requests.post(f"{self.base_url}/api/item/update", json={"id": item_id, "memo": new_memo})
            response.raise_for_status()
            return response.status_code == 200
        except Exception as e:
            print(f"Error updating memo: {e}")
        return False
