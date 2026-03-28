import discord
from discord.ui import View, Select
from utils.constants import application_channels

class ApplicationOpen(View):
    def __init__(self):
        super().__init__()

        dropdown = Select(
            placeholder="Select a department",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Intelligence Agency"),
                discord.SelectOption(label="Internal Security Department"),
                discord.SelectOption(label="Rapid Response Team"),
                discord.SelectOption(label="Omega-1"),
                discord.SelectOption(label="Alpha-1"),
                discord.SelectOption(label="Resh-1"),
                discord.SelectOption(label="Moderation Team")
            ]
        )

        async def dropdown_callback(interaction: discord.Interaction):
            try:
                channel_id = application_channels[dropdown.values[0]]
                channel = await interaction.guild.fetch_channel(channel_id)

                overwrite = channel.overwrites_for(interaction.guild.default_role)
                overwrite.view_channel = True
                await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)   
                embed = discord.Embed(title="The Blackstar Corporation", description=f"`{dropdown.values[0]}` applications have been temporarily opened.", color=discord.Color.light_gray())
                embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1450302678524756040/3557930241bf8360a9535a5f27d42cf4.png?size=1024")
                await channel.send(embed=embed)
                await interaction.response.send_message("Applications have been opened!", ephemeral=True)
            except KeyError:
                discord.Embed(title="The Blackstar Corporation", description=f"I have failed to locate this department's application channel.")

        dropdown.callback = dropdown_callback
        self.add_item(dropdown)

class ApplicationClose(View):
    def __init__(self):
        super().__init__()

        dropdown = Select(
            placeholder="Select a department",
            min_values=1,
            max_values=1,
            options=[
                discord.SelectOption(label="Intelligence Agency"),
                discord.SelectOption(label="Internal Security Department"),
                discord.SelectOption(label="Rapid Response Team"),
                discord.SelectOption(label="Omega-1"),
                discord.SelectOption(label="Alpha-1"),
                discord.SelectOption(label="Resh-1"),
                discord.SelectOption(label="Moderation Team")
            ]
        )

        async def dropdown_callback(interaction: discord.Interaction):
            try:
                channel_id = application_channels[dropdown.values[0]]
                channel = await interaction.guild.fetch_channel(channel_id)

                overwrite = channel.overwrites_for(interaction.guild.default_role)
                overwrite.view_channel = False
                await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)   
                embed = discord.Embed(title="The Blackstar Corporation", description=f"`{dropdown.values[0]}` applications have been temporarily closed.", color=discord.Color.light_gray())
                embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1450302678524756040/3557930241bf8360a9535a5f27d42cf4.png?size=1024")
                await channel.send(embed=embed)
                await interaction.response.send_message("Applications have been closed!", ephemeral=True)
            except KeyError:
                discord.Embed(title="The Blackstar Corporation", description=f"I have failed to locate this department's application channel.")

        dropdown.callback = dropdown_callback
        self.add_item(dropdown)


