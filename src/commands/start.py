import json
import asyncio
import requests
import telebot
from src.objs import *
from src.commands.addTorrent import addTorrent
from src.functions.keyboard import mainReplyKeyboard, githubAuthKeyboard

# 👇👇👇 உங்கள் சேனல் ஐடியை இங்கே போடவும் 👇👇👇
REQUIRED_CHANNEL = "-100XXXXXXXXXX" 
# 👆👆👆 (எ.கா: -1001234567890)

# ==========================================
# 🕵️ பிழை கண்டுபிடிக்கும் சேனல் செக்கர் (Debug Mode)
# ==========================================
def check_join_status(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # 1. ஐடி செக்
    if REQUIRED_CHANNEL == "-100XXXXXXXXXX":
        bot.send_message(chat_id, "⚠️ **Config Error:** சேனல் ஐடி மாற்றப்படவில்லை!")
        return True # உள்ளே அனுமதி
        
    try:
        # 2. மெம்பர்ஷிப் செக்
        chat_member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        status = chat_member.status
        
        # டிலிங் (Debugging) மெசேஜ் - இதை நீங்கள் ஸ்கிரீனில் பார்ப்பீர்கள்
        # bot.send_message(chat_id, f"🔍 **Debug Info:**\nUser Status: `{status}`", parse_mode='Markdown')

        if status in ['creator', 'administrator', 'member']:
            return True
        else:
            # மெம்பர் இல்லை என்றால்
            try:
                invite_link = bot.export_chat_invite_link(REQUIRED_CHANNEL)
            except Exception as e:
                bot.send_message(chat_id, f"⚠️ **Link Error:** பாட் சேனலில் அட்மினாக இல்லை!\nError: {e}")
                return False

            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(text="👉 Join Our Channel 👈", url=invite_link))
            markup.add(telebot.types.InlineKeyboardButton(text="✅ I Joined", callback_data="check_join_status"))
            
            bot.send_message(
                chat_id,
                "⚠️ **Access Denied!**\n\nTo use this bot, you must join our official channel first.",
                parse_mode='Markdown',
                reply_markup=markup
            )
            return False

    except Exception as e:
        # 🛑 உண்மையான பிரச்சனை இங்கே தெரியும்
        bot.send_message(chat_id, f"❌ **SYSTEM ERROR:**\n\n{e}\n\n(சேனல் ஐடி சரியா? பாட் அட்மினா?)")
        return False

