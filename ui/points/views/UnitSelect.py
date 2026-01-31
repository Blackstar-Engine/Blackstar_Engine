import discord

class UnitSelectView(discord.ui.View):
    def __init__(self, bot, options, profile):
        super().__init__(timeout=300)
        self.bot = bot
        self.profile = profile

        self.dept = None

        self.dept_role_select.options = options
    
    @discord.ui.select(
        placeholder="Select a Role",
        min_values=1,
        max_values=1,
        options=[]
    )
    async def dept_role_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        value = select.values[0]

        if value == "no_units":
            self.dept = "no_unit"
        else:
            self.dept = value

        self.stop()