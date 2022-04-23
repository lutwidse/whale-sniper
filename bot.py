from whale_sniper import WhaleSniper
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import schedule
import time
import os

ws = WhaleSniper()
def update_transactions():
    ws.get_transactions()
    ws.get_bids()
    ws.extract_bids()

HELP_TEXT = (
    "This bot is still in development. alert might be reset for some reason. \n"
    "/whale - Get latest whales bid. \n"
    "/alert - Set /whale notification every 1 hour. \n"
    "/unalert - Unset alert."
)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(text="Hi! Please use /help to see commands.")

def help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(text=HELP_TEXT)

def whale(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(ws.get_extracted_bids())

def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

def whale_alert(context: CallbackContext) -> None:
    job = context.job
    context.bot.send_message(job.context, text=ws.get_extracted_bids())

def set_whale_alert(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    context.job_queue.run_repeating(whale_alert, interval=60*60, context=chat_id, name=str(chat_id))

    if job_removed:
        update.message.reply_text("Alert has been reset.")
    else:
        update.message.reply_text("Alert has been set.")

def unset_whale_alert(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Unalerted   " if job_removed else 'You have no active alert.'
    update.message.reply_text(text)

if __name__ == "__main__":
    updater = Updater(os.environ["TOKEN"])
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", help))
    updater.dispatcher.add_handler(CommandHandler("whale", whale))
    updater.dispatcher.add_handler(CommandHandler("alert", set_whale_alert))
    updater.dispatcher.add_handler(CommandHandler("unalert", unset_whale_alert))
    updater.start_polling()
    
    # init
    update_transactions()

    schedule.every(1).hours.do(update_transactions)
    while True:
        schedule.run_pending()
        time.sleep(1)