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

i2c_bus = board.I2C()
sensor = Seesaw(i2c_bus, addr=0x36)

load_dotenv()
BOT_TOKEN = getenv('BOT_TOKEN')
CHAT_ID = getenv('CHAT_ID')

bot = telegram.Bot(BOT_TOKEN)
last_message_time = datetime.datetime.fromtimestamp(0)
last_log_time = datetime.datetime.fromtimestamp(0)

if not exists('soil_log.csv'):
    with open('soil_log.csv', 'w') as csvfile:
        soilwriter = csv.writer(csvfile, delimiter=',')
        soilwriter.writerow(['time', 'temp', 'moisture'])

def draw_text(text):
    global font
    image = Image.open('garden_auto_flower_bg.png')
    draw = ImageDraw.Draw(image)
    draw.text((10, 25), text, fill='#000000', font=font)
    st7735.display(image)

async def send_bot_message(message):
    global bot, last_message_time, CHAT_ID

    # 8 hour timeout so we don't spam ourselves
    if datetime.datetime.now() - last_message_time < datetime.timedelta(hours=8):
        return

    async with bot:
      await bot.send_message(text=message, chat_id=CHAT_ID)
    last_message_time = datetime.datetime.now()

async def main():
    global bot, last_log_time
    while True:

        moisture = sensor.moisture_read()
        temp = sensor.get_temp()

        # Log the current date/time, temp, and moisture if we haven't logged in over an hour
        if datetime.datetime.now() - last_log_time > datetime.timedelta(hours=1):
            with open('soil_log.csv', 'a') as csvfile:
                soilwriter = csv.writer(csvfile, delimiter=',')
                soilwriter.writerow([datetime.datetime.now().strftime('%X %x'), temp, moisture])
            last_log_time = datetime.datetime.now()

        if moisture > 400:
            draw_text('Damp')
        else:
           draw_text('Dry')
           await send_bot_message('Plants are dry! Water them plz ;-;')

        time.sleep(30)

if __name__ == '__main__':
    asyncio.run(main())
