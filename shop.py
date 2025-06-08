import aiosqlite
from economy import Economy

class Shop:
    def __init__(self, db_path="economy.db"):
        self.db_path = db_path
        self.economy = Economy()  

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS shop (
                    item_name TEXT PRIMARY KEY, 
                    price INTEGER,
                    stock INTEGER DEFAULT 0  -- Добавлен столбец для хранения количества товара
                )
            """)
            await db.commit()

    async def get_items(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT item_name, price, stock FROM shop") as cursor:
                return await cursor.fetchall()

    async def add_item(self, item_name, price, stock=0):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO shop (item_name, price, stock) VALUES (?, ?, ?) "
                "ON CONFLICT(item_name) DO UPDATE SET price = ?, stock = ?",
                (item_name, price, stock, price, stock)
            )
            await db.commit()

    async def remove_item(self, item_name: str):
        """Удаляет товар из магазина."""
        async with aiosqlite.connect(self.db_path) as db:
            result = await db.execute("DELETE FROM shop WHERE item_name = ?", (item_name,))
            await db.commit()
            return result.rowcount > 0  

    async def buy_item(self, user_id, item_name):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT price, stock FROM shop WHERE item_name = ?", (item_name,)) as cursor:
                item = await cursor.fetchone()

                if not item:
                    return False, 0  # Товар не найден

                price, stock = item

                if stock <= 0:
                    return False, 0  # Нет в наличии

                user_balance = await self.economy.get_balance(user_id)  # Получает баланс пользователя

                if user_balance < price:
                    return False, 0  # Недостаточно средств

                # Обновляет баланс пользователя и количество товара в магазине
                await self.economy.update_balance(user_id, -price)
                await self.update_stock(item_name, stock - 1)  

                return True, price

    async def update_stock(self, item_name, stock):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE shop SET stock = ? WHERE item_name = ?",
                (stock, item_name)
            )
            await db.commit()
