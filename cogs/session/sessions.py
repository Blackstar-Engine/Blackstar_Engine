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
from utils.constants import sessions

class SessionMainMenuView(discord.ui.View):
    def __init__(self, bot, user: discord.User):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user
    
    @discord.ui.button(label="View Sessions", style=discord.ButtonStyle.green, custom_id="view_sessions")
    async def view_sessions(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = await sessions.find({"guild_id": interaction.guild.id, "attendees": interaction.user.id}).to_list(length=None)
        print(items)
        view = PaginatorView(self.bot, self.user, items)

        await interaction.response.send_message(view = view)
    
    @discord.ui.button(label="Admin View", style=discord.ButtonStyle.blurple, custom_id="edit_sessions")
    async def edit_sessions(self, interaction: discord.Interaction, button: discord.ui.Button):   
        await interaction.response.send_message("Admin view...")

class Sessions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="session", description="Manage sessions", with_app_command=True)
    async def session(self, ctx: commands.Context):
        view = SessionMainMenuView(self.bot, ctx.author)

        embed=discord.Embed(
            title="Session Menu",
            description="**View Sessions:** View your sessions you participated in\n\n**Admin Menu:** View, edit, create, and delete all sessions in this server",
            color=discord.Color.light_gray()
        )

        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Sessions(bot))