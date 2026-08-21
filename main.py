import discord 
from discord.ext import commands
from cogwatch import watch
import os
import sys
import asyncio
from collections import defaultdict
from utils.constants import (
                            BlackstarConstants, auto_replys, enlistment_requests, point_requests,
                            promotion_requests, logger, discord_http_logger,
                            discord_logger, permission_tiers, permission_rules, permission_overrides,
                            bypassed_users, ids
                            )
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
                        logger.info(f"{cog_module} loaded successfully")
                    except Exception as e:
                        logger.error(f"{cog_module} failed to load: {e}")

        logger.info(f"Successfully loaded {cog_counter} cog(s)")

        from discord import app_commands

        for command in self.tree.walk_commands():
            app_commands.allowed_installs(guilds=True, users=False)(command)
            app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)(command)

        logger.info(f"Applied guild-only install/context to {len(list(self.tree.walk_commands()))} commands")

        async for req in enlistment_requests.find({"is_active": True}):
            view = EnlistmentRequestView(req["_id"], req["snapshot"])
            self.add_view(view)
            enlistment_counter += 1
        
        logger.info(f"Successfully loaded {enlistment_counter} enlistments")

        async for req in point_requests.find({"is_active": True}):
            view = PointsRequestView(req["_id"], req["snapshot"])
            self.add_view(view)
            points_counter += 1
        
        logger.info(f"Successfully loaded {points_counter} points")

        async for req in promotion_requests.find({"is_active": True}):
            view = PromotionRequestView(self, req["_id"], req["snapshot"])
            self.add_view(view)
            promotion_counter += 1
        
        logger.info(f"Successfully loaded {promotion_counter} promotions")

    async def on_connect(self):
        discord_http_logger.info('Connected to discord gateway')
    
    async def on_disconnected(self):
        discord_http_logger.error('Disconnected from discord gateway')

    async def on_shard_connect(self, shard_id: int):
        discord_http_logger.info(f'Shard {shard_id} has connected to discord gateway')
    
    async def on_shard_disconnected(self, shard_id: int):
        discord_http_logger.error(f'Shard {shard_id} has disconnected from discord gateway')
            

    @watch(path='cogs', preload=False)
    async def on_ready(self):
        bot.auto_replys = []

        records = await auto_replys.find().to_list(length=None)
        for record in records:
            bot.auto_replys.append(record)
        logger.info(f"All {len(bot.auto_replys)} auto-replys loaded")

        bot.tts_queues = defaultdict(asyncio.Queue)
        bot.tts_tasks = {}

        await bot.change_presence(activity=discord.CustomActivity(name=presence))

        # Get all tiers, generate a new dict obj
        raw_tiers = await permission_tiers.find().to_list(length=None)
        bot.permission_tiers = {}
        for tier in raw_tiers:
            bot.permission_tiers.setdefault(tier["guild_id"], {})[tier["name"]] = tier

        # Get all rules, generate a new dict obj
        raw_rules = await permission_rules.find().to_list(length=None)
        bot.permission_rules = {
            (rule["guild_id"], rule["scope_type"], rule["scope_key"]): rule
            for rule in raw_rules
        }

        # Get all overrides, generate a new dict obj
        raw_overrides = await permission_overrides.find().to_list(length=None)
        bot.permission_overrides = {}
        for override in raw_overrides:
            scope_key = (override["guild_id"], override["scope_type"], override["scope_key"])
            target_key = (override["target_type"], override["target_id"])
            bot.permission_overrides.setdefault(scope_key, {})[target_key] = override

        # Get all reaction roles
        bot.reaction_roles = await ids.find({"key": "reaction_roles"}).to_list(length=None)

        
        logger.info(f'{self.user} is ready.')

bot = Bot()

async def start_bot():
    max_retries = 10
    retry_delay = 5
    retries = 0

    while retries < max_retries:
        try:
            discord_logger.info(f'Starting bot... (Attempt {retries + 1})')
            await bot.start(constants.TOKEN)
        except (TimeoutError) as e:
            retries += 1
            discord_logger.error(f'Connection error occured. Thrown error: {e}')

            if retries < max_retries:
                discord_logger.info(f'Retrying in {retry_delay} seconds...')
                await asyncio.sleep(retry_delay)
            else:
                break

        except Exception as e:
            discord_logger.error(f'Unexpected error occured. {e}')
            sys.exit('FAILED TO START: UNEXPECTED ERROR')

    
    discord_logger.critical('Max retries reached - stopping bot...')
    sys.exit('FAILED TO START: MAX RETRIES')
            

if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        discord_logger.info('Bot shutting down...')
        sys.exit(0)