from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from functools import wraps


class Security:
    def __init__(self, db_manager, admin_ids: list, max_requests: int = 30):
        self.db = db_manager
        self.admin_ids = admin_ids
        self.max_requests = max_requests

    def is_admin(self, user_id: int) -> bool:
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
            result = c.fetchone()
            return bool(result[0]) if result else False

    def set_admin(self, user_id: int, is_admin: bool = True):
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute('UPDATE users SET is_admin = ? WHERE user_id = ?',
                      (is_admin, user_id))

    async def handle_access_request(self, update, context):
        query = update.callback_query
        data = query.data.split('_')
        user_id = int(data[1])

        if str(query.from_user.id) in self.admin_ids:
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute('UPDATE users SET is_authorized = TRUE WHERE user_id = ?', (user_id,))

            await query.edit_message_text(f"משתמש {user_id} אושר!")
            await context.bot.send_message(
                chat_id=user_id,
                text="חשבונך אושר! כעת תוכל להשתמש בבוט."
            )
        else:
            await query.answer("אין לך הרשאות מנהל")

    def authorize_user(self, func):
        @wraps(func)
        async def wrapped(update, context, *args, **kwargs):
            user_id = update.effective_user.id

            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute('SELECT is_authorized,requests_today, last_request_date, is_admin FROM users WHERE user_id = ?', (user_id,))
                user_data = c.fetchall()

                if not user_data:
                    keyboard = [[InlineKeyboardButton("אשר משתמש",
                                                      callback_data=f'approve_{user_id}')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)

                    for admin_id in self.admin_ids:
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text=f"בקשת הרשאה חדשה:\nID: {user_id}\nUsername: {update.effective_user.username}",
                            reply_markup=reply_markup
                        )
                    return await update.message.reply_text("בקשתך נשלחה למנהלים ותטופל בהקדם.")

                is_authorized, requests_today, last_request_date, is_admin = user_data[0]

                if not (is_authorized or is_admin):
                    return await update.message.reply_text("המשתמש שלך אינו מורשה. אנא פנה למנהלת המערכת.")

                if not is_admin:  # Skip request limit for admins
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    if current_date != last_request_date:
                        requests_today = 0

                    if requests_today >= self.max_requests:
                        return await update.message.reply_text("הגעת למגבלת הבקשות היומית. נסה שוב מחר.")

                    c.execute('''UPDATE users SET requests_today = ?, last_request_date = ? 
                                WHERE user_id = ?''', (requests_today + 1, current_date, user_id))

            return await func(update, context, *args, **kwargs)

        return wrapped