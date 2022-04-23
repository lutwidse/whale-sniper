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

def whale(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(ws.get_extracted_bids())
    
if __name__ == "__main__":
    updater = Updater(os.environ["TOKEN"])
    updater.dispatcher.add_handler(CommandHandler("whale", whale))
    updater.start_polling()
    
    # init
    update_transactions()

    schedule.every(1).hours.do(update_transactions)
    while True:
        schedule.run_pending()
        time.sleep(1)