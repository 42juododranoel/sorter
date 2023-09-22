import re
import os
import sys
import shutil
from pathlib import Path
from collections import defaultdict

# import enchant
# dictionary = enchant.Dict("en_US")

MARK_VK = "vk"
MARK_TWITTER = "twitter"
MARK_TELEGRAM = "telegram"
MARK_PINTEREST = "pinterest"
MARK_CAMERA = "camera"
MARK_ARCHIVE = "archives"
MARK_DOCUMENT = "documents"
MARK_SCREENSHOT = "screenshots"
MARK_TECH = "tech"
MARK_TORRENT = "torrent"

MARK_DANBOORU = "danbooru"
TOKEN_DANBOORU_ARTIST = "danbooru:artist"
TOKEN_DANBOORU_LETTER = "danbooru:letter"

TOKEN_VALUE_UNKNOWN = "unknown"

MARK_UNMARKED = "unmarked"
MARKS = [
    MARK_DANBOORU,
]


class Item:
    def __init__(self, item, parent):
        self.item = item
        self.parent = parent
        self.marks, self.tokens = self.load()
    
    def __repr__(self):
        return self.item

    def load(self):
        marks = []
        tokens = {}

        _, _, extension = self.item.rpartition(".")

        # Extensions
        if extension in ["zip", "tgz"] or self.item.endswith(".tar.xz"):
            mark = MARK_ARCHIVE
        elif extension.lower() in ["doc", "docx", "pdf"]:
            mark = MARK_DOCUMENT
        elif extension.lower() in ["json", "sql", "sh", "py"]:
            mark = MARK_TECH
        elif extension.lower() in ["torrent"]:
            mark = MARK_TORRENT
        # Special
        elif "_drawn_by_" in self.item or "__sample-" in self.item:
            mark = MARK_DANBOORU
            # danbooru_tokens = self.load_danbooru_tokens()
            # tokens.update(danbooru_tokens)
        # OS files
        elif self.item.startswith("photo_"):
            mark = MARK_TELEGRAM
        elif self.item.startswith("IMG_") and extension.lower() == "jpg":
            mark = MARK_CAMERA
        elif self.item.startswith("Screenshot") or self.item.startswith("Снимок экрана"):
            mark = MARK_SCREENSHOT
        # Hashes
        elif len(self.item) == 15 and extension == "jpg":
            mark = MARK_VK
        elif len(self.item) == 20 and extension == "jpeg":
            mark = MARK_TWITTER
        elif len(self.item) == 36 and extension == "jpg":
            mark = MARK_PINTEREST
        else:
            mark = MARK_UNMARKED

        marks.append(mark)

        return marks, tokens

    def load_danbooru_tokens(self):
        tokens = {}
        
        artist = re.findall(".*_drawn_by_(.*)__.*", self.item)
        artist_value = TOKEN_VALUE_UNKNOWN
        if artist:
            artist_value = artist[0]
        tokens[TOKEN_DANBOORU_ARTIST] = artist_value

        letter = re.findall("^([a-z0-9])", artist_value)
        letter_value = TOKEN_VALUE_UNKNOWN
        if letter:
            letter_value = letter[0]
        tokens[TOKEN_DANBOORU_LETTER] = letter_value

        return tokens

    def move(self, target):
        shutil.move(self.parent / self.item, target / self.item)


class Manager:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.items = self.load()
        self.map = self.reverse()

    def load(self):
        return [
            Item(item, self.directory) 
            for item in os.listdir(self.directory) 
            if os.path.isfile(self.directory / item)
        ]
    
    def reverse(self):
        map = defaultdict(list)

        for item in self.items:
            for mark in item.marks:
                map[mark].append(item)
            
            for token_name, token_value in item.tokens.items():
                map[f"{token_name}:{token_value}"].append(item)
        
        return map

    def show(self):
        for mark in self.map:
            print(f"{mark}: {len(self.map[mark])}")        
        print(f"---\ntotal: {len(self.items)}")


class Outputer:
    def __init__(self, directory):
        self.directory = Path(directory)

    def output(self, manager, mark):
        print(mark)
        final_directory = self.directory
        for nested_directory in mark.split("__"):
            final_directory /= nested_directory
            if not final_directory.exists():
                os.makedirs(final_directory)

        for item in manager.map[mark]:
            print("  ", item)
            item.move(final_directory)


if __name__ == "__main__":
    source_directory = sys.argv[1]
    target_directory = source_directory

    manager = Manager(source_directory)    
    manager.reverse()
    manager.show()

    outputer = Outputer(target_directory)
    for mark in [mark for mark in manager.map.keys() if mark != MARK_UNMARKED]:
        outputer.output(manager, mark=mark)
