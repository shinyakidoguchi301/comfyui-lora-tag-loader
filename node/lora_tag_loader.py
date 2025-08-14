import os, re, json, base64, requests
from io import BytesIO
from PIL import Image
from safetensors.torch import load_file
from comfy.sd import load_lora
import folder_paths

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
            for folder in response.json():
                if folder.get("name") == folder_name:
                    return folder.get("id")
        except Exception as e:
            print(f"Error getting folder ID: {e}")
        return None

    def get_item_id(self, folder_id, file_name):
        try:
            response = requests.get(f"{self.base_url}/api/item/list", params={"folderId": folder_id})
            response.raise_for_status()
            for item in response.json():
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

class LoRA_TagLoader:
    @classmethod
    def INPUT_TYPES(cls):
        lora_root = folder_paths.get_folder_paths("loras")[0]
        lora_files, cls.lora_map = [], {}
        for root, _, files in os.walk(lora_root):
            for file in files:
                if file.endswith((".safetensors", ".pt")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, lora_root).replace("\\", "/")
                    lora_files.append(rel_path)
                    cls.lora_map[rel_path] = full_path
        return {
            "required": {
                "lora_file": (lora_files,),
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "tag_source": ("STRING", {"default": "LoRAinfo", "choices": ["LoRAinfo", "Eagleinfo"]}),
                "tag_package": ("STRING", {"default": "default", "choices": ["default", "action", "portrait"]}),
                "ngrok_key": ("STRING", {"default": "home", "choices": ["home", "work"]}),
                "save_image": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "tags": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING", "IMAGE", "STRING")
    RETURN_NAMES = ("model", "clip", "lora_text", "preview_image", "preview_base64")
    FUNCTION = "load_lora_and_tags"
    CATEGORY = "LoRA"

    def parse_eagle_memo(self, memo_text, package_name):
        match = re.search(rf"-\s*{re.escape(package_name)}\s*:\s*(.+)", memo_text)
        return match.group(1).strip() if match else ""

    def image_to_base64(self, image):
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def load_lora_and_tags(self, lora_file, strength, tag_source="LoRAinfo", tag_package="default", ngrok_key="home", save_image=False, model=None, clip=None, tags=""):
        lora_root = folder_paths.get_folder_paths("loras")[0]
        lora_path = os.path.join(lora_root, lora_file)
        model, clip = load_lora(lora_path, strength, model, clip)

        if tag_source == "LoRAinfo" and lora_path.endswith(".safetensors"):
            try:
                metadata = load_file(lora_path, metadata_only=True).get("metadata", {})
                tags = metadata.get("ss_tag_frequency", tags)
            except Exception: pass
        elif tag_source == "Eagleinfo":
            try:
                api = EagleAPI(ngrok_key=ngrok_key)
                folder_id = api.get_folder_id("LoRA")
                item_id = api.get_item_id(folder_id, os.path.basename(lora_file))
                memo_text = api.get_memo(item_id)
                tags = self.parse_eagle_memo(memo_text, tag_package) or tags
            except Exception as e:
                print(f"Eagle API error: {e}")

        preview_path = os.path.join(os.path.dirname(lora_path), "preview.png")
        preview_image, preview_base64 = None, ""
        if os.path.exists(preview_path):
            try:
                with Image.open(preview_path) as img:
                    preview_image = img.copy()
                    preview_base64 = self.image_to_base64(preview_image)
            except Exception: pass

        if save_image and preview_image:
            try:
                with open(os.path.join(os.path.dirname(__file__), "config", "config.json"), "r", encoding="utf-8") as f:
                    save_dir = json.load(f).get("saveDirectory", "")
                if save_dir:
                    os.makedirs(save_dir, exist_ok=True)
                    file_name = f"{os.path.splitext(os.path.basename(lora_file))[0]}_{tag_package}.png"
                    preview_image.save(os.path.join(save_dir, file_name))
            except Exception as e:
                print(f"Failed to save image: {e}")

        lora_name = os.path.splitext(os.path.basename(lora_file))[0]
        lora_text = f"<lora:{lora_name}:{strength:.2f}>\n{tags.strip()}"
        return (model, clip, lora_text, preview_image, preview_base64)

NODE_CLASS_MAPPINGS = {
    "LoRA_TagLoader": LoRA_TagLoader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoRA_TagLoader": "LoRA Tag Loader"
}
