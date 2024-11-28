import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from app.c_stock_api import StockAPI
from utils import security
from utils.security import Security
from utils.db_utils import DatabaseManager
import requests
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# app/bot.py
from telegram.ext import Application, CommandHandler
from functools import partial


class StockTelegramBot:
    def __init__(self, telegram_token: str, db_manager, security: Security, alpha_vantage_key: str):
        self.application = Application.builder().token(telegram_token).build()
        self.db = db_manager
        self.stock_api = StockAPI(alpha_vantage_key)
        self._security = security


    def register_handlers(self):
        authorized_start = self._security.authorize_user(self.start)
        self.application.add_handler(CommandHandler("start", authorized_start))
        self.application.add_handler(CommandHandler("register", self.register))
        self.application.add_handler(CommandHandler("stock", self.get_stock_info))
        self.application.add_handler(CommandHandler("authorize", self.authorize))
        self.application.add_handler(CommandHandler("sentiment", self.get_sentiment))
        self.application.add_handler(CommandHandler("earnings", self.get_earnings))
        self.application.add_handler(CommandHandler("dividend", self.get_dividend_info))
        self.application.add_handler(CommandHandler("holdings", self.get_holdings))
        self.application.add_handler(CommandHandler("top_gainers", self.top_gainers))
        self.application.add_handler(CommandHandler("top_losers", self.top_losers))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "ברוכים הבאים לבוט מידע על מניות! 📈\n"
            "השתמשו בפקודות הבאות:\n"
            "/stock SYMBOL - מידע בסיסי על מניה\n"
            "/sentiment SYMBOL - ניתוח סנטימנט\n"
            "/earnings SYMBOL - מידע על דוחות כספיים\n"
            "/dividend SYMBOL - מידע על דיבידנדים\n"
            "/holdings SYMBOL - מידע על החזקות המוסדיים\n"
            "/top_gainers - המניות המובילות\n"
            "/top_losers - המניות המפסידות"
        )
    async def register(self, update, context):
        user_id = update.effective_user.id
        username = update.effective_user.username

        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            if c.fetchone():
                await update.message.reply_text("כבר רשום במערכת!")
                return

            c.execute('''INSERT INTO users (user_id, username, requests_today, last_request_date, is_authorized, is_admin) 
                        VALUES (?, ?, 0, ?, ?, ?)''',
                     (user_id, username, datetime.now().strftime('%Y-%m-%d'), False, False))

        keyboard = [[InlineKeyboardButton("אשר משתמש", callback_data=f'auth_{user_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        for admin_id in self._security.admin_ids:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"בקשת הרשאה חדשה:\nID: {user_id}\nUsername: {username}",
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"Failed to send message to admin {admin_id}: {e}")

        await update.message.reply_text("הרשמתך נקלטה! ממתין לאישור מנהל.")


    async def authorize(self, update, context):
        if str(update.effective_user.id) not in self.security.admin_ids:
            return

        if not context.args:
            await update.message.reply_text("Usage: /authorize USER_ID")
            return

        user_id = int(context.args[0])
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute('UPDATE users SET is_authorized = TRUE WHERE user_id = ?',
                      (user_id,))

        await update.message.reply_text(f"User {user_id} authorized")
        await context.bot.send_message(
            chat_id=user_id,
            text=f"User {user_id} account has been authorized!"
        )

    
    async def get_stock_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("אנא ציין סימול מניה, לדוגמה: /stock AAPL")
            return
        symbol = context.args[0].upper()
        response = self.stock_api.get_stock_info(symbol)
        formatted_response = (
            f"Symbol: {response['01. symbol']}\n"
            f"Open: {response['02. open']}\n"
            f"High: {response['03. high']}\n"
            f"Low: {response['04. low']}\n"
            f"Price: {response['05. price']}\n"
            f"Volume: {response['06. volume']}\n"
            f"Latest Trading Day: {response['07. latest trading day']}\n"
            f"Previous Close: {response['08. previous close']}\n"
            f"Change: {response['09. change']}\n"
            f"Change Percent: {response['10. change percent']}"
        )
        await update.message.reply_text(formatted_response)

    async def top_gainers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        response = self.stock_api.get_top_gainers()
        await update.message.reply_text(response)

    async def top_losers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        response = self.stock_api.get_top_losers()
        await update.message.reply_text(response)

    async def get_sentiment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("אנא ציין סימול מניה, לדוגמה: /sentiment AAPL")
            return
        symbol = context.args[0].upper()
        response =  self.stock_api.get_sentiment(symbol)
        await update.message.reply_text(response)

    
    async def get_holdings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("אנא ציין סימול מניה, לדוגמה: /holdings AAPL")
            return
        symbol = context.args[0].upper()
        response = self.stock_api.get_holdings(symbol)
        await update.message.reply_text(response)

    
    async def get_earnings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("אנא ציין סימול מניה, לדוגמה: /earnings AAPL")
            return
        symbol = context.args[0].upper()
        response = self.stock_api.get_earnings(symbol)
        await update.message.reply_text(response)

    
    async def get_dividend_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("אנא ציין סימול מניה, לדוגמה: /dividend AAPL")
            return
        symbol = context.args[0].upper()
        dividend_info =  self.stock_api.get_dividend(symbol)
        formatted_response = (
            f"Dividend Per Share: ${dividend_info['DividendPerShare']}\n"
            f"Dividend Yield: {dividend_info['DividendYield']}%\n"
            f"Ex-Dividend Date: {dividend_info['ExDividendDate']}\n"
            f"Dividend Date: {dividend_info['DividendDate']}"
        )
        await update.message.reply_text(formatted_response)
    def run(self):
        self.application.run_polling()


def load_environment():
    """
    טעינת משתני הסביבה מקובץ .env
    """
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)

    required_vars = [
        'TELEGRAM_TOKEN',
        'AZURE_API_KEY',
        'ALPHA_VANTAGE_KEY'
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please check your .env file"
        )

    return {
        'telegram_token': os.getenv('TELEGRAM_TOKEN'),
        'azure_api_key': os.getenv('AZURE_API_KEY'),
        'alpha_vantage_key': os.getenv('ALPHA_VANTAGE_KEY'),
        'admins': os.getenv('ALLOWED_USERS', '').split(','),
        'daily_cost_limit': float(os.getenv('DAILY_COST_LIMIT', '1.0')),
        'max_requests': float(os.getenv('MAX_REQUESTS', '25'))
    }


def main():
    try:
        db = DatabaseManager('bot_security.db')
        db.init_tables()
        env = load_environment()
        sec = Security(db, env['admins'])
        bot = StockTelegramBot(
            telegram_token=env['telegram_token'],
            alpha_vantage_key=env['alpha_vantage_key'],
            security=sec,
            db_manager=db
        )
        bot.register_handlers()
        print("הבוט מופעל! 🚀")
        bot.run()

    except Exception as e:
        print(f"שגיאה בהפעלת הבוט: {e}")
        raise

