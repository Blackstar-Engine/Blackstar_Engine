import discord
from discord.ext import commands
from utils.utils import fetch_id, fetch_profile, has_approval_perms

from utils.constants import jail_snapshots, profiles

class Moderation(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
    
    @commands.hybrid_command(name="jail", description="Sends a user to jail")
    async def jail(self, ctx: commands.Context, user: discord.Member, reason: str = "No reason provided"):
        await has_approval_perms(ctx.author, 4)

        await ctx.defer(ephemeral=True)

        results = await fetch_id(ctx.guild.id, ["prisoner_role"])
        prisoner_id = results["prisoner_role"]

        profile = await fetch_profile(ctx, send_message=False)
        codename = profile.get("codename", None)

        if not codename:
            codename = user.name

        snapshot = await jail_snapshots.find_one({"id": user.id})
        if snapshot:
            embed = discord.Embed(description=f"{user.mention} has already been jailed. | `{user.id}`", color=discord.Color.yellow())
            return await ctx.send(embed=embed, ephemeral=True)
        
        try:
            all_roles = [role.id for role in user.roles if not role.is_default()]
            jail_doc = {
                "id": user.id,
                "guild_id": ctx.guild.id,
                "reason": reason,
                "jailed_at": discord.utils.utcnow(),
                "jailed_by": ctx.author.id,
                "nickname": user.nick,
                "roles": all_roles
            }
            await jail_snapshots.insert_one(jail_doc)

            errored_roles = []
            for role in user.roles:
                if role.is_default():
                    continue

                try:
                    await user.remove_roles(role)
                except Exception:
                    errored_roles.append(role.name)
            
            prisoner_role = ctx.guild.get_role(prisoner_id)
            await user.add_roles(prisoner_role)
            try:
                await user.edit(nick=f"[JAILED] {codename}")
            except discord.Forbidden:
                pass

            embed = discord.Embed(description=f"{user.mention} has been **jailed** because **{reason}**. | `{user.id}`", color=discord.Color.yellow())
            if errored_roles:
                embed.add_field(name="I Couldn't Remove", value="\n".join(errored_roles), inline=False)

            await ctx.send(embed=embed, ephemeral=True)
        except Exception:
            embed = discord.Embed(description=f"I have failed to **jail** {user.mention}. | `{user.id}`", color=discord.Color.yellow())
            await ctx.send(embed=embed, ephemeral=True) 
            snapshot = await jail_snapshots.find_one({"id": user.id})
            if snapshot:
                await jail_snapshots.delete_one({"id": user.id})

        
    @commands.hybrid_command(name="release", description="Release a user from jail")
    async def release(self, ctx: commands.Context, user: discord.Member, reason: str = "No reason provided"):
        await has_approval_perms(ctx.author, 4)

        await ctx.defer(ephemeral=True)

        results = await fetch_id(ctx.guild.id, ["prisoner_role"])
        prisoner_id = results["prisoner_role"]

        snapshot = await jail_snapshots.find_one({"id": user.id})
        if snapshot is None:
            embed = discord.Embed(description=f"{user.mention} is not currently **jailed.** | `{user.id}`", color=discord.Color.yellow())
            return await ctx.send(embed=embed, ephemeral=True)
        
        roles = snapshot.get("roles", [])
        nickname = snapshot.get("nickname")

        errored_roles = []
        for role_id in roles:
            role = ctx.guild.get_role(role_id)
            if role.is_default():
                    continue
            try:
                await user.add_roles(role)
            except Exception:
                errored_roles.append(role.name)
        
        try:
            await user.edit(nick=nickname)
        except discord.Forbidden:
            pass

        prisoner_role = ctx.guild.get_role(prisoner_id)
        await user.remove_roles(prisoner_role)

        await jail_snapshots.delete_one({"id": user.id})

        embed = discord.Embed(description=f"{user.mention} has been **released** because **{reason}**. | `{user.id}`", color=discord.Color.yellow())
        if errored_roles:
            embed.add_field(name="I Couldn't Add", value="\n".join(errored_roles), inline=False)
        await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name="jailstatus", description="Check if a user is in jail or not")
    async def jailstatus(self, ctx: commands.Context, user: discord.Member):
        await has_approval_perms(ctx.author, 4)
        snapshot = await jail_snapshots.find_one({"id": user.id})
        if snapshot:
            embed = discord.Embed(description=f"{user.mention} is currently **jailed**. | `{user.id}`", color=discord.Color.yellow())
            embed.add_field(name="Reason", value=snapshot.get("reason", "No reason provided"), inline=False)
            embed.add_field(name="Jailed At", value=discord.utils.format_dt(snapshot.get("jailed_at"), style="F"), inline=False)
            jailed_by_id = snapshot.get("jailed_by")
            if jailed_by_id:
                jailed_by = ctx.guild.get_member(jailed_by_id)
                if jailed_by:
                    embed.add_field(name="Jailed By", value=f"{jailed_by.mention} | `{jailed_by_id}`", inline=False)
                else:
                    embed.add_field(name="Jailed By", value=f"User Left | `{jailed_by_id}`", inline=False)
            else:
                embed.add_field(name="Jailed By", value="Unknown", inline=False)
        else:
            embed = discord.Embed(description=f"{user.mention} is not currently **jailed**. | `{user.id}`", color=discord.Color.yellow())
        await ctx.send(embed=embed, ephemeral=True)
    
    @commands.hybrid_command(name="viewjailed", description="View all currently jailed users")
    async def viewjailed(self, ctx: commands.Context):
        await has_approval_perms(ctx.author, 4)

        await ctx.defer(ephemeral=True)

        snapshots = await jail_snapshots.find({}).to_list(length=None)
        if not snapshots:
            embed = discord.Embed(description="There are no users currently in jail.", color=discord.Color.yellow())
            return await ctx.send(embed=embed, ephemeral=True)

        description = ""
        embed = discord.Embed(title="Currently Jailed Users", color=discord.Color.yellow())
        for snapshot in snapshots:
            user = ctx.guild.get_member(snapshot["id"])
            if not user:
                continue

            description += f"{user.mention} | {snapshot.get("reason", "No reason provided")}\n"
            
        embed.description = description
        await ctx.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot=bot))