import os
import argparse
import re
from dotenv import load_dotenv
import requests
import io

import discord
import imagehash
import hashlib
from PIL import Image
from urllib.parse import urlparse

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
    parser.add_argument(
        '-threshold', help='Hamming distance threshold', default=3, type=float)

    return(parser.parse_args())


args = get_args()

load_dotenv()
db = Database(args.username, args.password, args.collection)

TOKEN = os.getenv('DISCORD_TOKEN')
client = discord.Client()

link_format = re.compile('http[s]?:\/\/.*')


def handle_images(attachments):
    '''
    Gets image attachments and returns their hashes

    param:
    attachments: list of attachments from discord message

    return:
    list of hashes
    '''
    hashes = []
    for attachment in attachments:
        if(attachment.url[:39] == 'https://cdn.discordapp.com/attachments/'):
            req = requests.get(attachment.url)
            img = Image.open(io.BytesIO(req._content))
            hashes.append(str(imagehash.whash(img)))

    return hashes


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    hashes = []
    if(message.attachments):
        hashes = handle_images(message.attachments)
        hash_type = 'image'
    else:
        content = message.content
        if(link_format.match(content)):
            # ignore gifs and links to the base of a server
            parsed_url = urlparse(content)
            if(parsed_url.netloc == 'tenor.com' or parsed_url.path):
                req = requests.get(content)
                # use url to deal with redirects
                content = req.url.encode('utf-8')
                hashes = [hashlib.sha256(content).hexdigest()]
                hash_type = 'link'

    for hash in hashes:
        results = []
        if(hash_type == 'link'):
            result = db.cursor.find_one(
                {'content': hash, 'type': hash_type})
            if(result):
                results.append(result)
        elif(hash_type == 'image'):
            # source for perceptual hashing: https://lvngd.com/blog/determining-how-similar-two-images-are-python-perceptual-hashing/
            db_result = db.cursor.find({'type': hash_type})
            for image in db_result:
                hamming = abs(int(hash, 16) - int(image['content'], 16))
                if(hamming < args.threshold):
                    results.append(image)

        if(results):
            await message.reply(f"Repost: {', '.join([entry['link'] for entry in results])}")
            await message.add_reaction('🚨')
        else:
            link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
            print(f"Saving link: {link}")
            db.cursor.insert_one(
                {'link': link, 'content': hash, 'type': hash_type})


if __name__ == '__main__':
    client.run(TOKEN)
