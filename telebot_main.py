import random
from typing import Final
from telebot import types
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

Token: Final = "6774761124:AAEBNfmTgmcJ6wbtL1zZKGAV0_xjifDmNfE"
BOT_USERNAME: Final = "@panhathun_bot"

# Command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command, presenting an outline keyboard."""

    # Construct your keyboard outline
    keyboard = [
      # Replace with the list of extracted titles
        ["Video","Image", "Document", "Audio"]
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)

    await update.message.reply_text(
        "Please select an area of interest:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I'm Thun Bot, here to assist you. You can ask me anything or use the available commands.")

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("You can contact me via:\n" \
                                   "Facebook: https://www.facebook.com/profile.php?id=100026153991813&mibextid=9R9pXO\n" \
                                    "Instagram: https://www.instagram.com/thun_nani?igsh=MTN4dmZ6cXkxM2EzMA==\n" \
                                    "Telegram: t.me/nhacool\n" \
                                    "Linkin: https://www.linkedin.com/in/duch-panhathun-406336235?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app\n" \
                                    "Email: duchpanhathun@gmail.com")
async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    markup = types.InlineKeyboardMarkup(row_width=2)

    iron = types.InlineKeyboardButton('1 Kilo of iron', callback_data='answer_iron')
    cotton = types.InlineKeyboardButton('1 Kilo of cotoon', callback_data='answer_cotoon')
    same = types.InlineKeyboardButton('1 Kilo of same', callback_data='answer_same')
    no_answer = types.InlineKeyboardButton('No answer', callback_data='answer_no')

    markup.add(iron, cotton, same, no_answer)

    # Convert InlineKeyboardMarkup to its dictionary representation
    markup_dict = markup.to_dict()

    # Send the message with inline keyboard markup
    await context.bot.send_message(chat_id=update.effective_chat.id, text='What is the hi?', reply_markup=markup_dict)

# Callback handler for answer
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await answer(update, context)

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == 'answer_same':
        await context.bot.send_message(chat_id=query.message.chat_id, text="Congratulations!")
    else:
        await context.bot.send_message(chat_id=query.message.chat_id, text="Try Again...")

    # Edit the original message to remove the inline keyboard markup
    await query.message.edit_reply_markup(reply_markup=None)


# Message
async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    processed_text: str = text.lower()

    greetings = ['hello', 'hi', 'hey', 'greetings']
    goodbyes = ['bye', 'goodbye', 'farewell', 'see you later']
    questions = ['how are you', 'what are you doing', 'how is your day']
    compliments = ['you are awesome', 'great job', 'well done']
    gratitude = ['thank you', 'thanks', 'appreciate it']
    apologies = ['sorry', 'my apologies', 'excuse me']
    affirmatives = ['yes', 'yeah', 'sure', 'absolutely']
    negatives = ['no', 'not really', 'nevermind']
    requests = ['please', 'can you', 'could you', 'help me with']
    jokes = ['tell me a joke', 'make me laugh', 'joke time']

    for greeting in greetings:
        if greeting in processed_text:
            return "Hello! How can I assist you today?"

    for goodbye in goodbyes:
        if goodbye in processed_text:
            return "Goodbye! Take care."

    for question in questions:
        if question in processed_text:
            return "I'm just a computer program, but thanks for asking! How can I help you?"

    for compliment in compliments:
        if compliment in processed_text:
            return "Thank you! I'm here to assist you. What can I do for you?"

    for thank_you in gratitude:
        if thank_you in processed_text:
            return "You're welcome! If you have any more questions, feel free to ask."

    for apology in apologies:
        if apology in processed_text:
            return "No need to apologize! How can I assist you?"

    for affirmative in affirmatives:
        if affirmative in processed_text:
            return "Great! What can I do for you?"

    for negative in negatives:
        if negative in processed_text:
            return "I see. If you change your mind, feel free to ask anything."

    for request in requests:
        if request in processed_text:
            return "Certainly! I'll do my best to help. What do you need assistance with?"

    for joke in jokes:
        if joke in processed_text:
            return "Why did the computer go to therapy? It had too many bytes of emotional baggage!"

    return "Sorry, I don't understand what you mean."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text.lower()

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
    response = await handle_response(update, context, text)
    if response:  # Only send if handle_response returned a response text
        await update.message.reply_text(response)
    if message_type in ['group', 'private'] and BOT_USERNAME in text:
        await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

# Main

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(Token).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))  # Corrected command name
    app.add_handler(CommandHandler('quiz', quiz_command))

    # Callback query handler
    app.add_handler(CallbackQueryHandler(callback_handler))
    # Messages
    text_filter = filters.Text and ~filters.COMMAND
    app.add_handler(MessageHandler(text_filter, handle_message))

    # Error
    print("Polling...")
    app.add_error_handler(error)

    app.run_polling(poll_interval=5)