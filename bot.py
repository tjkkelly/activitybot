#!/usr/bin/env python
# pylint: disable=C0116
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import stravaservice
import json
import os
import json_to_image

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

telegram_bot_key = os.getenv('telegram_bot_key')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def json_to_tg_photo( jsonObj, title ):
    img_path = json_to_image.json_2_table_png(jsonObj, format_len=21, table_title=title, txt_color="white", bg_color="black")
    return open(img_path, 'rb')

def get_latest_activity(update: Update, _: CallbackContext) -> None:
    """Returns the last activity that someone completed"""
    activites = stravaservice.getActivitesSinceDefinedTime()
    update.message.reply_text(str(activites[-1]))

def get_team_duration_totals(update: Update, _: CallbackContext) -> None:
    json_result = stravaservice.getTeamDurationTotals()
    update.message.reply_photo(photo=json_to_tg_photo(json_result, "Team Scores"))

def get_individual_leaderboard(update: Update, _: CallbackContext) -> None:
    json_result = stravaservice.getLeaderboardByTotalDuration()
    update.message.reply_photo(photo=json_to_tg_photo(json_result, "Individual Scores"))

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(telegram_bot_key)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("lastactivity", get_latest_activity))
    dispatcher.add_handler(CommandHandler("teamtotals", get_team_duration_totals))
    dispatcher.add_handler(CommandHandler("leaderboard", get_individual_leaderboard))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()