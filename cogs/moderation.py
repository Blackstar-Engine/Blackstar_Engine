import discord
from discord.ext import commands
from utils.utils import fetch_id, fetch_profile, has_approval_perms

from utils.constants import jail_snapshots, profiles

class Moderation(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
    
    @commands.hybrid_command(name="jail", description="Sends a user to jail")
    async def jail(self, ctx: commands.Context, user: discord.Member):
        if not await has_approval_perms(ctx.author, 4):
            embed = discord.Embed(description=f"You do not have permission to use **jail** | `{user.id}`", color=discord.Color.yellow())
            await ctx.send(embed=embed, ephemeral=True)
            return
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)

        results = await fetch_id(ctx.guild.id, ["prisoner_role"])
        prisoner_id = results["prisoner_role"]
        profile = await profiles.find_one({"user_id": user.id})
        codename = profile.get("codename") if profile else None

        if not codename:
            codename = user.name


        snapshot = await jail_snapshots.find_one({"id": user.id})
        if snapshot:
            embed = discord.Embed(description=f"This user has already been jailed. | `{user.id}`", color=discord.Color.yellow())
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        try:
            await jail_snapshots.insert_one({
                "id": user.id,
                "nickname": user.nick,
                "roles": []
            })

            for role in user.roles:
                await jail_snapshots.update_one(
                    {"id": user.id},
                    {
                        "$set": {"nickname": user.nick},
                        "$addToSet": {"roles": role.id}
                    }
                )
                try:
                    await user.remove_roles(role)
                except:
                    pass
            
            prisoner_role = ctx.guild.get_role(prisoner_id)
            await user.add_roles(prisoner_role)
            await user.edit(nick=f"[JAILED] {codename}")
            embed = discord.Embed(description=f"{user.mention} has been **jailed**. | `{user.id}`", color=discord.Color.yellow())
            await ctx.send(embed=embed, ephemeral=True)
        except:
            embed = discord.Embed(description=f"I have failed to **jail** {user.mention}. (MongoDB) | `{user.id}`", color=discord.Color.yellow())
            await ctx.send(embed=embed, ephemeral=True)   
        
    @commands.hybrid_command(name="release", description="Release a user from jail")
    async def release(self, ctx: commands.Context, user: discord.Member):
        if not await has_approval_perms(ctx.author, 4):
            embed = discord.Embed(description=f"You do not have permission to use **release** | `{user.id}`", color=discord.Color.yellow())
            await ctx.send(embed=embed, ephemeral=True)
            return
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)

        results = await fetch_id(ctx.guild.id, ["prisoner_role"])
        prisoner_id = results["prisoner_role"]
        snapshot = await jail_snapshots.find_one({"id": user.id})
        if snapshot is None:
            embed = discord.Embed(description=f"{user.mention} is not currently **jailed.** | `{user.id}`", color=discord.Color.yellow())
            await ctx.send(embed=embed, ephemeral=True)
            return
        roles = snapshot.get("roles", [])
        nickname = snapshot.get("nickname")
        for roleid in roles:
            role = ctx.guild.get_role(roleid)
            try:
                await user.add_roles(role)
            except:
                print(roleid)
                pass
        await user.edit(nick=nickname)

        prisoner_role = ctx.guild.get_role(prisoner_id)
        await user.remove_roles(prisoner_role)

        await jail_snapshots.delete_one({"id": user.id})

        embed = discord.Embed(description=f"{user.mention} has been **released**. | `{user.id}`", color=discord.Color.yellow())
        await ctx.send(embed=embed, ephemeral=True)

        



async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot=bot))