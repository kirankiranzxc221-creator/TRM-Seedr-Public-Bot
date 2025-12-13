from src.objs import *
from src.commands.cancel import cancel
from src.functions.floodControl import floodControl
from src.functions.keyboard import cancelReplyKeyboard, mainReplyKeyboard, yesNoReplyKeyboard

# =========================================================
# 🔒 100% வேலை செய்யும் சேனல் லாக் (Direct ID)
# =========================================================
def check_membership(message):
    
    # 👇👇👇 உங்கள் சேனல் ஐடியை இங்கே மாற்றவும்! (எ.கா: "-10012345678")
    required_channel = "-100xxxxxxxxxxxxx" 
    # 👆👆👆 இந்த இடத்தில் உங்கள் ஐடியை சரியாகப் போடவும் (Quotes குள்ளே)

    try:
        userId = message.from_user.id
        chatId = message.chat.id
        
        # பயனர் சேனலில் உள்ளாரா எனப் பார்க்கிறது
        status = bot.get_chat_member(required_channel, userId).status
        
        # மெம்பர், அட்மின், ஓனர் என்றால் அனுமதி
        if status in ['creator', 'administrator', 'member']:
            return True
        
        # இல்லை என்றால் லாக் போடு
        else:
            try:
                invite_link = bot.export_chat_invite_link(required_channel)
            except:
                # பாட் அட்மின் இல்லை என்றால் லிங்க் வராது
                invite_link = "https://t.me/YourChannelUser" 
            
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
        # ஐடி தப்பு அல்லது பாட் அட்மின் இல்லை என்றால் இந்த எரர் வரும்
        print(f"❌ Channel Check Error: {e}")
        bot.send_message(message.chat.id, f"⚠️ Error in Channel Check: {e}")
        return True # எரர் வந்தால் யூசரைத் தடுக்க வேண்டாம் (தற்காலிகமாக)

# =========================================================


#: Login or signup seedr account
@bot.message_handler(commands=['login'])
def login(message, called=False, userLanguage=None):
    
    # 🛑 லாக்: இங்கே செக் செய்கிறோம்
    if not check_membership(message):
        return
    # --------------------------------

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
