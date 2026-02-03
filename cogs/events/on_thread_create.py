import discord
from discord.ext import commands
from utils.constants import profile_thread_channel, profiles, departments
from datetime import datetime

class ThreadProfileCreation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        await self.bot.wait_until_ready()

        if thread.parent_id != profile_thread_channel:
            return
        
        guild = thread.guild
        member = guild.get_member(thread.owner_id)
        join_date = datetime.now().date()

        if not member:
            return
        
        existing_profile = await profiles.find_one({
            'user_id': member.id,
            'guild_id': guild.id
        })

        if existing_profile:
            embed = discord.Embed(title="Profile Creation Error", description="You already have a profile created in our system", color=discord.Color.red())
            return await thread.send(embed=embed)
        
        main_message = await thread.fetch_message(thread.id)

        main_message = str(main_message.content)

        codename_start = main_message.find("Codename:")
        discord_username = main_message.find("Discord User:")
        roblox_start = main_message.find("Roblox user:")
        department_start = main_message.find("Department:")
        unit_start = main_message.find("Unit:")
        reason_start = main_message.find("Reason:")
        timezone_start = main_message.find("Time zone:")

        if codename_start == -1 or roblox_start == -1 or timezone_start == -1 or department_start == -1:
            embed = discord.Embed(title="Enlistment Error", description="Your profile creation message is missing some required fields. Please make sure to include `Codename:`, `Roblox user:`, `Time zone:`, and `Department:`.", color=discord.Color.red())
            return await thread.send(embed=embed)
        
        codename = main_message[codename_start + 9:discord_username].strip()

        profanity_list = [
                        "dick", "cock", "whore", "tranny", "faggot", "nig", "nigga", "fag",
                        "pussy", "vagina", "penis", "bitch", "fuck", "shit", "asshole",
                        "cunt", "nigger", "mother fucker", "titties", "titty", "boobs", "cum",
                        "tit", "douche", "douchebag", "blowjob", "handjob", "ass", "seman", "anel", "wanker"
                        ]
        for word in profanity_list:
            result = codename.lower().find(word)
            if result != -1:
                embed = discord.Embed(title="Profanity Detected", description="We do not allow any type of profanity in codenames. Please reopen another thread and choose a different codename.", color=discord.Color.red())
                return await thread.send(embed=embed)

        roblox_name = main_message[roblox_start + 13:department_start].strip()
        department = main_message[department_start + 11:unit_start].strip()
        timezone = main_message[timezone_start + 10:reason_start].strip()

        departments_list = department.split("/")

        units = {}

        for dept in departments_list:

            department_doc = await departments.find_one({"display_name": dept, "is_private": False})
            if not department_doc:
                embed = discord.Embed(title="Department Error", description=f"`{dept}` could not be resolved. Please contact DSM if this is incorrect!", color=discord.Color.red())
                await thread.send(embed=embed)

                departments_list.remove(dept)
            else:
            
                first_rank = department_doc["ranks"][0]["name"] if department_doc.get("ranks") else "Recruit"

                unit_doc = {dept: {'rank': first_rank, 'is_active': True, 'current_points': 0, 'total_points': 0, 'subunits': []}}

                units.update(unit_doc)

        profile = {
                'user_id': member.id,
                'guild_id': guild.id,
                'codename': codename,
                'roblox_name': roblox_name,
                'unit': units,
                'private_unit': [],
                'status': 'Active',
                'join_date': str(join_date),
                'timezone': timezone,
            }
        
        await profiles.insert_one(profile)

        embed = discord.Embed(
                                title="Profile Created!",
                                description=f"Your profile has been created!\n\n**Codename: **{codename}\n**Roblox Name: **{roblox_name}\n**Timezone: **{timezone}\n**Departments: ** {", ".join(departments_list)}\n**Current Points: **0\n**Total Points: **0",
                                color=discord.Color.green()
                                )
        await thread.send(embed=embed)

        dm_embed=discord.Embed(
            title="Welcome to Blackstar!",
            description="This is a quick tutorial on how we run things around these parts!",
            color=discord.Color.light_grey()
        )

        dm_embed.add_field(
            name="-Points Ranking System",
            value = "> To earn points you need to attend server sessions which are broadcasted ahead of time in [**#👾 sessions**](https://discord.com/channels/1411941814923169826/1434351873518993509), you can also earn points a variety of other ways such as hosting and co-hosting deployments or attending those deployments! Deployments will also be broadcasted in [**#📢 mission-briefing**](https://discord.com/channels/1411941814923169826/1412241044392640654), The best way to keep track of your points is by using the personal roster system to document all your attended events in one place, this can be found in [**#🪪 personal-roster**](https://discord.com/channels/1411941814923169826/1412295943654735952)",
            inline=False
        )

        dm_embed.add_field(
            name="-How to Enlist",
            value="> To enlist in a department you first need to make an enlistment form in [**#🪪 enlistment**](https://discord.com/channels/1411941814923169826/1433946174791876740), if you want to join another department you will need to enlist under that teams department category.",
            inline=False
        )

        dm_embed.add_field(
            name="-Document Links",
            value="For more information on a specific topic please see out server documents listed below.\n\n"
                "> [Stature of Regulation](https://trello.com/b/5LzFYOKb/name-stature-of-regulation)\n"
                "> [Code of Conduct](https://docs.google.com/document/d/1qUqOgbX8CoB3jzaIrIZxheqBpAeHk5HVLIP252cViac/edit?usp=sharing)\n"
                "> [Hierarchy & Points System](https://docs.google.com/document/d/1abd4Qq6CanUCLqjdmka5RmYEeD6GTFWGo2Czym0-nyo/edit?usp=sharing)\n"
                "> [Unit Database](https://docs.google.com/spreadsheets/d/1BLlkDxLW7GqPwVPmDuwpu-XBU98aY5_0ADX9QALXp4w/edit?usp=sharing)\n\n"
                "**For any other documents please refer to https://discord.com/channels/1411941814923169826/1418081211246575617 or a departments specified documents channel, you may also create a ticket to resolve any query or problem you may have.**\n\n"
                "**Thank you for being apart of the fun!**",
                inline=False
        )

        dm_embed.set_footer(text=f"Blackstar Engine • {datetime.now().date()}")
        dm_embed.set_image(url="https://cdn.discordapp.com/attachments/1450512700034781256/1463307219159220316/Untitled_design_13.gif?ex=697be68b&is=697a950b&hm=53b2c67aedf52d6392e6c41c4d708e1a52b1c4c9bdda5c7c0f304c717e04cf04&")
        try:
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            return

async def setup(bot):
    await bot.add_cog(ThreadProfileCreation(bot))