import discord
from discord.ext import commands
from ui.CustomSelects import ChannelRow
from discord import ui
from ui.AcceptDenyButtons import AcceptDenyButtons
from ui.CustomButton import CustomButton

class SetupCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

        setup_doc = {
            "guild_id": 0,
            "logging_channels": {
                "point_addition_log": 0,
                "point_deduction_log": 0,
                "department_log": 0,
                "mod_command_log": 0,
            },
            "modules": {
                "loa": {
                    "is_active": False,
                    "role": 0,
                    "channel": 0
                },
                "roa": {
                    "is_active": False,
                    "role": 0,
                    "channel": 0
                },
                "enlistment": {
                    "is_active": False,
                    "channel": 0
                },
                "prisoner_system": {
                    "is_active": False,
                    "role": 0
                },
                "birthday_system": {
                    "is_active": False,
                    "role": 0,
                    "channel": 0
                },
                "application_system": {
                    "is_active": False,
                    "channels": [0]
                },
                "session_system": {
                    "is_active": False,
                    "channels": [0]
                }
            }
        }

    @commands.hybrid_command(name="setup", description="Setup the bot in this server", with_app_command=True, extras={'category': 'Administration'})
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx: commands.Context):
        accept_deny_buttons = AcceptDenyButtons(self.bot, ctx.author, ask_reason=False)
        accept_deny_buttons.accept_button.label = "Confirm"
        accept_deny_buttons.deny_button.label = "Cancel"

        confirm_view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay("## Setup Process"),
            ui.TextDisplay("Would you like to setup/re-setup this server? This will wipe all module configuration."),
            accept_deny_buttons,
            accent_color=discord.Color.light_grey()
        )
        confirm_view.add_item(container)

        confirm_message = await ctx.send(view=confirm_view, allowed_mentions=discord.AllowedMentions.none())
        await confirm_view.wait()

        if accept_deny_buttons.is_accepted:

            submit_button = CustomButton(label="Next", style=discord.ButtonStyle.green, auto_defer=False)
            submit_button.disabled = True

            channel_rows = []

            async def update_submit_button(interaction: discord.Interaction):
                submit_button.disabled = not all(row.channels for row in channel_rows)
                await interaction.response.edit_message(view=log_view)

            point_add_row = ChannelRow(self.bot, placeholder="Point Addition Channel", on_select=update_submit_button)
            point_remove_row = ChannelRow(bot=self.bot, placeholder="Point Remove Channel", on_select=update_submit_button)
            department_row = ChannelRow(bot=self.bot, placeholder="Department Channel", on_select=update_submit_button)
            mod_command_row = ChannelRow(bot=self.bot, placeholder="Mod Command Channel", on_select=update_submit_button)
            channel_rows.extend((point_add_row, point_remove_row, department_row, mod_command_row))

            async def submit_button_callback(interaction: discord.Interaction):
                if not all(row.channels for row in channel_rows):
                    await interaction.response.send_message("Please select all logging channels first.", ephemeral=True)
                    return
                await interaction.response.edit_message(content="Logging channels configured.", view=None)
                log_view.stop()

            submit_button.callback = submit_button_callback
            submit_button_row = ui.ActionRow(submit_button)

            log_view = ui.LayoutView()
            log_container = ui.Container(
                ui.TextDisplay("## Logging Channels"),
                ui.TextDisplay("**Point Addition Logs:** Logs when points are added.\n"),
                point_add_row,
                ui.TextDisplay("**Point Reduction log:** Logs when points are reduced.\n"),
                point_remove_row,
                ui.TextDisplay("**Department Logs:** Logs when departments are changed.\n"),
                department_row,
                ui.TextDisplay("**Mod Command Logs:** Logs when mod commands are used."),
                mod_command_row,
                ui.Separator(),
                submit_button_row,
                accent_color=discord.Color.light_grey()
            )
            log_view.add_item(log_container)
            await confirm_message.edit(view=log_view, allowed_mentions=discord.AllowedMentions.none())
            await log_view.wait()
            print("exited")
        else:
            cancel_view = ui.LayoutView()
            cancel_container = ui.Container(
                ui.TextDisplay("## Setup Cancelled"),
                ui.TextDisplay(f"<@{accept_deny_buttons.kwargs.get("moderator_obj").id}> has cancelled setup!"),
                accent_color=discord.Color.red()
            )
            cancel_view.add_item(cancel_container)
            await confirm_message.edit(view=cancel_view, allowed_mentions=discord.AllowedMentions.none())

async def setup(bot: commands.Bot):
    await bot.add_cog(SetupCommand(bot))