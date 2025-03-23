from aiogram import Bot, Dispatcher, types, executor
import sqlite3
import os
import aiocron

API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
GROUP_CHAT_ID = int(os.getenv('CHAT_ID'))

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Инициализация базы
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

# Работа с задачами
def add_task(text):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (task_text) VALUES (?)', (text,))
    conn.commit()
    conn.close()

def get_tasks():
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, task_text FROM tasks')
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def delete_task(task_id):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id=?', (task_id,))
    conn.commit()
    conn.close()

def edit_task(task_id, new_text):
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET task_text = ? WHERE id = ?', (new_text, task_id))
    conn.commit()
    conn.close()

# Команды
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        text = message.get_args()
        if text:
            add_task(text)
            await message.reply(f'✅ Задача добавлена: {text}')
        else:
            await message.reply('⚠️ Напиши текст задачи после /start')

@dp.message_handler(commands=['list'])
async def cmd_list(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        tasks = get_tasks()
        if tasks:
            msg = "📌 Активные задачи:\n"
            for task in tasks:
                msg += f"[{task[0]}] {task[1]}\n"
            await message.reply(msg)
        else:
            await message.reply("✅ Нет активных задач.")

@dp.message_handler(commands=['stop'])
async def cmd_stop(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        task_id = message.get_args()
        if task_id.isdigit():
            delete_task(int(task_id))
            await message.reply(f'❌ Задача [{task_id}] удалена')
        else:
            await message.reply('⚠️ Укажи ID задачи для удаления: /stop 1')

@dp.message_handler(commands=['edit'])
async def cmd_edit(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        args = message.get_args().split(maxsplit=1)
        if len(args) == 2 and args[0].isdigit():
            edit_task(int(args[0]), args[1])
            await message.reply(f'✏️ Задача [{args[0]}] изменена')
        else:
            await message.reply('⚠️ Формат: /edit ID новый_текст')

# Автоматическое напоминание каждый день в 12:00
@aiocron.crontab('0 12 * * *')
async def daily_reminder():
    tasks = get_tasks()
    if tasks:
        msg = "🔔 Напоминание! Активные задачи:\n"
        for task in tasks:
            msg += f"[{task[0]}] {task[1]}\n"
        await bot.send_message(GROUP_CHAT_ID, msg)

if __name__ == '__main__':
    print("✅ Бот запущен на POLLING")
    executor.start_polling(dp, skip_updates=True)
