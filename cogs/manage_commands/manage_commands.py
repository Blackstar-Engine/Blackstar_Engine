import discord
from discord.ext import commands
from discord.ui import View, Button, Modal
from utils.utils import interaction_check
from utils.constants import auto_replys
from utils.ui.paginator import PaginatorView

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

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await auto_replys.delete_one(self.record)

        embed = discord.Embed(
            title="Record Removed",
            description="The fire record has been successfully removed.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)

        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
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

class ManageCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.auto_reply_view = None
    

    async def remove_record(self, interaction: discord.Interaction):
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
        index = self.auto_reply_view.current_index
        self.auto_reply_view.items.pop(index)
        self.bot.auto_replys.pop(index)

        # Reloading the paginator to show the removed record
        self.auto_reply_view.current_index = 0
        self.auto_reply_view.update_buttons()
        embed = self.auto_reply_view.create_record_embed()
        await interaction.edit_original_response(embed=embed, view=self.auto_reply_view)

    async def edit_record(self, interaction: discord.Interaction):
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

    async def add_record(self, interaction: discord.Interaction):
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
        add_button.callback = self.add_record

        edit_button = Button(
            label="Edit",
            style=discord.ButtonStyle.gray,
            row=2
        )
        edit_button.callback = self.edit_record
        
        remove_button = Button(
            label="Remove",
            style=discord.ButtonStyle.red,
            row=2
        )
        remove_button.callback = self.remove_record

        self.auto_reply_view.extra_buttons = [add_button, edit_button, remove_button]
        self.auto_reply_view.update_buttons()

        embed = self.auto_reply_view.create_record_embed()
        await ctx.send(embed=embed, view=self.auto_reply_view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ManageCommands(bot))