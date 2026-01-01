import ssl
import requests
import validators
import telebot, asyncio
from aiohttp import web
import subprocess
import sys
import os 
import threading 
from http.server import HTTPServer, BaseHTTPRequestHandler 

# 🔹 புதிய மாற்றம்: GitHub Sync Helper-ஐ இம்போர்ட் செய்கிறோம்
try:
    from src.helpers.github_sync import sync_from_github, sync_to_github
except ImportError:
    # ஒருவேளை ஃபைல் இல்லை என்றால் எரர் வராமல் தடுக்க
    def sync_from_github(): pass
    def sync_to_github(): pass

# 🔹 Deploy ஆணவுடன் DB tables create/upgrade ஆக migrations.py run பண்ணுறோம்
subprocess.run([sys.executable, "migrations.py"])

# 🔹 புதிய மாற்றம்: பாட் தொடங்கும் போதே GitHub-ல் இருந்து பழைய DB-ஐ டவுன்லோட் செய்கிறோம்
# இது Render-ல் டேட்டா அழிந்தாலும் மீட்க உதவும்
sync_from_github()

from src import *

# ... (Configuration for webhook மற்றும் Keep-Alive Server அதே கோடிங்) ...

# ... (start_server மற்றும் handle ஃபங்க்ஷன்கள் அதே கோடிங்) ...

async def text(message):
    userLanguage = dbSql.getSetting(message.from_user.id, 'language')

    #! Add accounts
    if message.text == language['addAccountBtn'][userLanguage]:
        addAccount(message, called=False, userLanguage=userLanguage)
        # 🔹 புதிய மாற்றம்: லாகின் முடிந்ததும் புதிய டேட்டாவை GitHub-க்கு சிங்க் செய்கிறோம்
        sync_to_github()

    #! File manager
    elif message.text == language['fileManagerBtn'][userLanguage]:
        files(message, userLanguage)

    # ... (மீதமுள்ள கமாண்டுகள் - எதையும் மாற்றவில்லை) ...

    #! Adding torrent from remote URL
    elif validators.url(message.text):
        await remoteTorrent(message)
        # ஒருவேளை இது டேட்டாவை மாற்றினால் சிங்க் செய்யும்
        sync_to_github()

    #! Adding torrents via magnet link
    elif 'magnet:?' in message.text:
        await asyncio.gather(addTorrent(message, userLanguage, magnetLink=message.text))
        sync_to_github()

    else:
        invalidMagnet(message, userLanguage)

# ... (Text handler, document handler மற்றும் Polling/Webhook செட்டப் அதே கோடிங்) ...

