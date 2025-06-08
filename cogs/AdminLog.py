import discord
from discord.ext import commands

class AdminLog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1359876929909428314 

    # Очистка сообщений
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 Очищено {amount} сообщений!", delete_after=3)

    # Кик
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="Без причины"):
        await member.kick(reason=reason)
        await ctx.send(f"👢 {member.mention} был кикнут. Причина: {reason}")

    # Бан
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="Без причины"):
        await member.ban(reason=reason)
        await ctx.send(f"🔨 {member.mention} был забанен. Причина: {reason}")

    # Разбан
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        user = await self.bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ Пользователь {user} был разбанен.")

    # Вход/выход
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(self.log_channel_id)
        await channel.send(f"✅ Участник зашел: {member.mention}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.bot.get_channel(self.log_channel_id)
        await channel.send(f"❌ Участник вышел: {member.mention}")

    # Удаление сообщений
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        channel = self.bot.get_channel(self.log_channel_id)
        embed = discord.Embed(title="🗑️ Сообщение удалено", color=discord.Color.red())
        embed.add_field(name="Автор", value=message.author.mention)
        embed.add_field(name="Канал", value=message.channel.mention)
        embed.add_field(name="Содержание", value=message.content or "Пустое сообщение", inline=False)
        await channel.send(embed=embed)

    # Изменение ролей
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            channel = self.bot.get_channel(self.log_channel_id)
            embed = discord.Embed(title="🎭 Изменение ролей", color=discord.Color.orange())
            embed.add_field(name="Пользователь", value=after.mention, inline=True)
            added = [r.name for r in after.roles if r not in before.roles]
            removed = [r.name for r in before.roles if r not in after.roles]
            if added:
                embed.add_field(name="Добавлены роли", value=", ".join(added), inline=False)
            if removed:
                embed.add_field(name="Удалены роли", value=", ".join(removed), inline=False)
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdminLog(bot))
