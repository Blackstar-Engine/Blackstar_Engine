import discord
from discord.ext import commands
from discord import ui
import re
from utils.constants import LOARegFormat
from datetime import datetime, timedelta

class ApplicationCloseModal(ui.Modal):
    def __init__(self):
        super().__init__(title="App Closure")
        self.total_days = None

        self.time = discord.ui.TextInput(
            label="When will the application be closed?",
            placeholder="1y1m1w1d1h",
            required=True,
            row=1,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.time)

    async def on_submit(self, interaction: discord.Interaction):
        def extract_time_values(time_string):
            # Create a reg match
            search = re.match(LOARegFormat,time_string)

            # Check to see if it returns none or improper groups
            if search is None or search.group() == "":
                return 0, 0, 0, 0, 0
            
            # Return full list of items
            return map(int, search.groups(default="0"))
        
        time = self.time.value

        if not re.match(LOARegFormat, time):
            embed = discord.Embed(title="Invalid Time Format",
                                  description="Please use the correct time format: \n**<number>y<number>m<number>w<number>d<number>h**\n\n**__Examples:__**\n> `1y2m3w4d5h` = 1 year, 2 months, 3 weeks, 4 days, and 5 hours\n> `2w4d` = 2 weeks and 4 days\n> `5h` = 5 hours",
                                  color=discord.Color.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Break time into y, m, w, d, h and find total days from that
        years, months, weeks, days, hours = extract_time_values(time)
        days = years * 365 + months * 30 + weeks * 7 + days
        start_date = datetime.now()
        self.total_days = start_date + timedelta(days=days, hours=hours)


        await interaction.response.defer(ephemeral=True)
        self.stop()


        