import discord
from discord.ext import commands, tasks
from PIL import ImageGrab
from io import BytesIO
import datetime
import asyncio
import pygetwindow as gw
import keyboard

TOKEN = 'YOUR TOKEN HERE'
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = commands.Bot(command_prefix='/', intents=intents)

# Global variables to track screenshot state and counter message
screenshot_mode_active = False
counter_message = None
last_screenshot_message = None

@client.event
async def on_ready():
    print(f'Logged in as {client.user.name} - {client.user.id}')
    print('------')

@client.command(name='poe')  # Change the command name to '/poe'
async def path_of_exile(ctx):
    global screenshot_mode_active
    global counter_message
    global last_screenshot_message

    embed = discord.Embed(title='Path of Exile Controls', description='Choose an option:\n Set HotKey For Kuduku to F9', color=0x00ff00)
    embed.add_field(name='Start', value='Press F9', inline=False)
    embed.add_field(name='Stop', value='Press F9', inline=False)
    embed.add_field(name='Screenshot Mode', value='Take screenshots every 30 seconds for the next 5 minutes', inline=False)
    embed.add_field(name='Exit Path of Exile', value='Close the "Path of Exile" window', inline=False)
    embed.add_field(name='Exit Path of Exile in', value='Close the "Path of Exile" window in a specified time', inline=False)

    if not counter_message:
        msg = await ctx.send(embed=embed)
        counter_message = msg
        await msg.add_reaction('⏯️')  # Start
        await msg.add_reaction('❌')   # Stop
        await msg.add_reaction('📸')   # Screenshot
        await msg.add_reaction('🔪')   # Exit Path of Exile
        await msg.add_reaction('⏲️')   # Exit Path of Exile in

@client.event
async def on_reaction_add(reaction, user):
    if user.bot:  # Ignore reactions from bots
        return

    global screenshot_mode_active
    global counter_message
    global last_screenshot_message

    if reaction.message == counter_message:
        if str(reaction.emoji) == '⏯️':  # Start button clicked
            await reaction.message.channel.send('Start button clicked')
            keyboard.press_and_release('F9')  # Simulate the F9 key press
        elif str(reaction.emoji) == '❌':  # Stop button clicked
            await reaction.message.channel.send('Stop button clicked')
            screenshot_mode_active = False  # Stop the screenshot mode
            keyboard.press_and_release('F9')  # Simulate the F9 key press
        elif str(reaction.emoji) == '📸':  # Screenshot button clicked
            await reaction.message.channel.send('Screenshot button clicked')
            screenshot_mode_active = True

            poe_window = gw.getWindowsWithTitle('Path of Exile')[0]  # Find the "Path of Exile" window
            end_time = datetime.datetime.now() + datetime.timedelta(minutes=5)

            while datetime.datetime.now() < end_time and screenshot_mode_active:
                screenshot = ImageGrab.grab(bbox=(poe_window.left, poe_window.top, poe_window.right, poe_window.bottom))
                
                screenshot_bytes = BytesIO()
                screenshot.save(screenshot_bytes, format='PNG')
                screenshot_bytes.seek(0)

                file = discord.File(screenshot_bytes, filename='screenshot.png')
                new_screenshot_message = await reaction.message.channel.send(file=file)

                if last_screenshot_message:
                    await last_screenshot_message.delete()

                last_screenshot_message = new_screenshot_message

                countdown_seconds = (end_time - datetime.datetime.now()).seconds
                countdown_minutes = countdown_seconds // 60
                countdown_seconds_remainder = countdown_seconds % 60
                countdown_str = f'Next screenshot in: {countdown_minutes:02d}:{countdown_seconds_remainder:02d}'
                embed = reaction.message.embeds[0]
                embed.set_field_at(2, name='Screenshot Mode', value=f'Take screenshots every 30 seconds for the next 5 minutes\n{countdown_str}', inline=False)
                await counter_message.edit(embed=embed)

                for _ in range(30):  # Update the counter every second
                    countdown_seconds -= 1
                    countdown_minutes = countdown_seconds // 60
                    countdown_seconds_remainder = countdown_seconds % 60
                    countdown_str = f'Next screenshot in: {countdown_minutes:02d}:{countdown_seconds_remainder:02d}'
                    embed.set_field_at(2, name='Screenshot Mode', value=f'Take screenshots every 30 seconds for the next 5 minutes\n{countdown_str}', inline=False)
                    await counter_message.edit(embed=embed)
                    await asyncio.sleep(1)  # Wait for 1 second

            screenshot_mode_active = False
        elif str(reaction.emoji) == '🔪':  # Exit Path of Exile button clicked
            await reaction.message.channel.send('Exit Path of Exile button clicked')
            gw.getWindowsWithTitle('Path of Exile')[0].close()  # Close the "Path of Exile" window
        elif str(reaction.emoji) == '⏲️':  # Exit Path of Exile in button clicked
            await reaction.message.channel.send('Exit Path of Exile in button clicked. Please provide the time in minutes.')

            def check(message):
                return message.author == user and message.channel == reaction.message.channel

            try:
                await reaction.message.channel.send('Enter the time in minutes:')
                time_message = await client.wait_for('message', timeout=60.0, check=check)
                time_in_minutes = int(time_message.content)
                await reaction.message.channel.send(f'Closing "Path of Exile" in {time_in_minutes} minutes.')

                poe_window = gw.getWindowsWithTitle('Path of Exile')[0]  # Find the "Path of Exile" window
                end_time = datetime.datetime.now() + datetime.timedelta(minutes=time_in_minutes)

                while datetime.datetime.now() < end_time:
                    countdown_seconds = (end_time - datetime.datetime.now()).seconds
                    countdown_minutes = countdown_seconds // 60
                    countdown_seconds_remainder = countdown_seconds % 60
                    countdown_str = f'Closing in: {countdown_minutes:02d}:{countdown_seconds_remainder:02d}'
                    embed = reaction.message.embeds[0]
                    embed.set_field_at(4, name='Exit Path of Exile in', value=f'Close the "Path of Exile" window in {time_in_minutes} minutes\n{countdown_str}', inline=False)
                    await counter_message.edit(embed=embed)
                    await asyncio.sleep(1)  # Wait for 1 second

                gw.getWindowsWithTitle('Path of Exile')[0].close()  # Close the "Path of Exile" window
            except asyncio.TimeoutError:
                await reaction.message.channel.send('You took too long to provide the time.')
            except ValueError:
                await reaction.message.channel.send('Invalid input. Please provide a valid integer for time in minutes.')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower() == 'close poe':
        gw.getWindowsWithTitle('Path of Exile')[0].close()  # Close the "Path of Exile" window

    await client.process_commands(message)

client.run(TOKEN)
