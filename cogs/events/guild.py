import discord
from discord.ext import commands
from utils.constants import whitelisted_guilds
from datetime import datetime

class Guild(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if guild.id not in whitelisted_guilds:
            try:
                await guild.owner.send("I am a whitelisted only bot, you are not allowed to invite me!")
                await guild.leave()
            except Exception:
                await guild.owner.send(f"Please remove me from **{guild.name}**, I will not work!")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != 1411941814923169826:
            return
        
        thread = member.guild.get_channel_or_thread(1433946174791876740)
        help_channel = member.guild.get_channel(1419346953526837411)
        dm_embed = discord.Embed(
            title="Welcome to Blackstar Corp",
            description="Are you not sure what to do? Well this will explain how to get enlisted and more!",
            color=discord.Color.light_grey()
        )

        dm_embed.add_field(
            name="-Enlistment Process",
            value=f"> To gain access please make an enlistment request to a public department in {thread.mention}."
                "> Please reference [this thread](https://discord.com/channels/1411941814923169826/1433947466092515458) on what is avalible."
                "\n\nPlease copy this exact template\n"
                "```**Enlistment form**\n"
                "Codename:\n"
                "Discord User:\n"
                "Roblox user:\n"
                "Department: MTF/SD/MD/CD\n"
                "Unit:  E-11/NU-7/B-7\n"
                "VC: YES/NO\n"
                "Time zone:\n"
                "Reason:\n"
                "Invited from: ```",
            inline=False
        )

        dm_embed.add_field(
            name="-Need Help?",
            value=f"> If you need help you can talk with our server members in {help_channel.mention}.",
            inline=False
        )

        dm_embed.set_footer(text=f"Blackstar Engine • {datetime.now().date()}")
        dm_embed.set_image(url="https://cdn.discordapp.com/attachments/1450512700034781256/1463307219159220316/Untitled_design_13.gif?ex=697be68b&is=697a950b&hm=53b2c67aedf52d6392e6c41c4d708e1a52b1c4c9bdda5c7c0f304c717e04cf04&")
        dm_embed.set_thumbnail(url=member.display_avatar.url)

        await member.send(embed=dm_embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Guild(bot=bot))