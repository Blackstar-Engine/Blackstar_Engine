import discord
from discord import ui
from datetime import datetime
from utils.constants import profiles, promotion_requests
from utils.utils import has_approval_perms, fetch_id
from ui.PointsRemoval import PointsRemovalModal


# ---------- Persistent Buttons ----------

class PromotionAcceptButton(ui.Button):
    def __init__(self, request_id: str):
        super().__init__(
            label="Accept",
            style=discord.ButtonStyle.green,
            custom_id=f"promo_accept:{request_id}"
        )

    async def callback(self, interaction: discord.Interaction):
        await handle_promotion_decision(interaction, approved=True)


class PromotionDenyButton(ui.Button):
    def __init__(self, request_id: str):
        super().__init__(
            label="Deny",
            style=discord.ButtonStyle.red,
            custom_id=f"promo_deny:{request_id}"
        )

    async def callback(self, interaction: discord.Interaction):
        await handle_promotion_decision(interaction, approved=False)


# ---------- Persistent LayoutView ----------

class PromotionRequestView(ui.LayoutView):
    def __init__(self, bot, request_id: str, snapshot: dict):
        super().__init__(timeout=None)
        self.bot = bot
        self.request_id = request_id

        timestamp = f"<t:{snapshot['join_timestamp']}:d>"

        action_row = ui.ActionRow(
            PromotionAcceptButton(request_id),
            PromotionDenyButton(request_id)
        )

        container = ui.Container(
            ui.TextDisplay("## Promotion Request"),
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
            action_row,
            accent_color=discord.Color.yellow()
        )

        self.add_item(container)


# ---------- Decision Handler ----------

async def handle_promotion_decision(interaction: discord.Interaction, approved: bool):
    bot = interaction.client
    request_id = interaction.data["custom_id"].split(":")[1]

    if not await has_approval_perms(interaction.user, 3):
        return await interaction.response.send_message(
            "You do not have permission to manage promotions.",
            ephemeral=True
        )

    req = await promotion_requests.find_one({
        "_id": request_id,
        "is_active": True
    })

    if not req:
        return await interaction.response.send_message(
            "This promotion request is no longer active.",
            ephemeral=True
        )

    snapshot = req["snapshot"]
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
    color = discord.Color.green() if approved else discord.Color.red()
    title = "## Promotion Request Approved" if approved else "## Promotion Request Denied"

    timestamp = f"<t:{snapshot['join_timestamp']}:d>"

    container = ui.Container(
        ui.TextDisplay(title),
        ui.TextDisplay(
            f"**{snapshot['current_rank']}** ⟶ **{snapshot['new_rank']}**\n"
            f"> **Department:** {department}\n"
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
        ui.TextDisplay(f"> **Moderator:** {interaction.user.mention}"),
        accent_color=color
    )

    result_view.add_item(container)
    await interaction.message.edit(view=result_view)

    # DM user
    member = guild.get_member(snapshot["user_id"])
    if member:
        status = "APPROVED" if approved else "DENIED"
        await member.send(
            f"Your promotion to **{snapshot['new_rank']}** "
            f"in **{guild.name}** has been **{status}**."
        )

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