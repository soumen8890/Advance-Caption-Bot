from os import environ, getenv
import re
import os

id_pattern = re.compile(r"^.\d+$")


def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default


ADMIN = int(getenv("ADMIN", "6964203412 6233910543"))
SILICON_PIC = os.environ.get("SILICON_PIC", "https://telegra.ph/file/21a8e96b45cd6ac4d3da6.jpg")
API_ID = int(getenv("API_ID", ""))
API_HASH = str(getenv("API_HASH", "5e7701953107a273724b07f2beaf8f17"))
BOT_TOKEN = str(getenv("BOT_TOKEN", ""))
FORCE_SUB = os.environ.get("FORCE_SUB", "") 
MONGO_DB = str(getenv("MONGO_DB", "mongodb+srv://loheda1869:biui1nVXUtJhj2UJ@cluster0.dax5m4o.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",))
DEF_CAP = str(
    getenv(
        "DEF_CAP",
        "<b>File Name:- `{file_name}`\n\n{file_size}</b>",
    )
)
