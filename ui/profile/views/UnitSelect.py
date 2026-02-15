import discord

class UnitSelectView(discord.ui.View):
    def __init__(self, bot, options, profile):
        super().__init__(timeout=300)
        self.bot = bot
        self.profile = profile

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

        select.values.clear()

        await interaction.edit_original_response(view=self)

        if value == "no_units":
            return
        
        department = self.profile["unit"][value]

        embed = discord.Embed(
            title="Unit Information",
            description=f"**Unit Name: ** {value}\n**Rank: ** {department.get('rank')}\n**Current Points: ** {department.get('current_points')}\n**Total Points: ** {department.get('total_points')}\n**Subunits: ** {', '.join(department.get('subunits', [])) if department.get('subunits') else 'None'}",
            color=discord.Color.light_grey()
        )

        await interaction.followup.send(embed=embed, ephemeral=True)