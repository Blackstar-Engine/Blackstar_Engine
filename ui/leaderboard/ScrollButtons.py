import discord
from discord.ui import View, Button

class LeaderboardView(View):
    def __init__(self, pages):
        super().__init__(timeout=120)
        self.pages = pages
        self.current_page = 0
        self.max_page = len(pages)
        self.update_buttons()
    @discord.ui.button(label="←", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    @discord.ui.button(label="→", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page < self.max_page - 1:
            self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    def update_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.max_page - 1

    def get_embed(self):
        page = self.pages[self.current_page]
        per_page = 10
        lines = [
            f"**[#{rank}]** <@{user_id}> - {total_points:.1f} points"
            for rank, (user_id, total_points) in enumerate(
                page, start=self.current_page * per_page + 1
            )
        ]

        embed = discord.Embed(title=f"Point Leaderboard (Page {self.current_page + 1}/{self.max_page})", description="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n" + "\n".join(lines), color=discord.Color.light_grey())
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1450302678524756040/3557930241bf8360a9535a5f27d42cf4.png?size=1024")
        return embed