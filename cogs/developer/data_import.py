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

        # 2. Cache guild members
        guild = self.bot.get_guild(1411941814923169826)
        member_map = {member.name: member for member in guild.members}

        gids = [
            0, 500760323, 1553834578, 1687070402, 1486703883,
            1878972695, 1149971704, 920770931, 1563353687,
            983100165, 408975112, 1709565496
        ]

        gs = GSheet()
        total_imported = 0

        MTF_SUBUNITS = {
            "Epsilon-11",
            "Omega-1",
            "Nu-7",
            "Alpha-1",
            "Resh-1",
            "Beta-7"
        }

        for gid in gids:
            try:
                # 3. Fetch data
                await gs.connect(gid)
                rows = await gs.fetch_all_data()

                if not rows or len(rows) < 3:
                    continue

                # 4. Headers
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

                # 5. Process rows
                for row in rows[3:]:
                    discord_username = get_val(row, "Discord Username")

                    if not discord_username or discord_username.lower() == "nan":
                        continue

                    member = member_map.get(discord_username)
                    if not member:
                        print(f"⚠️ Member not found: {discord_username}")
                        continue

                    if await profiles.find_one({
                        'user_id': member.id,
                        'guild_id': ctx.guild.id
                    }):
                        continue

                    codename = get_val(row, "Codename").strip('"')
                    roblox_username = get_val(row, "Roblox Username")
                    current_points = get_val(row, "Current Points")
                    total_points = get_val(row, "Total Points")
                    join_date = get_val(row, "Join Date")
                    timezone = get_val(row, "Timezone")
                    raw_unit = get_val(row, "Unit")
                    rank = get_val(row, "Rank")
                    status = get_val(row, "Status")  # overall profile status

                    try:
                        cp_float = float(current_points) if current_points else 0.0
                        tp_float = float(total_points) if total_points else 0.0
                    except ValueError:
                        cp_float = 0.0
                        tp_float = 0.0

                    # ⬇️ Subunit detection (MTF only)
                    unit = raw_unit
                    subunits = []

                    if raw_unit in MTF_SUBUNITS:
                        unit = "MTF"
                        subunits = [raw_unit]

                    profile = await db.profiles.find_one({
                        'user_id': member.id,
                        'guild_id': ctx.guild.id
                    })

                    if profile:
                        await db.profiles.update_one(
                            {
                                'user_id': member.id,
                                'guild_id': ctx.guild.id
                            },
                            {
                                '$set': {
                                    f'unit.{unit}': {
                                        'rank': rank,
                                        'is_active': True,
                                        'current_points': cp_float,
                                        'total_points': tp_float,
                                        'subunits': subunits
                                    },
                                    'status': status
                                }
                            }
                        )
                        print(f"✅ Updated: {discord_username}")

                    else:
                        profile = {
                            'user_id': member.id,
                            'guild_id': ctx.guild.id,
                            'codename': codename,
                            'roblox_name': roblox_username,
                            'unit': {
                                unit: {
                                    'rank': rank,
                                    'is_active': True,
                                    'current_points': cp_float,
                                    'total_points': tp_float,
                                    'subunits': subunits
                                }
                            },
                            'private_unit': [],
                            'status': status,
                            'join_date': join_date,
                            'timezone': timezone,
                        }

                        await db.temp_profiles.insert_one(profile)
                        total_imported += 1
                        print(f"✅ Imported: {discord_username}")

            except Exception as e:
                print(f"❌ Error processing GID {gid}: {e}")

        await ctx.send(
            f"Import complete! Added {total_imported} new profiles."
        )

async def setup(bot):
    await bot.add_cog(DataImport(bot))
