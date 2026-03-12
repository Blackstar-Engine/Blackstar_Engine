import discord
from discord import ui

class RoleSelectRow(ui.ActionRow):
    def __init__(self, results):
        super().__init__()
        self.results = results

        self.role_select = ui.Select(
            placeholder='Select a Role',
            custom_id='blackstar_main_reactions',
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Annoucements Ping", value=int(results["annoucement_role_id"]), emoji='<:BlackStar_Announcement:1467561153499631738>'),
                discord.SelectOption(label="D.P.R Display Ping", value=int(results["dpr_display_role_id"]), emoji='<:BlackStar_DPR:1474396677686300702>'),
                discord.SelectOption(label="MISC Ping", value=int(results["misc_role_id"]), emoji='<:BlackStar_Miscellaneous:1467561252120166533>'),
                discord.SelectOption(label="Game Night Ping", value=int(results["game_night_role_id"]), emoji='<:BlackStar_Gamenight:1467561216720240831>'),
                discord.SelectOption(label="Question Ping", value=int(results["question_role_id"]), emoji='<:BlackStar_QOTD:1467561311398268938>'),
                discord.SelectOption(label="Vote Ping", value=int(results["vote_role_id"]), emoji='<:BlackStar_Vote:1467561338321502348>'),
                discord.SelectOption(label="Chat Revive Ping", value=int(results["chat_revive_role_id"]), emoji='<:BlackStar_ChatRevive:1467561189612716205>'),
                discord.SelectOption(label="Raid Ping", value=int(results["raid_role_id"]), emoji='<:BlackStar_Raid:1474396707780431882>'),
                discord.SelectOption(label="Session Ping", value=int(results["session_role_id"]), emoji='<:BlackStar_Session:1474396734909190201>'),
                discord.SelectOption(label="External Training Ping", value=int(results['external_role_id']))
            ]
        )

        self.role_select.callback = self.role_selection_menu

        self.add_item(self.role_select)

    async def role_selection_menu(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        value = self.role_select.values[0]

        role = await interaction.guild.fetch_role(value)

        self.role_select.values.clear()

        await interaction.message.edit(view=self.view)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role, reason="Reaction Roles Removal")
            await interaction.followup.send(f"**{role.name}** has been removed", ephemeral=True)
        else:
            await interaction.user.add_roles(role, reason="Reaction Roles Addition")
            await interaction.followup.send(f"**{role.name}** has been added", ephemeral=True)

class RoleSelect(discord.ui.LayoutView):
    def __init__(self, results):
        super().__init__(timeout=None)
        self.results = results

        container = ui.Container(
            ui.TextDisplay('## Blackstar Role Selection'),
            ui.Separator(),
            ui.TextDisplay('The following are roles you can recieve notifications for: '),
            ui.TextDisplay('> <:BlackStar_Announcement:1467561153499631738> | **Annoucements Ping: ** Main Annoucements\n'
                           '> <:BlackStar_DPR:1474396677686300702> | **D.P.R Display Ping: ** D.P.R Notifications\n'
                           '> <:BlackStar_Miscellaneous:1467561252120166533> | **MISC Ping: ** Miscellaneous\n'
                           '> <:BlackStar_Gamenight:1467561216720240831> | **Game Night Ping: ** Game Nights\n'
                           '> <:BlackStar_QOTD:1467561311398268938> | **Question Ping: ** Question of the Day\n'
                           '> <:BlackStar_Vote:1467561338321502348> | **Vote Ping: ** Votes\n'
                           '> <:BlackStar_ChatRevive:1467561189612716205> | **Chat Revive Ping: ** Chat Revival\n'
                           '> <:BlackStar_Raid:1474396707780431882> | **Raid Ping: ** Server Raid notifications\n'
                           '> <:BlackStar_Session:1474396734909190201> | **Session Ping: ** SSU Notifications\n'
                           '> **External Training Ping: ** Other Game Trainings'
                           ),
            ui.Separator(),
            ui.TextDisplay('*Select a role below to add or remove the role.*'),
            RoleSelectRow(results),
            accent_color=discord.Color.light_grey()
        )

        self.add_item(container)

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