# ==========================================
# ▶️ START கமாண்ட்
# ==========================================
@bot.message_handler(commands=['start'])
def start(message):
    # 🛑 செக்கிங் நடக்கிறது
    if not check_join_status(message):
        return
    # --------------------------------

    userId = message.from_user.id
    params = message.text.split()[1] if len(message.text.split()) > 1 else None

    userLanguage = dbSql.getSetting(userId, 'language')

    if not params:
        bot.send_message(message.chat.id, text=language['greet'][userLanguage], reply_markup=mainReplyKeyboard(userId, userLanguage))

    #! If start paramater is passed
    if params:
        sent = bot.send_message(message.chat.id, text=language['processing'][userLanguage])

        #! If add torrent paramater is passed via database key
        if params.startswith('addTorrent'):
            hash = params.split('_')[1]
            magnet = f"magnet:?xt=urn:btih:{hash}"

            asyncio.run(addTorrent(message, userLanguage, magnet, messageId=sent.id))

        #! If add torrent paramater is passed via URL
        elif params.startswith('addTorrentURL'):
            url = f'https://is.gd/{params[14:]}'
            response = requests.get(url, allow_redirects=False)
            magnetLink = response.headers['Location'] if 'Location' in response.headers else None

            asyncio.run(addTorrent(message, userLanguage, magnetLink, messageId=sent.id))

        #! Github oauth
        elif params.startswith('oauth'):
            code = params[6:]
            params = {'client_id': 'ba5e2296f2bbe59f5097', 'client_secret': config['githubSecret'], 'code':code}
            response = requests.get('https://github.com/login/oauth/access_token', params=params)

            if response.text[:13] == 'access_token=':
                accessToken = response.text[13:].split('&', 1)[0]
                headers = {'Authorization': f'token {accessToken}'}
                response = requests.get('https://api.github.com/user', headers=headers).json()

                if 'login' in response:
                    bot.edit_message_text(language['loggedInAs'][userLanguage].format(f"<a href='https://github.com/{response['login']}'>{response['login'].capitalize()}</a>"), chat_id=sent.chat.id, message_id=sent.id)
                    following = requests.get(f"https://api.github.com/users/{response['login']}/following").json()

                    if any(dicT['login'] == 'hemantapkh' for dicT in following):
                        dbSql.setSetting(userId, 'githubId', response['id'])
                        bot.send_message(chat_id=message.chat.id, text=language['thanksGithub'][userLanguage])
                    else:
                        bot.send_message(chat_id=message.chat.id, text=language['ghNotFollowed'][userLanguage], reply_markup=githubAuthKeyboard(userLanguage))
            else:
                bot.edit_message_text(language['processFailed'][userLanguage], chat_id=sent.chat.id, message_id=sent.id)

        else:
            data = requests.get(f"https://hemantapokharel.com.np/seedr/getdata?key={config['databaseKey']}&id={params}")
            data = json.loads(data.content)

            if data['status'] == 'success':
                data = json.loads(data['data'])
                login(sent, userLanguage, data)
            else:
                bot.edit_message_text(language['processFailed'][userLanguage], chat_id=sent.chat.id, message_id=sent.id)

#: Account login func
def login(sent, userLanguage, data):
    userId = sent.chat.id
    ac = dbSql.getDefaultAc(userId)

    if ac and ac['password']:
        data = {
            'username': ac['email'] or ac['userName'],
            'password': ac['password'],
            'rememberme': 'on',
            'g-recaptcha-response': data['captchaResponse'],
            'h-captcha-response': data['captchaResponse']
        }
        response = requests.post('https://www.seedr.cc/auth/login', data=data)
        cookies = requests.utils.dict_from_cookiejar(response.cookies)
        response = response.json()

        if cookies:
            dbSql.updateAcColumn(userId, response['user_id'], 'cookie', json.dumps(cookies))
            bot.delete_message(sent.chat.id, sent.id)
            bot.send_message(chat_id=sent.chat.id, text=language['loggedInAs'][userLanguage].format(response['username']), reply_markup=mainReplyKeyboard(userId, userLanguage))
        else:
            if response['reason_phrase'] in ['RECAPTCHA_UNSOLVED', 'RECAPTCHA_FAILED']:
                bot.edit_message_text(language['captchaFailled'][userLanguage], chat_id=sent.chat.id, message_id=sent.id)
            elif response['reason_phrase'] == 'INCORRECT_PASSWORD':
                bot.edit_message_text(language['incorrectDbPassword'][userLanguage], chat_id=sent.chat.id, message_id=sent.id)
            else:
                bot.edit_message_text(language['unknownError'][userLanguage], chat_id=sent.chat.id, message_id=sent.id)

# "I Joined" பட்டனுக்கான ஹேண்ட்லர்
@bot.callback_query_handler(func=lambda call: call.data == "check_join_status")
def check_join_btn(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    # பட்டன் அழுத்தியதும் மீண்டும் செக் பண்ணும்
    if check_join_status(call.message): # Re-using the check function
        bot.delete_message(chat_id, call.message.message_id)
        # வெல்கம் மெசேஜ் அனுப்புதல்
        userLanguage = dbSql.getSetting(user_id, 'language')
        bot.send_message(chat_id, text=language['greet'][userLanguage], reply_markup=mainReplyKeyboard(user_id, userLanguage))
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined yet!", show_alert=True)

