import discord
from discord.ext import commands
from discord.ui import Button
from utils.constants import profiles, foundation_command, site_command
from ui.paginator import PaginatorView
from ui.manage_commands.modals.AutoReply import AutoReplyAddModal
from ui.manage_commands.modals.AutoReplyEdit import AutoReplyEditModal
from ui.manage_commands.views.ConfirmRemoval import ConfirmRemovalView
from ui.manage_commands.views.ManageProfileButtons import ManageProfileButtons
from utils.utils import fetch_profile, fetch_unit_options
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
        # User must be in foundation or site command to run this command
        foundation_role = await ctx.guild.fetch_role(foundation_command)
        site_role = await ctx.guild.fetch_role(site_command)

        if foundation_role not in ctx.author.roles and site_role not in ctx.author.roles:
            return await ctx.send("You need to be apart of either foundation or site command to manage another user", ephemeral=True)
        
        # Find all auto replys and create the paginator view object
        items = [record for record in self.bot.auto_replys if record['guild_id'] == ctx.guild.id]
        self.auto_reply_view = PaginatorView(self.bot, ctx.author, items)

        # Add an "Add", "Edit", and "Remove" button to the paginator
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

        # Update the buttons and create the embed from the paginator
        self.auto_reply_view.update_buttons()

        embed = self.auto_reply_view.create_record_embed()
        await ctx.send(embed=embed, view=self.auto_reply_view, ephemeral=True)

    @manage.command(name="profile", description="Manage a users profile")
    async def manage_profile(self, ctx: commands.Context, user: discord.User):
        # User must be in foundation or site command to run this command
        foundation_role = await ctx.guild.fetch_role(foundation_command)
        site_role = await ctx.guild.fetch_role(site_command)

        if foundation_role not in ctx.author.roles and site_role not in ctx.author.roles:
            return await ctx.send("You need to be apart of either foundation or site command to manage another user", ephemeral=True)

        # check to see if they have a profile
        profile = await fetch_profile(ctx)
        if not profile:
            return
        else:
            # Fetch active departments
            options = fetch_unit_options(profile)

            private_unit = ", ".join(profile.get('private_unit', []))

            # Create the embed and view
            embed = discord.Embed(
                title="",
                description=f"**Codename: **{profile.get('codename')}\n**Roblox Name: **{profile.get('roblox_name')}\n**Timezone: **{profile.get('timezone')}\n**Private Unit(s): **{private_unit}\n**Join Date: ** {profile.get('join_date')}\n**Status: ** {profile.get('status')}",
                color=discord.Color.light_grey()
            )

            embed.set_author(name=f"{profile.get('codename')}'s Profile Information", icon_url=user.display_avatar.url)
            embed.set_thumbnail(url=user.display_avatar.url)

            view = ManageProfileButtons(self.bot, ctx.author, profile, embed, options)

            # Send to the user
            message = await ctx.send(embed=embed, view=view, ephemeral=True)

            # Add the message Object to the view
            view.main_message = message

async def setup(bot: commands.Bot):
    await bot.add_cog(ManageCommands(bot))