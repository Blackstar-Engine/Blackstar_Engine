import discord
from discord.ext import commands
from discord import ui

class ViewTiersActionRow(ui.ActionRow):
    def __init__(self, bot: commands.Bot, options: list, all_tiers: list):
        super().__init__()
        self.bot = bot
        self.options = options
        self.all_tiers = all_tiers

        self.select_tiers = ui.Select(min_values=1, max_values=1, placeholder="Select a Tier", options=options)
        self.select_tiers.callback = self.tiers_callback

        self.add_item(self.select_tiers)

    async def tiers_callback(self, interaction: discord.Interaction):
        view = ViewMemView(self.bot, self.options, self.all_tiers)
        await interaction.response.edit_message(view=view, content=None, embed=None)
        value = int(self.select_tiers.values[0])
        tier = next((tier for tier in self.all_tiers if tier["rank"] == value), None)
        if not tier:
            return await interaction.followup.send("I could not find a tier by that name")
        
        tier_roles = list(tier["role_ids"])

        members = ""
        for role in tier_roles:
            role_obj = interaction.guild.get_role(role)
            for member in interaction.guild.members:
                if role_obj in member.roles:
                    members += f"{member.mention}\n"

        view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay(f"## Members of {tier.get("name").title()}"),
            ui.Separator(),
            ui.TextDisplay(members),
            accent_color=discord.Color.light_grey()
        )
        view.add_item(container)
        await interaction.followup.send(view=view, allowed_mentions=discord.AllowedMentions.none())

class ViewMemView(ui.LayoutView):
    def __init__(self, bot: commands.Bot, options: list, all_tiers: list):
        super().__init__()
        self.bot = bot
        self.options = options
        self.all_tiers = all_tiers

        container = ui.Container(
            ui.TextDisplay("## Select a Tier"),
            ui.TextDisplay("Please select a tier to see who is in there."),
            ui.Separator(),
            ViewTiersActionRow(bot, options, all_tiers),
            accent_color=discord.Color.light_grey()
        )

        self.add_item(container)