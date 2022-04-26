from whale_sniper import WhaleSniper
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import schedule
import time
import os
import csv

ws = WhaleSniper()
def update_bids():
    ws.get_transactions()
    ws.get_bids()
    ws.extract_bids()

def update_liquidations():
    ws.get_liquidations()
    ws.extract_liquidations()

HELP_TEXT = (
    "This bot is still in development. alert might be reset for some reason. \n"
    "/whale - Get latest whales bid. \n"
    "/whale_alert - Set /whale notification every 1 hour. \n"
    "/whale_unalert - Unset alert. \n\n"

    "/liquidation - Get LUNA liquidation data\n" 
    "/liquidation_alert - Set /liquidation notification every 1 hour. \n"
    "/liquidation_unalert - Unset alert."
)

def get_extracted_bids(cnt):
        with open("whale_sniper/luna_whale.csv", "r") as csvfile:
            reader = csv.DictReader(csvfile)
            b = ""
            for i, j in enumerate(reader):
                b += (
                      f"{j['timestamp']} - {j['sender']} \n"
                    + f"[Amount] {j['amount']} [Premium] {j['premium_slot']} [BLT] {j['strategy_activate_ltv']} [ARCT] {j['strategy_activate_amount']} \n\n")
                if i == cnt-1:
                    return b

def get_extracted_liquidation(cnt):
        with open("whale_sniper/luna_liquidation.csv", "r") as csvfile:
            reader = csv.DictReader(csvfile)
            b = ""
            for i, j in enumerate(reader):
                b += (
                    f"[Liquidation Price] ${j['Luna_Liquidation_Price']} [Amount] {j['Loan_Value']}\n\n")
                if i == cnt-1:
                    return b

def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(text="Hi! Please use /help to see commands.")

def help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(text=HELP_TEXT)

def whale(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(get_extracted_bids(5))

def whale_alert(context: CallbackContext) -> None:
    job = context.job
    context.bot.send_message(job.context, text=get_extracted_bids(5))

def set_whale_alert(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    context.job_queue.run_repeating(whale_alert, interval=60*60, context=chat_id, name=str(chat_id)+"_whale")

    if job_removed:
        update.message.reply_text("Alert has been reset.")
    else:
        update.message.reply_text("Alert has been set.")

def unset_whale_alert(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id) + "_whale", context)
    text = "Unalerted   " if job_removed else 'You have no active alert.'
    update.message.reply_text(text)

def liquidation(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(get_extracted_liquidation(5))

def liquidation_alert(context: CallbackContext) -> None:
    job = context.job
    context.bot.send_message(job.context, text=get_extracted_liquidation(5))

def set_liquidation_alert(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id) + "_liquidation", context)
    context.job_queue.run_repeating(liquidation_alert, interval=60*60, context=chat_id, name=str(chat_id)+"_liquidation")

    if job_removed:
        update.message.reply_text("Alert has been reset.")
    else:
        update.message.reply_text("Alert has been set.")

def unset_liquidation_alert(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Unalerted   " if job_removed else 'You have no active alert.'
    update.message.reply_text(text)

if __name__ == "__main__":
    updater = Updater(os.environ["TOKEN"])
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", help))

    updater.dispatcher.add_handler(CommandHandler("whale", whale))
    updater.dispatcher.add_handler(CommandHandler("whale_alert", set_whale_alert))
    updater.dispatcher.add_handler(CommandHandler("whale_unalert", unset_whale_alert))

    updater.dispatcher.add_handler(CommandHandler("liquidation", liquidation))
    updater.dispatcher.add_handler(CommandHandler("liquidation_alert", set_liquidation_alert))
    updater.dispatcher.add_handler(CommandHandler("liquidation_unalert", unset_liquidation_alert))

    updater.start_polling()
    
    # init
    update_bids()
    update_liquidations()

    schedule.every(1).hours.do(update_bids)
    schedule.every(30).minutes.do(update_liquidations)
    while True:
        schedule.run_pending()
        time.sleep(1)