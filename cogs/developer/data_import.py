import discord
from discord.ext import commands
from utils.constants import profiles, db
from utils.google import GSheet 

class DataImport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="import_data")
    async def import_data(self, ctx: commands.Context):
        # 1. Permission Check
        bypassed_users = [758170288566566952, 934537337113804891]
        if ctx.author.id not in bypassed_users:
            return

        await ctx.send("Starting database import... ⏳")

        # 2. Cache guild members (username-based since sheet has no IDs)
        guild = self.bot.get_guild(1411941814923169826)
        member_map = {member.name: member for member in guild.members}

        gids = [
            0, # SD
            500760323, # E-11
            1553834578, # NU-7
            1486703883, # B-7
            1687070402, # A-1
            1878972695, # RRT
            1149971704, # SCD
            920770931, # MD
            1563353687, # IA
            983100165, # ISD
            408975112, # CI
            1709565496, # CD
        ]

        gs = GSheet()
        total_imported = 0

        for gid in gids:
            try:
                await gs.connect(gid)
                rows = await gs.fetch_all_data()

                if not rows or len(rows) < 3:
                    continue

                header_row = rows[2]
                headers = {
                    name.strip(): i
                    for i, name in enumerate(header_row)
                    if name
                }

                def get_val(r, col):
                    idx = headers.get(col)
                    if idx is not None and idx < len(r):
                        return r[idx].strip()
                    return ""

                for row in rows[3:]:
                    discord_username = get_val(row, "Discord Username")

                    if not discord_username or discord_username.lower() == "nan":
                        continue

                    member = member_map.get(discord_username)
                    if not member:
                        print(f"⚠️ Member not found: {discord_username}")
                        continue

                    codename = get_val(row, "Codename").strip('"')
                    roblox_username = get_val(row, "Roblox Username")
                    current_points = get_val(row, "Current Points")
                    total_points = get_val(row, "Total Points")
                    join_date = get_val(row, "Join Date")
                    timezone = get_val(row, "Timezone")
                    raw_unit = get_val(row, "Unit")
                    rank = get_val(row, "Rank")
                    status = get_val(row, "Status")

                    try:
                        cp_float = float(current_points) if current_points else 0.0
                        tp_float = float(total_points) if total_points else 0.0
                    except ValueError:
                        cp_float = 0.0
                        tp_float = 0.0

                    # Department mapping
                    unit = raw_unit

                    if gid == 500760323:
                        unit = "MTF:E-11"
                    elif gid == 1553834578:
                        unit = "MTF:NU-7"
                    elif gid == 1486703883:
                        unit = "MTF:B-7"
                    elif gid == 1687070402:
                        unit = "MTF:A-1"

                    # 🔥 SINGLE UPSERT = create or merge department
                    result = await db.temp_profiles.update_one(
                        {
                            'user_id': member.id,
                            'guild_id': ctx.guild.id
                        },
                        {
                            '$setOnInsert': {
                                'user_id': member.id,
                                'guild_id': ctx.guild.id,
                                'codename': codename,
                                'roblox_name': roblox_username,
                                'private_unit': [],
                                'status': status,
                                'join_date': join_date,
                                'timezone': timezone,
                            },
                            '$set': {
                                f'unit.{unit}': {
                                    'rank': rank,
                                    'is_active': True,
                                    'current_points': cp_float,
                                    'total_points': tp_float,
                                }
                            }
                        },
                        upsert=True
                    )

                    if result.upserted_id:
                        total_imported += 1
                        print(f"✅ Imported: {discord_username}")
                    else:
                        print(f"✅ Updated {unit}: {discord_username}")

            except Exception as e:
                print(f"❌ Error processing GID {gid}: {e}")

        await ctx.send(
            f"Import complete! Added {total_imported} new profiles."
        )

async def setup(bot):
    await bot.add_cog(DataImport(bot))
