from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
import aiocron
import sqlite3
import os

API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
GROUP_CHAT_ID = int(os.getenv('CHAT_ID'))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_text TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Работа с базой
def add_task(text):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (task_text) VALUES (?)', (text,))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id=?', (task_id,))
    conn.commit()
    conn.close()

def get_all_tasks():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, task_text FROM tasks')
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def edit_task(task_id, new_text):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET task_text = ? WHERE id = ?', (new_text, task_id))
    conn.commit()
    conn.close()

# Хендлеры команд
@dp.message_handler(commands=['start'])
async def start_task(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        text = message.get_args().strip()
        if text:
            add_task(text)
            await message.reply(f'Задача добавлена: {text}')
        else:
            await message.reply('Напиши текст задачи: /start Текст задачи')

@dp.message_handler(commands=['list'])
async def list_tasks(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        tasks = get_all_tasks()
        if tasks:
            text = '‼️ Активные задачи:\n'
            for task in tasks:
                text += f'[{task[0]}] {task[1]}\n'
            await message.reply(text)
        else:
            await message.reply('Нет активных задач.')

@dp.message_handler(commands=['stop'])
async def stop_task(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        task_id = message.get_args().strip()
        if task_id.isdigit():
            delete_task(int(task_id))
            await message.reply(f'Задача [{task_id}] удалена.')
        else:
            await message.reply('Укажи номер задачи: /stop 1')

@dp.message_handler(commands=['edit'])
async def edit_task_handler(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        args = message.get_args().strip().split(maxsplit=1)
        if len(args) == 2 and args[0].isdigit():
            task_id = int(args[0])
            new_text = args[1]
            edit_task(task_id, new_text)
            await message.reply(f'Задача [{task_id}] изменена на:\n{new_text}')
        else:
            await message.reply('Формат: /edit ID Новый текст\nНапример: /edit 2 Новый текст задачи')

# Автоматическое напоминание каждый день
@aiocron.crontab('0 12 * * *')  # каждый день в 12:00 UTC
async def daily_reminder():
    tasks = get_all_tasks()
    if tasks:
        text = '‼️ Напоминание по активным задачам:\n'
        for task in tasks:
            text += f'[{task[0]}] {task[1]}\n'
        await bot.send_message(GROUP_CHAT_ID, text)

# Webhook
async def on_startup(dispatcher):
    if not WEBHOOK_URL:
        raise Exception("WEBHOOK_URL is not set!")
    print(f'Webhook URL: {WEBHOOK_URL}')
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dispatcher):
    await bot.delete_webhook()

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path='',
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True
    )
