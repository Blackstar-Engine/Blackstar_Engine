import discord
from discord import ui
from ui.AcceptDenyButtons import AcceptDenyButtons

class RequestAcceptDenyButtons(ui.LayoutView):
    def __init__(self, bot, user, reason, start_date, end_date, time):
        super().__init__(timeout=None)
        self.bot = bot
        self.user: discord.User = user
        self.time = time
        self.reason = reason
        self.start_date = start_date
        self.end_date = end_date

        self.action_row = AcceptDenyButtons(bot, user, 3)
        container = ui.Container(
            ui.TextDisplay("## Leave Of Absence Request"),
            ui.TextDisplay(f"**Member:** {user.mention}\n**Start:** {discord.utils.format_dt(start_date)}\n**End:** {discord.utils.format_dt(end_date)}\n**Reason:** ``{reason}``\n**Time:** ``{time}``"),
            ui.Separator(),
            self.action_row,
            accent_color=discord.Color.yellow()
        )
        self.add_item(container)