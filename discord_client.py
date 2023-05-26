#!/usr/bin/env python3

import logging
from dotenv import load_dotenv
from time import time
import os
from rich.logging import RichHandler

import discord
from discord.ext import commands
from discord import app_commands

import gradio_chat

load_dotenv()
TOKEN = os.environ['DISCORD_BOT_TOKEN']
STREAM_MIN_DELAY_SECS = float(os.environ['DISCORD_STREAM_MIN_DELAY_SECS']) if os.environ.get('DISCORD_STREAM_MIN_DELAY_SECS', '') else 0
WHITELISTED_GUILD_IDS = list(map(int, filter(lambda id: id, os.environ.get('DISCORD_WHITELISTED_GUILD_IDS', '').split(','))))

# Logging
FORMAT = "%(name)-16s | %(message)s"
logging.basicConfig(level="NOTSET", format=FORMAT, datefmt="%X", handlers=[RichHandler(show_path=False)])
logger = logging.getLogger("Client")
logging.getLogger("discord").setLevel(logging.INFO)
logging.getLogger("websockets").setLevel(logging.INFO)
logging.getLogger("gradio_chat").setLevel(logging.INFO)

# Creating client
logger.debug("Starting bot...")
client = discord.Client(intents=discord.Intents.default())
@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user}")
    logger.info(f"Currently in {len(client.guilds)} guild(s): {', '.join([ f'{guild} (Id: {guild.id})' for guild in client.guilds ])}")
    synced = await tree.sync()
    logger.info(f"Synced {len(synced)} commands")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="/chat"))

@client.event
async def on_guild_join(guild: discord.Guild):
    logger.info(f"Joined guild {guild} (Id: {guild.id})")

@client.event
async def on_guild_remove(guild: discord.Guild):
    logger.info(f"Removed from guild {guild} (Id: {guild.id})")

# Adding commands
tree = app_commands.CommandTree(client)

class StopButton(discord.ui.View):
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.warning(f"{interaction.user} requested stopping a reponse!")
        await interaction.response.send_message(f"Stopped by {interaction.user.mention}", silent=True)
        await gradio_chat.stop(generalize_username(str(interaction.user)))

occupied = False
occupied_by_user = None
occupied_in_channel = None

