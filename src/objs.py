import json
from os import path

import telebot

from models import dbQuery
from seedrcc import Login, Seedr

config = json.load(open('src/config.json'))
language = json.load(open(config['language']))
dbSql = dbQuery(config['database'], config['magnetDatabase'])
bot = telebot.TeleBot(config['botToken'], parse_mode='HTML')
botUsername = bot.get_me().username

# ----------------- CHANNEL CHECK LOGIC START -----------------

REQUIRED_CHANNEL_ID = config.get('requiredChannelId')

def is_user_member(userId):
    if not REQUIRED_CHANNEL_ID:
        return True
    
    try:
        member_status = bot.get_chat_member(REQUIRED_CHANNEL_ID, userId).status
        return member_status in ['member', 'creator', 'administrator']
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        return False

# 🛑 நீக்கப்பட்டது: @bot.callback_query_handler ஃபங்ஷன் நீக்கப்பட்டது.
# இப்போது பட்டன் கிளிக்குகள் சரியாக மற்ற கமாண்ட்களுக்குச் செல்லும்.


# மெசேஜ்களைப் பெறுவதற்கு முன்பு சரிபார்க்கும் லாஜிக்
@bot.message_handler(func=lambda message: True)
def channel_membership_check(message):
    userId = message.from_user.id
    
    # சேனல் செக் ஆன் செய்யப்பட்டால்
    if REQUIRED_CHANNEL_ID:
        if not is_user_member(userId):
            # ... (ACCESS DENIED MESSAGE LOGIC REMAINS THE SAME) ...
            try:
                invite_link = bot.export_chat_invite_link(REQUIRED_CHANNEL_ID)
            except Exception:
                invite_link = "Unable to get Invite Link. Contact Admin."

            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(text="👉 Join Our Channel! 👈", url=invite_link))
            
            bot.send_message(
                message.chat.id,
                f"🚨 **ACCESS DENIED!**\n\n**You must join our official Telegram Channel first BEFORE you can use this bot.**\n\nPlease click the button below to join the channel and regain access.",
                reply_markup=markup,
                parse_mode='Markdown'
            )
            return

    # பயனர் உறுப்பினராக இருந்தால், மெசேஜை மற்ற கமாண்ட் ஹேண்ட்லர்களுக்கு அனுப்ப அனுமதிக்கிறது.
    bot.process_new_messages([message])
    
# ----------------- CHANNEL CHECK LOGIC END -----------------
