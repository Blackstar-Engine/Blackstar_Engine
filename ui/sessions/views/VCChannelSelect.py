import discord
from discord.ext import commands
from discord import ui
from utils.constants import active_sessions
from utils.utils import interaction_check

class VCSelect(ui.ChannelSelect):
    def __init__(self, game_link, user):
        self.user = user
        self.game_link = game_link
        super().__init__(placeholder="Choose a VC", channel_types=[discord.ChannelType.voice], min_values=1, max_values=1)
    
    async def _build_message(self, interaction: discord.Interaction, message: discord.Message, view: ui.LayoutView, container: ui.Container, vc: discord.VoiceChannel):
        users = {"\U0001F7E9": [], "\U0001F7E8": []}  # green + yellow

        valid_emojis = ("\U0001F7E9", "\U0001F7E8")  # green + yellow

        for reaction in message.reactions:
            emoji = str(reaction.emoji)

            if emoji in valid_emojis:
                async for user in reaction.users():
                    if not user.bot:
                        users[emoji] += [user.mention]

        if not users or users == {}:
            container.add_item(ui.TextDisplay("No voters found."))
            view.add_item(container)
            return await interaction.response.edit_message(view=view)


        send_message = f"**We are starting, please join {vc.mention}**\n{self.game_link}\n\n"
        
        for key, values in users.items():
            send_message += f"{key}: "
            send_message += " ".join(str(v) for v in values)
            send_message += "\n"
        
        return send_message

    async def callback(self, interaction: discord.Interaction):
        interaction_check(self.user, interaction.user)

        vc = interaction.guild.get_channel(int(self.values[0].id))

        data = await active_sessions.find_one({"guild_id": interaction.guild.id})

        view = ui.LayoutView()
        container = ui.Container()

        if not data:
            container.add_item(ui.TextDisplay("No active votes found."))
            view.add_item(container)
            return await interaction.response.edit_message(view=view)

        message_id = data.get("active_votes", {}).get(str(interaction.channel.id))

        if not message_id:
            container.add_item(ui.TextDisplay("No active vote in this channel."))
            view.add_item(container)
            return await interaction.response.edit_message(view=view)

        try:
            message = await interaction.channel.fetch_message(message_id)
        except discord.NotFound:
            container.add_item(ui.TextDisplay("Vote message was deleted."))
            view.add_item(container)
            return await interaction.response.edit_message(view=view)
        
        send_message = await self._build_message(interaction, message, view, container, vc)

        await message.reply(send_message)

        try:
            await message.clear_reactions()
        except discord.NotFound:
            pass

        await active_sessions.update_one(
            {"guild_id": interaction.guild.id},
            {
                "$unset": {
                    f"active_votes.{str(interaction.channel.id)}": ""
                }
            }
        )

        await interaction.message.delete()

class VCChannelSelectView(ui.LayoutView):
    def __init__(self, game_link, user):
        super().__init__(timeout=300)

        action_row = ui.ActionRow(VCSelect(game_link, user))
        container = ui.Container(
            ui.TextDisplay("## VC Selection"),
            ui.TextDisplay("Please select a vc to use below"),
            ui.Separator(),
            action_row,
            accent_color=discord.Color.light_grey()
        )
        self.add_item(container)