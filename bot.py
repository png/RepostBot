import os
import argparse
import re
from dotenv import load_dotenv
import requests

import discord
import hashlib

from db import Database


def get_args():
    '''
    Gets args for this program

    param:
    None

    return:
    parsed arguments object
    '''
    parser = argparse.ArgumentParser()

    parser.add_argument('username', default='data/',
                        help='Username for mongodb', type=str)
    parser.add_argument('password',
                        help='Password for mongodb', type=str)
    parser.add_argument('collection', help='Colleciton name', type=str)

    return(parser.parse_args())


args = get_args()

load_dotenv()
db = Database(args.username, args.password, args.collection)

TOKEN = os.getenv('DISCORD_TOKEN')
client = discord.Client()

link_format = re.compile('http[s]?:\/\/.*')


def handle_images(attachments):
    hashes = []
    for attachment in attachments:
        if(attachment.url[0:39] == 'https://cdn.discordapp.com/attachments/'):
            req = requests.get(attachment.url)
            hashes.append(hashlib.sha256(req._content).hexdigest())

    return hashes


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    # images
    if(message.attachments):
        hashes = handle_images(message.attachments)
    # links
    else:
        content = message.content
        if(link_format.match(content)):
            content = content.encode('utf-8')
            hashes = [hashlib.sha256(content).hexdigest()]

    for hash in hashes:
        result = db.cursor.find_one({'content': hash})
        if(result):
            await message.reply(f"Repost: {result['link']}")
            await message.add_reaction('🚨')
        else:
            link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
            print(f"Saving link: {link}")
            db.cursor.insert_one({'link': link, 'content' : hash})


if __name__ == '__main__':
    client.run(TOKEN)
