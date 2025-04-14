
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
    print(f'Бот {bot.user} подключен к Discord!')



@bot.command(name="stats")
async def stats(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = member.id

    # Получаем XP и уровень
    xp, level = get_user_data(user_id)
    xp_needed = level * 100
    progress = create_progress_bar(xp, xp_needed)

    # Получаем баланс из экономики
    balance = await economy.get_balance(user_id)

    # Роли (без @everyone)
    roles = [role.name for role in member.roles if role.name != "@everyone"]
    roles_display = ", ".join(roles) if roles else "Нет"

    # Создаём embed
    embed = discord.Embed(
        title=f"📊 Статистика пользователя {member.display_name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

    embed.add_field(name="Уровень", value=str(level), inline=True)
    embed.add_field(name="XP", value=f"{xp}/{xp_needed}", inline=True)
    embed.add_field(name="Прогресс", value=progress, inline=False)
    embed.add_field(name="Баланс", value=f"{balance:,} 🪙", inline=True)
    embed.add_field(name="Роли", value=roles_display, inline=False)
    embed.set_footer(text=f"ID: {user_id} • Присоединился: {member.joined_at.date()}")

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
    await ctx.send(f'Пинг бота: {latency}ms')

# Команда !8ball
@bot.command(name='8ball')
async def eight_ball(ctx, *, question: str = None):
    if not question:
        await ctx.send("🎱 Задайте свой вопрос, например: `!8ball Стоит ли мне учиться программированию?`")
        return

    if not question.endswith('?'):
        await ctx.send("🎱 Ваш вопрос должен заканчиваться на вопросительный знак `?`.")
        return

    # Список ответов
    responses = [
        "Безусловно да! 😊",
        "Это точно не так. 😔",
        "Скорее всего, да.",
        "Возможно.",
        "Я не уверен. Попробуйте позже. 🤔",
        "Шансы малы.",
        "Определенно нет.",
        "Даже не сомневайся!",
        "Я вижу, что да!",
        "Сейчас лучше не спрашивать."
    ]

    # Случайный выбор ответа
    answer = random.choice(responses)
    await ctx.send(f"🎱 Вопрос: {question}\nОтвет: {answer}")

@bot.command(name='commands')
async def show_commands(ctx):
    embed = discord.Embed(
        title="📜 Список команд",
        description="Вот доступные команды бота:",
        color=discord.Color.blue()
    )

    embed.add_field(name="🧍‍♂️ Общие", value="""
`!stats [пользователь]` — Показать статистику пользователя
`!Hello` — Приветствие от бота
`!ping` — Показать пинг бота
`!8ball [вопрос?]` — Магический шар ответит на твой вопрос
""", inline=False)

    embed.add_field(name="🪙 Экономика", value="""
`!balance` — Проверить баланс
`!work` — Получить ежедневную награду
`!give @пользователь <сумма>` — Передать монеты
`!shop` — Открыть магазин
`!buy <предмет>` — Купить предмет
`!removeitem <название>` — Удалить предмет из магазина
`!additem <название> <цена> <кол-во>` — Добавить предмет в магазин
""", inline=False)

    embed.add_field(name="🎮 Игры", value="""
`!slots <ставка>` — Игровой автомат
`!guess <ставка> <число от 1 до 10>` — Угадай число
""", inline=False)

    embed.add_field(name="📈 Уровни", value="""
`!lvl [пользователь]` — Показать уровень и опыт
`!givelvl @пользователь <уровень>` — Выдать уровень (Могут изпользовать админы)
""", inline=False)

    embed.add_field(name="👮 Модерация", value="""
`!apply` — Подать заявку на модератора
""", inline=False)

    embed.set_footer(text="Для подробностей по каждой команде — обратись к разработчику 😊")
    await ctx.send(embed=embed)



@bot.event
async def on_member_join(member):
    
    role = discord.utils.get(member.guild.roles, name="Зритель 👤")
    if role:
        await member.add_roles(role)
        print(f"Роль 'Зритель 👤' назначена {member.name}")

    
    welcome_channel_id = 1292845820898574470  
    channel = bot.get_channel(welcome_channel_id)

    if channel:
        welcome_message = f"Добро пожаловать, {member.mention}! 🎉"
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
        description=f"**{ctx.author.display_name}**, вот ваш текущий баланс:",
        color=discord.Color.gold()
    )
    embed.add_field(name="Монеты", value=f"**{bal:,}** 🪙", inline=False)
    embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    embed.set_footer(text=f"ID: {ctx.author.id}")

    await ctx.send(embed=embed)

@bot.command()
async def work(ctx):
    earnings = await economy.work(ctx.author.id)
    await ctx.send(f"{ctx.author.mention}, вы получили 100 монет за ежедневный бонус!")

@bot.command()
async def give(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Сумма перевода должна быть больше 0!")
        return

    success = await economy.transfer(ctx.author.id, member.id, amount)

    if success:
        embed = discord.Embed(
            title="🏦 Банковский перевод",
            description=f"{ctx.author.mention} → {member.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="💰 Сумма", value=f"{amount} монет", inline=False)
        embed.set_footer(text="Транзакция завершена успешно")
        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Ошибка перевода",
            description="Недостаточно средств для перевода.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Пожалуйста, проверьте свой баланс")
        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)


@bot.command()
async def shop(ctx):
    items = await shop_system.get_items()

    if not items:
        await ctx.send("Магазин пустой!")
    else:
        # Создаём embed
        embed = discord.Embed(
            title="Магазин товаров🏪",
            description="Вот что доступно в нашем магазине🏷:",
            color=discord.Color.green()
        )

        # Добавляем товары в embed
        for item in items:
            item_name = item[0]  # Название товара
            item_price = item[1]  # Цена товара
            item_stock = item[2]  # Количество товара

            embed.add_field(
                name=item_name,
                value=f"Цена: {item_price} монет\nНаличие: {item_stock} шт.",
                inline=False
            )

        # Загружаем изображение как файл
        file = discord.File("lavka_shop.png", filename="lavka_shop.png")
        embed.set_image(url="attachment://lavka_shop.png")


        await ctx.send(embed=embed, file=file)



@bot.command()
async def buy(ctx, item_name: str):
    success, price = await shop_system.buy_item(ctx.author.id, item_name)

    if success:
        embed = discord.Embed(
            title="🧾 Чек покупки",
            description="Спасибо за покупку в нашем магазине!",
            color=discord.Color.blue()
        )
        embed.add_field(name="🛍️ Товар", value=item_name, inline=False)
        embed.add_field(name="💰 Стоимость", value=f"{price} монет", inline=False)
        embed.add_field(name="👤 Покупатель", value=ctx.author.mention, inline=False)
        embed.set_footer(text="Возврату и обмену не подлежит 😄")
        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Покупка не удалась",
            description="Недостаточно средств или товар отсутствует в магазине.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Попробуйте выбрать другой товар или пополните баланс")
        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def additem(ctx, item_name: str, price: int, stock: int):
    if price <= 0 or stock < 0:
        await ctx.send("❌ Цена должна быть больше 0, и количество товара не может быть отрицательным!")
        return

    await shop_system.add_item(item_name, price, stock)
    await ctx.send(f"✅ Товар **{item_name}** добавлен в магазин за {price} монет, количество: {stock} шт.")

