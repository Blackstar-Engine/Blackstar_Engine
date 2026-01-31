import discord
from discord.ext import commands
import pandas as pd
from utils.constants import profiles, db

class DataImport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="import_data")
    async def import_data(self, ctx: commands.Context):
        bypassed_users = [758170288566566952]

        if ctx.author.id not in bypassed_users:
            return

        # 🔥 FIX 1: build member lookup ONCE
        member_lookup = {}
        for member in ctx.guild.members:
            member_lookup[member.name.lower()] = member
            if member.nick:
                member_lookup[member.nick.lower()] = member

        gids = [0, 500760323, 1553834578, 1687070402, 1486703883, 1878972695,
                1149971704, 920770931, 1563353687, 983100165, 408975112, 1709565496]

        for gid in gids:
            unit_db_link = (
                "https://docs.google.com/spreadsheets/d/"
                "1BLlkDxLW7GqPwVPmDuwpu-XBU98aY5_0ADX9QALXp4w/"
                f"export?format=csv&gid={gid}"
            )

            try:
                df = pd.read_csv(unit_db_link, header=2)
                df.columns = df.columns.str.strip()
                print(f"Connected to CSV successfully (gid={gid}).")

                for row in df.itertuples(index=False):
                    discord_username = str(row._asdict().get("Discord Username", "")).strip()

                    if not discord_username or discord_username.lower() == "nan":
                        continue

                    member = member_lookup.get(discord_username.lower())
                    if not member:
                        continue

                    unit_name = row.Unit
                    unit_data = {
                        'rank': row.Rank,
                        'is_active': True,
                        'current_points': float(row._asdict().get("Current Points", 0) or 0),
                        'total_points': float(row._asdict().get("Total Points", 0) or 0)
                    }

                    profile = await profiles.find_one({
                        'user_id': member.id,
                        'guild_id': ctx.guild.id
                    })

                    # 🆕 CREATE PROFILE
                    if not profile:
                        new_profile = {
                            'user_id': member.id,
                            'guild_id': ctx.guild.id,
                            'codename': str(row.Codename).strip('"'),
                            'roblox_name': row._asdict().get("Roblox Username"),
                            'unit': {
                                unit_name: unit_data
                            },
                            'private_unit': [],
                            'status': row.Status,
                            'join_date': row._asdict().get("Join Date"),
                            'timezone': row.Timezone,
                        }

                        await db.temp_profiles.insert_one(new_profile)
                        print(f"Created profile for {discord_username}")
                        continue

                    # 🔁 PROFILE EXISTS → CHECK UNIT
                    if unit_name in profile.get("unit", {}):
                        continue

                    # ➕ ADD NEW UNIT
                    await profiles.update_one(
                        {
                            'user_id': member.id,
                            'guild_id': ctx.guild.id
                        },
                        {
                            '$set': {
                                f'unit.{unit_name}': unit_data
                            }
                        }
                    )

                    print(f"Added {unit_name} to {discord_username}")

            except Exception as e:
                print(f"Error loading CSV from link (gid={gid}): {e}")

async def setup(bot):
    await bot.add_cog(DataImport(bot))