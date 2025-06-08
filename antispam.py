import time
import asyncio
import re
from collections import defaultdict
import discord
from discord.ext import commands

# Настройки
MAX_MESSAGES = 5
TIME_WINDOW = 10
MAX_CAPS_PERCENT = 70  # % капса, чтобы считать сообщение за капс-лок
REPEAT_MESSAGE_THRESHOLD = 3  # сколько одинаковых сообщений считается флудом

banned_words = ["negr", "niger", "pidor", "hohol", "zhid", "dayn", "pidoras", "gomik", "pedik", "gomosek", "simp", "incel"]
mute_durations = [0, 180, 540, 900]
LOG_CHANNEL_NAME = "логи-бота"

user_message_times = defaultdict(list)
user_warnings = defaultdict(int)
user_last_messages = defaultdict(list)

# === Вспомогательные функции ===

async def log_action(guild, user, reason):
    log_channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if not log_channel:
        return

    embed = discord.Embed(
        title="🚨 Порушення",
        description=f"**Користувач:** {user.mention}\n**Причина:** {reason}",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=f"ID користувача: {user.id}")
    await log_channel.send(embed=embed)

async def mute_user(guild, member, duration, reason):
    mute_role = discord.utils.get(guild.roles, name="Muted")
    if not mute_role:
        mute_role = await guild.create_role(name="Muted")
        for channel in guild.text_channels:
            await channel.set_permissions(mute_role, send_messages=False)

    if mute_role not in member.roles:
        await member.add_roles(mute_role)
        await log_action(guild, member, f"{reason} — мут {duration // 60} мин.")
        await asyncio.sleep(duration)
        await member.remove_roles(mute_role)
        await log_action(guild, member, f"Розмут після {reason}")

# === Проверка ===

def is_capslock(message: str):
    letters = [c for c in message if c.isalpha()]
    if not letters:
        return False
    caps = [c for c in letters if c.isupper()]
    return (len(caps) / len(letters)) * 100 >= MAX_CAPS_PERCENT

def is_flooding(message_list):
    if len(message_list) < REPEAT_MESSAGE_THRESHOLD:
        return False
    return all(msg == message_list[0] for msg in message_list)

# === Главная функция ===

async def handle_antispam(message):
    if message.author.bot:
        return

    user_id = message.author.id
    now = time.time()

    # === Флуд по частоте сообщений ===
    user_message_times[user_id].append(now)
    user_message_times[user_id] = [t for t in user_message_times[user_id] if now - t < TIME_WINDOW]

    if len(user_message_times[user_id]) > MAX_MESSAGES:
        await message.delete()
        user_warnings[user_id] += 1
        await log_action(message.guild, message.author, "Флуд повідомленнями")
        duration = mute_durations[min(user_warnings[user_id], len(mute_durations)-1)]
        if duration > 0:
            await mute_user(message.guild, message.author, duration, "Флуд повідомленнями")
        return

    # === Флуд одинаковыми сообщениями ===
    content = message.content.strip()
    user_last_messages[user_id].append(content)
    if len(user_last_messages[user_id]) > REPEAT_MESSAGE_THRESHOLD:
        user_last_messages[user_id].pop(0)

    if is_flooding(user_last_messages[user_id]):
        await message.delete()
        user_warnings[user_id] += 1
        await log_action(message.guild, message.author, "Флуд однаковими повідомленнями")
        duration = mute_durations[min(user_warnings[user_id], len(mute_durations)-1)]
        if duration > 0:
            await mute_user(message.guild, message.author, duration, "Флуд однаковими повідомленнями")
        return

    # === КАПС ===
    if is_capslock(content) and len(content) > 10:
        await message.delete()
        user_warnings[user_id] += 1
        await log_action(message.guild, message.author, "Повідомлення з капсом")
        duration = mute_durations[min(user_warnings[user_id], len(mute_durations)-1)]
        if duration > 0:
            await mute_user(message.guild, message.author, duration, "Капс")
        return

    # === Запрещённые слова ===
    lower = content.lower()
    for word in banned_words:
        if re.search(rf"\b{re.escape(word)}\b", lower):
            await message.delete()
            user_warnings[user_id] += 1
            reason = f"Заборонене слово: `{word}`"
            await log_action(message.guild, message.author, reason)
            duration = mute_durations[min(user_warnings[user_id], len(mute_durations)-1)]
            if duration > 0:
                await mute_user(message.guild, message.author, duration, reason)
            return
