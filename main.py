import discord

from discord.ext import commands

from dotenv import load_dotenv

import asyncio

import datetime

import os


intents = discord.Intents.default()
intents.message_content = True
intents.typing = False
intents.presences = False

warnings={}



class MyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='hello')
    async def hello(self, ctx):
        await ctx.send("Hello, world!")
    
    
    @commands.command(name='delete')
    async def delete_messages(self, ctx, amount: int):
        if amount <= 0:
            await ctx.send("Veuillez spécifier un nombre de messages à supprimer supérieur à 0.")
            return
        
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.send("Vous n'avez pas la permission de supprimer des messages.")
            return
        
        await ctx.message.delete()

        async for message in ctx.channel.history(limit=amount):
            await message.delete()
            
    @delete_messages.error
    async def delete_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Veuillez spécifier le nombre de messages à supprimer.')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('Veuillez spécifier un nombre valide de messages à supprimer.')
    
    @commands.command(name='mute')
    async def mute(self, ctx: commands.Context, member: discord.Member):
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.send("Vous n'avez pas la permission de gérer les rôles.")
            return
        
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not mute_role:
            mute_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(mute_role, speak=False, send_messages=False)
            
        await member.add_roles(mute_role)
        await ctx.send(f"{member.mention} a été mis en sourdine.")

    @commands.command(name='unmute')
    async def unmute(self, ctx, member: discord.Member):
        mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if mute_role in member.roles:
            await member.remove_roles(mute_role)
            await ctx.send(f"{member.mention} a été réactivé et n'est plus en sourdine.")
        else:
            await ctx.send(f"{member.mention} n'est pas en sourdine.")

def setup(bot):
    bot.add_cog(MyCommands(bot))
     
    


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.categories = {}

    def add_command_to_category(self, category, command):
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(command)

    @commands.command(name='helping')
    async def helping(self, ctx):
        embed = discord.Embed(title="Menu d'aide", description="Voici les commandes disponibles :")

        for category, commands in self.categories.items():
            command_list = [f'`{command.name}`' for command in commands]
            command_string = ' '.join(command_list)
            embed.add_field(name=category, value=command_string, inline=False)

        await ctx.send(embed=embed)
    
    class CustomHelpCommand(commands.HelpCommand):
        def __init__(self):
         super().__init__()

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Menu d'aide", description="Voici les commandes disponibles :")

        for cog, commands in mapping.items():
            if cog is None:
                category = "Autres"
            else:
                category = cog.qualified_name
                command_list = [f'`{command.name}`' for command in commands]
                command_string = ' '.join(command_list)
                embed.add_field(name=category, value=command_string, inline=False)
                
            destination = self.get_destination()
            await destination.send(embed=embed)
    
