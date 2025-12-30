import discord
from discord.ext import commands
class RoleSelect(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.select(
        placeholder="Select a Role",
        custom_id="blackstar_main_reactions",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Annoucements Ping", value=1450297860846387312),
            discord.SelectOption(label="Poll Ping", value=1450297861836247050),
            discord.SelectOption(label="MISC Ping", value=1450297863145001030),
            discord.SelectOption(label="Game Night Ping", value=1450297865569304596),
            discord.SelectOption(label="Question Ping", value=1450297866991042701),
            discord.SelectOption(label="Vote Ping", value=1450297868459049131),
            discord.SelectOption(label="Chat Revive Ping", value=1450297899811475558),
        ]
    )
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

class ReactionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.command(name="send-reactions", description="This will send an embed with all reaction roles for the server.")
    async def send_reaction_roles(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Blackstar Role Selection",
            description="The following are roles you can recieve notifications for: \n\n"
                        "> 📢 | **Annoucements Ping: ** Main Annoucements\n"
                        "> **Poll Ping: ** Polls\n"
                        "> **MISC Ping: ** Miscellaneous\n"
                        "> **Game Night Ping: ** Game Nights\n"
                        "> **Question Ping: ** Question of the Day\n"
                        "> **Vote Ping: ** Votes\n"
                        "> **Chat Revive Ping: ** Chat Revival\n\n"
                        "*Select a role below to add or remove the role.*",
            color=discord.Color.light_grey()
        )

        view = RoleSelect(self.bot)

        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot))
    bot.add_view(RoleSelect(bot=bot))