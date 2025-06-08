
import discord
from discord.ext import commands, tasks
import random
import json
from antispam import handle_antispam
import economy
from shop import Shop
from economy import Economy
import aiosqlite
import os
from discord import Embed
import sqlite3
import time
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  
intents.messages = True
intents.guilds = True
intents.voice_states = True 
intents.reactions = True
bot = commands.Bot(command_prefix='!', intents=intents)



@bot.event
async def on_ready():
    print(f'Бот {bot.user} підключений до Discord!')



@bot.command(name="stats")
async def stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = member.id

    # Получает XP и уровень
    xp, level = get_user_data(user_id)
    xp_needed = level * 100
    progress = create_progress_bar(xp, xp_needed)

    # Получает баланс из экономики
    balance = await economy.get_balance(user_id)

    # Роли (без @everyone)
    roles = [role.name for role in member.roles if role.name != "@everyone"]
    roles_display = ", ".join(roles) if roles else "Ні"

    # Создаёт embed
    embed = discord.Embed(
        title=f"📊 Статистика користувача {member.display_name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

    embed.add_field(name="Рівень", value=str(level), inline=True)
    embed.add_field(name="XP", value=f"{xp}/{xp_needed}", inline=True)
    embed.add_field(name="Прогрес", value=progress, inline=False)
    embed.add_field(name="Баланс", value=f"{balance:,} 🪙", inline=True)
    embed.add_field(name="Ролі", value=roles_display, inline=False)
    embed.set_footer(text=f"ID: {user_id} • Приєднався: {member.joined_at.date()}")

    # Отправка сообщения
    await ctx.send(embed=embed)

# Команда !прив
@bot.command(name='Hello')
async def hello(ctx):
    await ctx.send(f"Привiт, {ctx.author.mention}!")

# Команда 
@bot.command(name='ping')
async def ping(ctx):
    latency = round(bot.latency * 1000)  # задержка в миллисекундах
    await ctx.send(f'Пінг бота: {latency}ms')

# Команда !8ball
@bot.command(name='8ball')
async def eight_ball(ctx, *, question: str = None):
    if not question:
        await ctx.send("🎱 Поставте своє запитання, наприклад: `!8ball Чи варто мені вчитися програмуванню?")
        return

    if not question.endswith('?'):
        await ctx.send("🎱 Ваше запитання має закінчуватися на знак запитання `?`.")
        return

    # Список ответов
    responses = [
        "Безумовно так!😊",
        "Це точно не так. 😔",
        "Найімовірніше, так.",
        "Можливо.",
        "Я не впевнений. Спробуйте пізніше. 🤔",
        "Шанси малі.",
        "Безумовно ні.",
        "Навіть не сумнівайся!",
        "Я бачу, що так!",
        "Зараз краще не питати."
    ]

    # Случайный выбор ответа
    answer = random.choice(responses)
    await ctx.send(f"🎱 Питання: {question}\nОтвет: {answer}")

@bot.command(name='commands')
async def show_commands(ctx):
    embed = discord.Embed(
        title="📜 Список команд",
        description="Ось доступні команди бота:",
        color=discord.Color.blue()
    )

    embed.add_field(name="🧍‍♂️ Общие", value="""
`!stats [користувач]` - Показати статистику користувача
`!Hello` - Привітання від бота
``!ping` - Показати пінг бота
`!8ball [питання?]` - Магічна куля відповість на твоє запитання
""", inline=False)

    embed.add_field(name="🪙 Економіка", value="""
`!balance` - Перевірити баланс
`!work` - Отримати щоденну нагороду
`!give @користувач <сума>` - Передати монети
`!shop` - Відкрити магазин
`!buy <предмет>` - Купити предмет
`!removeitem <назва>` - Видалити предмет із магазину
`!additem <назва> <ціна> <кількість>` - Додати предмет у магазин
""", inline=False)

    embed.add_field(name="🎮 Игры", value="""
`!slots <ставка>` - Ігровий автомат
`!guess <ставка> <число від 1 до 10>` - Вгадай число
""", inline=False)

    embed.add_field(name="📈 Уровни", value="""
`!lvl [користувач]` - Показати рівень і досвід
`!givelvl @користувач <рівень>` - Видати рівень (Можуть використовувати адміни)
""", inline=False)

    embed.add_field(name="👮 Модерація", value="""
`!apply` — Подати заявку на модератора
""", inline=False)

    embed.set_footer(text="Для подробиць по кожній команді - звернися до розробника 😊")
    await ctx.send(embed=embed)



@bot.event
async def on_member_join(member):
    
    role = discord.utils.get(member.guild.roles, name="Зритель 👤")
    if role:
        await member.add_roles(role)
        print(f"Роль 'Глядач 👤' призначена {member.name}")

    
    welcome_channel_id = 1292845820898574470  
    channel = bot.get_channel(welcome_channel_id)

    if channel:
        welcome_message = f"Ласкаво просимо, {member.mention}! 🎉"
        await channel.send(welcome_message)




economy = Economy()
shop_system = Shop()


async def setup():
    await shop_system.initialize()

import asyncio
asyncio.run(setup())


@bot.command()
async def balance(ctx):
    bal = await economy.get_balance(ctx.author.id)

    embed = discord.Embed(
        title="💰 Баланс",
        description=f"**{ctx.author.display_name}**, ось ваш поточний баланс:",
        color=discord.Color.gold()
    )
    embed.add_field(name="Монети", value=f"**{bal:,}** 🪙", inline=False)
    embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    embed.set_footer(text=f"ID: {ctx.author.id}")

    await ctx.send(embed=embed)
    

@bot.command()
async def work(ctx):
    earnings = await economy.work(ctx.author.id)
    await ctx.send(f"{ctx.author.mention}, ви отримали 100 монет за щоденний бонус!")

@bot.command()
async def give(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Сума переказу має бути більшою за 0!")
        return

    success = await economy.transfer(ctx.author.id, member.id, amount)

    if success:
        embed = discord.Embed(
            title="🏦 Банківський переказ",
            description=f"{ctx.author.mention} → {member.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="💰 Сумма", value=f"{amount} монет", inline=False)
        embed.set_footer(text="Транзакцію завершено успішно")
        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Помилка перекладу",
            description="Недостатньо коштів для переказу.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Будь ласка, перевірте свій баланс")
        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)


@bot.command()
async def shop(ctx):
    items = await shop_system.get_items()

    if not items:
        await ctx.send("Магазин пустий!")
    else:
        # Создаёт embed
        embed = discord.Embed(
            title="Магазин товарів🏪",
            description="Ось що доступно в нашому магазині🏷:",
            color=discord.Color.green()
        )

        # Добавляем товары в embed
        for item in items:
            item_name = item[0]  # Название товара
            item_price = item[1]  # Цена товара
            item_stock = item[2]  # Количество товара

            embed.add_field(
                name=item_name,
                value=f"Ціна: {item_price} монет\nНаявність: {item_stock} шт.",
                inline=False
            )


        file = discord.File("lavka_shop.png", filename="lavka_shop.png")
        embed.set_image(url="attachment://lavka_shop.png")


        await ctx.send(embed=embed, file=file)



@bot.command()
async def buy(ctx, item_name: str):
    success, price = await shop_system.buy_item(ctx.author.id, item_name)

    if success:
        embed = discord.Embed(
            title="🧾 Чек купівлі",
            description="Дякуємо за покупку в нашому магазині!",
            color=discord.Color.blue()
        )
        embed.add_field(name="🛍️ Товар", value=item_name, inline=False)
        embed.add_field(name="💰 Вартість", value=f"{price} монет", inline=False)
        embed.add_field(name="👤 Покупець", value=ctx.author.mention, inline=False)
        embed.set_footer(text="Поверненню та обміну не підлягає 😄")
        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Покупка не вдалася",
            description="Недостатньо коштів або товар відсутній у магазині.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Спробуйте вибрати інший товар або поповніть баланс")
        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def additem(ctx, item_name: str, price: int, stock: int):
    if price <= 0 or stock < 0:
        await ctx.send("❌ Ціна має бути більшою за 0, і кількість товару не може бути від'ємною!")
        return

    await shop_system.add_item(item_name, price, stock)
    await ctx.send(f"✅ Товар **{item_name}** додано в магазин за {price} монет, кількість: {stock} шт.")

