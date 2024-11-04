import os
import requests
import asyncio
from typing import Final
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import json


class CarepBot:
    Token: Final = "6774761124:AAEBNfmTgmcJ6wbtL1zZKGAV0_xjifDmNfE"
    BOT_USERNAME: Final = "@panhathun_bot"
    FLASK_API_URL = "http://127.0.0.1:5000/upload"

    def __init__(self):
        self.app = Application.builder().token(self.Token).build()
        self.setup_handlers()

        # Create a directory to save images
        if not os.path.exists("images"):
            os.makedirs("images")

    def setup_handlers(self):
        # Commands
        self.app.add_handler(CommandHandler('start', self.start_command))
        self.app.add_handler(CommandHandler('help', self.help_command))
        self.app.add_handler(CommandHandler('custom', self.custom_command))
        self.app.add_handler(CommandHandler('quiz', self.quiz_command))
        self.app.add_handler(CommandHandler("result", self.get_result))
        
        # Callback query handler
        self.app.add_handler(CallbackQueryHandler(self.callback_handler))

        # Messages
        text_filter = filters.TEXT & ~filters.COMMAND
        self.app.add_handler(MessageHandler(text_filter, self.handle_message))

        # Add the photo handler
        self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))

        # Error handler
        self.app.add_error_handler(self.error)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyboard = [
            ["Video", "Image", "Document", "Audio"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)

        await update.message.reply_text(
            "Welcome! Please select an area of interest or send me an image and I will save it.",
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("I'm Thun Bot, here to assist you. You can ask me anything or use the available commands.")

    async def custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("You can contact me via: Telegram: t.me/nhacool")

    async def quiz_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton('1 Kilo of iron', callback_data='answer_iron'),
             InlineKeyboardButton('1 Kilo of cotton', callback_data='answer_cotton')],
            [InlineKeyboardButton('1 Kilo of same', callback_data='answer_same'),
             InlineKeyboardButton('No answer', callback_data='answer_no')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text('What is the heaviest?', reply_markup=reply_markup)

    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == 'answer_same':
            await query.edit_message_text(text="Congratulations!")
        else:
            await query.edit_message_text(text="Try Again...")

        await query.message.edit_reply_markup(reply_markup=None)

    async def handle_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        processed_text: str = text.lower()

        greetings = ['hello', 'hi', 'hey', 'greetings']

        for greeting in greetings:
            if greeting in processed_text:
                return "Hello! How can I assist you today?"

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message_type: str = update.message.chat.type
        text: str = update.message.text.lower()

        print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
        response = await self.handle_response(update, context, text)
        if response:
            await update.message.reply_text(response)
        if message_type in ['group', 'private'] and self.BOT_USERNAME in text:
            await update.message.reply_text(response)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print("Handling photo...")
        if not update.message.photo:
            await update.message.reply_text("Please send an image.")
            return

        file = await context.bot.get_file(update.message.photo[-1].file_id)
        file_path = f"images/{file.file_id}.jpg"
        await file.download_to_drive(file_path)

        await update.message.reply_text(f"Image saved successfully with ID: {file.file_id}")
        await update.message.reply_text("Your image has been received and is being processed. Please wait...")

        try:
            with open(file_path, 'rb') as image_file:
                files = {'file': ('image.jpg', image_file, 'image/jpeg')}
                response = requests.post(self.FLASK_API_URL, files=files)

            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.content}")

            if response.status_code == 200:
                response_json = response.json()
                image_id = response_json.get('image_id')
                if not image_id:
                    await update.message.reply_text("Error: No image ID received from the server.")
                    return
                await update.message.reply_text(f"Your image has been successfully uploaded with ID: {image_id}. Processing...")

                result = await self.get_processing_results(image_id)

                if result:
                    if isinstance(result, dict):
                        disease = result.get('predicted_disease', 'Unknown')
                        confidence = result.get('confidence', 'N/A')
                        details = result.get('details', {})
                        disease_km = details.get('disease_km', 'Unknown')
                        cure = details.get('cure', 'Not provided')
                        symptoms = details.get('symtom', 'Not provided')
                        reference = details.get('reference', 'Not provided')
                        await update.message.reply_text(
                            f"Plant detection result:\n"
                            f"Predicted Disease: {disease}\n"
                            f"Confidence: {confidence:.2f}\n"
                            f"Disease (Khmer): {disease_km}\n"
                            f"Cure: {cure}\n"
                            f"Symptoms: {symptoms}\n"
                            f"Reference: {reference}"
                        )
                    elif isinstance(result, str):
                        await update.message.reply_text(f"Error: {result}")
                    else:
                        await update.message.reply_text("Processing complete, but no specific result was returned.")
                else:
                    await update.message.reply_text("No result received from the server after multiple attempts.")
            else:
                await update.message.reply_text(f"There was an error uploading your image. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            await update.message.reply_text(f"An error occurred while processing your image: {str(e)}")
        finally:
            # Clean up by deleting the local file
            if os.path.exists(file_path):
                os.remove(file_path)

    async def get_processing_results(self, image_id):
        max_retries = 10
        retry_delay = 2  # seconds
        result_url = f"{self.FLASK_API_URL.rsplit('/', 1)[0]}/result/{image_id}"

        for _ in range(max_retries):
            try:
                response = requests.get(result_url)
                print(f"Response status code: {response.status_code}")
                print(f"Response content: {response.content}")
                
                if response.status_code == 200:
                    if response.content:
                        result = response.json()
                        if result.get('status') == 'completed':
                            return result['result']
                        elif result.get('status') == 'error':
                            return f"Error: {result.get('message', 'Unknown error')}"
                    else:
                        print("Empty response received")
                elif response.status_code == 404:
                    return "Image not found"
                await asyncio.sleep(retry_delay)
            except Exception as e:
                print(f"Error retrieving results: {str(e)}")
                await asyncio.sleep(retry_delay)

        return "No result received from the server after multiple attempts"

    async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f'Update {update} caused error {context.error}')

    async def get_result(self, update: Update, context):
        if len(context.args) == 0:
            await update.message.reply_text("Please provide an image ID. Usage: /result <image_id>")
            return

        image_id = context.args[0]
        result_url = f"{self.FLASK_API_URL.rsplit('/', 1)[0]}/result/{image_id}"
        
        try:
            response = requests.get(result_url)
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.content}")
            
            if response.status_code == 200:
                if response.content:
                    # Decode the JSON response content with unicode escape
                    result = json.loads(response.content.decode('unicode_escape'))
                    
                    status = result.get('status', 'Unknown')
                    if status == 'completed':
                        predicted_disease = result['result']['predicted_disease']
                        confidence = result['result']['confidence']
                        details = result['result']['details']
                        await update.message.reply_text(
                            f"Image ID: {image_id}\n"
                            f"Status: {status}\n"
                            f"Predicted Disease: {predicted_disease}\n"
                            f"Confidence: {confidence:.2f}\n"
                            f"Disease (Khmer): {details.get('disease_km', 'N/A')}\n"
                            f"Cure: {details.get('cure', 'N/A')}\n"
                            f"Symptoms: {details.get('symtom', 'N/A')}\n"
                            f"Reference: {details.get('reference', 'N/A')}"
                        )
                    else:
                        await update.message.reply_text(f"Image ID: {image_id}\nStatus: {status}")
                else:
                    await update.message.reply_text("Error: Empty response received from server")
            else:
                await update.message.reply_text(f"Error: {response.text}")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
    def run(self):
        print('Starting bot...')
        print("Polling...")
        self.app.run_polling(poll_interval=5)

if __name__ == '__main__':
    bot = CarepBot()
    bot.run()
