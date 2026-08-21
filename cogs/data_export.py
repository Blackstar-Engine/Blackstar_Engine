import discord
from discord.ext import commands
from utils.constants import db, bypassed_users
from utils.utils import permissions, get_permission_node
import csv
import io
import os
import aiofiles

def flatten_dict(data, parent_key=""):
        items = {}

        for key, value in data.items():
            new_key = f"{parent_key}.{key}" if parent_key else key

            if isinstance(value, dict):
                items.update(flatten_dict(value, new_key))
            else:
                items[new_key] = str(value)

        return items

class IDInputModal(discord.ui.Modal):
    def __init__(self, bot, collection_name):
        super().__init__(title="Export by ID")
        self.bot = bot
        self.collection_name = collection_name

        self.id_input = discord.ui.TextInput(
            label="User ID",
            placeholder="12345678910",
            required=True,
            max_length=100
        )
        self.add_item(self.id_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            record_id = int(self.id_input.value)
        except ValueError:
            return await interaction.response.send_message("Please make sure its an ID!", ephemeral=True)
        collection = db[self.collection_name]
        records = await collection.find({"$or": [{"user_id": record_id}, {"target_user_id": record_id}, {"id": record_id}]}).to_list(length=None)


        if records:
            clean_records = []

            for record in records:
                record.pop("_id", None)

                clean_record = flatten_dict(record)

                clean_records.append(clean_record)
            
            fieldnames = set()

            for record in clean_records:
                fieldnames.update(record.keys())

            fieldnames = sorted(fieldnames)

            # build CSV content in-memory then write asynchronously to disk
            csv_buffer = io.StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(record)
            csv_content = csv_buffer.getvalue()
            file_path = f"{interaction.user.id}_{self.collection_name}_{record_id}.csv"
            async with aiofiles.open(file_path, "w", encoding="utf-8", newline="") as af:
                await af.write(csv_content)
            await interaction.response.send_message(file=discord.File(file_path), content=f"Exported record with user id `{record_id}` from `{self.collection_name}` collection.", ephemeral=True)
            os.remove(file_path)
        else:
            await interaction.response.send_message(f"No record found with user id: {record_id}", ephemeral=True)


class CollectionSelectView(discord.ui.View):
    def __init__(self, bot, options):
        super().__init__()
        self.bot = bot
        
        self.collection_select.options = options

    @discord.ui.select(
        placeholder="Select a collection to export",
        min_values=1,
        max_values=1,
        options = []
    )
    async def collection_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        selected_collection = select.values[0]

        view = AllOrRecordButtons(self.bot, selected_collection)
        embed = discord.Embed(
            title="Export Options",
            description=f"In `{selected_collection}`, you can you either use user_id to export a users records or export the entire collection.",
            color=discord.Color.light_grey()
        )
        embed.add_field(name="Note", value="When opening in excel, click 'Dont Convert' to see ids as they should be")
        embed.set_footer(text="Exporting entire collections can take a WHILE, please export on off hours.")
        await interaction.response.edit_message(embed=embed, view=view)

class AllOrRecordButtons(discord.ui.View):
    def __init__(self, bot, collection_name):
        super().__init__()
        self.bot = bot
        self.collection_name = collection_name

    @discord.ui.button(label="All Records", style = discord.ButtonStyle.primary)
    async def all_records(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id in bypassed_users or await get_permission_node(interaction, "export_data.manage"):
            collection = db[self.collection_name]
            records = await collection.find().to_list(length=None)

            if records:
                clean_records = []

                for record in records:
                    record.pop("_id", None)

                    clean_record = flatten_dict(record)

                    clean_records.append(clean_record)
                
                fieldnames = set()

                for record in clean_records:
                    fieldnames.update(record.keys())

                fieldnames = sorted(fieldnames)

                # build CSV content in-memory then write asynchronously to disk
                csv_buffer = io.StringIO()
                writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(clean_records)
                csv_content = csv_buffer.getvalue()
                file_path = f"{interaction.user.id}_{self.collection_name}.csv"
                async with aiofiles.open(file_path, "w", encoding="utf-8", newline="") as af:
                    await af.write(csv_content)

                await interaction.followup.send(file=discord.File(file_path), content=f"Exported all records from `{self.collection_name}` collection.", ephemeral=True)
                os.remove(file_path)

                

    
    @discord.ui.button(label="By ID", style = discord.ButtonStyle.primary)
    async def by_id(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in bypassed_users or await get_permission_node(interaction, "export_data.manage"):
            modal = IDInputModal(self.bot, self.collection_name)
            await interaction.response.send_modal(modal)

    
    @discord.ui.button(label="Return", style = discord.ButtonStyle.secondary)
    async def return_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in bypassed_users or await get_permission_node(interaction, "export_data.manage"):
            options = []
            collections = await db.list_collection_names()

            for collection in collections:
                options.append(discord.SelectOption(label=collection, value=collection))

            view = CollectionSelectView(self.bot, options)
            embed = discord.Embed(
                title="Data Export",
                description="Please select a collection to export from the dropdown menu below.",
                color=discord.Color.light_grey()
            )

            await interaction.response.edit_message(embed=embed, view=view)


class DataExport(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
    
    @commands.hybrid_command(name="export_data", description="Export entire collections or individual records by user_id to a CSV file (DSM/Foundation Command +).", extras={'category': 'Administration'})
    @permissions()
    async def export_data(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        

        if ctx.author.id in bypassed_users or await get_permission_node(ctx, "export_data.manage"):
            options = []
            collections = await db.list_collection_names()

            for collection in collections:
                options.append(discord.SelectOption(label=collection, value=collection))

            view = CollectionSelectView(self.bot, options)
            embed = discord.Embed(
                title="Data Export",
                description="Please select a collection to export from the dropdown menu below.",
                color=discord.Color.light_grey()
            )

            await ctx.send(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(DataExport(bot=bot))