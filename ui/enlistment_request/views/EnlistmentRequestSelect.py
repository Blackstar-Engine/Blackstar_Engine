import discord
from discord.ui import Select
from ui.enlistment_request.views.EnlistmentRequestView import EnlistmentRequestView
from utils.utils import interaction_check, fetch_department, generate_timestamp
from discord import ui
import uuid
from utils.constants import enlistment_requests

async def send_enlistment_request(channel, user, department, profile):
    request_id = str(uuid.uuid4())

    snapshot = {
        "department_name": department["display_name"],
        "codename": profile.get("codename"),
        "roblox_name": profile.get("roblox_name"),
        "status": profile.get("status"),
        "user_id": user.id,
        "join_timestamp": generate_timestamp(profile["join_date"])
    }

    view = EnlistmentRequestView(request_id, snapshot)
    msg = await channel.send(view=view)

    await enlistment_requests.insert_one({
        "_id": request_id,
        "guild_id": channel.guild.id,
        "target_user_id": user.id,
        "department": department["display_name"],
        "join_timestamp": snapshot["join_timestamp"],
        "snapshot": snapshot,
        "channel_id": channel.id,
        "message_id": msg.id,
        "is_active": True
    })

class EnlistmentSelect(Select):
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

                await send_enlistment_request(channel, self.view.user, department, self.view.profile)
        
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

class EnlistmentRequestSelect(ui.LayoutView):
    def __init__(self, user, options, profile):
        super().__init__()
        self.user = user
        self.options = options
        self.profile = profile

        action_row = ui.ActionRow(EnlistmentSelect(options))

        container = ui.Container(
            ui.TextDisplay('## Department Selection'),
            ui.TextDisplay('Please select all departments you would like to enlist to.'),
            ui.Separator(),
            action_row,
            accent_color=discord.Color.light_grey()
        )

        self.add_item(container)
