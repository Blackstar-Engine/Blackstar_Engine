import discord
from discord import ui
from discord.ext import commands
from utils.constants import profiles
from ui.paginator import PaginatorView
from utils.utils import interaction_check
from ui.manage_commands.views.ManageDeptChannelRoles import ManageDeptChannelRolesView

class ManageDeptSelect(ui.Select):
    def __init__(self, bot, user, department_doc, parent_view):
        super().__init__(min_values=1, 
                         max_values=1, 
                         placeholder="What would you like to do?",
                         options=[
                             discord.SelectOption(label="View Ranks", value="view_ranks"),
                             discord.SelectOption(label="View Members", value="view_members"),
                             discord.SelectOption(label="Manage Channels/Roles", value="manage_channels_roles"),
                             discord.SelectOption(label="Manage Enlistments", value="manage_enlistments"),
                         ])
        self.bot = bot
        self.user = user
        self.department_doc = department_doc
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        interaction_check(self.user, interaction.user)
        selected_option = self.values[0]

        if selected_option == "view_ranks":
            ranks = ""
            for info in self.department_doc.get("ranks", []):
                name = info.get("name", "N/A")
                points = info.get("required_points", "N/A")
                appointment_only = info.get("appointment_only", False)

                ranks += f"__**{name}**__ -\n> **Required Points:** {points["current"]}/{points["total"]}\n> **Appointment Only:** {appointment_only}\n"
            
            view = ui.LayoutView()
            container = ui.Container(
                ui.TextDisplay("## All Ranks"),
                ui.Separator(),
                ui.TextDisplay(ranks),
                accent_color=discord.Color.light_grey()
            )
            view.add_item(container)

            await interaction.response.edit_message(view=self.parent_view)

            await interaction.followup.send(view=view, ephemeral=True)

        elif selected_option == "view_members":
            all_profiles = await profiles.find({f"unit.{self.department_doc['display_name']}.is_active": True}, {"user_id": 1, "codename": 1, "roblox_name": 1, "private_unit": 1, "status": 1, "join_date": 1, "timezone": 1, f"unit.{self.department_doc['display_name']}": 1}).to_list(length=None)
            
            view = PaginatorView(self.bot, self.user, all_profiles)
            embed = view.create_record_embed()

            await interaction.response.edit_message(view=self.parent_view)

            await interaction.followup.send(view=view, embed=embed, ephemeral=True)

        elif selected_option == "manage_channels_roles":
            view = ManageDeptChannelRolesView(self.bot, self.user, self.department_doc, self.parent_view)
            await interaction.response.send_message(view=view, ephemeral=True)

        elif selected_option == "manage_enlistments":
            await interaction.response.send_message("This feature is coming soon!", ephemeral=True)

class ManageDeptMainView(ui.LayoutView):
    def __init__(self, bot, user, department_doc: dict):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user
        self.department_doc = department_doc

        action_row = ui.ActionRow(ManageDeptSelect(bot, user, department_doc, self))
        container = ui.Container(
            ui.TextDisplay(f"## {department_doc.get("display_name")} Department Management"),
            ui.Separator(),
            ui.TextDisplay("**Department Information**\n"),
            ui.TextDisplay(f"**Name**: {department_doc.get("name")}\n"
                           f"**Display Name**: {department_doc.get("display_name")}\n"
                           f"**Promotion Channel**: <#{department_doc.get("promo_request_channel", 0)}>\n"
                           f"**Point Request Channel:** <#{department_doc.get("points_request_channel", 0)}>\n"
                           f"**First Rank:** <@&{department_doc.get("first_rank_id", 0)}>\n"
                           f"**Overall Role:** <@&{department_doc.get("role_id", 0)}>\n"
                           f"**Number of Ranks:** {len(department_doc.get("ranks", []))}"
                           ),
            ui.Separator(),
            action_row,
            accent_color=discord.Color.light_grey()   
        )

        self.add_item(container)