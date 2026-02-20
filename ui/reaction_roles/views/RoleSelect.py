import discord
from utils.constants import annoucement_role_id, chat_revive_role_id, dpr_display_role_id, game_night_role_id, misc_role_id, question_role_id, raid_role_id, session_role_id, vote_role_id

class RoleSelect(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.select(
        placeholder="Select a Role",
        custom_id="blackstar_main_reactions",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Annoucements Ping", value=int(annoucement_role_id), emoji='<:BlackStar_Announcement:1467561153499631738>'),
            discord.SelectOption(label="D.P.R Display Ping", value=int(dpr_display_role_id), emoji='<:BlackStar_DPR:1474396677686300702>'),
            discord.SelectOption(label="MISC Ping", value=int(misc_role_id), emoji='<:BlackStar_Miscellaneous:1467561252120166533>'),
            discord.SelectOption(label="Game Night Ping", value=int(game_night_role_id), emoji='<:BlackStar_Gamenight:1467561216720240831>'),
            discord.SelectOption(label="Question Ping", value=int(question_role_id), emoji='<:BlackStar_QOTD:1467561311398268938>'),
            discord.SelectOption(label="Vote Ping", value=int(vote_role_id), emoji='<:BlackStar_Vote:1467561338321502348>'),
            discord.SelectOption(label="Chat Revive Ping", value=int(chat_revive_role_id), emoji='<:BlackStar_ChatRevive:1467561189612716205>'),
            discord.SelectOption(label="Raid Ping", value=int(raid_role_id), emoji='<:BlackStar_Raid:1474396707780431882>'),
            discord.SelectOption(label="Session Ping", value=int(session_role_id), emoji='<:BlackStar_Session:1474396734909190201>')
        ]
    )
    async def role_selection_menu(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        value = select.values[0]

        role = await interaction.guild.fetch_role(value)

        select.values.clear()

        await interaction.edit_original_response(view=self)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role, reason="Reaction Roles Removal")
            await interaction.followup.send(f"**{role.name}** has been removed", ephemeral=True)
        else:
            await interaction.user.add_roles(role, reason="Reaction Roles Addition")
            await interaction.followup.send(f"**{role.name}** has been added", ephemeral=True)