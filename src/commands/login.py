from src.objs import *
from src.commands.cancel import cancel
from src.functions.floodControl import floodControl
from src.functions.keyboard import cancelReplyKeyboard, mainReplyKeyboard, yesNoReplyKeyboard

# =========================================================
# 🔒 புதிய லாஜிக்: சேனலில் இணைந்தால் மட்டுமே லாகின் வேலை செய்யும்
# =========================================================
def check_membership(message):
    try:
        # config.json-ல் இருந்து சேனல் ID எடுக்கிறது
        required_channel = config.get('requiredChannelId')
        
        # சேனல் ID இல்லை என்றால், லாக் போடாதே (அனுமதித்துவிடு)
        if not required_channel:
            return True

        userId = message.from_user.id
        chatId = message.chat.id
        
        # டெலிகிராமிடம் பயனர் நிலையைச் சரிபார்க்கிறது
        # (குறிப்பு: பாட் அந்த சேனலில் அட்மினாக இருக்க வேண்டும்)
        status = bot.get_chat_member(required_channel, userId).status
        
        # பயனர் ஏற்கனவே உள்ளாரா?
        if status in ['creator', 'administrator', 'member']:
            return True
        
        # பயனர் இல்லை என்றால், Invite Link எடுத்து அனுப்பு
        else:
            try:
                invite_link = bot.export_chat_invite_link(required_channel)
            except:
                invite_link = "Unable to get link. Make sure Bot is Admin in Channel."
            
            # ஜாயின் பட்டன் உருவாக்கம்
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(text="👉 Join Our Channel! 👈", url=invite_link))
            
            bot.send_message(
                chatId, 
                "🚨 **ACCESS DENIED!**\n\nTo use this bot, you must first **Join our Channel**.\n\n👇 Click the button below to join, then try /login again.", 
                reply_markup=markup, 
                parse_mode='Markdown'
            )
            return False

    except Exception as e:
        print(f"Channel Check Error: {e}")
        return True # பிழை வந்தால் தற்காலிகமாக அனுமதிக்கிறோம்
# =========================================================


#: Login or signup seedr account
@bot.message_handler(commands=['login'])
def login(message, called=False, userLanguage=None):
    
    # 🛑 இங்கே தான் லாக் போடுகிறோம் (சேனலில் இல்லை என்றால் ரிட்டர்ன் ஆகிவிடும்)
    if not check_membership(message):
        return
    # -----------------------------------------------------

    userId = message.from_user.id

    if floodControl(message, userLanguage):
        userLanguage = userLanguage or dbSql.getSetting(userId, 'language')

        if called:
            bot.delete_message(message.message.chat.id, message.message.id)

        sent = bot.send_message(message.from_user.id, language['enterEmail'][userLanguage], reply_markup=cancelReplyKeyboard(userLanguage))

        bot.register_next_step_handler(sent, login2, userLanguage)


def login2(message, userLanguage):
    if message.text == language['cancelBtn'][userLanguage]:
        cancel(message, userLanguage)

    else:
        email = message.text

        sent = bot.send_message(message.from_user.id, language['enterPassword'][userLanguage])

        bot.register_next_step_handler(sent, login3, userLanguage, email)

def login3(message, userLanguage, email):
    if message.text == language['cancelBtn'][userLanguage]:
        cancel(message, userLanguage)

    else:
        password = message.text

        sent = bot.send_message(message.from_user.id, language['storePassword?'][userLanguage], reply_markup=yesNoReplyKeyboard(userLanguage))
        bot.register_next_step_handler(sent, login4, userLanguage, email, password)

def login4(message, userLanguage, email, password):
    if message.text == language['cancelBtn'][userLanguage]:
        cancel(message, userLanguage)

    else:
        storePassword = True if message.text == language['yesBtn'][userLanguage] else False

        seedr = Login(email, password)
        response = seedr.authorize()

        if seedr.token:
            ac = Seedr(
                    token = seedr.token,
                    callbackFunc = lambda token: dbSql.updateAccount(
                        token, message.from_user.id, ac['accountId']
                    )
            )
            acSettings = ac.getSettings()

            dbSql.setAccount(
                userId=message.from_user.id,
                accountId=acSettings['account']['user_id'],
                userName=acSettings['account']['username'],
                token=seedr.token,
                isPremium=acSettings['account']['premium'],
                invitesRemaining=acSettings['account']['invites'],
                email=acSettings['account']['email'],
                password=password if storePassword else None
            )

            bot.send_message(message.chat.id, language['loggedInAs'][userLanguage].format(acSettings['account']['username']), reply_markup=mainReplyKeyboard(message.from_user.id, userLanguage))

        elif response['error'] == 'invalid_grant':
            bot.send_message(message.chat.id, language['incorrectPassword'][userLanguage], reply_markup=mainReplyKeyboard(message.from_user.id, userLanguage))

        else:
            bot.send_message(message.chat.id, language['somethingWrong'][userLanguage], mainReplyKeyboard(message.from_user.id, userLanguage))

