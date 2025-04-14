from balethon import Client
from datetime import datetime, time
import pytz
import asyncio
import os

class FoodBot:
    def __init__(self, token):
        self.client = Client(token)
        self.responses = {}
        self.message_id = None
        self.group_chat_id = os.getenv("GROUP_CHAT_ID")  # آیدی گروه از متغیر محیطی

    async def start(self):
        print("Bot is running!")
        await self.schedule_daily_task()

    async def schedule_daily_task(self):
        tehran_tz = pytz.timezone('Asia/Tehran')
        while True:
            now = datetime.now(tehran_tz)
            target_time = tehran_tz.localize(datetime.combine(now.date(), time(9, 0)))

            if now.time() > time(9, 0):
                target_time = target_time.replace(day=now.day + 1)

            seconds_until = (target_time - now).total_seconds()
            await asyncio.sleep(seconds_until)

            # ساعت ۹ صبح سوال رو می‌پرسه
            await self.ask_food_question()

            # تا ساعت ۱۰ صبر می‌کنه و نتایج رو جمع‌آوری می‌کنه
            await asyncio.sleep(3600)  # ۱ ساعت
            await self.collect_results()

    async def ask_food_question(self):
        self.responses.clear()
        keyboard = {
            "keyboard": [
                [{"text": "بله"}, {"text": "خیر"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": True
        }
        message = await self.client.send_message(
            chat_id=self.group_chat_id,
            text="آیا امروز غذا می‌خواهید؟",
            reply_markup=keyboard
        )
        self.message_id = message["message_id"]

    async def on_message(self, message):
        # فقط پاسخ‌هایی که بعد از سوال هستن و "بله" یا "خیر" هستن
        if self.message_id and message["text"] in ["بله", "خیر"]:
            user_id = message["from"]["id"]
            self.responses[user_id] = message["text"]

    async def collect_results(self):
        yes_count = sum(1 for response in self.responses.values() if response == "بله")
        no_count = sum(1 for response in self.responses.values() if response == "خیر")

        report = f"نتایج سفارش غذا:\nبله: {yes_count} نفر\nخیر: {no_count} نفر"
        await self.client.send_message(
            chat_id=self.group_chat_id,
            text=report
        )

        # ریست برای روز بعد
        self.responses.clear()
        self.message_id = None

def main():
    bot = FoodBot(os.getenv("BOT_TOKEN"))  # توکن از متغیر محیطی

    # ثبت هندلر پیام‌ها
    @bot.client.on_message()
    async def handle_message(client, message):
        await bot.on_message(message)

    # اجرای تسک اصلی ربات
    asyncio.get_event_loop().create_task(bot.start())

    # اجرای کلاینت Balethon
    bot.client.run()

if __name__ == "__main__":
    main()
