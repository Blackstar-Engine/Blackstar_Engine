import discord
from discord.ext import commands
from discord.ui import View, Select
from ui.department_request.view.AcceptDenyButtons import AcceptDenyButtons
from utils.utils import interaction_check, fetch_department

class DepartmentsRequestView(View):
    def __init__(self, bot, user, options, profile):
        super().__init__()
        self.bot = bot
        self.user = user
        self.options = options
        self.profile = profile

        self.department_request_select.max_values = len(options)
        self.department_request_select.options = options


    @discord.ui.select(placeholder="Select the departments", min_values=1, options=[])
    async def department_request_select(self, interaction: discord.Interaction, select: Select):
        await interaction_check(self.user, interaction.user)
        await interaction.response.defer(ephemeral=True)

        values = select.values
        cannot_send_list = []

        for value in values:
            print("value: ", value)
            if value in self.profile.get("unit"):
                cannot_send_list.append(value)
            else:
                department = await fetch_department(interaction, value)

                channel = await interaction.guild.fetch_channel(department.get("promo_request_channel"))

                embed = discord.Embed(title="Enlistment Request",
                                    description=f"**Codename: **{self.profile.get("codename")}\n**Roblox Name: ** {self.profile.get("roblox_name")}\n**Status: ** {self.profile.get("status")}\n**Join Date: ** {self.profile.get("join_date")}\n**Time Zone: **{self.profile.get("timezone")}",
                                    color = discord.Color.yellow())
                
                view = AcceptDenyButtons(self.bot, self.user, embed, self.profile, department)
                
                try:
                    await channel.send(embed=embed, view=view)
                except discord.Forbidden:
                    pass
        

        user_embed = discord.Embed(title="Enlistments Sent!", description="All enlistments have been sent for review!", color=discord.Color.green())
        if len(cannot_send_list) > 0:
            user_embed.add_field(name="Unable to Sent to:", value=", ".join(cannot_send_list))

        await interaction.followup.send(embed=user_embed)

        self.stop()
