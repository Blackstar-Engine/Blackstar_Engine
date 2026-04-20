import discord
from discord import ui
from datetime import datetime
from utils.constants import profiles, promotion_requests
from utils.utils import has_approval_perms, fetch_id
from ui.PointsRemoval import PointsRemovalModal
from ui.ReasonModal import ReasonModal


# ---------- Persistent Buttons ----------
class PromotionAcceptButton(ui.Button):
    def __init__(self, request_id: str):
        super().__init__(
            label="Accept",
            style=discord.ButtonStyle.green,
            custom_id=f"promo_accept:{request_id}"
        )

    async def callback(self, interaction: discord.Interaction):
        await promotion_requests.update_one(
            {"_id": self.custom_id.split(":")[1]},
            {"$set": {"snapshot.moderator_id": interaction.user.id}}
        )
        await handle_promotion_decision(interaction, approved=True)


class PromotionDenyButton(ui.Button):
    def __init__(self, request_id: str):
        super().__init__(
            label="Deny",
            style=discord.ButtonStyle.red,
            custom_id=f"promo_deny:{request_id}"
        )

    async def callback(self, interaction: discord.Interaction):
        modal = ReasonModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        await promotion_requests.update_one(
            {"_id": self.custom_id.split(":")[1]},
            {"$set": {"snapshot.moderator_id": interaction.user.id}}
        )

        await handle_promotion_decision(interaction, approved=False, reason = modal.data)

class AppointmentVCOpen(ui.Button):
    def __init__(self, request_id: str):
        super().__init__(
            label="Open VC",
            style=discord.ButtonStyle.blurple,
            custom_id=f"appointment_vc_open:{request_id}"
        )

    async def callback(self, interaction: discord.Interaction):
        await has_approval_perms(interaction.user, 6)    
            
        snapshot = await promotion_requests.find_one({"_id": self.custom_id.split(":")[1]}, {"snapshot": 1})

        user = interaction.guild.get_member(snapshot["snapshot"]["user_id"])

        channel = await interaction.guild.create_voice_channel(
            name=f"Appointment - {interaction.user.display_name[0:10]}",
            category=interaction.channel.category,
            overwrites={
                interaction.guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=False),
                interaction.user: discord.PermissionOverwrite(connect=True, manage_channels=True, send_voice_messages=True, view_channel=True),
                user: discord.PermissionOverwrite(connect=True, view_channel=True, send_voice_messages=True)
            },
            reason=f"Appointment VC for {user} opened by {interaction.user}"
            )
        await interaction.response.send_message(f"VC has been opened. Please join {channel.mention}.", ephemeral=True)
        
        await promotion_requests.update_one(
            {"_id": self.custom_id.split(":")[1]},
            {"$set": {"appointment_vc_id": channel.id}}
        )

        # Edit message to show Close VC button
        request_id = self.custom_id.split(":")[1]
        new_view = ui.LayoutView(timeout=None)
        action_row = ui.ActionRow(
            AppointmentVCClose(request_id)
        )
        container, _ = generate_container(snapshot=snapshot["snapshot"], action_row=action_row, initial=True)
        new_view.add_item(container)
        await interaction.message.edit(view=new_view)

class AppointmentVCClose(ui.Button):
    def __init__(self, request_id: str):
        super().__init__(
            label="Close VC",
            style=discord.ButtonStyle.red,
            custom_id=f"appointment_vc_close:{request_id}"
        )

    async def callback(self, interaction: discord.Interaction):
        await has_approval_perms(interaction.user, 6)

        snapshot = await promotion_requests.find_one({"_id": self.custom_id.split(":")[1]})

        channel_id = snapshot.get("appointment_vc_id", None)
        if not channel_id:
            return await interaction.response.send_message("No VC found for this appointment.", ephemeral=True)

        channel = interaction.guild.get_channel(channel_id)
        if channel:
            await channel.delete(reason=f"Appointment VC closed by {interaction.user}")

        await promotion_requests.update_one(
            {"_id": self.custom_id.split(":")[1]},
            {"$unset": {"appointment_vc_id": ""}}
        )

        # After closing VC, edit message to show Accept and Deny buttons
        request_id = self.custom_id.split(":")[1]
        new_view = ui.LayoutView(timeout=None)
        action_row = ui.ActionRow(
            PromotionAcceptButton(request_id),
            PromotionDenyButton(request_id)
        )
        container, _ = generate_container(snapshot=snapshot["snapshot"], action_row=action_row, initial=True)
        new_view.add_item(container)
        await interaction.message.edit(view=new_view)
        await interaction.response.send_message("VC closed. Now you can accept or deny the promotion.", ephemeral=True)


# ---------- Persistent LayoutView ----------

