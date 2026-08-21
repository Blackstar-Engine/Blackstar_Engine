import discord
from discord.ext import commands
from ui.CustomModal import CustomModal
from discord import ui

class HelpCommandOptions(discord.ui.LayoutView):
    def __init__(self, bot, commands_list, user):
        super().__init__(timeout=600)

        self.bot: commands.Bot = bot
        self.commands_list = commands_list
        self.user = user

        # SELECT OPTIONS
        options_list = [
            discord.SelectOption(
                label=category,
                value=category
            )
            for category in commands_list
        ]

        # SELECT MENU
        self.help_select = discord.ui.Select(
            placeholder="Select an option",
            min_values=1,
            max_values=1,
            options=options_list
        )

        self.help_select.callback = self.help_options_select

        # SEARCH BUTTON
        self.search_button_component = discord.ui.Button(
            emoji="<:search:1275199409067393024>",
            style=discord.ButtonStyle.green
        )

        self.search_button_component.callback = self.search_button

        self.select_row = ui.ActionRow(self.help_select)
        self.button_row = ui.ActionRow(self.search_button_component)

        container = ui.Container(
            ui.TextDisplay("## Vaptic"),
            ui.TextDisplay("Vaptic is a multi-purpose roleplay bot target to help make manual processes easy and automated."),
            self.select_row,
            ui.Separator(),
            self.button_row,
            accent_color=discord.Color.light_grey()
        )

        self.add_item(container)

    async def help_options_select(
        self,
        interaction: discord.Interaction
    ):

        selected = self.help_select.values[0]

        view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay(f"## {selected}"),
            ui.TextDisplay(self.commands_list[selected]),
            self.select_row,
            ui.Separator(),
            self.button_row,
            accent_color=discord.Color.light_grey()
        )
        view.add_item(container)

        await interaction.response.edit_message(
            view=view
        )
    
    async def _handle_group_command(self, interaction: discord.Interaction, command_name, command_data):
        group_name = command_name.lower()

        all_commands = [
            cmd for cmd in self.bot.walk_commands()
            if (
                cmd.full_parent_name
                and cmd.full_parent_name.lower() == group_name
            )
        ]
        view = discord.ui.LayoutView()
        container = discord.ui.Container(
            ui.TextDisplay(f"## Search Results: {command_name}"),
            accent_color=discord.Color.light_grey()
        )

        if all_commands:

            for cmd in all_commands:

                container.add_item(ui.TextDisplay(f"**→** </{cmd.qualified_name}:{command_data['id']}>\n"
                    f"> {cmd.description}\n\n"))

        container.add_item(self.select_row)
        container.add_item(ui.Separator())
        container.add_item(self.button_row)

        view.add_item(container)
        return await interaction.edit_original_response(
            view=view
        )

    async def search_button(self, interaction: discord.Interaction):
        modal = CustomModal(
            "Command Search",
            [
                (
                    "command_name",
                    discord.ui.TextInput(
                        label="Command Name",
                        placeholder="config",
                        required=True,
                        max_length=25,
                    )
                )
            ]
        )

        await interaction.response.send_modal(modal)
        await modal.wait()

        fetched_commands = await self.bot.tree.fetch_commands()

        command_ids = {}

        for cmd in fetched_commands:
            if cmd.id:
                command_ids[str(cmd)] = {
                    "id": cmd.id,
                    "description": cmd.description
                }

            if hasattr(cmd, "options"):

                for sub_cmd in cmd.options:

                    full_name = f"{cmd.name} {sub_cmd.name}"

                    command_ids[full_name] = {
                        "id": cmd.id,
                        "description": str(sub_cmd.description)
                    }

        command_name = modal.command_name.value
        command_data = command_ids.get(command_name)

        if not command_data:
            return await interaction.followup.send(
            "Command not found.",
            ephemeral=True
        )

        command = self.bot.get_command(command_name)
        extras = command.extras if command else {}
        category = extras.get("category")

        # NORMAL COMMAND
        if category and category not in ("Staff", "Group"):
            view = discord.ui.LayoutView()
            container = discord.ui.Container(
                ui.TextDisplay(f"## Search Results: {command_name}"),
                ui.TextDisplay(f"**→** </{command_name}:{command_data['id']}>\n> {command_data['description']}"),
                self.select_row,
                ui.Separator(),
                self.button_row,
                accent_color=discord.Color.light_grey()
            )

            view.add_item(container)

            return await interaction.edit_original_response(
                view=view
            )

        # GROUP COMMANDS
        if category == "Group":
            await self._handle_group_command(interaction, command_name, command_data)

        

class HelpCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        description="Display all of Vaptic's commands.",
        with_app_command=True,
        extras={"category": "Other"}
    )
    async def help(self, ctx: commands.Context):
        await ctx.defer()
        commands_list = {}

        fetched_commands = await self.bot.tree.fetch_commands()

        command_ids = {}

        def add_command_ids(command, parent_name="", root_id=None):
            # Only top-level AppCommands have an ID
            if root_id is None:
                root_id = command.id

            command_name = (
                f"{parent_name} {command.name}"
                if parent_name
                else command.name
            )

            command_ids[command_name] = root_id

            for option in getattr(command, "options", []):
                if hasattr(option, "name"):
                    add_command_ids(
                        option,
                        command_name,
                        root_id
                    )


        for command in fetched_commands:
            if hasattr(command, "id"):
                add_command_ids(command)

        # YOUR EXISTING HYBRID/PREFIX COMMANDS
        for command in self.bot.walk_commands():
            category = command.extras.get('category')
            if category and category not in ('Group', 'Staff'):
                commands_list.setdefault(category, "")
                commands_list[category] += f"**→** </{command}:{command_ids.get(str(command))}> \n> {command.description}\n\n"

        # -------------------------------------------------
        # ADD SLASH COMMANDS
        # -------------------------------------------------

        for command in self.bot.tree.walk_commands():

            # Skip groups themselves
            if isinstance(command, discord.app_commands.Group):
                continue

            category = command.extras.get("category")

            # No category = don't add it
            if not category or category in ("Group", "Staff"):
                continue

            command_name = command.qualified_name

            # Don't add hybrid commands a second time
            if self.bot.get_command(command_name):
                continue

            # Find the Discord ID using the same command_ids
            command_id = command_ids.get(command_name)

            if command_id is None:
                # For a subcommand, the ID is the parent command's ID
                command_id = command_ids.get(
                    f"{command.parent.name} {command.name}"
                    if command.parent
                    else command.name
                )

            if command_id is None:
                continue

            commands_list.setdefault(category, "")

            commands_list[category] += (
                f"**→** </{command_name}:{command_id}> \n"
                f"> {command.description}\n\n"
            )

        help_view = HelpCommandOptions(
            self.bot,
            commands_list,
            ctx.author.id
        )

        await ctx.send(view=help_view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))