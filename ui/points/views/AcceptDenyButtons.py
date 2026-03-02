import discord
from discord import ui
from utils.constants import (
    ia_id, central_command, high_command, site_command,
    foundation_command, wolf_id, profiles, point_requests, BlackstarConstants,
    ghost_id
)
from utils.utils import generate_timestamp

constants = BlackstarConstants()

# ---------- Permission Logic ----------

def has_points_approval_perms(member: discord.Member, snapshot: dict, guild: discord.Guild):
    if (member.id == wolf_id) or (constants.ENVIRONMENT == "DEVELOPMENT" and member.id == ghost_id):
        return True
    
    if int(member.id) == int(snapshot['user_id']):
        return False

    ia_role = guild.get_role(ia_id)
    central_role = guild.get_role(central_command)
    high_role = guild.get_role(high_command)
    site_role = guild.get_role(site_command)
    foundation_role = guild.get_role(foundation_command)

    points = snapshot["points"]

    if 1 <= points <= 1.5:
        allowed = [ia_role, central_role, high_role, site_role, foundation_role]
    elif 1.5 < points <= 2:
        allowed = [central_role, high_role, site_role, foundation_role]
    elif 2 < points <= 7.99:
        allowed = [site_role, foundation_role]
    elif points >= 8:
        allowed = [foundation_role]
    else:
        allowed = []

    allowed = [r for r in allowed if r is not None]
    return any(role in member.roles for role in allowed)


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
        await handle_points_decision(interaction, approved=False)


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

async def handle_points_decision(interaction: discord.Interaction, approved: bool):
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

    if not has_points_approval_perms(interaction.user, snapshot, guild):
            return await interaction.response.send_message(
                "❌ You do not have permission to act on this point request.",
                ephemeral=True
            )

    if approved:

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

    result_view.add_item(container)
    await interaction.response.edit_message(view=result_view)

    member = guild.get_member(snapshot["user_id"])
    if member:
        status = "ACCEPTED" if approved else "DENIED"
        await member.send(
            f"Your points request for **{snapshot['points']}** "
            f"in **{guild.name}** has been **{status}**."
        )