import discord
from discord.ext import commands
from utils.constants import profiles, departments, profanity_list
from datetime import datetime
import re 
from utils.utils import profile_creation_embed, fetch_id, log_action
import asyncio

class ClaimButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Claim Enlistment", style=discord.ButtonStyle.blurple, custom_id="enlistment_claim_button")
    async def claim_enlistment_button(self, interaction: discord.Interaction, button: discord.Button):
        results = await fetch_id(interaction.guild.id, ['drm_id'])
        drm_role = interaction.guild.get_role(results['drm_id'])
        if drm_role not in interaction.user.roles:
            return await interaction.response.send_message("This is a D.R.M only button!", ephemeral=True)
        embed = discord.Embed(
            title="Claimed",
            description=f"This enlistment has been claimed by {interaction.user.mention}",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await interaction.followup.send("You have claimed this enlistment!", ephemeral=True)
        self.stop()

class EnlistmentByThread(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
    
    async def _check_profile(self, main_message, member, thread: discord.Thread):
        is_citizen = "citizenship form" in main_message.lower()

        if not member or is_citizen:
            return False

        existing_profile = await profiles.find_one({'user_id': member.id,'guild_id': thread.guild.id})

        if existing_profile:
            embed = discord.Embed(title="Profile Creation Error", description="You already have a profile created in our system", color=discord.Color.red())
            await thread.send(embed=embed)
            return False

        return True
    
    def _run_pattern(self, main_message):
        patterns = {
            "Codename": r"code\s*name:\s*([^\n]+)",
            "Roblox User": r"roblox\s*user:\s*([^\n]+)",
            "Department": r"department:\s*([^\n/]+(?:\s*/\s*[^\n/]+)*)",
            "Time Zone": r"time\s*zone:\s*([^\n]+)",
            "Unit": r"unit:\s*([^\n/]+(?:\s*/\s*[^\n/]+)*)"
        }

        results = {}

        for label, pattern in patterns.items():
            # re.IGNORECASE handles 'CODENAME' vs 'codename'
            match = re.search(pattern, main_message, re.IGNORECASE)
            if match:
                results[label] = match.group(1).strip(" `*~_.")
            else:
                results[label] = -1
        
        return results

    async def _handle_mtf_subunits(self, subunit: str, thread: discord.Thread, units: dict) -> list:
        mtf_subunits = subunit.split("/")
        units_to_remove = []

        for unit in mtf_subunits:
            unit = unit.strip().upper()
            subunit_name = f"MTF:{unit}"
            department_doc: dict = await departments.find_one({"display_name": subunit_name, "is_private": False})

            if not department_doc:
                embed = discord.Embed(title="Department Error", description=f"`{subunit_name}` could not be resolved. Please contact **DSM** if this is incorrect!", color=discord.Color.yellow())
                await thread.send(embed=embed)
                units_to_remove.append(unit)
            elif unit in ('A-1'):
                embed = discord.Embed(title="Application Only Department", description=f"`{subunit_name}` can only be joined by completing an application. I am **removing** `{subunit_name}`!", color=discord.Color.yellow())
                await thread.send(embed=embed)
                units_to_remove.append(unit)
            else:
                first_rank = department_doc["ranks"][0]["name"] if department_doc.get("ranks") else "Recruit"
                unit_doc = {subunit_name: {'rank': first_rank, 'is_active': True, 'current_points': 0, 'total_points': 0}}
                units.update(unit_doc)

        full_list = [unit for unit in mtf_subunits if unit not in units_to_remove]

        return full_list

    async def _handle_regular_department(self, dept: str, thread: discord.Thread, units: dict) -> bool:
        department_doc: dict = await departments.find_one({"display_name": dept, "is_private": False})
        
        if not department_doc:
            embed = discord.Embed(title="Department Error", description=f"`{dept}` could not be resolved. Please contact **DSM** if this is incorrect!", color=discord.Color.yellow())
            await thread.send(embed=embed)
            return False
        
        first_rank = department_doc["ranks"][0]["name"] if department_doc.get("ranks") else "Recruit"
        unit_doc = {dept: {'rank': first_rank, 'is_active': True, 'current_points': 0, 'total_points': 0}}
        units.update(unit_doc)
        return True

    async def _generate_units(self, department: str, thread: discord.Thread, subunit):
        departments_list = [d.strip().upper() for d in department.split("/")]
        units = {}
        mtf_subunits = []
        depts_to_remove = []

        for dept in departments_list:
            dept = dept.strip().upper()
            if dept in ["RRT", "ISD", "IA", "CI", "SCD"]:
                embed = discord.Embed(title="Application Only Department", description=f"`{dept}` can only be joined by completing an application. I am **removing** `{dept}`!", color=discord.Color.yellow())
                await thread.send(embed=embed)
                depts_to_remove.append(dept)
            elif dept == "MTF":
                if subunit == -1 or not subunit:
                    await thread.send(embed=discord.Embed(
                        title="Missing MTF Unit",
                        description="You must specify an MTF subunit using `Unit:`",
                        color=discord.Color.red()
                    ))
                    continue
                mtf_subunits = await self._handle_mtf_subunits(subunit, thread, units)

                if mtf_subunits == []:
                    depts_to_remove.append(dept)
            else:
                if not await self._handle_regular_department(dept, thread, units):
                    depts_to_remove.append(dept)

        departments_list = [d for d in departments_list if d not in depts_to_remove]
        return units, departments_list, mtf_subunits
    
    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        await self.bot.wait_until_ready()

        # Only run in enlistment channel
        results = await fetch_id(thread.guild.id, ['profile_thread_channel'])
        if thread.parent_id != results['profile_thread_channel']:
            return
        
        # Variable Declarations
        guild = thread.guild
        member = guild.get_member(thread.owner_id)
        join_date = datetime.now().date()

        main_message = None

        for _ in range(5):
            try:
                main_message = await thread.fetch_message(thread.id)
                break
            except discord.NotFound:
                await asyncio.sleep(1)

        if not main_message:
            return

        main_message = str(main_message.content)

        claim_embed = discord.Embed(
            title="Click to Claim",
            description="D.R.M, please click this button to claim the enlistment!",
            color=discord.Color.yellow()
        )

        view = ClaimButtonView()

        await thread.send(embed=claim_embed, view=view)

        # Preliminary Checks
        if not await self._check_profile(main_message, member, thread):
            return
        
        results = self._run_pattern(main_message)
        
        # Initializing variables for profile creation
        codename: str = results.get("Codename")
        roblox_user: str = results.get("Roblox User")
        department: str = results.get("Department")
        timezone: str = results.get("Time Zone")
        subunit: str = results.get("Unit")

        # Preliminary validation for profile creation
        if codename == -1 or roblox_user == -1 or department == -1 or timezone == -1:
            embed = discord.Embed(title="Enlistment Error", description="I was unable to process your profile. **Please create your profile via `!profile`!**", color=discord.Color.red())
            return await thread.send(embed=embed)

        if any(word in codename.lower() for word in profanity_list):
            embed = discord.Embed(title="Profanity Detected", description="We do not allow any type of profanity in codenames. Please reopen another thread and choose a different codename.", color=discord.Color.red())
            return await thread.send(embed=embed) 
        
        profile_check = await profiles.find_one({"guild_id": guild.id, "codename": codename})
        if profile_check:
            embed = discord.Embed(title="Codename Taken", description="Sorry but that codename is already taken! Please reopen another thread and choose a different codename.", color=discord.Color.red())
            return await thread.send(embed=embed)

        # Generating the needed variables for profile creation
        units, departments_list, mtf_subunits = await self._generate_units(department, thread, subunit)

        # Creating profile and sending confirmation message
        profile = {
                'user_id': member.id,
                'guild_id': guild.id,
                'codename': codename[0:15],
                'roblox_name': roblox_user,
                'unit': units,
                'private_unit': [],
                'status': 'Active',
                'join_date': str(join_date),
                'timezone': timezone,
            }
        
        await profiles.insert_one(profile)

        created_embed = discord.Embed(
                                title="Profile Created!",
                                description=(
                                        f"Your profile has been created!\n\n"
                                        f"**Codename:** {codename}\n"
                                        f"**Roblox Name:** {roblox_user}\n"
                                        f"**Timezone:** {timezone}\n"
                                        f"**Departments:** {', '.join(departments_list)}\n"
                                        f"**Subunits:** {', '.join(mtf_subunits)}\n"
                                        f"**Current Points:** 0\n"
                                        f"**Total Points:** 0"
                                    ),
                                color=discord.Color.green()
                                )
        await thread.send(embed=created_embed)

        # await log_action(ctx=thread, log_type="department", user_id=member.id, department=', '.join(departments_list) or 'None')

        dm_embed = profile_creation_embed()
        
        try:
            await member.send(embed=dm_embed)
        except Exception:
            return

async def setup(bot: commands.Bot):
    await bot.add_cog(EnlistmentByThread(bot))
    bot.add_view(ClaimButtonView())