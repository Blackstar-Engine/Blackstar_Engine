import discord
from discord import ui
from ui.AcceptDenyButtons import AcceptDenyButtons

class RequestAcceptDenyButtons(ui.LayoutView):
    def __init__(self, bot, user: discord.Member, reason: str, start_date, end_date, time):
        super().__init__(timeout=None)
        self.bot = bot
        self.user = user
        self.time = time
        self.reason = reason
        self.start_date = start_date
        self.end_date = end_date

        self.action_row = AcceptDenyButtons(bot, user, 3)
        container = ui.Container(
            ui.TextDisplay("## LOA Request"),
            ui.TextDisplay(f"**Member:** {user.mention}\n"
                           f"**Start:** {discord.utils.format_dt(start_date)}\n"
                           f"**End:** {discord.utils.format_dt(end_date)}\n"
                           f"**Reason:** ``{reason}``\n"
                           f"**Time:** ``{time}``"),
            ui.Separator(),
            self.action_row,
            accent_color=discord.Color.yellow()
        )
        self.add_item(container)