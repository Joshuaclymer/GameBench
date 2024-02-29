import importlib
import os
import json
from PIL import Image
from io import BytesIO
import base64
import re

def save_json(data, file_path):
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def load_json(file_path):
    if not os.path.exists(file_path):
        raise ValueError(f"File {file_path} does not exist")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def import_class(class_path):
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

def base64_encode_image(image: Image) -> str:
    img_buffer = BytesIO()
    image.save(img_buffer, format="PNG")
    img_str = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    return img_str

def extract_json(input: str) -> dict:
    json_match = re.search(r'{.*}', input, re.DOTALL)
    if json_match == None:
        raise ValueError(f"Could not find JSON in input: {input}")
    json_content = json_match.group(0)
    return json_content
    # Parse the JSON content into a Python dictionary
    response_data = json.loads(json_content)
    return response_data