class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}

    @commands.command(name='warn')
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.send("Tu n'as pas la permission d'utiliser les commadnes de modération")
            return
        
        if reason is None:
            reason= "Aucune raison spécifiée"

        if member.id not in self.warnings:
            self.warnings[member.id] = []

        self.warnings[member.id].append(reason)

        await ctx.send(f'{member.mention}a été averti pour la raison suivante : {reason}')

    @commands.command(name='checkwarnings')
    async def checkwarnings(self, ctx, member: discord.Member):
        if member.id not in self.warnings or len(self.warnings[member.id]) == 0:
            await ctx.send(f"{member.mention} n'a aucun avertissement")
            return

        embed =  discord.Embed(title=f"Avertissments de {member.display_name}", color=discord.Color.red())
        for idx, reason in enumerate(self.warnings[member.id]):
            embed.add_field(name=f"Avertissment {idx+1}", value=reason,inline=False)

            await ctx.send(embed=embed)

    @warn.error
    async def warn_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Veuillez spécifier le membre a avertir')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('Membre invalide. Veuillez mentionner un membre du serveur')


    @checkwarnings.error
    async def view_warnings_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Veuillez spécifier le membre pour afficher ses aavertissments')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('Membre invalide. Veuillez mentionner un membre du serveur')
        
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        if member == ctx.author:
            await ctx.send("Vous ne pouvez pas vous bannir vous-même")
            return
            
        if not member.bot and member.top_role >= ctx.author.top_role:
            await ctx.send("Tu n'as pas la permission d'utiliser les commandes de modération")
            return
            
        if reason is None:
            reason = "Aucune raison n'est spécifiée"

        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} a été banni pour la raison suivante:")

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Veuillez spécifier le membre à bannir')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('Membre invalide. Veuillez mentinner le membre à bannir')
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send('Tu n\'as pas la permission d\' utiliser les commandes de modération')
        
    @commands.command(name='logout')
    @commands.is_owner()
    async def logout(self, ctx):
        await ctx.send("Déconnexion du bot en cours...")
        await self.bot.close()

    @commands.command(name='tempmute')
    @commands.guild_only()
    async def tempmute(self, ctx, member: discord.Member, duration: int, time_unit: str):
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.send("Tu n'as pas la permission d'utiliser les commandes de modération")
            return
        
        if not ctx.me.guild_permissions.manage_roles:
            await ctx.send("Je n'ai pas la permission de gérer les rôles")
            return
                
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

        if muted_role is None:
            await ctx.send("Le rôle 'Muted' n'existe pas sur ce serveur.")
            return

        await member.add_roles(muted_role)
        await ctx.send(f"{member.mention} a été mis temporairement muet")

        duration_in_seconds = convert_to_seconds(duration, time_unit)
        if duration_in_seconds is None:
                await ctx.send("Unité de temps invalide. Veuillez utiliser 's' pour les secondes, 'm' pour les minutes, ou 'h' pour les heures.")
                return
            
        await asyncio.sleep(duration_in_seconds)
        await member.remove_roles(muted_role)
        await ctx.send(f"{member.mention} n'est plus muet")
        
    @tempmute.error
    async def tempmute_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Veuillez spécifier le membre à tempmute, la durée et l\'unité de temps.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Argument invalide. Veuillez vérifier les types de données entrées.")

def convert_to_seconds(duration, time_unit):
    if time_unit == 's':
        return duration
    elif time_unit == 'm':
        return duration * 60
    elif time_unit == 'h':
        return duration * 60 * 60
    else:
        return None

def setup(bot):
    bot.add_cog(ModerationCog(bot))


class PingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping')
    async def ping(self, ctx):
        start_time = datetime.datetime.now()
        message = await ctx.send("Calcul du ping en cours...")
        end_time = datetime.datetime.now()

        latency = end_time - start_time
        latency_ms = latency.total_seconds() * 1000

        await message.edit(content=f"Pong! La latance est de: {latency_ms} ms")

bot = commands.Bot(command_prefix='!', intents=intents)
            



@bot.event
async def on_ready():
    print(f"We have logged in as")
    await bot.add_cog(MyCommands(bot))
    await bot.add_cog(ModerationCog(bot))
    await bot.add_cog(PingCog(bot))
    help_command = Help(bot)
        
    help_command.add_command_to_category('Informations', help_command.helping)
    help_command.add_command_to_category('Modération', MyCommands.mute)
    help_command.add_command_to_category('Modération', MyCommands.unmute)
    help_command.add_command_to_category('Modération', ModerationCog.tempmute)
    help_command.add_command_to_category('Modération', ModerationCog.warn)
    help_command.add_command_to_category('Modération', ModerationCog.checkwarnings)
    help_command.add_command_to_category('Modération', ModerationCog.ban)
    help_command.add_command_to_category('Modération', MyCommands.delete_messages)

    await bot.add_cog(help_command)

    while True:
        
        total_members = sum([guild.member_count for guild in bot.guilds])

        await bot.change_presence(activity=discord.Game(name='!helping'))

        await asyncio.sleep(600)

        await bot.change_presence(activity=discord.Streaming(name='Version bêta 0.5', url='https://www.twitch.tv/gimxi_exe'))

        await asyncio.sleep(600)

        await bot.change_presence(activity=discord.Streaming(name=f' {total_members} membres!!', url='https://www.twitch.tv/gimxi_exe'))
        
        await asyncio.sleep(600)
        return




token = os.getenv('DISCORD_TOKEN')
bot.run(token)


    


    
