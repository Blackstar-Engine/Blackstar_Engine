import discord
from discord import ui
from utils.constants import (
    profiles, point_requests, BlackstarConstants
)
from utils.utils import generate_timestamp, has_approval_perms, log_action
from ui.ReasonModal import ReasonModal

constants = BlackstarConstants()

# ---------- Permission Logic ----------

async def has_points_approval_perms(interaction: discord.Interaction, snapshot: dict):
    member = interaction.user
    if int(member.id) == int(snapshot['user_id']):
        return False

    points = snapshot["points"]

    if 0.5 <= points <= 1.5:
        if not await has_approval_perms(interaction, 1):
            return False
    elif 1.5 < points <= 2:
        if not await has_approval_perms(interaction, 3):
            return False
    elif 2 < points <= 7.99:
        if not await has_approval_perms(interaction, 5):
            return False
    elif points >= 8:
        if not await has_approval_perms(interaction, 6):
            return False
    else:
        return False
    
    return True

# ---------- Persistent Buttons ----------

class PointsAcceptButton(ui.Button):
    def __init__(self, request_id: str):
        super().__init__(
            label="Accept",
            style=discord.ButtonStyle.green,
            custom_id=f"points_accept:{request_id}"
        )

    async def callback(self, interaction: discord.Interaction):
        await handle_points_decision(interaction, approved=True)


class PointsDenyButton(ui.Button):
    def __init__(self, request_id: str):
        super().__init__(
            label="Deny",
            style=discord.ButtonStyle.red,
            custom_id=f"points_deny:{request_id}"
        )

    async def callback(self, interaction: discord.Interaction):
        modal = ReasonModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        await handle_points_decision(interaction, approved=False, reason=modal.data)


# ---------- Persistent LayoutView ----------

class PointsRequestView(ui.LayoutView):
    def __init__(self, request_id: str, snapshot: dict):
        super().__init__(timeout=None)
        self.request_id = request_id

        timestamp = f"<t:{snapshot['join_timestamp']}:d>"
        
        action_row = ui.ActionRow(
            PointsAcceptButton(request_id),
            PointsDenyButton(request_id),
        )

        container = ui.Container(
            ui.TextDisplay("## Point Request"),
            ui.TextDisplay(
                f"> **User:** <@{snapshot['user_id']}>\n"
                f"> **Requested Points:** {snapshot['points']}\n"
                f"> **Proof:** {snapshot['proof']}"
            ),
            ui.Separator(),
            ui.TextDisplay("### Profile Information"),
            ui.TextDisplay(
                f"> **Codename:** {snapshot['codename']}\n"
                f"> **Join Date:** {timestamp}\n"
                f"> **{snapshot['department']} Points:** "
                f"{snapshot['current_points']}/{snapshot['total_points']}"
            ),
            ui.Separator(),
            action_row,
            accent_color=discord.Color.yellow()
        )

        self.add_item(container)


# ---------- Decision Handler ----------

async def handle_points_decision(interaction: discord.Interaction, approved: bool, reason: str = None):
    request_id = interaction.data["custom_id"].split(":")[1]

    req = await point_requests.find_one({
        "_id": request_id,
        "is_active": True
    })

    if not req:
        return await interaction.response.send_message(
            "This point request is no longer active.",
            ephemeral=True
        )

    snapshot = req["snapshot"]
    guild = interaction.guild

    if not await has_points_approval_perms(interaction, snapshot):
        try:
            return await interaction.response.send_message("❌ You do not have permission to act on this point request.", ephemeral=True) 
        except discord.InteractionResponded:
            return await interaction.followup.send("❌ You do not have permission to act on this point request.", ephemeral=True) 
    
    if approved:
        await log_action(ctx=interaction, log_type="point_addition", user_id=snapshot["user_id"], points=snapshot["points"], command_name="point request")

        profile = await profiles.find_one({
            "guild_id": guild.id,
            "user_id": snapshot["user_id"]
        })

        dept = snapshot["department"]

        await profiles.update_one(
            {"_id": profile["_id"]},
            {
                "$inc": {
                    f"unit.{dept}.current_points": snapshot["points"],
                    f"unit.{dept}.total_points": snapshot["points"]
                }
            }
        )

    # mark inactive
    await point_requests.update_one(
        {"_id": request_id},
        {"$set": {"is_active": False}}
    )

    # ---------- Result UI ----------

    result_view = ui.LayoutView()
    color = discord.Color.green() if approved else discord.Color.red()
    title = "## Point Request Accepted" if approved else "## Point Request Denied"

    timestamp = f"<t:{snapshot['join_timestamp']}:d>"

    container = ui.Container(
        ui.TextDisplay(title),
        ui.TextDisplay(
            f"> **User:** <@{snapshot['user_id']}>\n"
            f"> **Requested Points:** {snapshot['points']}\n"
            f"> **Proof:** {snapshot['proof']}"
        ),
        ui.Separator(),
        ui.TextDisplay("### Profile Information"),
        ui.TextDisplay(
            f"> **Codename:** {snapshot['codename']}\n"
            f"> **Join Date:** {timestamp}\n"
            f"> **{snapshot['department']} Points:** "
            f"{snapshot['current_points']}/{snapshot['total_points']}"
        ),
        ui.Separator(),
        ui.TextDisplay(f"> **Moderator:** {interaction.user.mention}"),
        accent_color=color
    )

    if reason:
        container.add_item(ui.TextDisplay(f"> **Reason: ** {reason}"))

    result_view.add_item(container)
    try:
        await interaction.response.edit_message(view=result_view)
    except discord.InteractionResponded:
        await interaction.edit_original_response(view=result_view)

    member = guild.get_member(snapshot["user_id"])
    if member:
        status = "ACCEPTED" if approved else "DENIED"
        embed = discord.Embed(
            title=f"Points Request {status}",
            description=(
                f"> **Requested Points:** {snapshot['points']}\n"
                f"> **Moderator:** {interaction.user.mention}\n"
                f"> **Reason:** {reason if reason else 'No reason provided.'}\n"
                f"> **Server: **{guild.name}"
            ),
            color=color
        )

        await member.send(embed=embed)