@bot.command()
@commands.has_permissions(administrator=True)
async def removeitem(ctx, item_name: str):
    """Удаляет товар из магазина по имени."""
    
    # Пытаемся удалить товар
    success = await shop_system.remove_item(item_name)
    
    if success:
        await ctx.send(f"Товар '{item_name}' был успешно удален из магазина.")
    else:
        await ctx.send(f"Товар '{item_name}' не найден в магазине.")

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
        title="🎰 Игровой автомат",
        description=result,
        color=discord.Color.gold()
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed)

@slots.error
async def slots_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❗ Пожалуйста, укажите ставку. Пример: `!slots <ставка>`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❗ Ставка должна быть числом. Пример: `!slots 100`")

@bot.command()
async def guess(ctx, bet: int, guess: int):
    user_id = ctx.author.id

    if guess < 1 or guess > 10:
        embed = discord.Embed(
            title="❌ Неверное число!",
            description="Пожалуйста, выбери число от **1 до 10**.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    result = await economy.guess_number(user_id, bet, guess)

    embed = discord.Embed(
        title="🎲 Угадай число",
        description=result,
        color=discord.Color.green() if "выиграл" in result else discord.Color.red()
    )
    embed.set_footer(
        text=f"Игрок: {ctx.author.display_name}",
        icon_url=ctx.author.display_avatar.url  # заменил на display_avatar для совместимости
    )

    await ctx.send(embed=embed)

@guess.error
async def guess_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❗ Пожалуйста, укажите ставку и число. Пример: !guess <ставка> <число от 1 до 10>")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❗ Аргументы должны быть числами. Пример: !guess 100 5")

