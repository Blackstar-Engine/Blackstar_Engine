import discord
from discord.ext import commands
from utils.constants import db
from utils.utils import fetch_id
import csv
import os

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

            with open(f"{interaction.user.id}_{self.collection_name}_{record_id}.csv", "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(record)
            await interaction.response.send_message(file=discord.File(f"{interaction.user.id}_{self.collection_name}_{record_id}.csv"), content=f"Exported record with user id `{record_id}` from `{self.collection_name}` collection.", ephemeral=True)
            os.remove(f"{interaction.user.id}_{self.collection_name}_{record_id}.csv")
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
        bypassed_ids = await fetch_id(interaction.guild.id, ["foundation_command", "wolf_id", "ghost_id", "option_id"])
        
        foundation_role = interaction.guild.get_role(bypassed_ids["foundation_command"])

        if foundation_role in interaction.user.roles or interaction.user.id in [bypassed_ids["wolf_id"], bypassed_ids["ghost_id"], bypassed_ids["option_id"]]:
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

                with open(f"{interaction.user.id}_{self.collection_name}.csv", "w", newline="", encoding="utf-8") as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(clean_records)
                
                await interaction.followup.send(file=discord.File(f"{interaction.user.id}_{self.collection_name}.csv"), content=f"Exported all records from `{self.collection_name}` collection.", ephemeral=True)
                os.remove(f"{interaction.user.id}_{self.collection_name}.csv")

                

    
    @discord.ui.button(label="By ID", style = discord.ButtonStyle.primary)
    async def by_id(self, interaction: discord.Interaction, button: discord.ui.Button):
        bypassed_ids = await fetch_id(interaction.guild.id, ["foundation_command", "wolf_id", "ghost_id", "option_id"])
        
        foundation_role = interaction.guild.get_role(bypassed_ids["foundation_command"])

        if foundation_role in interaction.user.roles or interaction.user.id in [bypassed_ids["wolf_id"], bypassed_ids["ghost_id"], bypassed_ids["option_id"]]:
            modal = IDInputModal(self.bot, self.collection_name)
            await interaction.response.send_modal(modal)

    
    @discord.ui.button(label="Return", style = discord.ButtonStyle.secondary)
    async def return_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bypassed_ids = await fetch_id(interaction.guild.id, ["foundation_command", "wolf_id", "ghost_id", "option_id"])
        
        foundation_role = interaction.guild.get_role(bypassed_ids["foundation_command"])

        if foundation_role in interaction.user.roles or interaction.user.id in [bypassed_ids["wolf_id"], bypassed_ids["ghost_id"], bypassed_ids["option_id"]]:
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
    async def export_data(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        bypassed_ids = await fetch_id(ctx.guild.id, ["foundation_command", "wolf_id", "ghost_id", "option_id"])
        
        foundation_role = ctx.guild.get_role(bypassed_ids["foundation_command"])

        if foundation_role in ctx.author.roles or ctx.author.id in [bypassed_ids["wolf_id"], bypassed_ids["ghost_id"], bypassed_ids["option_id"]]:
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