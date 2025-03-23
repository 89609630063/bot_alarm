from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import aiocron
import os

API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
GROUP_CHAT_ID = int(os.getenv('CHAT_ID'))

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

tasks = {}
task_counter = 1

@dp.message_handler(commands=['start'])
async def start_task(message: types.Message):
    global task_counter
    if message.from_user.id == ADMIN_ID:
        text = message.get_args().strip()
        if text:
            tasks[task_counter] = text
            await message.reply(f'Задача [{task_counter}] добавлена: {text}')
            task_counter += 1
        else:
            await message.reply('Напиши текст задачи: /start Текст задачи')

@dp.message_handler(commands=['list'])
async def list_tasks(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        if tasks:
            text = '‼️ Активные задачи:\n'
            for id, task in tasks.items():
                text += f'[{id}] {task}\n'
            await message.reply(text)
        else:
            await message.reply('Нет активных задач.')

@dp.message_handler(commands=['stop'])
async def stop_task(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        task_id = message.get_args().strip()
        if task_id.isdigit() and int(task_id) in tasks:
            removed = tasks.pop(int(task_id))
            await message.reply(f'Задача [{task_id}] удалена: {removed}')
        else:
            await message.reply('Укажи номер задачи из списка: /stop 1')

@aiocron.crontab('0 12 * * *')  # каждый день в 12:00 UTC
async def daily_reminder():
    if tasks:
        text = '‼️ Напоминание по активным задачам:\n'
        for id, task in tasks.items():
            text += f'[{id}] {task}\n'
        await bot.send_message(GROUP_CHAT_ID, text)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
