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

        # 2. Optimization: Map all guild members once
        # This prevents looking them up thousands of times inside the loop
        member_map = {member.name: member for member in ctx.guild.members}
        
        # Also map nicknames just in case the sheet uses them
        for member in ctx.guild.members:
            if member.nick:
                member_map[member.nick] = member

        gids = [0, 500760323, 1553834578, 1687070402, 1486703883, 1878972695, 
                1149971704, 920770931, 1563353687, 983100165, 408975112, 1709565496]
        
        gs = GSheet()
        total_imported = 0

        for gid in gids:
            try:
                # 3. Connect and Fetch
                await gs.connect(gid)
                rows = await gs.fetch_all_data()

                if not rows or len(rows) < 3:
                    print(f"Skipping GID {gid}: Not enough data.")
                    continue

                # 4. Parse Headers (Row 3 / Index 2)
                header_row = rows[2] 
                # Creates a map like {'Discord Username': 4, 'Rank': 8}
                headers = {name.strip(): i for i, name in enumerate(header_row) if name}

                # Helper to get data safely
                def get_val(r, col_name):
                    idx = headers.get(col_name)
                    if idx is not None and idx < len(r):
                        return r[idx].strip()
                    return ""

                # 5. Process Rows (Start at Row 4 / Index 3)
                for i, row in enumerate(rows[3:], start=4):
                    discord_username = get_val(row, "Discord Username")

                    # Skip empty rows or "nan"
                    if not discord_username or discord_username.lower() == "nan":
                        continue

                    # 6. Find Discord Member
                    member = member_map.get(discord_username)

                    if member:
                        # Check if profile already exists in DB
                        existing_profile = await profiles.find_one({'user_id': member.id, 'guild_id': ctx.guild.id})
                        
                        if existing_profile:
                            # print(f"Skipping {discord_username}: Already exists.")
                            continue

                        # Extract Data
                        codename = get_val(row, "Codename").strip('"')
                        roblox_username = get_val(row, "Roblox Username")
                        current_points = get_val(row, "Current Points")
                        total_points = get_val(row, "Total Points")
                        join_date = get_val(row, "Join Date")
                        timezone = get_val(row, "Timezone")
                        unit = get_val(row, "Unit")
                        rank = get_val(row, "Rank")
                        status = get_val(row, "Status")

                        # Convert Points to Float
                        try:
                            cp_float = float(current_points) if current_points else 0.0
                            tp_float = float(total_points) if total_points else 0.0
                        except ValueError:
                            cp_float = 0.0
                            tp_float = 0.0

                        # 7. Construct Profile
                        profile = {
                            'user_id': member.id,
                            'guild_id': ctx.guild.id,
                            'codename': codename,
                            'roblox_name': roblox_username,
                            'unit': {
                                f"{unit}": {
                                    'rank': rank,
                                    'is_active': status,
                                    'current_points': cp_float,
                                    'total_points': tp_float
                                }
                            },
                            'private_unit': [],
                            'status': 'Active',
                            'join_date': join_date,
                            'timezone': timezone,
                        }

                        # 8. Insert into Database
                        await db.temp_profiles.insert_one(profile)
                        total_imported += 1
                        print(f"✅ Imported: {discord_username} ({codename})")
                    
                    else:
                        print(f"⚠️ Member not found in server: {discord_username}")

            except Exception as e:
                print(f"❌ Error processing GID {gid}: {e}")

        await ctx.send(f"Import complete! Added {total_imported} new profiles to the database.")

async def setup(bot):
    await bot.add_cog(DataImport(bot))