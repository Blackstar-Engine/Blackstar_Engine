import discord
from discord.ext import commands
from discord.ui import View, Select
from ui.department_request.view.AcceptDenyButtons import AcceptDenyButtons
from utils.utils import interaction_check, fetch_department
from discord import ui

class DepartmentSelect(Select):
    def __init__(self, options):
        super().__init__(
            placeholder="Select the departments",
            min_values=1,
            max_values=len(options),
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        interaction_check(self.view.user, interaction.user)
        await interaction.response.defer(ephemeral=True)

        values = self.values
        cannot_send_list = []

        for value in values:
            if value in self.view.profile.get("unit") and self.view.profile["unit"][value]["is_active"]:
                cannot_send_list.append(value)
            else:
                department = await fetch_department(interaction, value)

                channel = await interaction.guild.fetch_channel(department.get("request_channel"))
                
                view = AcceptDenyButtons(self.view.bot, self.view.user, department, self.view.profile)
                
                try:
                    await channel.send(view=view)
                except discord.Forbidden:
                    pass
        
        view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay('## Enlistments Sent!'),
            ui.TextDisplay('All enlistments have been sent for review!'),
            accent_color=discord.Color.green()
        )

        if len(cannot_send_list) > 0:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay('### Unable to Send to:'))
            container.add_item(ui.TextDisplay(", ".join(cannot_send_list)))

        view.add_item(container)
        await interaction.edit_original_response(view=view)
        self.view.stop()

class DepartmentsRequestView(ui.LayoutView):
    def __init__(self, bot, user, options, profile):
        super().__init__()
        self.bot = bot
        self.user = user
        self.options = options
        self.profile = profile

        action_row = ui.ActionRow(DepartmentSelect(options))

        container = ui.Container(
            ui.TextDisplay('## Department Selection'),
            ui.TextDisplay('Please select all departments you would like to enlist to.'),
            ui.Separator(),
            action_row,
            accent_color=discord.Color.light_grey()
        )

        self.add_item(container)
