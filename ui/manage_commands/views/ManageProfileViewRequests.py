import discord
from discord.ext import commands
from discord import ui
from ui.paginator import PaginatorView
from utils.constants import enlistment_requests, promotion_requests, point_requests

class ManageProfileViewRequests(ui.LayoutView):
    def __init__(self, bot: commands.Bot, moderator: discord.Member, inacted_user: discord.Member, profile: dict):
        super().__init__(timeout=None)
        self.bot = bot
        self.moderator = moderator
        self.inacted_user = inacted_user
        self.profile = profile
        from ui.manage_commands.views.ReturnButton import ReturnButton
        return_button = ReturnButton(self.bot, self.moderator, self.inacted_user)

        self.select_menu = ui.Select(
            placeholder="Select a request",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Enlistments", value="enlistments", description="View all enlistment requests"),
                discord.SelectOption(label="Promotion Requests", value="promotions", description="View all promotion requests"),
                discord.SelectOption(label="Point Requests", value="points", description="View all point requests"),
            ]
        )

        self.select_menu.callback = self.select_menu_callback

        select_menu = ui.ActionRow(self.select_menu)
        return_button = ui.ActionRow(return_button)

        container = ui.Container(
            ui.TextDisplay("## View Requests"),
            ui.TextDisplay("Please select a request type to view all records."),
            ui.Separator(),
            select_menu,
            return_button,
            accent_color=discord.Color.light_grey()
        )

        self.add_item(container)
    
    async def select_menu_callback(self, interaction: discord.Interaction):
        if self.select_menu.values[0] == "enlistments":
            records = await enlistment_requests.find({"guild_id": interaction.guild.id, "target_user_id": self.inacted_user.id, "is_active": False}, {"_id": 0, "snapshot": 1}).to_list(length=None)
            new_records = [record["snapshot"] for record in records]

            self.select_menu.values.clear()
            await interaction.response.edit_message(view=self)

            if records:
                paginator = PaginatorView(self.bot, self.moderator, new_records)
                embed = paginator.create_record_embed()
                await interaction.followup.send(embed=embed, view=paginator, ephemeral=True)
            else:
                await interaction.followup.send("No enlistment requests found.", ephemeral=True)
            

        elif self.select_menu.values[0] == "promotions":
            records = await promotion_requests.find({"guild_id": interaction.guild.id, "target_user_id": self.inacted_user.id, "is_active": False}, {"_id": 0, "snapshot": 1}).to_list(length=None)
            new_records = [record["snapshot"] for record in records]

            self.select_menu.values.clear()
            await interaction.response.edit_message(view=self)

            if records:
                paginator = PaginatorView(self.bot, self.moderator, new_records)
                embed = paginator.create_record_embed()
                await interaction.followup.send(embed=embed, view=paginator, ephemeral=True)
            else:
                await interaction.followup.send("No promotion requests found.", ephemeral=True)
        elif self.select_menu.values[0] == "points":
            records = await point_requests.find({"guild_id": interaction.guild.id, "target_user_id": self.inacted_user.id, "is_active": False}, {"_id": 0, "snapshot": 1}).to_list(length=None)
            new_records = [record["snapshot"] for record in records]

            self.select_menu.values.clear()
            await interaction.response.edit_message(view=self)

            if records:
                paginator = PaginatorView(self.bot, self.moderator, new_records)
                embed = paginator.create_record_embed()
                await interaction.followup.send(embed=embed, view=paginator, ephemeral=True)
            else:
                await interaction.followup.send("No point requests found.", ephemeral=True)