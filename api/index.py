import io
import logging
import requests
from PIL import Image
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from telegram import Update, ForceReply, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Load configuration from .env file
from decouple import config

token = config('TELEGRAM_ACCESS_TOKEN')

app = FastAPI()

WEBHOOK_URL = "https://image2pdf-bot.vercel.app/webhook"

logging.basicConfig(
    format="%(levelname)s (%(asctime)s): %(message)s (Line: %(lineno)d [%(filename)s])",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

telegram_app = Application.builder().token(token).build()


class TelegramWebhook(BaseModel):
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
        pdf.seek(0)
        return pdf.getvalue()


async def convert(update: Update, context: CallbackContext):
    img = await update.message.photo[-1].get_file()
    img_path = img.file_path
    pdf_content = convert_image_to_pdf(img_path)
    await update.message.reply_document(document=io.BytesIO(pdf_content), filename="converted.pdf")


async def start(update: Update, context: CallbackContext):
    message = """Welcome to the image to pdf converter Telegram Bot that is magical!
Just send the image you want to convert and watch the magic happen! built by @Kaleb_Mu
    """
    await update.message.reply_text(message, reply_markup=ForceReply())


@app.get('/')
def index():
    webhook_info = telegram_app.bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        telegram_app.bot.set_webhook(url=WEBHOOK_URL)
        logger.info("Setting webhook: %s", webhook_info.url)
        return "Webhook has been updated"

    return "Webhook has already been set! I'm ready to work!"


@app.post('/webhook')
async def webhook_handler(webhook_data: TelegramWebhook):
    try:
        update = Update.de_json(webhook_data.__dict__, telegram_app.bot)
        
        # Add the start command handler
        start_handler = CommandHandler('start', start)
        convert_handler = MessageHandler(filters.PHOTO, convert)
        telegram_app.add_handler(start_handler)
        telegram_app.add_handler(convert_handler)

        await telegram_app.process_update(update)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing update: {str(e)}")

    return {"message": "ok"}


async def main():
    # Build the application using the token
    

     
    # Set the webhook
    await telegram_app.bot.setWebhook(
        url=f"https://image2pdf-bot.vercel.app/webhook", allowed_updates=Update.ALL_TYPES
    )
  

    # Run the application
    import uvicorn
    uvicorn.run(telegram_app, host="0.0.0.0")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
