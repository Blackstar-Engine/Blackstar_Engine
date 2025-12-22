'''
training = {
    'name': 'session',
    'date': str(datetime.utcnow()),
    'duration': 0,
    'host_id': host.id,
    'co_host_id': co_host.id,
    'supervisor_id': supervisor.id,
    'guild_id': guild.id,
    'attendees': [],
    'mvp': None,
    'note': ''

}
'''

import discord
from discord.ext import commands
from utils.ui.paginator import PaginatorView

class TrainingMainMenuView(discord.ui.View):
    def __init__(self, bot, user: discord.User):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user
    
    @discord.ui.button(label="View Trainings", style=discord.ButtonStyle.green, custom_id="view_trainings")
    async def view_trainings(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PaginatorView(self.bot, self.user)

        await interaction.response.send_message(view = view)
    
    @discord.ui.button(label="Admin View", style=discord.ButtonStyle.blurple, custom_id="edit_trainings")
    async def edit_trainings(self, interaction: discord.Interaction, button: discord.ui.Button):   
        await interaction.response.send_message("Admin view...")

class Trainings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="training", description="Manage training sessions", with_app_command=True)
    async def training(self, ctx: commands.Context):
        view = TrainingMainMenuView(self.bot, ctx.author)

        embed=discord.Embed(
            title="Training Menu",
            description="**View Trainings:** View your trainings you participated in\n\n**Admin Menu:** View, edit, create, and delete all trainings in this server",
            color=discord.Color.light_gray()
        )

        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Trainings(bot))