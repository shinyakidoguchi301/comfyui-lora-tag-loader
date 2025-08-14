import os, json, base64
from io import BytesIO
from PIL import Image

class Base64ToImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base64_string": ("STRING", {"multiline": True}),
                "save_image": ("BOOLEAN", {"default": False}),
                "file_name": ("STRING", {"default": "output.png"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "image_path")
    FUNCTION = "decode_image"
    CATEGORY = "Utils"

    def load_config(self):
        try:
            with open(os.path.join(os.path.dirname(__file__), "config", "config.json"), "r", encoding="utf-8") as f:
                return json.load(f).get("saveDirectory", "")
        except Exception as e:
            print(f"設定読み込み失敗: {e}")
            return ""

    def decode_image(self, base64_string, save_image, file_name):
        try:
            image = Image.open(BytesIO(base64.b64decode(base64_string))).convert("RGB")
            image_path = ""
            if save_image:
                save_dir = self.load_config()
                if save_dir:
                    os.makedirs(save_dir, exist_ok=True)
                    image_path = os.path.join(save_dir, file_name)
                    image.save(image_path)
            return (image, image_path)
        except Exception as e:
            print(f"デコード失敗: {e}")
            return (None, "")
