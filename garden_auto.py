#!/usr/bin/env python

import time
import datetime
import board
from os.path import exists
from os import getenv
import csv
from dotenv import load_dotenv

from PIL import Image, ImageDraw, ImageFont
from ST7735 import ST7735

from adafruit_seesaw.seesaw import Seesaw

import asyncio
import telegram

import SoilState

# The threshold for what counts as 'damp' on the sensor. Normal range is 200-2000
# (Allegedly? Seeing some weird values in the logs so far...)
DAMP_THRESHOLD = 400

# Screen init
SPI_SPEED_MHZ = 80

font = ImageFont.truetype('DejaVuSans-Bold.ttf', 30)

st7735 = ST7735(
    rotation=270,  
    port=0,       
    cs=1,
    dc=9,         
    backlight=25,
    spi_speed_hz=SPI_SPEED_MHZ * 1000 * 1000
)
st7735.begin()

# Sensor init
i2c_bus = board.I2C()
sensor = Seesaw(i2c_bus, addr=0x36)

# Using a state machine to smooth out fluctuations in sensor measurement
state = SoilState.SoilState()

# Telegram bot init
load_dotenv()
BOT_TOKEN = getenv('BOT_TOKEN')
CHAT_ID = getenv('CHAT_ID')
bot = telegram.Bot(BOT_TOKEN)

# Set initial last times to forever ago
last_dry_message_time = datetime.datetime.fromtimestamp(0)
last_watered_message_time = datetime.datetime.fromtimestamp(0)
last_log_time = datetime.datetime.fromtimestamp(0)

# Create soil log file with csv headers if it doesn't exist
if not exists('soil_log.csv'):
    with open('soil_log.csv', 'w') as csvfile:
        soilwriter = csv.writer(csvfile, delimiter=',')
        soilwriter.writerow(['time', 'temp', 'moisture'])

# Update text on the screen with specified text
def draw_text(text):
    global font
    image = Image.open('garden_auto_flower_bg.png')
    draw = ImageDraw.Draw(image)
    draw.text((10, 25), text, fill='#000000', font=font)
    st7735.display(image)

# Send message to specified chat_id using telegram bot
async def send_bot_message(message):
    global bot, CHAT_ID

    async with bot:
      await bot.send_message(text=message, chat_id=CHAT_ID)
    
async def send_dry_message():
    # 8 hour timeout so we don't spam ourselves
    global last_dry_message_time
    if datetime.datetime.now() - last_dry_message_time < datetime.timedelta(hours=8):
        return

    await send_bot_message('Plants are dry! Water us plz ;-;')
    last_dry_message_time = datetime.datetime.now()

async def send_watered_message():
    # 8 hour timeout so we don't spam ourselves
    global last_watered_message_time
    if datetime.datetime.now() - last_watered_message_time < datetime.timedelta(hours=8):
        return

    await send_bot_message('Yay! Thank you for watering us! <3')
    last_watered_message_time = datetime.datetime.now()

# Main program loop
async def main():
    global bot, last_log_time
    print('Hello from garden bot!')
    while True:

        moisture = sensor.moisture_read()
        temp = sensor.get_temp()

        # Log the current date/time, temp, and moisture if we haven't logged in over an hour
        if datetime.datetime.now() - last_log_time > datetime.timedelta(hours=1):
            with open('soil_log.csv', 'a') as csvfile:
                soilwriter = csv.writer(csvfile, delimiter=',')
                soilwriter.writerow([datetime.datetime.now().strftime('%X %x'), temp, moisture])
            last_log_time = datetime.datetime.now()

        # Next state logic
        if moisture > DAMP_THRESHOLD:
            if state.is_preDamp:
                state.seeDampWhenPDamp()
            elif state.is_preDry:
                state.seeDampWhenPDry()
            elif state.is_realDry:
                state.seeDampWhenRDry()
            else:
                pass 
        else:
            if state.is_preDamp:
                state.seeDryWhenPDamp()
            elif state.is_preDry:
                state.seeDryWhenPDry()
            elif state.is_realDamp:
                state.seeDryWhenRDamp()
            else:
                pass 

        # Update display based on state
        if state.is_preDamp:
            draw_text('Damp')
            await send_watered_message()
            
        elif state.is_realDry:
            draw_text('Dry')
            await send_dry_message()
        
        else:
            pass


        time.sleep(30)

if __name__ == '__main__':
    asyncio.run(main())
