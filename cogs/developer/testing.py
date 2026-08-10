import discord
from discord.ext import commands
from utils.utils import fetch_id
from datetime import datetime
from utils.utils import format_permission_node, format_id, format_permission_rule, format_permission_tier
from utils.constants import economy_profiles, permission_tiers, permission_rules, ids
class DevTestingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command(name="testing", guild_only=True, guild_ids=[1450297281088720928])
    @commands.is_owner()
    async def testing(self, ctx: commands.Context):
        # input all ids
        all_ids = {
            "1": format_id(ctx.guild.id, "loa", {"channel": 1412244838660968590, "role": 1418067647177691156}),
            "2": format_id(ctx.guild.id, "promotion_channel", 1412244417380618320),
            "3": format_id(ctx.guild.id, "enlistment_channel", 1433946174791876740),
            "4": format_id(ctx.guild.id, "sessions_channels", [1434351873518993509, 1452343119327662242, 1412241044392640654, 1412242444271095929, 1479239105119260682, 1479239661158269099, 1479239280646815918, 1479239218952798330, 1435445029702336533, 1447292841842708691, 1428172682075045898, 1453068290124546088]),
            "5": format_id(ctx.guild.id, "logging_channels", {"point_deduction_log": 1481380606125543567, "point_addition_log": 1481380665961480202, "department_log": 1481380730029474144, "mod_command_log": 1481381002797649960}),
            "6": format_id(ctx.guild.id, "prisoner_role", 1494501787569492069),
            "7": format_id(ctx.guild.id, "roa", {"channel": 1412244838660968590, "role": 1418072422267228251}),
            "8": format_id(ctx.guild.id, "birthdays", {"channel": 1412129039635710017, "role": 1481462452301467730}),
            "9": format_id(ctx.guild.id, "reaction_roles", [1413199178934259844, 1413199348753498222, 1413199433264398517, 1413199535081259079, 1416830734760546476, 1450660091442368612, 1456018515050893425, 1486817352384385135, 1457222250817392661, 1481419195903381716, 1460112895252758569]),
            "10": format_id(ctx.guild.id, "application_channels", {
                                                                    "intelligence_agency":1450297920896237623,
                                                                    "moderation_team":1486904854965387334,
                                                                    "rapid_response_team":1450297912188993690,
                                                                    "omega-1":1450297923991769148,
                                                                    "alpha-1":1450297927976095838,
                                                                    "internal_security_department":1450297930060791977,
                                                                    "resh-1":1450297939510689986,
                                                                    "bcs_officer":1500126140478525451
                                                                }),
        }
        for id_doc in all_ids.values():
            await ids.insert_one(id_doc)
        await ctx.send("All ids have been inserted")
        # input all tiers 
        all_tiers = {
            "1": format_permission_tier(ctx.guild.id, "Administration", 8, [1413208971304636597], True, 6),
            "2": format_permission_tier(ctx.guild.id, "Site Command", 7, [1422416268585341049], True, 4),
            "3": format_permission_tier(ctx.guild.id, "High Command", 6, [1413226553982320713], True, 3),
            "4": format_permission_tier(ctx.guild.id, "Central Command", 5, [1413226456968069180], True, 1),
            "5": format_permission_tier(ctx.guild.id, "Moderation", 4, [1471901247345922300], False, 0),
            "6": format_permission_tier(ctx.guild.id, "IA", 3, [1413193754013073459], False, 0),
            "7": format_permission_tier(ctx.guild.id, "DRM", 2, [1428178727824658502], False, 0),
            "8": format_permission_tier(ctx.guild.id, "BSC Officer", 1, [1466462977309020303], False, 0),
        }
        for tier in all_tiers.values():
            await permission_tiers.insert_one(tier)
        await ctx.send("All tiers have been inserted")
        # input all features
        all_features = {
            "1": format_permission_rule(ctx.guild.id, "feature", "ManageCommands", 8),
            "2": format_permission_rule(ctx.guild.id, "feature", "Moderation", 6),
            "3": format_permission_rule(ctx.guild.id, "feature", "SCC", 2),
            "4": format_permission_rule(ctx.guild.id, "feature", "Sessions", 5),
            "5": format_permission_rule(ctx.guild.id, "feature", "ReactionRoles", 8),
            "6": format_permission_rule(ctx.guild.id, "feature", "Applications", 8),
            "7": format_permission_rule(ctx.guild.id, "feature", "General", 4),
            "8": format_permission_rule(ctx.guild.id, "feature", "ROA", 7),
            "9": format_permission_rule(ctx.guild.id, "feature", "TTS", 5),
            "10": format_permission_rule(ctx.guild.id, "feature", "LOA", 7),
            "11": format_permission_rule(ctx.guild.id, "feature", "RoleUser", 2),
            "12": format_permission_rule(ctx.guild.id, "feature", "Points", 5),
            "13": format_permission_rule(ctx.guild.id, "feature", "DataExport", 8),
        }
        for feature in all_features.values():
            await permission_rules.insert_one(feature)
        await ctx.send("All features have been inserted")
        # input all nodes
        all_nodes = {
            "1": format_permission_node(ctx.guild.id, "permission", "roa.manage", 5),
            "2": format_permission_node(ctx.guild.id, "permission", "roa.accept", 5),
            "3": format_permission_node(ctx.guild.id, "permission", "roa.deny", 5),
            "4": format_permission_node(ctx.guild.id, "permission", "loa.manage", 5),
            "5": format_permission_node(ctx.guild.id, "permission", "loa.accept", 5),
            "6": format_permission_node(ctx.guild.id, "permission", "loa.deny", 5),
            "7": format_permission_node(ctx.guild.id, "permission", "promotion.appointment", 8),
            "8": format_permission_node(ctx.guild.id, "permission", "promotion.accept", 5),
            "9": format_permission_node(ctx.guild.id, "permission", "promotion.deny", 5),
            "10": format_permission_node(ctx.guild.id, "permission", "enlistment.accept", 5),
            "11": format_permission_node(ctx.guild.id, "permission", "enlistment.deny", 5),
            "12": format_permission_node(ctx.guild.id, "permission", "enlistment.claim", 2),
            "13": format_permission_node(ctx.guild.id, "permission", "point_request.max_1.5", 3),
            "14": format_permission_node(ctx.guild.id, "permission", "point_request.max_2", 5),
            "15": format_permission_node(ctx.guild.id, "permission", "point_request.max_7.99", 6),
            "16": format_permission_node(ctx.guild.id, "permission", "point_request.max_8", 8),
            "17": format_permission_node(ctx.guild.id, "permission", "manage_profile.admin", 8),
            "18": format_permission_node(ctx.guild.id, "permission", "export_data.manage", 8),
        }
        for node in all_nodes.values():
            await permission_rules.insert_one(node)
        await ctx.send("All nodes have been inserted")

        await ctx.send("All Records have been inserted")

async def setup(bot):
    await bot.add_cog(DevTestingCog(bot=bot))