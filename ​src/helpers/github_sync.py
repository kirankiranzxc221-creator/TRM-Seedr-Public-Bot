import os
import requests
import base64

GH_TOKEN = os.environ.get('GH_TOKEN')
GH_REPO = os.environ.get('GH_REPO')
DB_FILE = "seedrBot.db"

# 1. GitHub-ல் இருந்து டேட்டாவை மீட்டெடுத்தல்
def sync_from_github():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{DB_FILE}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()['content'])
        with open(DB_FILE, 'wb') as f:
            f.write(content)
        print("பழைய டேட்டா GitHub-ல் இருந்து மீட்டெடுக்கப்பட்டது! ✅")

# 2. மாற்றங்களை GitHub-க்கு அனுப்புதல்
def sync_to_github():
    url = f"https://api.github.com/repos/{GH_REPO}/contents/{DB_FILE}"
    headers = {"Authorization": f"token {GH_TOKEN}"}
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None

    with open(DB_FILE, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    data = {"message": "Auto-sync DB", "content": content, "sha": sha}
    requests.put(url, json=data, headers=headers)
    print("டேட்டாபேஸ் GitHub-ல் பாதுகாப்பாகச் சேமிக்கப்பட்டது! 🚀")
