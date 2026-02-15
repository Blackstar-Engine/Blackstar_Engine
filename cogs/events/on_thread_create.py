import discord
from discord.ext import commands
from utils.constants import profile_thread_channel, profiles, departments
from datetime import datetime
import re 
from utils.utils import profile_creation_embed

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

        main_message = await thread.fetch_message(thread.id)
        main_message = str(main_message.content)

        is_citizen = main_message.lower().find("Citizenship form")

        if not member or is_citizen != -1:
            return
        
        existing_profile = await profiles.find_one({
            'user_id': member.id,
            'guild_id': guild.id
        })

        if existing_profile:
            embed = discord.Embed(title="Profile Creation Error", description="You already have a profile created in our system", color=discord.Color.red())
            return await thread.send(embed=embed)
        
        patterns = {
            "Codename": r"code\s*name:\s*(.*)",
            "Roblox User": r"roblox\s*user:\s*(.*)",
            "Department": r"department:\s*([^\n/]+(?:\s*/\s*[^\n/]+)*)",
            "Time Zone": r"time\s*zone:\s*(.*)",
            "Unit": r"unit:\s*([^\n/]+(?:\s*/\s*[^\n/]+)*)"
        }

        results = {}

        for label, pattern in patterns.items():
            # re.IGNORECASE handles 'CODENAME' vs 'codename'
            match = re.search(pattern, main_message, re.IGNORECASE)
            if match:
                results[label] = match.group(1).strip()
            else:
                results[label] = -1

        profanity_list = [
                        "dick", "cock", "whore", "tranny", "faggot", "nig", "nigga", "fag",
                        "pussy", "vagina", "penis", "bitch", "fuck", "shit", "asshole",
                        "cunt", "nigger", "mother fucker", "titties", "titty", "boobs", "cum",
                        "tit", "douche", "douchebag", "blowjob", "handjob", "ass", "seman", "anel", "wanker"
                        ]
        
        codename: str = results.get("Codename")
        roblox_user: str = results.get("Roblox User")
        department: str = results.get("Department")
        timezone: str = results.get("Time Zone")
        subunit: str = results.get("Unit")

        if codename == -1 or roblox_user == -1 or department == -1 or timezone == -1:
            embed = discord.Embed(title="Enlistment Error", description="Please make sure to include the following as listed `Codename:`, `Roblox user:`, `Time zone:`, and `Department:`.", color=discord.Color.red())
            return await thread.send(embed=embed)

        for word in profanity_list:
            result = codename.lower().find(word)
            if result != -1:
                embed = discord.Embed(title="Profanity Detected", description="We do not allow any type of profanity in codenames. Please reopen another thread and choose a different codename.", color=discord.Color.red())
                return await thread.send(embed=embed) 

        departments_list = department.split("/")

        units = {}
        mtf_subunits = []

        for dept in departments_list:
            if dept in ["RRT", "ISD", "IA", "CI", "ScD", "SCD"]:
                embed = discord.Embed(title="Application Only Department", description=f"`{dept}` can only be joined by completing an application. I am **removing** `{dept}`!", color=discord.Color.yellow())
                await thread.send(embed=embed)
                departments_list.remove(dept)
            else:
                if dept == "MTF":
                    mtf_subunits = subunit.split("/")
                    print(mtf_subunits)
                    for unit in mtf_subunits:
                        subunit = f"MTF:{unit.strip()}"
                        department_doc = await departments.find_one({"display_name": subunit, "is_private": False})

                        if not department_doc:
                            embed = discord.Embed(title="Department Error", description=f"`{subunit}` could not be resolved. Please contact **DSM** if this is incorrect!", color=discord.Color.yellow())
                            await thread.send(embed=embed)
                            mtf_subunits.remove(unit)
                        else:
                        
                            first_rank = department_doc["ranks"][0]["name"] if department_doc.get("ranks") else "Recruit"

                            unit_doc = {subunit: {'rank': first_rank, 'is_active': True, 'current_points': 0, 'total_points': 0}}

                            units.update(unit_doc)
                else:
                    department_doc = await departments.find_one({"display_name": dept, "is_private": False})
                
                    if not department_doc:
                        embed = discord.Embed(title="Department Error", description=f"`{dept}` could not be resolved. Please contact **DSM** if this is incorrect!", color=discord.Color.yellow())
                        await thread.send(embed=embed)
                        departments_list.remove(dept)
                    else:
                    
                        first_rank = department_doc["ranks"][0]["name"] if department_doc.get("ranks") else "Recruit"

                        unit_doc = {dept: {'rank': first_rank, 'is_active': True, 'current_points': 0, 'total_points': 0}}

                        units.update(unit_doc)

        profile = {
                'user_id': member.id,
                'guild_id': guild.id,
                'codename': codename,
                'roblox_name': roblox_user,
                'unit': units,
                'private_unit': [],
                'status': 'Active',
                'join_date': str(join_date),
                'timezone': timezone,
            }
        
        await profiles.insert_one(profile)

        embed = discord.Embed(
                                title="Profile Created!",
                                description=f"Your profile has been created!\n\n**Codename: **{codename}\n**Roblox Name: **{roblox_user}\n**Timezone: **{timezone}\n**Departments: ** {", ".join(departments_list)}\n**Subunits: ** {", ".join(mtf_subunits)}\n**Current Points: **0\n**Total Points: **0",
                                color=discord.Color.green()
                                )
        await thread.send(embed=embed)

        dm_embed = profile_creation_embed()
        
        try:
            await member.send(embed=dm_embed)
        except Exception:
            return

async def setup(bot):
    await bot.add_cog(ThreadProfileCreation(bot))