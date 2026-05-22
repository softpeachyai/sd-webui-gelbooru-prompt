import random
import re
import traceback

import gradio as gr
import contextlib

from modules import script_callbacks, scripts, shared
from modules.shared import opts
import requests
import bs4
from bs4 import BeautifulSoup


def on_ui_settings():
    section = ('gelbooru-prompt', "Gelbooru Prompt")


def fetch(image):
    # update hash based on image
    name = image.name
    if "\\" in name:
        name = name.split("\\")[-1]
    elif "/" in name:
        name = name.split("/")[-1]
    print("name: " + name)
    
    hash = name.split(".")[0]
    if hash.startswith("sample_"):
        hash = hash.replace("sample_", "")
    if hash.startswith("thumbnail_"):
        hash = hash.replace("thumbnail_", "")
    print("hash: " + hash)

    # === ADD YOUR CREDENTIALS HERE ===
    api_key = "YOUR_API_KEY_HERE"
    user_id = "YOUR_USER_ID_HERE"
    # =================================

    url = f"https://gelbooru.com/index.php?page=dapi&s=post&q=index&json=1&tags=md5:{hash}&api_key={api_key}&user_id={user_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
    }
    
    req = requests.get(url, headers=headers)
    print("Status code:", req.status_code)   # ← for debugging
    
    if req.status_code != 200:
        return f"Error: HTTP {req.status_code} from Gelbooru"
    
    try:
        data = req.json()
    except Exception as e:
        print("Raw response:", req.text[:500])  # debug
        return "Failed to parse JSON (possibly blocked or rate limited)"

    if not data or "@attributes" not in data or data["@attributes"].get("count", 0) == 0:
        return "No image found with that hash..."

    post = data["post"][0]
    tags = post["tags"]

    parsed = []
    for tag in tags.split():
        tag = tag.replace("_", " ")
        parsed.append(tag)
    return ", ".join(parsed)


class BooruPromptsScript(scripts.Script):
    def __init__(self) -> None:
        super().__init__()

    def title(self):
        return ("Gelbooru Prompt")

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Group():
            with gr.Accordion("Gelbooru Prompt", open=False):
                fetch_tags = gr.Button(value='Get Tags', variant='primary')
                image = gr.File(type="filepath", label="Image with MD5 Hash")

            with contextlib.suppress(AttributeError):
                if is_img2img:
                    fetch_tags.click(fn=fetch, inputs=[image], outputs=[self.boxxIMG])
                else:
                    fetch_tags.click(fn=fetch, inputs=[image], outputs=[self.boxx])

        return [image, fetch_tags]

    def after_component(self, component, **kwargs):
        if kwargs.get("elem_id") == "txt2img_prompt":
            self.boxx = component
        if kwargs.get("elem_id") == "img2img_prompt":
            self.boxxIMG = component


script_callbacks.on_ui_settings(on_ui_settings)