class PromotionRequestView(ui.LayoutView):
    def __init__(self, bot, request_id: str, snapshot: dict):
        super().__init__(timeout=None)
        self.bot = bot
        self.request_id = request_id

        try:
            is_appointment = snapshot.get("is_appointment", False)
        except KeyError:
            is_appointment = False
        
        if is_appointment:
            action_row = ui.ActionRow(
                AppointmentVCOpen(request_id)
            )
        else:
            action_row = ui.ActionRow(
                PromotionAcceptButton(request_id),
                PromotionDenyButton(request_id)
            )

        container, _ = generate_container(snapshot=snapshot, action_row=action_row, initial=True)

        self.add_item(container)

# ---------- Decision Handler ----------

def generate_container(snapshot: dict, action_row: ui.ActionRow = None, reason: str = None, initial: bool = False):
    if not initial:
        color = discord.Color.green() if reason is None else discord.Color.red()
        title = "## Promotion Request Approved" if reason is None else "## Promotion Request Denied"
    else:
        color = discord.Color.yellow()
        title = "## Promotion Request"

    timestamp = f"<t:{snapshot['join_timestamp']}:d>"

    container = ui.Container(
        ui.TextDisplay(title),
        ui.TextDisplay(
            f"**{snapshot['current_rank']}** ⟶ **{snapshot['new_rank']}**\n"
            f"> **Department:** {snapshot['department']}\n"
            f"> **Proof:** {snapshot['proof']}"
        ),
        ui.Separator(),
        ui.TextDisplay("### Profile Information"),
        ui.TextDisplay(
            f"> **User:** <@{snapshot['user_id']}>\n"
            f"> **Codename:** {snapshot['codename']}\n"
            f"> **Status:** {snapshot['status']}\n"
            f"> **Join Date:** {timestamp}\n"
            f"> **Points:** {snapshot['current_points']}/{snapshot['total_points']}"
        ),
        ui.Separator(),
        accent_color=color
    )

    if action_row:
        container.add_item(action_row)

    if not initial:
        container.add_item(ui.TextDisplay(f"> **Moderator:** <@{snapshot.get('moderator_id', 'Unknown')}>"),)

    if reason:
        container.add_item(ui.TextDisplay(f"> **Reason: ** {reason}"))

    return container, color

async def handle_promotion_decision(interaction: discord.Interaction, approved: bool, reason: str = None):
    bot = interaction.client
    request_id = interaction.data["custom_id"].split(":")[1]


    req = await promotion_requests.find_one({
        "_id": request_id,
        "is_active": True
    })

    if not req:
        try:
            return await interaction.response.send_message(
                "This promotion request is no longer active.",
                ephemeral=True
            )
        except discord.InteractionResponded:
            return await interaction.followup.send(
                "This promotion request is no longer active.",
                ephemeral=True
            )

    snapshot = req["snapshot"]

    if snapshot.get("is_appointment", False):
        await has_approval_perms(interaction.user, 6)
    else:
        await has_approval_perms(interaction.user, 3)
            
    guild = interaction.guild
    department = snapshot["department"]

    profile = await profiles.find_one({
        "guild_id": guild.id,
        "user_id": snapshot["user_id"]
    })

    if approved:
        modal = PointsRemovalModal(profile)
        await interaction.response.send_modal(modal)
        await modal.wait()

        points_to_remove = modal.data
        if points_to_remove is None:
            return await interaction.followup.send(
                "Promotion approval cancelled.",
                ephemeral=True
            )

        await profiles.update_one(
            {"user_id": snapshot["user_id"], "guild_id": interaction.guild.id},
            {
                "$set": {
                    f"unit.{department}.rank": snapshot["new_rank"]
                },
                "$inc": {
                    f"unit.{department}.current_points": -float(points_to_remove)
                }
            }
        )

    # mark inactive
    await promotion_requests.update_one(
        {"_id": request_id},
        {"$set": {"is_active": False}}
    )

    # ---------- Result UI ----------

    result_view = ui.LayoutView()
    container, color = generate_container(snapshot=snapshot, reason=reason, initial=False, action_row=None)

    result_view.add_item(container)

    try:
        await interaction.message.edit(view=result_view)
    except discord.InteractionResponded:
        await interaction.edit_original_response(view=result_view)

    # DM user
    member = guild.get_member(snapshot["user_id"])
    if member:
        status = "APPROVED" if approved else "DENIED"
        embed = discord.Embed(
            title=f"Promotion {status}",
            description=(
                f"> **New Rank:** {department} | {snapshot['new_rank']}\n"
                f"> **Moderator:** {interaction.user.mention}\n"
                f"> **Reason:** {reason if reason else 'No reason provided.'}\n"
                f"> **Server: **{guild.name}"
            ),
            color=color
        )

        await member.send(embed=embed)

    # announce promotion
    results = await fetch_id(interaction.guild.id, ["overall_promotion_channel"])
    if approved:
        channel = bot.get_channel(results["overall_promotion_channel"])
        if channel and member:
            embed = discord.Embed(
                title="New Promotion",
                description=(
                    f"**User:** {member.mention}\n"
                    f"**New Rank:** {snapshot['new_rank']}\n"
                    f"**Department:** {department}"
                ),
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Blackstar Engine • {datetime.now().date()}")
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)