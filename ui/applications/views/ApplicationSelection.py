import discord
from discord.ui import View, Select
from utils.constants import application_channels
from ui.applications.modals.app_closure import ApplicationCloseModal

class ApplicationOpen(View):
    def __init__(self, options):
        super().__init__()

        dropdown = Select(
            placeholder="Select a department",
            min_values=1,
            max_values=1,
            options=options
        )

        async def dropdown_callback(interaction: discord.Interaction):
            try:
                modal = ApplicationCloseModal()
                await interaction.response.send_modal(modal)
                await modal.wait()

                value = int(dropdown.values[0])
                channel = await interaction.guild.fetch_channel(value)

                selected_option = next(
                    option for option in dropdown.options
                    if int(option.value) == value
                )

                overwrite = channel.overwrites_for(interaction.guild.default_role)
                overwrite.view_channel = True
                overwrite.send_messages = False
                await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)   
                embed = discord.Embed(title="The Blackstar Corporation", description=f"`{selected_option.label}` applications have been temporarily opened.\n\nApplication will be closed at {discord.utils.format_dt(modal.total_days)}.", color=discord.Color.light_grey())
                embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1450302678524756040/3557930241bf8360a9535a5f27d42cf4.png?size=1024")
                await channel.send(embed=embed)
                await interaction.followup.send("Applications have been opened!", ephemeral=True)
            except KeyError:
                discord.Embed(title="The Blackstar Corporation", description="I have failed to locate this department's application channel.")

        dropdown.callback = dropdown_callback
        self.add_item(dropdown)

class ApplicationClose(View):
    def __init__(self, options):
        super().__init__()

        dropdown = Select(
            placeholder="Select a department",
            min_values=1,
            max_values=1,
            options=options
        )

        async def dropdown_callback(interaction: discord.Interaction):
            try:
                value = int(dropdown.values[0])
                channel = await interaction.guild.fetch_channel(value)

                selected_option = next(
                    option for option in dropdown.options
                    if int(option.value) == value
                )

                overwrite = channel.overwrites_for(interaction.guild.default_role)
                overwrite.view_channel = False
                overwrite.send_messages = False
                await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)   
                embed = discord.Embed(title="The Blackstar Corporation", description=f"`{selected_option.label}` applications have been temporarily closed.", color=discord.Color.light_gray())
                embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1450302678524756040/3557930241bf8360a9535a5f27d42cf4.png?size=1024")
                await channel.send(embed=embed)
                await interaction.response.send_message("Applications have been closed!", ephemeral=True)
            except KeyError:
                discord.Embed(title="The Blackstar Corporation", description="I have failed to locate this department's application channel.")

        dropdown.callback = dropdown_callback
        self.add_item(dropdown)