application_channel_id = 1347910187184291931

moderator_role_name = "Moderator"

@bot.command()
async def apply(ctx):
    if "Moderator" in [role.name for role in ctx.author.roles]:
        await ctx.send("Вы уже являетесь модератором!")
        return

    #Создание заявки
    await ctx.send("Заявка на роль модератора была отправлена. Ожидайте ответа от модераторов.")

    #Отправка заявки в канал для заявок
    application_channel = bot.get_channel(application_channel_id)
    embed = Embed(
        title="Новая заявка на роль модератора",
        description=f"Заявку подал: {ctx.author.mention}\nID пользователя: {ctx.author.id}",
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
                await reaction.message.channel.send(f"Заявка от {applicant.mention} одобрена. Роль модератора назначена.")
            else:
                await reaction.message.channel.send("Роль модератора не найдена.")
        else:
            await reaction.message.channel.send("Не удалось найти пользователя в заявке.")
    
    elif reaction.emoji == "❌":
        # Отклонение заявки
        applicant = reaction.message.mentions[0] if reaction.message.mentions else None
        if applicant:
            await reaction.message.channel.send(f"Заявка от {applicant.mention} отклонена.")  

@bot.command()
async def leaderboard(ctx):
    top_users = await economy.leaderboard()

    if not top_users:
        await ctx.send("Таблица лидеров пуста!")
        return

    embed = discord.Embed(title="🏆 Топ 10 богатых пользователей", color=discord.Color.gold())

    for index, (user_id, balance) in enumerate(top_users, start=1):
        user = bot.get_user(user_id) or f"Пользователь {user_id}"
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


# 📊 Получить данные пользователя
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

# ➕ Обновить XP и уровень
def update_xp(user_id, xp_gain):
    xp, level = get_user_data(user_id)
    xp += xp_gain
    current_xp_needed = level * 100  # ✅ сохраняем XP, нужный для текущего уровня
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
            f"🎉 {message.author.mention} получил уровень {level}!\n{progress_bar} ({xp}/{xp_needed} XP)"
        )

    await bot.process_commands(message)

# 📈 Команда: !lvl
@bot.command(name='lvl')
async def lvl(ctx, member: discord.Member = None):
    member = member or ctx.author
    xp, level = get_user_data(member.id)
    xp_needed = level * 100
    progress = create_progress_bar(xp, xp_needed)

    embed = discord.Embed(title=f"📊 Уровень игрока: {member.display_name}", color=discord.Color.purple())
    embed.add_field(name="Уровень", value=str(level))
    embed.add_field(name="Опыт", value=f"{xp}/{xp_needed}")
    embed.add_field(name="Прогресс", value=progress, inline=False)
    await ctx.send(embed=embed)


@bot.command(name="givelvl")
@commands.has_permissions(administrator=True)
async def set_level(ctx, member: discord.Member, level: int):
    if level < 1:
        await ctx.send("❌ Уровень должен быть больше 0!")
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
        title="🎓 Уровень выдан",
        description=f"{member.mention} теперь имеет уровень **{level}**!",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Выдано: {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)


@set_level.error
async def set_level_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 У тебя нет прав для этого!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Использование: `!выдатьуровень @пользователь <уровень>`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❗ Убедись, что указал пользователя и целое число уровня.")
    else:
        await ctx.send("❌ Произошла ошибка при выполнении команды.")


import asyncio
create_db()
async def main():
    await bot.load_extension("cogs.AdminLog")

bot.run(TOKEN)
asyncio.run(main())


