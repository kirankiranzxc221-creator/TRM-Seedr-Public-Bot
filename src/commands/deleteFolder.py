from src.objs import *
from src.functions.floodControl import floodControl
from src.functions.exceptions import exceptions, noAccount


#: Delete folder (அசல் லாஜிக் - User Logic applied)
@bot.message_handler(func=lambda message: message.text and message.text[:8] == '/delete_')
def deleteFolder(message, called=False):
    userId = message.from_user.id
    userLanguage = dbSql.getSetting(userId, 'language')

    if floodControl(message, userLanguage):
        # 🟢 அட்மின் லாக் நீக்கம்: யூசர் லாஜிக் சேர்க்கப்பட்டது
        ac = dbSql.getDefaultAc(userId)

        #! If user has an account
        if ac:
            account = Seedr(
                token=ac['token'],
                callbackFunc=lambda token: dbSql.updateAccount(
                    token, userId, ac['accountId']
                )
            )

            id = message.data[7:] if called else message.text[8:]
            response = account.deleteFolder(id)

            if 'error' not in response:
                #! If folder is deleted successfully
                if response['result'] == True:
                    if called:
                        bot.answer_callback_query(message.id)
                        bot.edit_message_text(text=language['deletedSuccessfully'][userLanguage], chat_id=message.message.chat.id, message_id=message.message.id)
                    else:
                        bot.send_message(message.chat.id, language['deletedSuccessfully'][userLanguage])

            else:
                exceptions(message, response, ac, userLanguage, called=called)

        #! If no accounts
        else:
            noAccount(message, userLanguage)


# --- ADDED FEATURE: DELETE ALL FUNCTIONS ---

# 1. DELETE ALL CONFIRMATION HANDLER (Yes/No Buttons)
@bot.callback_query_handler(func=lambda call: call.data == 'deleteAllConfirm')
def deleteAllConfirm(call):
    userId = call.from_user.id
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(text="❌ Yes, Delete Everything", callback_data='deleteAllExecute'),
        telebot.types.InlineKeyboardButton(text="✅ Cancel", callback_data='cancel')
    )
    
    warning_text = (
        "🚨 **WARNING!** Are you sure you want to delete ALL files and folders "
        "from your Seedr account? This cannot be undone."
    )
    bot.edit_message_text(
        warning_text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.answer_callback_query(call.id)


# 2. DELETE ALL EXECUTION HANDLER (Actual Deletion)
@bot.callback_query_handler(func=lambda call: call.data == 'deleteAllExecute')
def deleteAllExecute(call):
    userId = call.from_user.id
    userLanguage = dbSql.getSetting(userId, 'language')
    
    # 🟢 அட்மின் லாக் நீக்கம்: யூசர் லாஜிக் சேர்க்கப்பட்டது
    ac = dbSql.getDefaultAc(userId) 

    if not ac:
        noAccount(call, userLanguage, called=True)
        return

    bot.edit_message_text(
        "⏳ Deleting all contents... This may take a moment.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id
    )

    account = Seedr(token=ac['token'], callbackFunc=lambda token: dbSql.updateAccount(token, userId, ac['accountId']))
    
    response = account.listContents()
    
    # பிழைகளைக் கையாளுகிறது
    if 'error' in response:
        exceptions(call, response, ac, userLanguage, called=True)
        return

    deleted_count = 0
    
    # 1. அனைத்து கோப்புறைகளையும் நீக்குதல்
    if 'folders' in response:
        for folder in response['folders']:
            delete_response = account.deleteFolder(folder['id'])
            if delete_response.get('result') is True:
                deleted_count += 1
    
    # 2. அனைத்து ரூட் ஃபைல்களையும் நீக்குதல்
    if 'files' in response:
        for file in response['files']:
            delete_response = account.deleteFile(file['folder_file_id']) 
            if delete_response.get('result') is True:
                deleted_count += 1

    # இறுதி முடிவு
    if deleted_count > 0:
        final_text = f"✅ Success! **{deleted_count}** files/folders have been deleted from your Seedr account."
    else:
        final_text = "🤷 Nothing found to delete, or deletion failed."

    bot.edit_message_text(
        final_text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=None
    )
    bot.answer_callback_query(call.id, final_text)

