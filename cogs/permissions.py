from aiohttp.web_routedef import view
import discord
from discord.ext import commands
from discord import app_commands
from utils.constants import permission_tiers, permission_rules, permission_overrides, PERMISSION_NODES
from ui.paginator import PaginatorView
from discord.ui import Button
from ui.CustomModal import CustomModal
from ui.CustomSelects import RoleView, UserView
from ui.CustomButton import CustomButton
from utils.utils import permissions

class Permissions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.manage_permissions_tiers_view = None
        self.manage_perm_view = None
        self.manage_perm_type = None

    def _autocomplete_is_expired(self, interaction: discord.Interaction | None) -> bool:
        if interaction is None:
            return True

        created_at = getattr(interaction, "created_at", None)
        if created_at is None:
            return False

        # Discord requires an autocomplete response within ~3 seconds of the
        # interaction being created. Bail out early once we're close to that
        # so we don't waste time building choices for a token that's already
        # (or about to be) invalid.
        elapsed = (discord.utils.utcnow() - created_at).total_seconds()
        return elapsed >= 2.5

    async def command_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ):
        """Get all permission-managed commands and return them as choices."""

        if self._autocomplete_is_expired(interaction):
            return []

        query = str(current or "").lower()

        try:
            all_commands = [
                cmd.qualified_name
                for cmd in self.bot.walk_commands()
                if (
                    isinstance(cmd, commands.Command)
                    and not isinstance(cmd, (commands.Group, commands.HybridGroup))
                    and not cmd.qualified_name.startswith("jishaku")
                    and getattr(cmd.callback, "permission_managed", False)
                )
            ]
        except (AttributeError, TypeError):
            return []

        matches = [cmd for cmd in sorted(all_commands) if query in cmd.lower()]
        return [app_commands.Choice(name=cmd, value=cmd) for cmd in matches[:25]]
    
    async def feature_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ):
        """Get all cogs that contain at least one permission-managed command."""

        if self._autocomplete_is_expired(interaction):
            return []

        query = str(current or "").lower()

        try:
            all_cogs = []

            for cog_name, cog in self.bot.cogs.items():
                if cog_name == "jishaku":
                    continue

                has_permission_command = any(
                    getattr(command.callback, "permission_managed", False)
                    for command in cog.walk_commands()
                    if isinstance(command, commands.Command)
                )

                if has_permission_command:
                    all_cogs.append(cog_name)
        except (AttributeError, TypeError):
            return []

        matches = [cog for cog in sorted(all_cogs) if query in cog.lower()]
        return [app_commands.Choice(name=cog, value=cog) for cog in matches[:25]]
    
    async def min_rank_autocomplete(self, interaction: discord.Interaction, current: str):
        '''Get all min ranks for this guild, ordered from highest to lowest rank.'''
        if self._autocomplete_is_expired(interaction):
            return []

        query = str(current or "").lower()
        guild_id = interaction.guild.id if interaction.guild else None

        try:
            guild_tiers = list(self.bot.permission_tiers.get(guild_id, {}).values())
            ordered_tiers = sorted(
                guild_tiers,
                key=lambda tier: int((tier or {}).get("rank", 0) or 0),
                reverse=True,
            )
            all_ranks = [str((tier or {}).get("name", "Unknown") or "Unknown") for tier in ordered_tiers]
        except Exception:
            return []

        matches = [rank for rank in all_ranks if query in rank.lower()]
        return [app_commands.Choice(name=rank, value=rank) for rank in matches[:25]]

    async def perm_nodes_autocomplete(self, interaction: discord.Interaction, current: str):
        '''get all permission nodes located in constants and return them as a choice'''
        if self._autocomplete_is_expired(interaction):
            return []

        query = str(current or "").lower()
        matches = [node for node in PERMISSION_NODES.keys() if query in node.lower()]
        return [app_commands.Choice(name=node, value=node) for node in matches[:25]]

    async def PT_add_record(self, interaction: discord.Interaction):
        modal = CustomModal(
            "Tier Addition",
            [
                (
                    "tier_name",
                    discord.ui.TextInput(
                        label="Tier Name",
                        placeholder="Central Command",
                        required=True,
                        max_length=50,
                    )
                ),
                (
                    "tier_rank",
                    discord.ui.TextInput(
                        label="Tier Rank(1-100 | Lowest-Highest)",
                        placeholder="1",
                        required=True,
                        max_length=3,
                    )
                ),
                (
                    "gift_amt",
                    discord.ui.TextInput(
                        label="Point Gift Limit (blank or 0 or nothing)?",
                        placeholder="1",
                        required=False,
                        max_length=25,
                    )
                )
            ]
        )

        await interaction.response.send_modal(modal)
        await modal.wait()

        name_results = await permission_tiers.find_one({"guild_id": interaction.guild.id, "name": modal.tier_name.value})
        rank_results = await permission_tiers.find_one({"guild_id": interaction.guild.id, "rank": int(modal.tier_rank.value)})

        if name_results:
            return await interaction.followup.send(f"It looks like theres already a tier named `{modal.tier_name.value}`", ephemeral=True)
        elif rank_results:
            return await interaction.followup.send(f"It looks like theres already a tier with the rank of `{modal.tier_rank.value}`", ephemeral=True)
        
        gift_amt = modal.gift_amt.value
        try:
            if gift_amt:
                gift_amt = int(gift_amt)
        except ValueError:
            await interaction.channel.send(f"Failed to convert number of gift points from `{gift_amt}` to a number! Reverting to 0!")
            gift_amt = 0

        view = RoleView(self.bot, min_values=1, max_values=25)
        embed = discord.Embed(title="Roles", description="Please input the roles for this permission tier", color=discord.Color.light_grey())
        await interaction.followup.send(view=view, embed=embed, ephemeral=True)

        await view.wait()

        can_gift = True if gift_amt and gift_amt > 0 else False
        gift_points = 0 if not gift_amt or gift_amt <= 0 else gift_amt

        perms_tier_doc = {
            "guild_id": interaction.guild.id,
            "name": modal.tier_name.value,
            "rank": int(modal.tier_rank.value),
            "role_ids": [int(role.id) for role in view.roles],
            "can_gift_points": can_gift,
            "gift_points_amount": gift_points
        }
        await permission_tiers.insert_one(perms_tier_doc)

        self.manage_permissions_tiers_view.items.append(perms_tier_doc)
        self.bot.permission_tiers.setdefault(interaction.guild.id, {})[perms_tier_doc["name"]] = perms_tier_doc

        self.manage_permissions_tiers_view.update_buttons()
        new_embed = self.manage_permissions_tiers_view.create_record_embed()

        await interaction.edit_original_response(view=self.manage_permissions_tiers_view, embed=new_embed, content=None)

    async def PT_edit_points(self, interaction: discord.Interaction):
        if not self.manage_permissions_tiers_view.items or self.manage_permissions_tiers_view.current_index >= len(self.manage_permissions_tiers_view.items):
            return await interaction.response.send_message("No record to edit.", ephemeral=True)
        current_record = self.manage_permissions_tiers_view.items[self.manage_permissions_tiers_view.current_index]
        current_gift = current_record.get("gift_points_amount", 0) or 0

        modal = CustomModal(
            "Edit Gift Points",
            [
                (
                    "gift_amt",
                    discord.ui.TextInput(
                        label="Point Gift Limit (blank or 0 or nothing)?",
                        placeholder=str(current_gift),
                        default=str(current_gift),
                        required=False,
                        max_length=25,
                    )
                )
            ]
        )

        await interaction.response.send_modal(modal)
        await modal.wait()

        gift_amt = modal.gift_amt.value
        try:
            if gift_amt:
                gift_amt = int(gift_amt)
        except ValueError:
            await interaction.channel.send(f"Failed to convert number of gift points from `{gift_amt}` to a number! Reverting to 0!")
            gift_amt = 0

        can_gift = True if gift_amt and gift_amt > 0 else False
        gift_points = 0 if not gift_amt or gift_amt <= 0 else gift_amt

        # current_record already set above
        await permission_tiers.update_one({"guild_id": interaction.guild.id, "name": current_record.get("name"), "rank": int(current_record.get("rank"))}, {"$set": {"can_gift_points": can_gift, "gift_points_amount": gift_points}})

        self.manage_permissions_tiers_view.items[self.manage_permissions_tiers_view.current_index]["can_gift_points"] = can_gift
        self.manage_permissions_tiers_view.items[self.manage_permissions_tiers_view.current_index]["gift_points_amount"] = gift_points

        self.manage_permissions_tiers_view.update_buttons()
        new_embed = self.manage_permissions_tiers_view.create_record_embed()

        await interaction.edit_original_response(view=self.manage_permissions_tiers_view, embed=new_embed, content=None)

    async def PT_edit_roles(self, interaction: discord.Interaction):
        if not self.manage_permissions_tiers_view.items or self.manage_permissions_tiers_view.current_index >= len(self.manage_permissions_tiers_view.items):
            return await interaction.response.send_message("No record to edit.", ephemeral=True)
        # present a role-select + cancel button on the paginator message itself
        current_record = self.manage_permissions_tiers_view.items[self.manage_permissions_tiers_view.current_index]

        embed = discord.Embed(title="Roles", description="Please select the roles for this permission tier then submit. Or Cancel to return.", color=discord.Color.light_grey())

        class RolesEditView(discord.ui.View):
            def __init__(self, bot, min_values: int = 1, max_values: int = 25, placeholder: str = "Select roles"):
                super().__init__(timeout=None)
                self.bot = bot
                self.roles = None
                self.cancelled = False
                # configure the select callback's constraints
                self.role_select_callback.min_values = min_values
                self.role_select_callback.max_values = max_values
                self.role_select_callback.placeholder = placeholder

            @discord.ui.select(cls=discord.ui.RoleSelect)
            async def role_select_callback(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
                self.roles = select.values
                await interaction.response.defer(ephemeral=True)
                self.stop()

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
            async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.cancelled = True
                await interaction.response.defer(ephemeral=True)
                self.stop()

        view = RolesEditView(self.bot, min_values=1, max_values=25)

        # replace the paginator message with the role editor
        await interaction.response.edit_message(embed=embed, view=view)

        await view.wait()

        # if cancelled, restore paginator view
        if getattr(view, "cancelled", False):
            self.manage_permissions_tiers_view.update_buttons()
            embed = self.manage_permissions_tiers_view.create_record_embed()
            await interaction.edit_original_response(view=self.manage_permissions_tiers_view, embed=embed, content=None)
            return

        # otherwise, update roles and return to paginator
        if not getattr(view, "roles", None):
            # no roles selected; just return paginator
            self.manage_permissions_tiers_view.update_buttons()
            embed = self.manage_permissions_tiers_view.create_record_embed()
            await interaction.edit_original_response(view=self.manage_permissions_tiers_view, embed=embed, content=None)
            return

        roles = [int(role.id) for role in view.roles]
        await permission_tiers.update_one({"guild_id": interaction.guild.id, "name": current_record.get("name"), "rank": int(current_record.get("rank"))}, {"$set": {"role_ids": roles}})

        self.manage_permissions_tiers_view.items[self.manage_permissions_tiers_view.current_index]["role_ids"] = roles

        self.manage_permissions_tiers_view.update_buttons()
        new_embed = self.manage_permissions_tiers_view.create_record_embed()

        await interaction.edit_original_response(view=self.manage_permissions_tiers_view, embed=new_embed, content=None)
    
    async def PT_edit_record(self, interaction: discord.Interaction):
        if not self.manage_permissions_tiers_view.items or self.manage_permissions_tiers_view.current_index >= len(self.manage_permissions_tiers_view.items):
            return await interaction.response.send_message("No record to edit.", ephemeral=True)
        
        embed = discord.Embed(
            title="Record Edit",
            description="You can only edit roles or gift points for this tier. If you want to edit the name or rank, please delete and re-add the tier.",
            color=discord.Color.light_grey()
        )
        view = discord.ui.View()
        edit_gift_points_button = CustomButton(label="Edit Gift Points", style=discord.ButtonStyle.gray, row=1, auto_defer=False)
        edit_roles_button = CustomButton(label="Edit Roles", style=discord.ButtonStyle.gray, row=1, auto_defer=False)
        cancel_button = CustomButton(label="Cancel", style=discord.ButtonStyle.red, row=1)
        
        view.add_item(cancel_button)
        view.add_item(edit_gift_points_button)
        view.add_item(edit_roles_button)
        await interaction.response.edit_message(embed=embed, view=view)
        await view.wait()
        # prefer the interaction from the button click so we can send modals/messages
        button_interaction = None
        if edit_gift_points_button.status:
            button_interaction = getattr(edit_gift_points_button, "clicked_interaction", None)
        elif edit_roles_button.status:
            button_interaction = getattr(edit_roles_button, "clicked_interaction", None)
        elif cancel_button.status:
            button_interaction = getattr(cancel_button, "clicked_interaction", None)

        if button_interaction is None:
            button_interaction = interaction

        if edit_gift_points_button.status and not cancel_button.status:
            await self.PT_edit_points(button_interaction)
        elif edit_roles_button.status and not cancel_button.status:
            await self.PT_edit_roles(button_interaction)

        self.manage_permissions_tiers_view.update_buttons()
        new_embed = self.manage_permissions_tiers_view.create_record_embed()

        await interaction.edit_original_response(view=self.manage_permissions_tiers_view, embed=new_embed, content=None)
    
    async def PT_remove_record(self, interaction: discord.Interaction):
        if not self.manage_permissions_tiers_view.items or self.manage_permissions_tiers_view.current_index >= len(self.manage_permissions_tiers_view.items):
            return await interaction.response.send_message("No record to delete.", ephemeral=True)
        
        current_record = self.manage_permissions_tiers_view.items[self.manage_permissions_tiers_view.current_index]
        embed = discord.Embed(
            title="Confirm Removal",
            description=f"Are you sure you want to remove `{current_record.get("name")}` tier?",
            color=discord.Color.red()
        )

        confirm = CustomButton(label="Confirm", style=discord.ButtonStyle.green)
        cancel = CustomButton(label="Cancel", style=discord.ButtonStyle.red)
        view = discord.ui.View()
        view.add_item(confirm)
        view.add_item(cancel)

        await interaction.response.edit_message(view=view, embed=embed)
        await view.wait()

        if confirm.status and not cancel.status:
            self.manage_permissions_tiers_view.items.remove(current_record)
            guild_tiers = self.bot.permission_tiers.get(interaction.guild.id, {})
            guild_tiers.pop(current_record.get("name"), None)

            await permission_tiers.delete_one({"guild_id": interaction.guild.id, "name": current_record.get("name")})
        
        self.manage_permissions_tiers_view.current_index = 0
        self.manage_permissions_tiers_view.update_buttons()
        embed = self.manage_permissions_tiers_view.create_record_embed()

        await interaction.edit_original_response(embed=embed, view=self.manage_permissions_tiers_view)
    
    async def P_delete_record(self, interaction: discord.Interaction):
        if not self.manage_rules_view.items or self.manage_rules_view.current_index >= len(self.manage_rules_view.items):
            return await interaction.response.send_message("No record to delete.", ephemeral=True)
        
        
        current_record = self.manage_rules_view.items[self.manage_rules_view.current_index]
        embed = discord.Embed(
            title="Confirm Removal",
            description="Are you sure you want to remove this rule?",
            color=discord.Color.red()
        )

        confirm = CustomButton(label="Confirm", style=discord.ButtonStyle.green)
        cancel = CustomButton(label="Cancel", style=discord.ButtonStyle.red)
        view = discord.ui.View()
        view.add_item(confirm)
        view.add_item(cancel)

        await interaction.response.edit_message(view=view, embed=embed)
        await view.wait()

        if confirm.status and not cancel.status:
            self.manage_rules_view.items.remove(current_record)

            if self.manage_perm_type == "rules":
                await permission_rules.delete_one(current_record)
                rule_key = (
                    current_record["guild_id"],
                    current_record["scope_type"],
                    current_record["scope_key"],
                )
                self.bot.permission_rules.pop(rule_key, None)
            elif self.manage_perm_type == "overrides":
                await permission_overrides.delete_one(current_record)
                scope_key = (
                    current_record["guild_id"],
                    current_record["scope_type"],
                    current_record["scope_key"],
                )
                target_key = (current_record["target_type"], current_record["target_id"])
                scoped_overrides = self.bot.permission_overrides.get(scope_key, {})
                scoped_overrides.pop(target_key, None)

        self.manage_rules_view.current_index = 0
        self.manage_rules_view.update_buttons()
        embed = self.manage_rules_view.create_record_embed()

        await interaction.edit_original_response(embed=embed, view=self.manage_rules_view)


    permissions_group = app_commands.Group(name="permissions", description="Manage permissions for commands and features.")
    
    set_permissions = app_commands.Group(name="set", description="Set permissions for commands and features.", parent=permissions_group)

    override_permissions = app_commands.Group(name="override", description="Override permissions for commands and features.", parent=permissions_group)

    permission_tiers = app_commands.Group(name="tiers", description="Manage permission tiers.", parent=permissions_group)


    @permission_tiers.command(name="manage", description="Manage permission tier.", extras={'category': 'Permissions'})
    @permissions()
    async def manage_permissions_tiers(self, interaction: discord.Interaction):
        guild_tiers = list(self.bot.permission_tiers.get(interaction.guild.id, {}).values())
        self.manage_permissions_tiers_view = PaginatorView(self.bot, interaction.user, guild_tiers)

        add_button = Button(
            label="Add",
            style=discord.ButtonStyle.green,
            row=2
        )
        add_button.callback = self.PT_add_record

        edit_button = Button(
            label="Edit",
            style=discord.ButtonStyle.gray,
            row=2
        )
        edit_button.callback = self.PT_edit_record
        
        remove_button = Button(
            label="Remove",
            style=discord.ButtonStyle.red,
            row=2
        )
        remove_button.callback = self.PT_remove_record

        self.manage_permissions_tiers_view.extra_buttons = [add_button, edit_button, remove_button]
        self.manage_permissions_tiers_view.update_buttons()

        embed = self.manage_permissions_tiers_view.create_record_embed()
        await interaction.response.send_message(view=self.manage_permissions_tiers_view, embed=embed, ephemeral=True)
    
    @permissions_group.command(name="manage", description="Manage all permission rules and overrides", extras={'category': 'Permissions'})
    @permissions()
    @app_commands.describe(perm_type="Would you like to manage features or commands?")
    @app_commands.choices(
        perm_level=[
            app_commands.Choice(name="Feature", value="feature"),
            app_commands.Choice(name="Command", value="command")
        ],
        perm_type = [
            app_commands.Choice(name="Rules", value="rules"),
            app_commands.Choice(name="Overrides", value="overrides")
        ]
    )
    async def set_command_delete(self, interaction: discord.Interaction, perm_level: str, perm_type: str):
        if perm_type == "rules":
            type_perm_records = await permission_rules.find({"guild_id": interaction.guild.id, "scope_type": perm_level}).to_list(length=None)
        elif perm_type == "overrides":
            type_perm_records = await permission_overrides.find({"guild_id": interaction.guild.id, "scope_type": perm_level}).to_list(length=None)
        else:
            return await interaction.response.send_message("This is not a valid type!", ephemeral=True)
        
        self.manage_perm_type = perm_type

        self.manage_rules_view = PaginatorView(self.bot, interaction.user, type_perm_records)
        delete_button = CustomButton(label="Delete", style=discord.ButtonStyle.danger, row=2)
        delete_button.callback = self.P_delete_record

        self.manage_rules_view.extra_buttons = [delete_button]

        self.manage_rules_view.update_buttons()
        embed = self.manage_rules_view.create_record_embed()
        await interaction.response.send_message(embed=embed, view=self.manage_rules_view, ephemeral=True)

    @set_permissions.command(name="all", description="Set the permission for every command, feature, or node at once.", extras={'category': 'Permissions'})
    @permissions()
    @app_commands.describe(scope="Which set of things to bulk-update.", min_rank="The min tier required.")
    @app_commands.choices(scope=[
        app_commands.Choice(name="Commands", value="command"),
        app_commands.Choice(name="Features", value="feature"),
        app_commands.Choice(name="Nodes", value="permission"),
    ])
    @app_commands.autocomplete(min_rank=min_rank_autocomplete)
    async def set_all_permissions(self, interaction: discord.Interaction, scope: app_commands.Choice[str], min_rank: str):
        await interaction.response.defer(ephemeral=True)

        tier_info = await permission_tiers.find_one({"guild_id": interaction.guild.id, "name": min_rank})
        if not tier_info:
            return await interaction.followup.send("Failed to find tier!", ephemeral=True)

        scope_type = scope.value
        new_rank = tier_info.get("rank")

        if scope_type == "command":
            keys = sorted({
                cmd.qualified_name
                for cmd in self.bot.walk_commands()
                if (
                    isinstance(cmd, commands.Command)
                    and not isinstance(cmd, (commands.Group, commands.HybridGroup))
                    and not cmd.qualified_name.startswith("jishaku")
                    and getattr(cmd.callback, "permission_managed", False)
                )
            })
        elif scope_type == "feature":
            keys = []
            for cog_name, cog in self.bot.cogs.items():
                if cog_name == "jishaku":
                    continue
                has_permission_command = any(
                    getattr(cmd.callback, "permission_managed", False)
                    for cmd in cog.walk_commands()
                    if isinstance(cmd, commands.Command)
                )
                if has_permission_command:
                    keys.append(cog_name)
            keys.sort()
        elif scope_type == "permission":
            keys = sorted(PERMISSION_NODES.keys())
        else:
            keys = []

        if not keys:
            return await interaction.followup.send("Couldn't find anything to update for that scope.", ephemeral=True)

        for key in keys:
            await permission_rules.update_one(
                {"guild_id": interaction.guild.id, "scope_type": scope_type, "scope_key": key},
                {"$set": {
                    "guild_id": interaction.guild.id,
                    "scope_type": scope_type,
                    "scope_key": key,
                    "min_rank": new_rank,
                }},
                upsert=True,
            )

            rule_key = (interaction.guild.id, scope_type, key)
            cached_rule = self.bot.permission_rules.get(rule_key)
            if cached_rule:
                cached_rule["min_rank"] = new_rank
            else:
                self.bot.permission_rules[rule_key] = {
                    "guild_id": interaction.guild.id,
                    "scope_type": scope_type,
                    "scope_key": key,
                    "min_rank": new_rank,
                }

        await interaction.followup.send(
            f"Set all **{scope.name.lower()}** to require a min rank of `{min_rank}` ({len(keys)} updated).",
            ephemeral=True,
        )

    @set_permissions.command(name="node", description="Set the permissions for a node.", extras={'category': 'Permissions'})
    @permissions()
    @app_commands.describe(node="This is the node name", min_rank="The min tier required for this command.")
    @app_commands.autocomplete(node=perm_nodes_autocomplete, min_rank=min_rank_autocomplete)
    async def set_node_permissions(self, interaction: discord.Interaction, node: str, min_rank: str):
        tier_info = await permission_tiers.find_one({"guild_id": interaction.guild.id, "name": min_rank})
        if not tier_info:
            return await interaction.response.send_message("Failed to find tier!", ephemeral=True)
        
        node_doc = {
            "guild_id": interaction.guild.id,
            "scope_type": "permission",
            "scope_key": node,
            "min_rank": tier_info.get("rank")
        }

        await permission_rules.update_one({"guild_id": interaction.guild.id, "scope_type": "permission", "scope_key": node}, {"$set": node_doc}, upsert=True)
        self.bot.permission_rules[(interaction.guild.id, "permission", node)] = node_doc

        await interaction.response.send_message(f"Set permission node `{node}` to require a min rank of `{min_rank}`", ephemeral=True)

    @set_permissions.command(name="command", description="Set the permissions for a command.", extras={'category': 'Permissions'})
    @permissions()
    @app_commands.describe(command="The command to set permissions for.", min_rank="The min tier required for this command.")
    @app_commands.autocomplete(command=command_autocomplete, min_rank=min_rank_autocomplete)
    async def set_command_permissions(self, interaction: discord.Interaction, command: str, min_rank: str):
        tier_info = await permission_tiers.find_one({"guild_id": interaction.guild.id, "name": min_rank})
        if not tier_info:
            return await interaction.response.send_message("Failed to find tier!", ephemeral=True)
        
        perm_rules_doc = {
            "guild_id": interaction.guild.id,
            "scope_type": "command",
            "scope_key": command,
            "min_rank": tier_info.get("rank")
        }

        rule_key = (interaction.guild.id, "command", command)
        cached_rule = self.bot.permission_rules.get(rule_key)

        if cached_rule:

            await permission_rules.update_one(
                {"guild_id": interaction.guild.id, "scope_type": "command", "scope_key": command},
                {"$set": {"min_rank": tier_info.get("rank")}}
            )
            cached_rule["min_rank"] = tier_info["rank"]

        else:
            await permission_rules.insert_one(perm_rules_doc)
            self.bot.permission_rules[rule_key] = perm_rules_doc

        await interaction.response.send_message(f"Set minimum rank for command `{command}` to `{min_rank}`.", ephemeral=True)

    @set_permissions.command(name="feature", description="Set the permissions for a feature.", extras={'category': 'Permissions'})
    @permissions()
    @app_commands.describe(feature="The feature to set permissions for.", min_rank="The min tier required for this feature.")
    @app_commands.autocomplete(feature=feature_autocomplete, min_rank=min_rank_autocomplete)
    async def set_feature_permissions(self, interaction: discord.Interaction, feature: str, min_rank: str):
        tier_info = await permission_tiers.find_one({"guild_id": interaction.guild.id, "name": min_rank})
        if not tier_info:
            return await interaction.response.send_message("Failed to find tier!", ephemeral=True)
        
        perm_rules_doc = {
            "guild_id": interaction.guild.id,
            "scope_type": "feature",
            "scope_key": feature,
            "min_rank": tier_info.get("rank")
        }

        rule_key = (interaction.guild.id, "feature", feature)
        cached_rule = self.bot.permission_rules.get(rule_key)

        if cached_rule:
            await permission_rules.update_one(
                {"guild_id": interaction.guild.id, "scope_type": "feature", "scope_key": feature},
                {"$set": {"min_rank": tier_info.get("rank")}}
            )
            cached_rule["min_rank"] = tier_info["rank"]
        else:
            await permission_rules.insert_one(perm_rules_doc)
            self.bot.permission_rules[rule_key] = perm_rules_doc

        await interaction.response.send_message(f"Set minimum rank for feature `{feature}` to `{min_rank}`.", ephemeral=True)

    @override_permissions.command(name="command", description="Override permissions for a command.", extras={'category': 'Permissions'})
    @permissions()
    @app_commands.describe(command="The command to set permissions for.", scope_type="Is it a role or user?", effect="Should it be allowed or denied?")
    @app_commands.choices(scope_type=[
        app_commands.Choice(name="Role", value="role"),
        app_commands.Choice(name="User", value="user")
    ],
    effect=[
        app_commands.Choice(name="Allow", value="allow"),
        app_commands.Choice(name="Deny", value="deny")
    ])
    @app_commands.autocomplete(command=command_autocomplete)
    async def overwrite_command_permissions(self, interaction: discord.Interaction, command: str, scope_type: str, effect: str):
        perm_override_doc = {
            "guild_id": interaction.guild.id,
            "scope_type": "command",
            "scope_key": command,
            "target_type": '',
            "target_id": 0,
            "effect": effect
        }

        if scope_type == "role":
            view = RoleView(self.bot)
            await interaction.response.send_message("Please select a role to override permissions for:", view=view, ephemeral=True)
            await view.wait()
            if not view.roles:
                await interaction.followup.send("No role was selected. Please try again.", ephemeral=True)
                return
            perm_override_doc["target_type"] = "role"
            perm_override_doc["target_id"] = int(view.roles[0].id)
        elif scope_type == "user":
            view = UserView(self.bot)
            await interaction.response.send_message("Please select a user to override permissions for:", view=view, ephemeral=True)
            await view.wait()
            if not view.users:
                await interaction.followup.send("No user was selected. Please try again.", ephemeral=True)
                return
            perm_override_doc["target_type"] = "user"
            perm_override_doc["target_id"] = int(view.users[0].id)

        scope_key = (interaction.guild.id, "command", command)
        target_key = (perm_override_doc["target_type"], perm_override_doc["target_id"])
        cached_rule = self.bot.permission_overrides.get(scope_key, {}).get(target_key)
        
        if cached_rule:
            await permission_overrides.update_one(
                {"guild_id": interaction.guild.id, "scope_type": "command", "scope_key": command, "target_type": perm_override_doc["target_type"], "target_id": perm_override_doc["target_id"]},
                {"$set": {"effect": effect}}
            )
            cached_rule["effect"] = effect
        else:
            await permission_overrides.insert_one(perm_override_doc)
            self.bot.permission_overrides.setdefault(scope_key, {})[target_key] = perm_override_doc

        await interaction.followup.send(f"Overwrote permissions for command `{command}` for {scope_type} `{perm_override_doc['target_id']}` with effect `{effect}`.", ephemeral=True)

    @override_permissions.command(name="feature", description="Override permissions for a feature.", extras={'category': 'Permissions'})
    @permissions()
    @app_commands.describe(feature="The feature to set permissions for.", scope_type="Is it a role or user?", effect="Should it be allowed or denied?")
    @app_commands.choices(scope_type=[
        app_commands.Choice(name="Role", value="role"),
        app_commands.Choice(name="User", value="user")
    ],
    effect=[
        app_commands.Choice(name="Allow", value="allow"),
        app_commands.Choice(name="Deny", value="deny")
    ])
    @app_commands.autocomplete(feature=feature_autocomplete)
    async def overwrite_feature_permissions(self, interaction: discord.Interaction, feature: str, scope_type: str, effect: str):
        perm_override_doc = {
            "guild_id": interaction.guild.id,
            "scope_type": "feature",
            "scope_key": feature,
            "target_type": '',
            "target_id": 0,
            "effect": effect
        }

        if scope_type == "role":
            view = RoleView(self.bot)
            await interaction.response.send_message("Please select a role to override permissions for:", view=view, ephemeral=True)
            await view.wait()
            if not view.roles:
                await interaction.followup.send("No role was selected. Please try again.", ephemeral=True)
                return
            perm_override_doc["target_type"] = "role"
            perm_override_doc["target_id"] = int(view.roles[0].id)
        elif scope_type == "user":
            view = UserView(self.bot)
            await interaction.response.send_message("Please select a user to override permissions for:", view=view, ephemeral=True)
            await view.wait()
            if not view.users:
                await interaction.followup.send("No user was selected. Please try again.", ephemeral=True)
                return
            perm_override_doc["target_type"] = "user"
            perm_override_doc["target_id"] = int(view.users[0].id)

        scope_key = (interaction.guild.id, "feature", feature)
        target_key = (perm_override_doc["target_type"], perm_override_doc["target_id"])
        cached_rule = self.bot.permission_overrides.get(scope_key, {}).get(target_key)
        
        if cached_rule:
            await permission_overrides.update_one(
                {"guild_id": interaction.guild.id, "scope_type": "feature", "scope_key": feature, "target_type": perm_override_doc["target_type"], "target_id": perm_override_doc["target_id"]},
                {"$set": {"effect": effect}}
            )
            cached_rule["effect"] = effect
        else:
            await permission_overrides.insert_one(perm_override_doc)
            self.bot.permission_overrides.setdefault(scope_key, {})[target_key] = perm_override_doc

        await interaction.followup.send(f"Overwrote permissions for feature `{feature}` for {scope_type} `{perm_override_doc['target_id']}` with effect `{effect}`.", ephemeral=True)
        


async def setup(bot: commands.Bot):
    await bot.add_cog(Permissions(bot))