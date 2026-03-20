import discord
from discord import ui
from discord.ext import commands
from utils.constants import enlistment_requests, profiles
from utils.utils import has_approval_perms, log_action, fetch_department

# ---------- Buttons ----------

class DeptAcceptButton(ui.Button):
    def __init__(self, request_id: str):
        super().__init__(
            label="Accept",
            style=discord.ButtonStyle.green,
            custom_id=f"dept_accept:{request_id}"
        )

    async def callback(self, interaction: discord.Interaction):
        await handle_enlistment_decision(interaction, approved=True)


class DeptDenyButton(ui.Button):
    def __init__(self, request_id: str):
        super().__init__(
            label="Deny",
            style=discord.ButtonStyle.red,
            custom_id=f"dept_deny:{request_id}"
        )

    async def callback(self, interaction: discord.Interaction):
        await handle_enlistment_decision(interaction, approved=False)


# ---------- Persistent LayoutView ----------

class EnlistmentRequestView(ui.LayoutView):
    def __init__(self, request_id: str, snapshot: dict):
        super().__init__(timeout=None)
        self.request_id = request_id

        timestamp = f"<t:{snapshot['join_timestamp']}:d>"

        button_row = ui.ActionRow(
                                    DeptAcceptButton(request_id),
                                    DeptDenyButton(request_id)
                                    )

        container = ui.Container(
            ui.TextDisplay("## Enlistment Request"),
            ui.TextDisplay(
                f"**Department:** {snapshot['department_name']}\n"
                f"**User:** <@{snapshot['user_id']}>\n"
                f"**Codename:** {snapshot['codename']}\n"
                f"**Roblox Name:** {snapshot['roblox_name']}\n"
                f"**Status:** {snapshot['status']}\n"
                f"**Join Date:** {timestamp}\n"
            ),
            ui.Separator(),
            button_row,
            accent_color=discord.Color.yellow()
        )

        self.add_item(container)


# ---------- Decision Handler ----------

async def handle_enlistment_decision(interaction: discord.Interaction, approved: bool):
    request_id = interaction.data["custom_id"].split(":")[1]

    if not await has_approval_perms(interaction.user, 3):
        return await interaction.response.send_message(
            "You need foundation, site, central, or high command.",
            ephemeral=True
        )

    req = await enlistment_requests.find_one({
        "_id": request_id,
        "is_active": True
    })

    if not req:
        return await interaction.response.send_message(
            "This enlistment request is no longer active.",
            ephemeral=True
        )

    guild = interaction.guild
    target_user = guild.get_member(req["target_user_id"])

    profile = await profiles.find_one({
        "guild_id": guild.id,
        "user_id": req["target_user_id"]
    })

    department = req["department"]

    # ---------- APPLY RESULT ----------

    if approved:
        department_doc = await fetch_department(interaction, department)
        await apply_department_accept(profile, department_doc)

    await enlistment_requests.update_one(
        {"_id": request_id},
        {"$set": {"is_active": False}}
    )

    # ---------- RESULT UI ----------

    color = discord.Color.green() if approved else discord.Color.red()
    title = "## Enlistment Accepted" if approved else "## Enlistment Denied"

    timestamp = f"<t:{req['join_timestamp']}:d>"

    result_view = ui.LayoutView()
    container = ui.Container(
        ui.TextDisplay(title),
        ui.TextDisplay(
            f"**Department:** {req['snapshot']['department_name']}\n"
            f"**User:** <@{req['snapshot']['user_id']}>\n"
            f"**Codename:** {req['snapshot']['codename']}\n"
            f"**Roblox Name:** {req['snapshot']['roblox_name']}\n"
            f"**Status:** {req['snapshot']['status']}\n"
            f"**Join Date:** {timestamp}\n"
        ),
        ui.Separator(),
        ui.TextDisplay(f"**Moderator:** {interaction.user.mention}"),
        accent_color=color
    )

    result_view.add_item(container)

    await log_action(ctx=interaction, log_type="department", user_id=req['snapshot']['user_id'], department=req['snapshot']['department_name'])

    if target_user:
        status = "ACCEPTED" if approved else "DENIED"
        await target_user.send(
            f"Your department request for **{department}** "
            f"in **{guild.name}** has been **{status}**."
        )

    await interaction.response.edit_message(view=result_view)


# ---------- Profile Update Logic ----------

async def apply_department_accept(profile: dict, department: dict):
    unit_key = department["display_name"]
    unit_data = profile.get("unit", {}).get(unit_key)

    if unit_data is None:
        await profiles.update_one(
            {"_id": profile["_id"]},
            {
                "$set": {
                    f"unit.{unit_key}": {
                        "rank": department["ranks"][0]["name"],
                        "is_active": True,
                        "current_points": 0,
                        "total_points": 0,
                        "subunits": []
                    }
                }
            }
        )

    elif unit_data.get("is_active") is False:
        unit_data["is_active"] = True
        await profiles.update_one(
            {"_id": profile["_id"]},
            {"$set": {f"unit.{unit_key}": unit_data}}
        )

    else:
        raise commands.CommandInvokeError("Failed to add unit")