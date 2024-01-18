import os
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from decouple import config
from telegram import Update, ForceReply
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
import io
import requests
from PIL import Image


token = config('TELEGRAM_ACCESS_TOKEN')

app = FastAPI()


class TelegramWebhook(BaseModel):
    '''
    Telegram Webhook Model using Pydantic for request body validation
    '''
    update_id: int
    message: Optional[dict]
    edited_message: Optional[dict]
    channel_post: Optional[dict]
    edited_channel_post: Optional[dict]
    inline_query: Optional[dict]
    chosen_inline_result: Optional[dict]
    callback_query: Optional[dict]
    shipping_query: Optional[dict]
    pre_checkout_query: Optional[dict]
    poll: Optional[dict]
    poll_answer: Optional[dict]



def convert_image_to_pdf(image_path):
    response = requests.get(image_path)
    if response.status_code == 200:
        img_res = io.BytesIO(response.content)
        img = Image.open(img_res)
        pdf = io.BytesIO()
        img.save(pdf, "PDF", resolution=100.0)
        # pdf.seek(0)
        return pdf.getvalue()
    

async def convert(update:Update, context:ContextTypes):
    img = await update.message.photo[-1].get_file()
    img_path = img.file_path
    pdf_content = convert_image_to_pdf(img_path)
    await update.message.reply_document(document=io.BytesIO(pdf_content), filename="converted.pdf")
    


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = """Welcome to the image to pdf converter telegram Bot that is magical!
Just send the image you want to convert and watch the magic happen! built by @Kaleb_Mu
    """
    await update.message.reply_text(message, reply_markup=ForceReply())


async def main():
    # Build the application using the token
    app = Application.builder().token(token).build()

    # Add the start command handler
    start_handler = CommandHandler('start', start)
    convert_handler = MessageHandler(filters.PHOTO, convert)
    app.add_handler(start_handler)
    app.add_handler(convert_handler)

    app.bot.set_webhook(
        url=f"https://image2pdf-bot.vercel.app/webhook", allowed_updates=Update.ALL_TYPES)

    @app.get('/')
    def hello():
         return {'message': 'hello world'}

    @app.post('/webhook')
    async def webhook(webhook_data: TelegramWebhook):
        """Handle incoming Telegram updates by putting them into the `update_queue`"""
        await app.update_queue.put(Update.de_json(webhook_data.__dict__, bot=app.bot))
        return {"message": "ok"}

        

    # Run the polling loop
    # app.run_polling(allowed_updates=Update.ALL_TYPES, timeout=300)



if __name__ == '__main__':
    main()






