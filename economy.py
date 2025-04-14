import aiosqlite
import random
import time
from datetime import datetime, timedelta

class Economy:
    def __init__(self, db_path="economy.db"):
        self.db_path = db_path

    async def initialize(self):
       async with aiosqlite.connect(self.db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                last_work INTEGER DEFAULT 0
            )
        """)
        await db.commit()


    async def get_balance(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def update_balance(self, user_id, amount):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO users (user_id, balance) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?",
                             (user_id, amount, amount))
            await db.commit()


    async def daily(self, user_id):
        await self.update_balance(user_id, 100)  

    async def transfer(self, from_user, to_user, amount):
        from_balance = await self.get_balance(from_user)
        if from_balance < amount:
            return False
        await self.update_balance(from_user, -amount)
        await self.update_balance(to_user, amount)
        return True

    async def lottery(self, user_id, ticket_price=50):
        """Игрок покупает билет, случайный участник получает весь фонд."""
        participants = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users WHERE balance >= ?", (ticket_price,)) as cursor:
                participants = [row[0] for row in await cursor.fetchall()]
        
        if user_id not in participants:
            return "Недостаточно средств для покупки билета."
        
        prize_pool = len(participants) * ticket_price
        winner = random.choice(participants) if participants else None
        
        if winner:
            await self.update_balance(winner, prize_pool)
            return f"Победитель лотереи: {winner}, выигрыш: {prize_pool} монет!"
        return "Лотерея не состоялась, недостаточно участников."
    
    async def slots(self, user_id, bet):
        """Игра в слоты, шанс на выигрыш x2 ставки."""
        if bet <= 0:
           return "❌ Ставка должна быть больше 0."
    
        user_balance = await self.get_balance(user_id)
        if user_balance < bet:
           return "❌ Недостаточно средств."
    
        symbols = ["🍒", "🍋", "🔔", "⭐", "💎"]
        result = [random.choice(symbols) for _ in range(3)]
        display = " | ".join(result)
    
        if len(set(result)) == 1:
             winnings = bet * 2
             await self.update_balance(user_id, winnings)
             return f"`{display}`\n🎉 **Поздравляем!** Вы выиграли **{winnings}** монет!"
        else:
             await self.update_balance(user_id, -bet)
        return f"`{display}`\n😢 Увы, вы проиграли **{bet}** монет. Попробуйте ещё раз!"

    
    async def guess_number(self, user_id, bet, guess):
       if bet <= 0:
           return "Ставка должна быть больше 0."

       user_balance = await self.get_balance(user_id)
       if user_balance < bet:
           return "У тебя недостаточно средств для ставки."

       number = random.randint(1, 10)

       if guess == number:
           winnings = bet * 5
           await self.update_balance(user_id, winnings)
           return f"🎉 Поздравляем! Ты угадал число **{number}** и выиграл **{winnings}** монет!"
       else:
           await self.update_balance(user_id, -bet)
           return f"😢 Увы, ты выбрал **{guess}**, а выпало число **{number}**. Ты проиграл **{bet}** монет."



    async def leaderboard(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10") as cursor:
                return await cursor.fetchall()    