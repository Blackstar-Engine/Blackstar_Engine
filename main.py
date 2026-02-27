import discord 
from discord.ext import commands
from cogwatch import watch
import os
import sys
import asyncio
from collections import defaultdict
from utils.constants import BlackstarConstants, auto_replys, enlistment_requests, point_requests, promotion_requests, whitelisted_guilds
from ui.promotion.views.PromotionRequest import PromotionRequestView
from ui.points.views.AcceptDenyButtons import PointsRequestView
from ui.enlistment_request.views.EnlistmentRequestView import EnlistmentRequestView

constants = BlackstarConstants()

if constants.ENVIRONMENT == "PRODUCTION":
    presence = "Viva La Blackstar"
else:
    presence = "Doing Da Testing"


class Bot(commands.Bot):
    def __init__(self):
        intent = discord.Intents.default()
        intent.message_content = True
        intent.members = True

        super().__init__(
            command_prefix=constants.PREFIX,
            intents=intent,
            chunk_guilds_at_startup=False,
            help_command=None,
            reconnect=True,
        )
    
    async def is_owner(self, user: discord.User) -> bool:
        bypassed_users = [
            758170288566566952, #Ghost
            1371489554279825439, #Wolf
            412192199028113408, #Maz
            934537337113804891 #Bread
        ]

        return user.id in bypassed_users

    async def setup_hook(self):
        cog_counter = 0
        enlistment_counter = 0
        points_counter = 0
        promotion_counter = 0

        for root, _, files in os.walk("./cogs"):
            for file in files:
                if file.endswith(".py"):
                    cog_path = os.path.relpath(os.path.join(root, file), "./cogs")
                    cog_module = cog_path.replace(os.sep, ".")[:-3]
                    
                    try:
                        await bot.load_extension(f"cogs.{cog_module}")
                        cog_counter += 1
                        print(f"{cog_module} loaded successfully")
                    except Exception as e:
                        print(f"{cog_module} failed to load: {e}")

        print(f"Successfully loaded {cog_counter} cog(s)")

        async for req in enlistment_requests.find({"is_active": True}):
            view = EnlistmentRequestView(req["_id"], req["snapshot"])
            self.add_view(view)
            enlistment_counter += 1
        
        print(f"Successfully loaded {enlistment_counter} enlistments")

        async for req in point_requests.find({"is_active": True}):
            view = PointsRequestView(req["_id"], req["snapshot"])
            self.add_view(view)
            points_counter += 1
        
        print(f"Successfully loaded {points_counter} points")

        async for req in promotion_requests.find({"is_active": True}):
            view = PromotionRequestView(self, req["_id"], req["snapshot"])
            self.add_view(view)
            promotion_counter += 1
        
        print(f"Successfully loaded {promotion_counter} promotions")

    async def on_connect(self):
        print('Connected to discord gateway')
    
    async def on_disconnected(self):
        print('Disconnected from discord gateway')

    async def on_shard_connect(self, shard_id: int):
        await self.tree.sync()
        print(f'Shard {shard_id} has connected to discord gateway')
    
    async def on_shard_disconnected(self, shard_id: int):
        print(f'Shard {shard_id} has disconnected from discord gateway')
            

    @watch(path='cogs', preload=False)
    async def on_ready(self):
        bot.auto_replys = []

        records = await auto_replys.find().to_list(length=None)
        for record in records:
            bot.auto_replys.append(record)
        print(f"All {len(bot.auto_replys)} auto-replys loaded")

        bot.tts_queues = defaultdict(asyncio.Queue)
        bot.tts_tasks = {}

        await bot.change_presence(activity=discord.CustomActivity(name=presence))

        for guild in bot.guilds:
            if guild.id not in whitelisted_guilds:
                print(f"Server not found: {guild.name}({guild.id})")
                try:
                    await guild.leave()
                except Exception:
                    await guild.owner.send(f"Please remove me from **{guild.name}**, I will not work!")
                
            else:
                print(f'Chunked: {guild.id}')
                await guild.chunk()
        
        print(f'{self.user} is ready.')

bot = Bot()

async def start_bot():
    max_retries = 10
    retry_delay = 5
    retries = 0

    while retries < max_retries:
        try:
            print(f'Starting bot... (Attempt {retries + 1})')
            await bot.start(constants.TOKEN)
        except (TimeoutError) as e:
            retries += 1
            print(f'Connection error occured. Thrown error: {e}')

            if retries < max_retries:
                print(f'Retrying in {retry_delay} seconds...')
                await asyncio.sleep(retry_delay)
            else:
                break

        except Exception as e:
            print(f'Unexpected error occured. {e}')
            sys.exit('FAILED TO START: UNEXPECTED ERROR')

    
    print('Max retries reached - stopping bot...')
    sys.exit('FAILED TO START: MAX RETRIES')
            

if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print('Bot shutting down...')
        sys.exit(0)