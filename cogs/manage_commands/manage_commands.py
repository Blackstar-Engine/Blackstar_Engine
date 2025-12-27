import discord
from discord.ext import commands
from discord.ui import View, Button, Modal
from utils.utils import interaction_check
from utils.constants import auto_replys, sessions, profiles, departments
from utils.ui.paginator import PaginatorView
from datetime import datetime
from cogs.profile.profile import EditProfileModal

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


class SessionEditModal(Modal):
    def __init__(self, bot, record):
        super().__init__(title="Edit Record")
        self.bot = bot
        self.record = record

        self.name = discord.ui.TextInput(
            label="Session Name",
            placeholder=record.get('name'),
            default=record.get('name'),
            required=True,
            row=1,
            style=discord.TextStyle.short
        )
        self.add_item(self.name)

        self.session_id = discord.ui.TextInput(
            label="Session ID (Number)",
            placeholder=record.get('session_id'),
            default=record.get('session_id'),
            required=True,
            row=2,
            style=discord.TextStyle.short
        )
        self.add_item(self.session_id)

        self.duration = discord.ui.TextInput(
            label="Duration",
            placeholder=record.get('duration'),
            default=record.get('duration'),
            required=True,
            row=3,
            style=discord.TextStyle.short
        )
        self.add_item(self.duration)

        self.note = discord.ui.TextInput(
            label="Note",
            placeholder=record.get('note'), 
            default=record.get('note'), 
            required=False,
            row=4,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.note)
    
    async def on_submit(self, interaction: discord.Interaction):
        name = self.name.value
        note = self.note.value
        session_id = self.session_id.value
        duration = self.duration.value

        embed = discord.Embed(
            title="Session Edited",
            description=f"**Name:** {name}\n"
                       f"**Session ID:** {session_id}\n"
                       f"**Duration: ** {duration}\n"
                       f"**Note: ** {note}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
        self.stop()

class SessionRoleSelections(View):
    def __init__(self, bot, user, session_data):
        super().__init__()
        self.bot = bot
        self.host = None
        self.co_host = None
        self.supervisor = None
        self.attendees = None
        self.mvp = None
        self.user = user
        self.session_data = session_data

    async def check_select_options(self, interaction: discord.Interaction):
        if self.host and self.attendees:
            self.finish_button.disabled = False
        else:
            self.finish_button.disabled = True
        
        await interaction.response.edit_message(view=self)

    @discord.ui.select(cls=discord.ui.UserSelect,
                       max_values=1,
                       min_values=1, 
                       placeholder="Select the Host")
    async def host_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction_check(self.user, interaction.user)
        value = select.values[0]
        self.host = value.id

        await self.check_select_options(interaction)
    
    @discord.ui.select(cls=discord.ui.UserSelect,
                       max_values=1,
                       min_values=0, 
                       placeholder="Select the Co-Host")
    async def co_host_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction_check(self.user, interaction.user)
        value = select.values[0]
        self.co_host = value.id

        await self.check_select_options(interaction)

    @discord.ui.select(cls=discord.ui.UserSelect,
                       max_values=1,
                       min_values=0, 
                       placeholder="Select the Supervisor")
    async def supervisor_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction_check(self.user, interaction.user)
        value = select.values[0]
        self.supervisor = value.id

        await self.check_select_options(interaction)
    
    @discord.ui.select(cls=discord.ui.UserSelect,
                       max_values=25,
                       min_values=1, 
                       placeholder="Select the Attendees")
    async def attendees_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction_check(self.user, interaction.user)
        self.attendees = [role.id for role in select.values]

        await self.check_select_options(interaction)
    
    @discord.ui.button(
        label="Finish",
        style=discord.ButtonStyle.grey,
        disabled=True
    )
    async def finish_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(self.user, interaction.user)

        if self.host and self.attendees:
            embed=discord.Embed(
                                title="Session Added", 
                                description="This session has been added", 
                                color=discord.Color.green()
                                )
            
            self.session_data['host_id'] = self.host
            self.session_data['co_host_id'] = self.co_host
            self.session_data['supervisor_id'] = self.supervisor
            self.session_data['attendees'] = self.attendees
            
            await interaction.response.edit_message(embed=embed, view=None, delete_after=5)
            self.stop()
        else:
            await interaction.response.send_message("Please make sure to have roles selected for admin, mod, and user!", ephemeral=True)

class SessionAddModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Add New Session", custom_id="session_add_modal")
        self.bot = bot
        self.data = None

        self.name = discord.ui.TextInput(
            label="Session Name",
            placeholder="Messin Around",
            required=True,
            row=1,
            style=discord.TextStyle.short
        )
        self.add_item(self.name)

        self.session_id = discord.ui.TextInput(
            label="Session ID (Number)",
            placeholder="1234",
            required=True,
            row=2,
            style=discord.TextStyle.short
        )
        self.add_item(self.session_id)

        self.duration = discord.ui.TextInput(
            label="Duration",
            placeholder="2 hours 30 minutes",
            required=True,
            row=3,
            style=discord.TextStyle.short
        )
        self.add_item(self.duration)

        self.note = discord.ui.TextInput(
            label="Note",
            placeholder="Everything went well", 
            required=False,
            row=4,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.note)
    
    async def on_submit(self, interaction: discord.Interaction):
        name = self.name.value
        note = self.note.value
        session_id = self.session_id.value
        duration = self.duration.value
        
        self.data = {
            'guild_id': interaction.guild.id,
            'name': name,
            'session_id': session_id,
            'date': str(datetime.now().date()),
            'duration': duration,
            'host_id': None,
            'co_host_id': None,
            'supervisor_id': None,
            'mvp': None,
            'attendees': [],
            'note': note

        }

        embed = discord.Embed(
            title="New Session Started",
            description=f"**Name:** {name}\n"
                       f"**Session ID:** {session_id}\n"
                       f"**Duration: ** {duration}\n"
                       f"**Note: ** {note}",
            color=discord.Color.yellow()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.stop()

class ProfileManageUnitsView(discord.ui.View):
    def __init__(self, bot, profile, user, normal_units, private_units):
        super().__init__(timeout=300)

        self.bot = bot
        self.profile = profile
        self.user = user

        # ORIGINAL state (used for comparison)
        self.original_units = set(profile.get("unit", []))
        self.original_private_units = set(profile.get("private_unit", []))

        # Current state (will be read from selects)
        self.unit = list(self.original_units)
        self.private_unit = list(self.original_private_units)

        # Configure selects
        self.profile_manage_units.options = normal_units
        self.profile_manage_units.max_values = len(normal_units)

        self.profile_manage_private_units.options = private_units
        self.profile_manage_private_units.max_values = len(private_units)

    @discord.ui.select(
        placeholder="No Units Selected",
        options=[]
    )
    async def profile_manage_units(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction_check(self.user, interaction.user)
        await interaction.response.defer(ephemeral=True)

    @discord.ui.select(
        placeholder="No Private Units Selected",
        options=[]
    )
    async def profile_manage_private_units(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction_check(self.user, interaction.user)
        await interaction.response.defer(ephemeral=True)

    @discord.ui.button(
        label="Submit",
        style=discord.ButtonStyle.green
    )
    async def profile_manage_units_submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(self.user, interaction.user)

        # 🔑 Read current select state
        new_units = set(self.profile_manage_units.values or [])
        new_private_units = set(self.profile_manage_private_units.values or [])

        # 🔍 Check if anything actually changed
        if (
            new_units == self.original_units
            and new_private_units == self.original_private_units
        ):
            # Nothing changed → do nothing
            embed = discord.Embed(
                title="No Changes Made",
                description="No unit changes were detected.",
                color=discord.Color.greyple()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            self.stop()
            return

        # ✅ Something changed → update DB
        await profiles.update_one(
            {"_id": self.profile["_id"]},
            {"$set": {
                "unit": list(new_units),
                "private_unit": list(new_private_units)
            }}
        )

        embed = discord.Embed(
            title="Profile Units Updated",
            description=(
                f"**Units:** {', '.join(new_units) or 'None'}\n"
                f"**Private Units:** {', '.join(new_private_units) or 'None'}"
            ),
            color=discord.Color.green()
        )

        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

class ManageProfileButtons(discord.ui.View):
    def __init__(self, bot, user, profile, embed):
        super().__init__(timeout=None)
        self.bot = bot
        self.profile = profile
        self.user = user
        self.embed: discord.Embed = embed
        self.main_message: discord.Message = None

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.gray)
    async def manage_profile_edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(self.user, interaction.user)

        modal = EditProfileModal(self.bot, self.profile, self.embed)
        await interaction.response.send_modal(modal)
        await modal.wait()

        self.profile["roblox_name"] = modal.roblox_name.value
        self.profile["timezone"] = modal.timezone.value
        self.profile["codename"] = modal.codename.value
        self.profile["status"] = modal.status.value

    @discord.ui.button(label="Manage Units", style=discord.ButtonStyle.gray)
    async def manage_profile_units(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction_check(self.user, interaction.user)

        # 🔄 Always reload profile
        self.profile = await profiles.find_one({"_id": self.profile["_id"]})

        results = await departments.find().to_list(length=None)

        user_units = set(self.profile.get("unit", []))
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

        units = ", ".join(self.profile.get("unit", [])) or "None"
        private_units = ", ".join(self.profile.get("private_unit", [])) or "None"

        self.embed.description = (
            f"**Codename:** {self.profile.get('codename')}\n"
            f"**Roblox Name:** {self.profile.get('r_name')}\n"
            f"**Timezone:** {self.profile.get('timezone')}\n"
            f"**Rank:** {self.profile.get('rank')}\n"
            f"**Unit(s):** {units}\n"
            f"**Private Unit(s):** {private_units}\n"
            f"**Join Date:** {self.profile.get('join_date')}\n"
            f"**Status:** {self.profile.get('status').title()}"
        )

        await self.main_message.edit(embed=self.embed)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red)
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
    
    async def S_remove_record(self, interaction: discord.Interaction):
        # Checking if theres no records to remove
        if not self.sessions_view.items or self.sessions_view.current_index >= len(self.sessions_view.items):
            await interaction.response.send_message("No record to remove.", ephemeral=True)
            return
        
        # Getting the current record and sending the confirmation message
        current_record = self.sessions_view.items[self.sessions_view.current_index]
        embed = discord.Embed(
            title="Confirm Removal",
            description="Are you sure you want to remove this session?",
            color=discord.Color.red()
        )
        
        confirm_view = ConfirmRemovalView(self.bot, current_record, self.sessions_view.current_index)
        await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)

        #waiting for the user to interaction with the modal
        await confirm_view.wait()

        # Removing the item from the list in the pagnaitor and from the main bot list

        if confirm_view.status == 1:
            index = self.sessions_view.current_index
            try:
                self.sessions_view.items.pop(index)
            except Exception as e:
                print("Session item view pop error: ", e)

            try:
                await sessions.delete_one(current_record)
            except Exception as e:
                print("session record remove error: ", e)

        # Reloading the paginator to show the removed record
        self.sessions_view.current_index = 0
        self.sessions_view.update_buttons()
        embed = self.sessions_view.create_record_embed()
        await interaction.edit_original_response(embed=embed, view=self.sessions_view)

    async def S_edit_record(self, interaction: discord.Interaction):
        # Checking if theres no records to edit
        if not self.sessions_view.items or self.sessions_view.current_index >= len(self.sessions_view.items):
            return await interaction.response.send_message("No record to edit.", ephemeral=True)
        
        # Getting current record and sending the modal to edit the record
        current_record = self.sessions_view.items[self.sessions_view.current_index]
        
        edit_view = SessionEditModal(self.bot, current_record)
        await interaction.response.send_modal(edit_view)

        #waiting for the user to interact with the modal
        await edit_view.wait()

        # Updating the record in the pagiantor list and the main bot list
        name = edit_view.name.value
        note = edit_view.note.value
        session_id = edit_view.session_id.value
        duration = edit_view.duration.value

        await sessions.update_one(current_record, {"$set": {'name': name, 'session_id': session_id, 'duration': duration, 'note': note}})
        self.sessions_view.items[self.sessions_view.current_index]['name'] = name
        self.sessions_view.items[self.sessions_view.current_index]['session_id'] = session_id
        self.sessions_view.items[self.sessions_view.current_index]['duration'] = duration
        self.sessions_view.items[self.sessions_view.current_index]['note'] = note

        # reloading paginator to reflect changes
        self.sessions_view.update_buttons()
        embed = self.sessions_view.create_record_embed()
        await interaction.edit_original_response(embed=embed, view=self.sessions_view)

    async def S_add_record(self, interaction: discord.Interaction):
        # Sending the modal to add a new record
        session_add_view = SessionAddModal(self.bot)
        await interaction.response.send_modal(session_add_view)

        #waiting for the user to interact with the modal
        await session_add_view.wait()

        session_role_view = SessionRoleSelections(self.bot, interaction.user, session_add_view.data)
        embed = discord.Embed(
            title="User Selection",
            description="**Host (Required):** The user that is the main host\n**Co-Host (Optional):** The user that is the co-host\n**Supervisor (Optional):** The user that is the supervisor\n**Attendees (Required):** Anyone that actually attended the session",
            color=discord.Color.yellow()
        )
        await interaction.followup.send(embed=embed, view = session_role_view, ephemeral=True)

        await session_role_view.wait()

        # adding the record to the pagiantor list and the main bot list
        session_doc = await sessions.insert_one(session_role_view.session_data)
        self.sessions_view.items.append(session_role_view.session_data)

        for attendee in session_role_view.session_data.get('attendees'):
            await profiles.update_one({'guild_id': interaction.guild.id, 'user_id': attendee}, {'$addToSet': {'sessions': session_doc.inserted_id}})

        # Reloading the paginator to reflect the new record
        self.sessions_view.current_index = len(self.sessions_view.items) - 1
        self.sessions_view.update_buttons()
        embed = self.sessions_view.create_record_embed()
        await interaction.edit_original_response(embed=embed, view=self.sessions_view)
    
    @manage.command(name="sessions", description="Manage all sessions in this server")
    async def sessions(self, ctx: commands.Context):
        records = await sessions.find({"guild_id": ctx.guild.id}).to_list(length=None)
        self.sessions_view = PaginatorView(self.bot, ctx.author, records)

        add_button = Button(
            label="Add",
            style=discord.ButtonStyle.green,
            row=2
        )
        add_button.callback = self.S_add_record

        edit_button = Button(
            label="Edit",
            style=discord.ButtonStyle.gray,
            row=2
        )
        edit_button.callback = self.S_edit_record
        
        remove_button = Button(
            label="Remove",
            style=discord.ButtonStyle.red,
            row=2
        )
        remove_button.callback = self.S_remove_record

        self.sessions_view.extra_buttons = [add_button, edit_button, remove_button]
        self.sessions_view.update_buttons()

        embed = self.sessions_view.create_record_embed()
        await ctx.send(embed=embed, view=self.sessions_view, ephemeral=True)

    @manage.command(name="profile", description="Manage a users profile")
    async def manage_profile(self, ctx: commands.Context, user: discord.User):
        profile = await profiles.find_one({'user_id': user.id, 'guild_id': ctx.guild.id})
        if not profile:
            await ctx.send(f"I cannot find a profile for {user.mention}! Please try again.", ephemeral=True)
        else:
            unit = ", ".join(profile.get('unit', []))
            private_unit = ", ".join(profile.get('private_unit', []))
            embed = discord.Embed(
                title="",
                description=f"**Codename: **{profile.get('codename')}\n**Roblox Name: **{profile.get('roblox_name')}\n**Timezone: **{profile.get('timezone')}\n**Rank: ** {profile.get('rank')}\n**Unit(s): **{unit}\n**Private Unit(s): **{private_unit}\n**Join Date: ** {profile.get('join_date')}\n**Status: ** {profile.get('status')}",
                color=discord.Color.light_grey()
            )
            embed.add_field(name="Points", value=f"**Current Points: **{profile.get('current_points')}\n**Total Points: **{profile.get('total_points')}", inline=True)
            embed.add_field(name="Sessions Completed", value=f"{len(profile.get('sessions', []))} sessions(s) completed.", inline=True)
            #embed.add_field(name="Missions Completed", value=f"{len(profile.get('missions', []))} mission(s) completed.", inline=True)

            embed.set_author(name=f"{profile.get('codename')}'s Profile Information", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)

            view = ManageProfileButtons(self.bot, ctx.author, profile, embed)

            message = await ctx.send(embed=embed, view=view, ephemeral=True)

            view.main_message = message

async def setup(bot: commands.Bot):
    await bot.add_cog(ManageCommands(bot))