@bot.command()
@commands.has_permissions(administrator=True)
async def removeitem(ctx, item_name: str):
    """Удаляет товар из магазина по имени."""
    
    # удалить товар
    success = await shop_system.remove_item(item_name)
    
    if success:
        await ctx.send(f"Товар '{item_name}' було успішно видалено з магазину.")
    else:
        await ctx.send(f"Товар '{item_name}' не знайдено в наявності.")

##@bot.command()
## async def lottery(ctx):
##    user_id = ctx.author.id
##    result = await economy.lottery(user_id)
##    await ctx.send(f"{ctx.author.mention} {result}")

@bot.command()
async def slots(ctx, bet: int):
    user_id = ctx.author.id
    result = await economy.slots(user_id, bet)

    embed = discord.Embed(
        title="🎰 Ігровий автомат",
        description=result,
        color=discord.Color.gold()
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed)

@slots.error
async def slots_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❗ Будь ласка, вкажіть ставку. Приклад: `!slots <ставка>`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❗ Ставка має бути числом. Приклад: `!slots 100")

@bot.command()
async def guess(ctx, bet: int, guess: int):
    user_id = ctx.author.id

    if guess < 1 or guess > 10:
        embed = discord.Embed(
            title="❌ Невірне число!",
            description="Будь ласка, вибери число від **1 до 10**.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    result = await economy.guess_number(user_id, bet, guess)

    embed = discord.Embed(
        title="🎲 Вгадай число",
        description=result,
        color=discord.Color.green() if "виграв" in result else discord.Color.red()
    )
    embed.set_footer(
        text=f"Гравець: {ctx.author.display_name}",
        icon_url=ctx.author.display_avatar.url  
    )

    await ctx.send(embed=embed)

@guess.error
async def guess_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❗ Будь ласка, вкажіть ставку і число. Приклад: !guess <ставка> <число від 1 до 10>")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❗ Аргументи мають бути числами. Приклад: !guess 100 5")

application_channel_id = 1347910187184291931

moderator_role_name = "Moderator"

@bot.command()
async def apply(ctx):
    if "Moderator" in [role.name for role in ctx.author.roles]:
        await ctx.send("Ви вже є модератором!")
        return

    #Создание заявки
    await ctx.send("Заявку на роль модератора було надіслано. Очікуйте відповіді від модераторів.")

    #Отправка заявки в канал для заявок
    application_channel = bot.get_channel(application_channel_id)
    embed = Embed(
        title="Нова заявка на роль модератора",
        description=f"Заявку подав: {ctx.author.mention}\nID користувача:: {ctx.author.id}",
        color=discord.Color.blue()
    )
    message = await application_channel.send(embed=embed)
    message = await application_channel.send(f"{ctx.author.mention}", embed=embed)

    #Добавление реакций на сообщение
    await message.add_reaction("✅")  # Принять
    await message.add_reaction("❌")  # Отклонить

@bot.event
async def on_reaction_add(reaction, user):
    """Обработка реакции модератора на заявку."""
    if user.bot:  # Игнорировать реакции ботов
        return

    # Проверка, что это модератор
    if "Moderator" not in [role.name for role in user.roles]:
        return

    # Получение заявки и сообщения
    if reaction.message.channel.id != application_channel_id:
        return

    # Проверка на правильные эмодзи
    if reaction.emoji == "✅":
        # Получение пользователя, который подал заявку
        applicant = reaction.message.mentions[0] if reaction.message.mentions else None
        if applicant:
            # Назначение роли модератора
            role = discord.utils.get(reaction.message.guild.roles, name="Moderator")
            if role:
                await applicant.add_roles(role)
                await reaction.message.channel.send(f"Заявка від {applicant.mention} схвалено. Роль модератора призначено.")
            else:
                await reaction.message.channel.send("Роль модератора не знайдено.")
        else:
            await reaction.message.channel.send("Не вдалося знайти користувача в заявці.")
    
    elif reaction.emoji == "❌":
        # Отклонение заявки
        applicant = reaction.message.mentions[0] if reaction.message.mentions else None
        if applicant:
            await reaction.message.channel.send(f"Заявка від {applicant.mention} відхилена.")  

@bot.command()
async def leaderboard(ctx):
    top_users = await economy.leaderboard()

    if not top_users:
        await ctx.send("Таблиця лідерів пуста!")
        return

    embed = discord.Embed(title="🏆 Топ-10 найбагатших користувачів", color=discord.Color.gold())

    for index, (user_id, balance) in enumerate(top_users, start=1):
        user = bot.get_user(user_id) or f"Користувач {user_id}"
        embed.add_field(name=f"{index}. {user}", value=f"💰 Баланс: {balance} монет", inline=False)

    await ctx.send(embed=embed)

def create_db():
    conn = sqlite3.connect("leveling.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1
    )
    """)
    conn.commit()
    conn.close()



def get_user_data(user_id):
    conn = sqlite3.connect("leveling.db")
    c = conn.cursor()
    c.execute("SELECT xp, level FROM users WHERE user_id = ?", (user_id,))
    data = c.fetchone()
    if not data:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        data = (0, 1)
    conn.close()
    return data

# Обновить XP и уровень
def update_xp(user_id, xp_gain):
    xp, level = get_user_data(user_id)
    xp += xp_gain
    current_xp_needed = level * 100  # сохраняет XP, нужный для текущего уровня
    xp_needed = current_xp_needed
    leveled_up = False
    while xp >= xp_needed:
        xp -= xp_needed
        level += 1
        xp_needed = level * 100
        leveled_up = True
    conn = sqlite3.connect("leveling.db")
    c = conn.cursor()
    c.execute("REPLACE INTO users (user_id, xp, level) VALUES (?, ?, ?)", (user_id, xp, level))
    conn.commit()
    conn.close()
    return level, xp, current_xp_needed, leveled_up


def create_progress_bar(xp, xp_needed, bar_length=15):
    if xp_needed == 0:
        return '[⚪' * bar_length + ']'
    progress = int(bar_length * xp / xp_needed)
    return f"[{'🔵' * progress}{'⚪' * (bar_length - progress)}]"


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await handle_antispam(message)
    
    user_id = message.author.id
    xp_gain = random.randint(5, 15)
    level, xp, xp_needed, leveled_up = update_xp(user_id, xp_gain)

    progress_bar = create_progress_bar(xp, xp_needed)

    if leveled_up:
        await message.channel.send(
            f"🎉 {message.author.mention} отримав рівень {level}!\n{progress_bar} ({xp}/{xp_needed} XP)"
        )

    await bot.process_commands(message)

# Команда: !lvl
@bot.command(name='lvl')
async def lvl(ctx, member: discord.Member = None):
    member = member or ctx.author
    xp, level = get_user_data(member.id)
    xp_needed = level * 150
    progress = create_progress_bar(xp, xp_needed)

    embed = discord.Embed(title=f"📊 Рівень гравця: {member.display_name}", color=discord.Color.purple())
    embed.add_field(name="Рівень", value=str(level))
    embed.add_field(name="Досвід", value=f"{xp}/{xp_needed}")
    embed.add_field(name="Прогрес", value=progress, inline=False)
    await ctx.send(embed=embed)


@bot.command(name="givelvl")
@commands.has_permissions(administrator=True)
async def set_level(ctx, member: discord.Member, level: int):
    if level < 1:
        await ctx.send("❌ Рівень має бути більшим за 0!")
        return

    
    xp = 0
    for lvl in range(1, level):
        xp += lvl * 100

    conn = sqlite3.connect("leveling.db")
    c = conn.cursor()
    c.execute("REPLACE INTO users (user_id, xp, level) VALUES (?, ?, ?)", (member.id, xp, level))
    conn.commit()
    conn.close()

    embed = discord.Embed(
        title="🎓 Рівень видано",
        description=f"{member.mention} тепер має рівень **{level}**!",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Видано: {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)


@set_level.error
async def set_level_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 У тебе немає прав для цього!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Використання: `!видатирівень @користувач <рівень>`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❗ Переконайся, що вказав користувача і ціле число рівня.")
    else:
        await ctx.send("❌ Сталася помилка під час виконання команди.")

import unittest
from discord.ext import commands
from DSBotPrince import bot 

class BotTest(unittest.TestCase):
    def test_prefix(self):
        self.assertEqual(bot.command_prefix, "!")

if __name__ == '__main__':
    unittest.main()


import asyncio
create_db()
async def main():
    await bot.load_extension("cogs.AdminLog")

bot.run(TOKEN)
asyncio.run(main())


