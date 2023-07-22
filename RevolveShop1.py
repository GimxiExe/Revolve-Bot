import discord

from discord import Intents

from discord.ext import commands

from RevolveShopBotCommands import MyCommands

from dotenv import load_dotenv

import os

intents = Intents.default()
client = discord.Client(intents=intents)



@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

@client.event
async def on_message(message):
    if message.content.startswith("!del"):
        number = int(message.content.split()[1])
        messages = await message.channel.history(limit=number + 1).flatten()

        for each_message in messages:
            await each_message.delete()


@client.event
async def on_message(message):
    if message.content == '!logout':
        await client.logout()


token = os.getenv("DISCORD_TOKEN")
client.run(token)





