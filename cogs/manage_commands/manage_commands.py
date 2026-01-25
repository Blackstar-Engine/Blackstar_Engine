import discord
from discord.ext import commands
from discord.ui import View, Button, Modal
from utils.utils import interaction_check
from utils.constants import auto_replys, profiles, departments, foundation_command, site_command
from utils.ui.paginator import PaginatorView
from datetime import datetime

class EditProfileModal(discord.ui.Modal):
    def __init__(self, bot, profile: dict, embed: discord.Embed):
        self.bot = bot
        self.profile = profile
        self.embed = embed

        super().__init__(title="Edit Your Profile")

        self.codename = discord.ui.TextInput(
            label="Codename",
            placeholder=profile.get('codename'),
            default=profile.get('codename'),
            required=True,
            max_length=5,
            style=discord.TextStyle.short
        )

        self.roblox_name = discord.ui.TextInput(
            label="Roblox Username",
            placeholder=profile.get('roblox_name'),
            default=profile.get('roblox_name'),
            required=True,
            max_length=32,
            style=discord.TextStyle.short
        )

        self.timezone = discord.ui.TextInput(
            label="Timezone",
            placeholder=profile.get('timezone'),
            default=profile.get('timezone'),
            required=True,
            max_length=5,
            style=discord.TextStyle.short
        )

        self.status = discord.ui.TextInput(
            label="Status (Active or Inactive)",
            placeholder=profile.get('status'),
            default=profile.get('status'),
            required=True,
            max_length=8,
            style=discord.TextStyle.short
        )

        self.add_item(self.codename)
        self.add_item(self.roblox_name)
        self.add_item(self.timezone)
        self.add_item(self.status)

    async def on_submit(self, interaction: discord.Interaction):
        r_name = self.roblox_name.value
        timezone = self.timezone.value
        codename = self.codename.value
        status = self.status.value

        if status.lower() not in ['active', 'inactive']:
            await interaction.response.send_message("Status must be either 'Active' or 'Inactive'. Please try again.", ephemeral=True)
            return

        await profiles.update_one({'user_id': interaction.user.id, 'guild_id': interaction.guild.id}, {'$set': {'roblox_name': r_name, 'timezone': timezone, 'codename': codename, 'status': status.title()}})

        edit_embed = discord.Embed(
                                title="Profile Edited!",
                                description=f"Your profile has been edited!\n\n**Codename: **{codename}\n**Roblox Name: **{r_name}\n**Timezone: **{timezone}\n**Status: ** {status.title()}",
                                color=discord.Color.green()
                                )
        
        self.embed.description = f"**Codename: **{codename}\n**Roblox Name: **{r_name}\n**Timezone: **{timezone}\n**Rank: ** {self.profile.get('rank')}\n**Unit(s): **{', '.join(self.profile.get('unit', []))}\n**Private Unit(s): **{', '.join(self.profile.get('private_unit', []))}\n**Join Date: ** {self.profile.get('join_date')}\n**Status: ** {status.title()}"

        await interaction.response.edit_message(embed=self.embed)
        await interaction.followup.send(embed=edit_embed, ephemeral=True)

class AutoReplyAddModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Add New Record")
        self.bot = bot
        self.data = None

        self.message = discord.ui.TextInput(
            label="Message",
            placeholder="Hello",
            required=True,
            row=1,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.message)

        self.response = discord.ui.TextInput(
            label="Response",
            placeholder="Welcome to the server!", 
            required=True,
            row=2,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.response)
    
    async def on_submit(self, interaction: discord.Interaction):
        message = self.message.value
        response = self.response.value
        
        self.data = {
            "guild_id": interaction.guild.id,
            "message": message,
            "response": response,
            "created_by": interaction.user.id
        }

        await auto_replys.insert_one(self.data)

        embed = discord.Embed(
            title="New Auto Reply Added",
            description=f"**Message:** {message}\n"
                       f"**Response:** {response}",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

class ConfirmRemovalView(View):
    def __init__(self, bot, record, index):
        super().__init__()
        self.bot = bot
        self.record = record
        self.index = index

        self.status = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        self.status = 1

        embed = discord.Embed(
            title="Record Removed",
            description="The fire record has been successfully removed.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)

        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        self.status = 0
        embed = discord.Embed(
            title="Removal Cancelled",
            description="The removal of the fire record has been cancelled.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

class AutoReplyEditModal(Modal):
    def __init__(self, bot, record):
        super().__init__(title="Edit Record")
        self.bot = bot
        self.record = record
        self.data = None

        self.message = discord.ui.TextInput(
            label="Message",
            default=record.get("message", ""),
            placeholder=record.get("message", ""),
            required=True,
            row=1,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.message)

        self.response = discord.ui.TextInput(
            label="Response",
            default=record.get("response", ""),
            placeholder=record.get("response", ""),
            required=True,
            row=2,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.response)
    
    async def on_submit(self, interaction: discord.Interaction):
        message = self.message.value
        response = self.response.value
        
        self.data = {
            "guild_id": interaction.guild.id,
            "message": message,
            "response": response,
            "created_by": interaction.user.id
        }


        await auto_replys.update_one(self.record, {"$set": self.data})

        embed = discord.Embed(
            title="Record Updated",
            description=f"**Message:** {message}\n"
                       f"**Response:** {response}",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.stop()

class ProfileManageUnitsView(discord.ui.View):
    def __init__(self, bot, profile, user, normal_units, private_units):
        super().__init__(timeout=300)

        self.bot = bot
        self.profile = profile
        self.user = user

        self.profile_manage_units.options = normal_units
        self.profile_manage_units.max_values = len(normal_units)

        self.profile_manage_private_units.options = private_units
        self.profile_manage_private_units.max_values = len(private_units)

    @discord.ui.select(placeholder="No Units Selected", options=[])
    async def profile_manage_units(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction_check(self.user, interaction.user)
        await interaction.response.defer(ephemeral=True)

    @discord.ui.select(placeholder="No Private Units Selected", options=[])
    async def profile_manage_private_units(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction_check(self.user, interaction.user)
        await interaction.response.defer(ephemeral=True)

    @discord.ui.button(label="Submit", style=discord.ButtonStyle.green)
    async def profile_manage_units_submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(self.user, interaction.user)

        # ✅ FALLBACK TO DEFAULTS IF NOT INTERACTED
        selected_units = (
            set(self.profile_manage_units.values)
            if self.profile_manage_units.values
            else {opt.label for opt in self.profile_manage_units.options if opt.default}
        )

        selected_private_units = (
            set(self.profile_manage_private_units.values)
            if self.profile_manage_private_units.values
            else {opt.label for opt in self.profile_manage_private_units.options if opt.default}
        )

        all_departments = await departments.find(
            {"is_private": False}
        ).to_list(length=None)

        dept_map = {d["display_name"]: d for d in all_departments}

        units = dict(self.profile.get("unit", {}))

        for unit in selected_units:
            dept = dept_map.get(unit)
            if not dept:
                continue

            first_rank = dept["ranks"][0]["name"] if dept.get("ranks") else None

            units.setdefault(unit, {
                "rank": first_rank,
                "is_active": True
            })
            units[unit]["is_active"] = True

        for unit in units:
            if unit not in selected_units:
                units[unit]["is_active"] = False

        await profiles.update_one(
            {"_id": self.profile["_id"]},
            {"$set": {
                "unit": units,
                "private_unit": list(selected_private_units)
            }}
        )

        active_units = [
            u for u, d in units.items() if d.get("is_active")
        ]

        embed = discord.Embed(
            title="Profile Units Updated",
            description=(
                f"**Units:** {', '.join(active_units) or 'None'}\n"
                f"**Private Units:** {', '.join(selected_private_units) or 'None'}"
            ),
            color=discord.Color.green()
        )

        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

class ManageProfileButtons(discord.ui.View):
    def __init__(self, bot, user, profile, embed, options):
        super().__init__(timeout=None)
        self.bot = bot
        self.profile = profile
        self.user = user
        self.embed: discord.Embed = embed
        self.main_message: discord.Message = None

        self.dept_role_select.options = options
    
    @discord.ui.select(
        placeholder="Select a Role",
        min_values=1,
        max_values=1,
        options=[]
    )
    async def dept_role_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        value = select.values[0]

        select.values.clear()

        await interaction.edit_original_response(view=self)

        if value == "no_units":
            return
        
        department = self.profile["unit"][value]

        embed = discord.Embed(
            title="Unit Information",
            description=f"**Unit Name: ** {value}\n**Rank: ** {department.get('rank')}",
            color=discord.Color.light_grey()
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.gray, row=2)
    async def manage_profile_edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(self.user, interaction.user)

        modal = EditProfileModal(self.bot, self.profile, self.embed)
        await interaction.response.send_modal(modal)
        await modal.wait()

        self.profile["roblox_name"] = modal.roblox_name.value
        self.profile["timezone"] = modal.timezone.value
        self.profile["codename"] = modal.codename.value
        self.profile["status"] = modal.status.value

    @discord.ui.button(label="Manage Units", style=discord.ButtonStyle.gray, row=2)
    async def manage_profile_units(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(self.user, interaction.user)

        self.profile = await profiles.find_one({"_id": self.profile["_id"]})

        results = await departments.find().to_list(length=None)

        user_units = []
        units = dict(self.profile.get("unit", {}))

        for unit, data in units.items():
            if data.get("is_active"):
                user_units.append(unit)

        user_private_units = set(self.profile.get("private_unit", []))

        normal_unit_results = []
        private_unit_results = []

        for result in results:
            unit_name = result.get("display_name")
            is_private = result.get("is_private", False)

            option = discord.SelectOption(label=unit_name)

            if is_private:
                if unit_name in user_private_units:
                    option.default = True
                private_unit_results.append(option)
            else:
                if unit_name in user_units:
                    option.default = True
                normal_unit_results.append(option)

        view = ProfileManageUnitsView(
            self.bot,
            self.profile,
            self.user,
            normal_unit_results,
            private_unit_results
        )

        embed = discord.Embed(
            title="Units Selection",
            description="Please select all units you want this user to be a part of",
            color=discord.Color.light_grey()
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await view.wait()

        # 🔄 Reload profile after submit
        self.profile = await profiles.find_one({"_id": self.profile["_id"]})

        private_units = ", ".join(self.profile.get("private_unit", [])) or ""

        self.embed.description = (
            f"**Codename:** {self.profile.get('codename')}\n"
            f"**Roblox Name:** {self.profile.get('r_name')}\n"
            f"**Timezone:** {self.profile.get('timezone')}\n"
            f"**Private Unit(s):** {private_units}\n"
            f"**Join Date:** {self.profile.get('join_date')}\n"
            f"**Status:** {self.profile.get('status').title()}"
        )

        options = []
        units = dict(self.profile.get("unit", {}))

        for unit, data in units.items():
            if data.get("is_active"):
                options.append(discord.SelectOption(label=unit))
        
        if options == []:
            options.append(discord.SelectOption(label="No Active Units", value="no_units"))

        view = ManageProfileButtons(self.bot, self.user, self.profile, self.embed, options)

        await self.main_message.edit(embed=self.embed, view=view)

    @discord.ui.button(label="Demote", style=discord.ButtonStyle.blurple, row=2)
    async def demote_user_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(self.user, interaction.user)
        await interaction.response.send_message(
            view=DemoteUnitView(self.profile),
            ephemeral=True
        )

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red, row=3)
    async def manage_profile_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(self.user, interaction.user)

        result = ConfirmRemovalView(self.bot, self.profile, 0)
        embed = discord.Embed(
            title="Confirm Deletion",
            description="Are you sure you would like to remove this profile?",
            color=discord.Color.yellow()
        )

        await interaction.response.send_message(embed=embed, view=result, ephemeral=True)
        await result.wait()

        if result.status == 1:
            await profiles.delete_one(self.profile)
            await self.main_message.edit(content="Profile was deleted", embed=None, view=None)
            self.stop()

class DemoteUnitView(discord.ui.View):
    def __init__(self, profile):
        super().__init__(timeout=120)
        self.profile = profile

        options = [
            discord.SelectOption(label=unit)
            for unit, data in profile.get("unit", {}).items()
            if data.get("is_active")
        ]

        self.unit_select.options = options

    @discord.ui.select(placeholder="Select unit to demote", options=[])
    async def unit_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        unit = select.values[0]

        dept = await departments.find_one({"display_name": unit})
        if not dept:
            await interaction.response.send_message("Department not found.", ephemeral=True)
            return

        current_rank = self.profile["unit"][unit]["rank"]

        await interaction.response.send_message(
            view=DemoteRankView(
                profile=self.profile,
                unit=unit,
                ranks=dept.get("ranks", []),
                current_rank=current_rank
            ),
            ephemeral=True
        )

class DemoteRankView(discord.ui.View):
    def __init__(self, profile, unit, ranks, current_rank):
        super().__init__(timeout=120)

        self.profile = profile
        self.unit = unit

        # Find current rank order
        current_rank_obj = next(
            (r for r in ranks if r["name"] == current_rank),
            None
        )

        if not current_rank_obj:
            self.valid_ranks = []
        else:
            current_order = current_rank_obj["order"]
            self.valid_ranks = [
                r for r in ranks
                if r.get("order", 0) <= current_order
            ]

        options = [
            discord.SelectOption(label=r["name"])
            for r in self.valid_ranks
        ]

        self.rank_select.options = options

    @discord.ui.select(placeholder="Select rank to demote to", options=[])
    async def rank_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        new_rank = select.values[0]

        await profiles.update_one(
            {"_id": self.profile["_id"]},
            {"$set": {
                f"unit.{self.unit}.rank": new_rank
            }}
        )

        await interaction.response.send_message(
            f"✅ {self.unit} rank updated to **{new_rank}**",
            ephemeral=True
        )


class ManageCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.auto_reply_view = None
        self.sessions_view = None
    

    async def AR_remove_record(self, interaction: discord.Interaction):
        # Checking if theres no records to remove
        if not self.auto_reply_view.items or self.auto_reply_view.current_index >= len(self.auto_reply_view.items):
            await interaction.response.send_message("No record to remove.", ephemeral=True)
            return
        
        # Getting the current record and sending the confirmation message
        current_record = self.auto_reply_view.items[self.auto_reply_view.current_index]
        embed = discord.Embed(
            title="Confirm Removal",
            description="Are you sure you want to remove this auto reply?",
            color=discord.Color.red()
        )
        
        confirm_view = ConfirmRemovalView(self.bot, current_record, self.auto_reply_view.current_index)
        await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)

        #waiting for the user to interaction with the modal
        await confirm_view.wait()

        # Removing the item from the list in the pagnaitor and from the main bot list
        if confirm_view.status == 1:
            index = self.auto_reply_view.current_index
            self.auto_reply_view.items.pop(index)
            self.bot.auto_replys.pop(index)

        # Reloading the paginator to show the removed record
        self.auto_reply_view.current_index = 0
        self.auto_reply_view.update_buttons()
        embed = self.auto_reply_view.create_record_embed()
        await interaction.edit_original_response(embed=embed, view=self.auto_reply_view)

    async def AR_edit_record(self, interaction: discord.Interaction):
        # Checking if theres no records to edit
        if not self.auto_reply_view.items or self.auto_reply_view.current_index >= len(self.auto_reply_view.items):
            return await interaction.response.send_message("No record to edit.", ephemeral=True)
        
        # Getting current record and sending the modal to edit the record
        current_record = self.auto_reply_view.items[self.auto_reply_view.current_index]
        
        edit_view = AutoReplyEditModal(self.bot, current_record)
        await interaction.response.send_modal(edit_view)

        #waiting for the user to interact with the modal
        await edit_view.wait()

        # Updating the record in the pagiantor list and the main bot list
        self.bot.auto_replys[self.auto_reply_view.current_index] = edit_view.data
        self.auto_reply_view.items[self.auto_reply_view.current_index] = edit_view.data

        # reloading paginator to reflect changes
        self.auto_reply_view.update_buttons()
        embed = self.auto_reply_view.create_record_embed()
        await interaction.edit_original_response(embed=embed, view=self.auto_reply_view)

    async def AR_add_record(self, interaction: discord.Interaction):
        # Sending the modal to add a new record
        add_view = AutoReplyAddModal(self.bot)
        await interaction.response.send_modal(add_view)

        #waiting for the user to interact with the modal
        await add_view.wait()

        # adding the record to the pagiantor list and the main bot list
        self.bot.auto_replys.append(add_view.data)
        self.auto_reply_view.items.append(add_view.data)

        # Reloading the paginator to reflect the new record
        self.auto_reply_view.current_index = len(self.auto_reply_view.items) - 1
        self.auto_reply_view.update_buttons()
        embed = self.auto_reply_view.create_record_embed()
        await interaction.edit_original_response(embed=embed, view=self.auto_reply_view)

    @commands.hybrid_group(name='manage')
    async def manage(self, ctx: commands.Context):
        '''
        This is the main manage command for all commands that require to be managed
        '''
        pass

    @manage.command(name='auto_reply', description='Manage auto replys')
    async def auto_reply(self, ctx: commands.Context):
        foundation_role = await ctx.guild.fetch_role(foundation_command)
        site_role = await ctx.guild.fetch_role(site_command)

        if foundation_role not in ctx.author.roles and site_role not in ctx.author.roles:
            return await ctx.send("You need to be apart of either foundation or site command to manage another user", ephemeral=True)
        
        items = [record for record in self.bot.auto_replys if record['guild_id'] == ctx.guild.id]
        self.auto_reply_view = PaginatorView(self.bot, ctx.author, items)

        add_button = Button(
            label="Add",
            style=discord.ButtonStyle.green,
            row=2
        )
        add_button.callback = self.AR_add_record

        edit_button = Button(
            label="Edit",
            style=discord.ButtonStyle.gray,
            row=2
        )
        edit_button.callback = self.AR_edit_record
        
        remove_button = Button(
            label="Remove",
            style=discord.ButtonStyle.red,
            row=2
        )
        remove_button.callback = self.AR_remove_record

        self.auto_reply_view.extra_buttons = [add_button, edit_button, remove_button]
        self.auto_reply_view.update_buttons()

        embed = self.auto_reply_view.create_record_embed()
        await ctx.send(embed=embed, view=self.auto_reply_view, ephemeral=True)

    @manage.command(name="profile", description="Manage a users profile")
    async def manage_profile(self, ctx: commands.Context, user: discord.User):
        foundation_role = await ctx.guild.fetch_role(foundation_command)
        site_role = await ctx.guild.fetch_role(site_command)

        if foundation_role not in ctx.author.roles and site_role not in ctx.author.roles:
            return await ctx.send("You need to be apart of either foundation or site command to manage another user", ephemeral=True)

        profile = await profiles.find_one({'user_id': user.id, 'guild_id': ctx.guild.id})
        if not profile:
            await ctx.send(f"I cannot find a profile for {user.mention}! Please try again.", ephemeral=True)
        else:
            options = []
            units = dict(profile.get("unit", {}))

            for unit, data in units.items():
                if data.get("is_active"):
                    options.append(discord.SelectOption(label=unit))

            
            if options == []:
                options.append(discord.SelectOption(label="No Active Units", value="no_units"))

            private_unit = ", ".join(profile.get('private_unit', []))
            embed = discord.Embed(
                title="",
                description=f"**Codename: **{profile.get('codename')}\n**Roblox Name: **{profile.get('roblox_name')}\n**Timezone: **{profile.get('timezone')}\n**Private Unit(s): **{private_unit}\n**Join Date: ** {profile.get('join_date')}\n**Status: ** {profile.get('status')}",
                color=discord.Color.light_grey()
            )
            embed.add_field(name="Points", value=f"**Current Points: **{profile.get('current_points')}\n**Total Points: **{profile.get('total_points')}", inline=True)

            embed.set_author(name=f"{profile.get('codename')}'s Profile Information", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)

            view = ManageProfileButtons(self.bot, ctx.author, profile, embed, options)

            message = await ctx.send(embed=embed, view=view, ephemeral=True)

            view.main_message = message

async def setup(bot: commands.Bot):
    await bot.add_cog(ManageCommands(bot))