import discord
from discord.ext import commands
import pandas as pd
from utils.constants import profiles

class DataImport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="import_data")
    async def import_data(self, ctx: commands.Context):
        bypassed_users = [758170288566566952]

        for user in bypassed_users:
            if ctx.author.id != user:
                return
            
        gids = [0, 500760323, 1553834578, 1687070402, 1486703883, 1878972695, 1149971704, 920770931, 1563353687, 983100165, 408975112, 1709565496]
        for gid in gids:
            unit_db_link = f"https://docs.google.com/spreadsheets/d/1BLlkDxLW7GqPwVPmDuwpu-XBU98aY5_0ADX9QALXp4w/export?format=csv&gid={gid}"
            

            try:
                df = pd.read_csv(unit_db_link, header=2)
                print("Connected to CSV successfully.")
                
                codenames = df["Codename"].str.strip('"').tolist()
                discord_usernames = df["Discord Username"].tolist()
                roblox_usernames = df["Roblox Username"].tolist()
                current_points = df["Current Points"].tolist()
                total_points = df["Total Points"].tolist()
                join_dates = df["Join Date"].tolist()
                timezones = df["Timezone"].tolist()
                units = df["Unit"].tolist()
                rankings = df["Rank"].tolist()
                statuses = df["Status"].tolist()

                for codename, discord_username, roblox_username, current_point, total_point, join_date, timezone, unit, rank, status in zip(
                    codenames,
                    discord_usernames,
                    roblox_usernames,
                    current_points,
                    total_points,
                    join_dates,
                    timezones,
                    units,
                    rankings,
                    statuses
                ):
                    if discord_username == "N/A" or discord_username == "" or discord_username == "na":
                        print(f"Skipping entry with codename {codename} due to missing Discord username.")
                        continue
                    else:

                        for member in ctx.guild.members:
                            if member.name == discord_username:

                                profile = await profiles.find_one({'user_id': member.id, 'guild_id': ctx.guild.id})
                                if profile:
                                    print(f"Profile for {discord_username} already exists. Skipping...")
                                    break
                                else:

                                    profile = {
                                        'user_id': member.id,
                                        'guild_id': ctx.guild.id,
                                        'codename': codename,
                                        'roblox_name': roblox_username,
                                        'unit': {
                                            f"{unit}": {
                                                'rank': rank,
                                                'is_active': status,
                                                'current_points': float(current_point),
                                                'total_points': float(total_point)
                                            }
                                        },
                                        'private_unit': [],
                                        'status': 'Active',
                                        'join_date': join_date,
                                        'timezone': timezone,
                                    }

                                    print(profile)
                            else:
                                print(f"{discord_username} not found in guild!")
                
            except Exception as e:
                print(f"Error loading CSV from link: {e}")

async def setup(bot):
    await bot.add_cog(DataImport(bot))