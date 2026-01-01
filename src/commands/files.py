from src.objs import *
from src.functions.floodControl import floodControl
from src.functions.convert import convertSize
from src.functions.exceptions import exceptions, noAccount

#: File manager
@bot.message_handler(commands=['files'])
def files(message, userLanguage=None):
    userId = message.from_user.id
    userLanguage = userLanguage or dbSql.getSetting(userId, 'language')

    if floodControl(message, userLanguage):
        # 🟢 User Logic: அட்மின் ஐடி இல்லாமல், யூசரின் ஐடியை வைத்து அக்கவுண்ட் எடுக்கப்படுகிறது.
        ac = dbSql.getDefaultAc(userId)

        #! If user has an account
        if ac:
            account = Seedr(
                token=ac['token'],
                callbackFunc=lambda token: dbSql.updateAccount(
                    token, userId, ac['accountId']
                )
            )

            response = account.listContents()

            if 'error' not in response:
                text = ''
                has_content = False

                #! If user has folders
                if response['folders']:
                    has_content = True
                    for i in response['folders']:
                        text += f"<b>📂 {i['fullname']}</b>\n\n💾 {convertSize(i['size'])}B, ⏰ {i['last_update']}"
                        text += f"\n\n{language['files'][userLanguage]} /getFiles_{i['id']}\n{language['link'][userLanguage]} /getLink_{i['id']}\n{language['delete'][userLanguage]} /delete_{i['id']}\n\n"

                #! Root files
                if response.get('files'):
                    has_content = True
                    for f in response['files']:
                        text += f"<b>📄 {f['name']}</b>\n\n💾 {convertSize(f['size'])}B, ⏰ {f['last_update']}"
                        text += f"\n\n{language['link'][userLanguage]} /fileLink_{f['folder_file_id']}\n{language['delete'][userLanguage]} /deleteFile_{f['folder_file_id']}\n\n"
                
                #! If user has files or folders
                if has_content:
                    # 🟢 உங்கள் பாட் பெயர் (Branding) இங்கே சேர்க்கப்பட்டுள்ளது
                    text += f"\n🔥 via @TRM_bot_All"

                    # Send the file list first
                    bot.send_message(message.chat.id, text[:4000])

                    # --- Delete All Button Section ---
                    delete_all_markup = telebot.types.InlineKeyboardMarkup()
                    delete_all_btn = telebot.types.InlineKeyboardButton(
                        text='⚠️ DELETE ALL FILES', 
                        callback_data='deleteAllConfirm' 
                    )
                    delete_all_markup.add(delete_all_btn)
                    
                    bot.send_message(
                        message.chat.id, 
                        "--- File Operations ---",
                        reply_markup=delete_all_markup
                    )
                    # ---------------------------------
                
                #! If user has no files
                else:
                    bot.send_message(message.chat.id, language['noFiles'][userLanguage])

            else:
                exceptions(message, response, ac, userLanguage, called=False) 

        #! If no accounts (User hasn't logged in)
        else:
            noAccount(message, userLanguage)