@tree.command(name="chat", description="Send a message to the bot and get a response!")
async def chat_command(interaction: discord.Interaction, message: str):
    #message = discord.utils.escape_mentions(discord.utils.remove_markdown(message))
    cleaned_message = discord.utils.escape_markdown(message)
    allowed_mentions = discord.AllowedMentions(everyone=False, users=False, roles=False, replied_user=False)
    global occupied, occupied_by_user, occupied_in_channel
    logger.info(f"{interaction.user} executed /chat")
    if interaction.guild_id is None:
        logger.warning(f"Command was triggered in DMs from {interaction.user} (Id: {interaction.user.id})")
        await interaction.response.send_message(content="*CTA is very shy and doesn't want to respond in private DMs.*")
        return
    if len(WHITELISTED_GUILD_IDS) > 0 and interaction.guild_id not in WHITELISTED_GUILD_IDS:
        logger.warning(f"Command was triggered from non-whitelisted Guild {interaction.guild} (Id: {interaction.guild_id}) by {interaction.user} (Id: {interaction.user.id})")
        await interaction.response.send_message(content="*CTA wonders what strange, unknown Discord server this is.*")
        return
    your_name = generalize_username(str(interaction.user))

    if message == "!help":
        response = "**SYSTEM:** Commands: !stop, !reset"
        await interaction.response.send_message(content=response)
        return
    if message == "!stop":
        response = "**SYSTEM:** Attempting to stop output..."
        await interaction.response.send_message(content=response)
        try:
            await gradio_chat.pre_stop(your_name)
            await gradio_chat.stop()
            await interaction.edit_original_response(content=response + " Done")
        except BaseException as ex:
            logger.exception("Failed stopping output")
            await interaction.edit_original_response(content=response + "\n**ERROR**: ```" + str(ex) + "```")
        return
    if message == "!reset":
        response = "**SYSTEM:** Resetting context..."
        await interaction.response.send_message(content=response)
        try:
            await gradio_chat.pre_set_context()
            await gradio_chat.set_context()
            await interaction.edit_original_response(content=response + " Done")
        except BaseException as ex:
            logger.exception("Failed resetting context")
            await interaction.edit_original_response(content=response + "\n**ERROR**: ```" + str(ex) + "```")
        return
    if occupied:
        logger.warning(f"Ignored message from {interaction.user} (Id: {interaction.user.id}) in channel {interaction.channel} (Id: {interaction.channel_id}) because already occupied.")
        await interaction.response.send_message(content="*CTA is currently occupied answering" + ("" if occupied_by_user is None else " " + occupied_by_user) + ("" if occupied_in_channel is None else " in " + occupied_in_channel) + " and doesn't notice your message*", allowed_mentions=allowed_mentions)
        return
    logger.info(f"Processing message from {interaction.user} (Id: {interaction.user.id}) in channel {interaction.channel} (Id: {interaction.channel_id}): {message}")
    occupied = True
    occupied_by_user = interaction.user.mention
    occupied_in_channel = interaction.channel.mention

    content_prefix=f"**{your_name}:** {cleaned_message}\n**Me:** "
    #await interaction.response.send_message(content=content_prefix + "*Sending…*", view=StopButton())
    await interaction.response.send_message(content=shorten_output(content_prefix + "*Sending…*"), allowed_mentions=allowed_mentions, silent=True)
    #await interaction.response.send_message(content="*Sending…*", view=StopButton())
    #embed = discord.Embed(color=0xF0F0F0)
    #embed.add_field(name=your_name, value=message, inline=False)
    #embed.add_field(name="Me", value="*Sending…*", inline=False)
    #await interaction.response.send_message(embed=embed, view=StopButton())

    last_output = None
    try:
        #chat_message = generalize_username(str(interaction.user)) + ": " + message
        chat_message = message
        last_update_at = None
        async for (output, completed) in gradio_chat.configure_send_and_receive(chat_message, your_name=your_name):
            if not completed and last_update_at is not None and time() - last_update_at < STREAM_MIN_DELAY_SECS and STREAM_MIN_DELAY_SECS > 0:
                continue
            last_update_at = time()
            #logger.info("Response: " + output + ("" if completed else " (generating)"))
            if completed:
                logger.info("Completed response: " + output)
            last_output = output
            show_typing_indicator = not completed and not output.strip().endswith("...") and not output.strip().endswith("..._")
            #await interaction.edit_original_response(content=output + (" …" if show_typing_indicator else ""))
            #embed = discord.Embed(color=0xF0F0F0)
            #embed.add_field(name=your_name, value=message, inline=False)
            #embed.add_field(name="Me", value=output + (" …" if show_typing_indicator else ""), inline=False)
            #maybe_remove_view = { "view": None } if completed else {}
            maybe_remove_view = {}
            #if completed:
            #    await interaction.edit_original_response(embed=embed, view=None)
            #else:
            #    await interaction.edit_original_response(embed=embed)
            await interaction.edit_original_response(content=shorten_output(content_prefix + output + (" …" if show_typing_indicator else "")), **maybe_remove_view, allowed_mentions=allowed_mentions)
    except BaseException as ex:
        logger.exception("Failed generating output")
        try: # Prevent goofs trying to occupy the bot forever
            await interaction.edit_original_response(content=shorten_output(("" if last_output is None else content_prefix + last_output + "\n") + "**ERROR: **```" + str(ex) + "```"))
        except:
            pass
    occupied = False
    occupied_by_user = None
    occupied_in_channel = None

def shorten_output(output):
    MAX_LEN = 2000
    if len(output) > MAX_LEN:
        logger.warning(f"Some output would be longer than {MAX_LEN} chars and will be shortened!")
        suffix = "...and XXXXXX more characters"
        output = output[:MAX_LEN-len(suffix)] + suffix.replace("XXXXXX", str(len(output) - (MAX_LEN-len(suffix))))
    return output

def generalize_username(discord_username):
    if discord_username.startswith("@"):
        discord_username = discord_username[1:]
    if '#' in discord_username:
        discord_username = discord_username.split('#')[0]
    return discord_username

# Running client
client.run(token=TOKEN, log_handler=None)
logger.warning("Bot stopped for some reason!")
