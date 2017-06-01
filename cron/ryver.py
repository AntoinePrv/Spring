import requests
import json


class Post(object):

    def __init__(self, url=None):
        if url is None:
            with open("config.json") as f:
                url = json.load(f)["RyverHook"]
        self.url = url

    @property
    def payload(self):
        return {
            "username": self.author,
            "icon_url": self.author_image,
            "text":     self.text
        }

    def send(self):
        requests.post(self.url, json=self.payload)
