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

# ----------------- NEW LOGIC START: CHANNEL CHECK -----------------

REQUIRED_CHANNEL_ID = config.get('requiredChannelId')

# தேவைப்படும் சேனலில் பயனர் உறுப்பினராக இருக்கிறாரா என்று சரிபார்க்கும் ஃபங்ஷன்.
def is_user_member(userId):
    # சேனல் ஐடி config-இல் இல்லை என்றால், எந்தச் சரிபார்ப்பும் தேவையில்லை.
    if not REQUIRED_CHANNEL_ID:
        return True
    
    try:
        # பயனர் உறுப்பினர் நிலையைப் பெறுகிறது.
        member_status = bot.get_chat_member(REQUIRED_CHANNEL_ID, userId).status
        
        # 'member', 'creator', 'administrator' ஆகிய நிலைகள் அனுமதிக்கப்படுகின்றன.
        return member_status in ['member', 'creator', 'administrator']
    except Exception as e:
        # பிழை ஏற்பட்டால், அனுமதிக்காமல் இருக்கலாம்.
        print(f"Error checking channel membership: {e}")
        return False

# மெசேஜ்களைப் பெறுவதற்கு முன்பு சரிபார்க்கும் லாஜிக்
@bot.message_handler(func=lambda message: True)
def channel_membership_check(message):
    userId = message.from_user.id
    
    # சேனல் செக் ஆன் செய்யப்பட்டால்
    if REQUIRED_CHANNEL_ID:
        if not is_user_member(userId):
            # பயனர் உறுப்பினராக இல்லை என்றால், இந்த எச்சரிக்கை மெசேஜை அனுப்புகிறது
            
            # Invite Link-ஐ உருவாக்க முயற்சிக்கிறது (பிரைவேட் சேனலுக்கு அவசியம்)
            try:
                invite_link = bot.export_chat_invite_link(REQUIRED_CHANNEL_ID)
            except Exception:
                # பாட் அட்மின் இல்லை என்றால் அல்லது வேறு பிழை என்றால்
                invite_link = "Unable to get Invite Link. Contact Admin."

            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(text="👉 Join Our Channel! 👈", url=invite_link))
            
            # 🟢 நீங்கள் கேட்ட ஆங்கில மெசேஜ் இங்கே:
            bot.send_message(
                message.chat.id,
                f"🚨 **ACCESS DENIED!**\n\n**You must join our official Telegram Channel first BEFORE you can use this bot.**\n\nPlease click the button below to join the channel and regain access.",
                reply_markup=markup,
                parse_mode='Markdown'
            )
            return

    # பயனர் உறுப்பினராக இருந்தால், மெசேஜை மற்ற கமாண்ட் ஹேண்ட்லர்களுக்கு அனுப்ப அனுமதிக்கிறது.
    bot.process_new_messages([message])
    
# ----------------- NEW LOGIC END -----------------

# (நீங்கள் கொடுத்த அசல் கோடிங்கின் மற்ற பகுதிகள், கீழே தொடரும்)
