import discord

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
            discord.SelectOption(label="Annoucements Ping", value=1450297860846387312, emoji='<:BlackStar_Announcement:1467561153499631738>'),
            discord.SelectOption(label="Poll Ping", value=1450297861836247050, emoji='<:BlackStar_Poll:1467561281698660565>'),
            discord.SelectOption(label="MISC Ping", value=1450297863145001030, emoji='<:BlackStar_Miscellaneous:1467561252120166533>'),
            discord.SelectOption(label="Game Night Ping", value=1450297865569304596, emoji='<:BlackStar_Gamenight:1467561216720240831>'),
            discord.SelectOption(label="Question Ping", value=1450297866991042701, emoji='<:BlackStar_QOTD:1467561311398268938>'),
            discord.SelectOption(label="Vote Ping", value=1450297868459049131, emoji='<:BlackStar_Vote:1467561338321502348>'),
            discord.SelectOption(label="Chat Revive Ping", value=1450297899811475558, emoji='<:BlackStar_ChatRevive:1467561189612716205>'),
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