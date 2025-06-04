import telebot
from telebot.types import Message, CallbackQuery
from config import ADMIN_ID, CHANNEL_ID
from messages import messages
from keyboards import (
    language_keyboard, join_channel_keyboard, broker_keyboard, register_keyboard,
    quote_type_keyboard, signal_time_keyboard, currency_pair_keyboard, signal_keyboard,
    subscribe_keyboard, admin_verification_keyboard, admin_account_id_keyboard, admin_subscription_keyboard
)
from database import save_user_data, load_user_data
import random
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

user_data = {}

def get_user_data(user_id):
    if user_id not in user_data:
        data = load_user_data(user_id)
        if data:
            user_data[user_id] = data
        else:
            user_data[user_id] = {
                "language": None, "broker": None, "quote": None, "time": None, "pair": None,
                "signals_used": 0, "last_signal_date": None, "verified": False,
                "registered": False, "account_id_approved": False, "subscribed": False
            }
    return user_data[user_id]

def update_user_data(user_id, data):
    user_data[user_id] = data
    save_user_data(user_id, data)

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def start(message: Message):
        user_id = message.from_user.id
        user = get_user_data(user_id)
        logging.info(f"User {user_id} starting with language: {user['language']}")
        bot.set_state(user_id, UserState.LANGUAGE, message.chat.id)
        bot.send_message(message.chat.id, messages["en"]["start"], reply_markup=language_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
    def handle_language(call: CallbackQuery):
        user_id = call.from_user.id
        user = get_user_data(user_id)
        lang = call.data.split("_")[1]
        user["language"] = lang
        update_user_data(user_id, user)
        logging.info(f"User {user_id} selected language: {lang}")
        bot.set_state(user_id, UserState.JOIN_VERIFICATION, call.message.chat.id)
        bot.edit_message_text(
            messages[lang]["join_channel"],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=join_channel_keyboard()
        )

    @bot.callback_query_handler(func=lambda call: call.data == "verify")
    def handle_verification(call: CallbackQuery):
        user_id = call.from_user.id
        user = get_user_data(user_id)
        lang = user["language"]
        bot.edit_message_text(
            messages[lang]["verify_success"],
            call.message.chat.id,
            call.message.message_id
        )
        user["verified"] = True
        update_user_data(user_id, user)
        bot.send_message(
            ADMIN_ID,
            messages[lang]["admin_verify_msg"].format(call.from_user.username or user_id, lang),
            reply_markup=admin_verification_keyboard(user_id)
        )
        bot.set_state(user_id, UserState.BROKER_SELECTION, call.message.chat.id)
        bot.send_message(call.message.chat.id, messages[lang]["select_broker"], reply_markup=broker_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("broker_"))
    def handle_broker(call: CallbackQuery):
        user_id = call.from_user.id
        user = get_user_data(user_id)
        lang = user["language"]
        broker = call.data.split("_")[1]
        user["broker"] = broker
        update_user_data(user_id, user)
        bot.edit_message_text(
            messages[lang]["select_broker"],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=broker_keyboard()
        )
        bot.set_state(user_id, UserState.REGISTRATION, call.message.chat.id)
        bot.send_message(call.message.chat.id, messages[lang]["register"], reply_markup=register_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data == "registered")
    def handle_registration(call: CallbackQuery):
        user_id = call.from_user.id
        user = get_user_data(user_id)
        lang = user["language"]
        user["registered"] = True
        update_user_data(user_id, user)
        bot.edit_message_text(
            messages[lang]["register"],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=register_keyboard()
        )
        bot.set_state(user_id, UserState.ACCOUNT_ID, call.message.chat.id)
        bot.send_message(call.message.chat.id, messages[lang]["send_account_id"])

    @bot.message_handler(func=lambda message: bot.get_state(message.from_user.id, message.chat.id) == UserState.ACCOUNT_ID)
    def handle_account_id(message: Message):
        user_id = message.from_user.id
        user = get_user_data(user_id)
        lang = user["language"]
        bot.send_message(
            ADMIN_ID,
            messages[lang]["admin_account_id_msg"].format(message.from_user.username or user_id, lang, message.text),
            reply_markup=admin_account_id_keyboard(user_id)
        )
        bot.send_message(message.chat.id, "Account ID sent to admin for approval.")
        bot.set_state(user_id, UserState.QUOTE_TYPE, message.chat.id)
        bot.send_message(message.chat.id, messages[lang]["select_quote_type"], reply_markup=quote_type_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("quote_"))
    def handle_quote_type(call: CallbackQuery):
        user_id = call.from_user.id
        user = get_user_data(user_id)
        lang = user["language"]
        quote = call.data.split("_")[1]
        user["quote"] = quote
        update_user_data(user_id, user)
        bot.edit_message_text(
            messages[lang]["select_quote_type"],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=quote_type_keyboard()
        )
        bot.set_state(user_id, UserState.SIGNAL_TIME, call.message.chat.id)
        bot.send_message(call.message.chat.id, messages[lang]["select_signal_time"], reply_markup=signal_time_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
    def handle_signal_time(call: CallbackQuery):
        user_id = call.from_user.id
        user = get_user_data(user_id)
        lang = user["language"]
        time = call.data.split("_")[1]
        user["time"] = time
        update_user_data(user_id, user)
        bot.edit_message_text(
            messages[lang]["select_signal_time"],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=signal_time_keyboard()
        )
        bot.set_state(user_id, UserState.CURRENCY_PAIR, call.message.chat.id)
        bot.send_message(call.message.chat.id, messages[lang]["select_currency_pair"], reply_markup=currency_pair_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("pair_"))
    def handle_currency_pair(call: CallbackQuery):
        user_id = call.from_user.id
        user = get_user_data(user_id)
        lang = user["language"]
        pair = call.data.split("_")[1]
        user["pair"] = pair
        update_user_data(user_id, user)
        bot.edit_message_text(
            messages[lang]["select_currency_pair"],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=currency_pair_keyboard()
        )
        bot.set_state(user_id, UserState.SHOW_SIGNAL, call.message.chat.id)
        show_signal(call.message, user_id)

    @bot.callback_query_handler(func=lambda call: call.data == "next_signal")
    def handle_next_signal(call: CallbackQuery):
        user_id = call.from_user.id
        show_signal(call.message, user_id)

    def show_signal(message, user_id):
        user = get_user_data(user_id)
        lang = user["language"]
        today = datetime.now().date().isoformat()
        
        # Reset signal count if new day
        if user["last_signal_date"] != today:
            user["signals_used"] = 0
            user["last_signal_date"] = today
            update_user_data(user_id, user)

        # Check signal limit
        if user["signals_used"] >= 15 and not user["subscribed"]:
            bot.send_message(
                message.chat.id,
                messages[lang]["signal_limit_reached"],
                reply_markup=subscribe_keyboard()
            )
            return

        # Generate signal
        direction = random.choice(["UP", "DOWN"])
        confidence = random.randint(70, 95)
        signal = f"Signal: {direction}\nConfidence: {confidence}%\nPair: {user['pair']}\nTime: {user['time']}"
        user["signals_used"] += 1
        update_user_data(user_id, user)
        bot.send_message(message.chat.id, signal, reply_markup=signal_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data == "subscribe")
    def handle_subscription(call: CallbackQuery):
        user_id = call.from_user.id
        user = get_user_data(user_id)
        lang = user["language"]
        bot.send_message(
            ADMIN_ID,
            messages[lang]["admin_subscription_msg"].format(call.from_user.username or user_id, lang),
            reply_markup=admin_subscription_keyboard(user_id)
        )
        bot.send_message(call.message.chat.id, messages[lang]["subscribe_prompt"])

    @bot.callback_query_handler(func=lambda call: call.data.startswith("approve_sub_"))
    def approve_subscription(call: CallbackQuery):
        user_id = int(call.data.split("_")[2])
        user = get_user_data(user_id)
        lang = user["language"]
        user["subscribed"] = True
        update_user_data(user_id, user)
        bot.send_message(user_id, "Subscription approved! You now have unlimited signals.")
        bot.edit_message_text(
            "Subscription approved for user {}".format(call.from_user.username or user_id),
            call.message.chat.id,
            call.message.message_id
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("reject_sub_"))
    def reject_subscription(call: CallbackQuery):
        user_id = int(call.data.split("_")[2])
        lang = get_user_data(user_id)["language"]
        bot.send_message(user_id, "Subscription request rejected.")
        bot.edit_message_text(
            "Subscription rejected for user {}".format(call.from_user.username or user_id),
            call.message.chat.id,
            call.message.message_id
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("approve_id_"))
    def approve_account_id(call: CallbackQuery):
        user_id = int(call.data.split("_")[2])
        user = get_user_data(user_id)
        lang = user["language"]
        user["account_id_approved"] = True
        update_user_data(user_id, user)
        bot.send_message(user_id, "Account ID approved!")
        bot.edit_message_text(
            "Account ID approved for user {}".format(call.from_user.username or user_id),
            call.message.chat.id,
            call.message.message_id
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("reject_id_"))
    def reject_account_id(call: CallbackQuery):
        user_id = int(call.data.split("_")[2])
        lang = get_user_data(user_id)["language"]
        bot.send_message(user_id, "Account ID rejected. Please send a valid ID.")
        bot.edit_message_text(
            "Account ID rejected for user {}".format(call.from_user.username or user_id),
            call.message.chat.id,
            call.message.message_id
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("approve_verify_"))
    def approve_verification(call: CallbackQuery):
        user_id = int(call.data.split("_")[2])
        lang = get_user_data(user_id)["language"]
        bot.send_message(user_id, "Verification approved!")
        bot.edit_message_text(
            "Verification approved for user {}".format(call.from_user.username or user_id),
            call.message.chat.id,
            call.message.message_id
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("reject_verify_"))
    def reject_verification(call: CallbackQuery):
        user_id = int(call.data.split("_")[2])
        lang = get_user_data(user_id)["language"]
        bot.send_message(user_id, "Verification rejected. Please join the channels and try again.")
        bot.edit_message_text(
            "Verification rejected for user {}".format(call.from_user.username or user_id),
            call.message.chat.id,
            call.message.message_id
        )

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_broker")
    def back_to_broker(call: CallbackQuery):
        user_id = call.from_user.id
        user = get_user_data(user_id)
        lang = user["language"]
        bot.set_state(user_id, UserState.BROKER_SELECTION, call.message.chat.id)
        bot.edit_message_text(
            messages[lang]["select_broker"],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=broker_keyboard()
        )

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_quote")
    def back_to_quote(call: CallbackQuery):
        user_id = call.from_user.id
        user = get_user_data(user_id)
        lang = user["language"]
        bot.set_state(user_id, UserState.QUOTE_TYPE, call.message.chat.id)
        bot.edit_message_text(
            messages[lang]["select_quote_type"],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=quote_type_keyboard()
        )

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_time")
    def back_to_time(call: CallbackQuery):
        user_id = call.from_user.id
        user = get_user_data(user_id)
        lang = user["language"]
        bot.set_state(user_id, UserState.SIGNAL_TIME, call.message.chat.id)
        bot.edit_message_text(
            messages[lang]["select_signal_time"],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=signal_time_keyboard()
        )

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_pair")
    def back_to_pair(call: CallbackQuery):
        user_id = call.from_user.id
        user = get_user_data(user_id)
        lang = user["language"]
        bot.set_state(user_id, UserState.CURRENCY_PAIR, call.message.chat.id)
        bot.edit_message_text(
            messages[lang]["select_currency_pair"],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=currency_pair_keyboard()
  )
