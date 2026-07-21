import discord
from discord.ext import commands
from discord import app_commands
from utils.constants import permission_tiers, permission_rules, permission_overrides
from ui.paginator import PaginatorView
from discord.ui import Button
from ui.CustomModal import CustomModal
from ui.CustomSelects import RoleView, UserView
from ui.CustomButton import CustomButton

class Permissions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.manage_permissions_tiers_view = None
        self.manage_perm_view = None
        self.manage_perm_type = None

    async def command_autocomplete(self, interaction: discord.Interaction, current: str):
        '''Get all commands and return them as choices'''
        all_commands = [
                        cmd.qualified_name
                        for cmd in self.bot.walk_commands()
                        if (
                            isinstance(cmd, commands.Command)
                            and not isinstance(cmd, (commands.Group, commands.HybridGroup))
                            and not cmd.qualified_name.startswith("jishaku")
                        )
                    ]
        
        matches = [cmd for cmd in all_commands if current.lower() in cmd.lower()]
        return [app_commands.Choice(name=cmd, value=cmd) for cmd in matches[:25]]
    
    async def feature_autocomplete(self, interaction: discord.Interaction, current: str):
        '''Get all cogs and return them as features'''
        all_cogs = [cog for cog in self.bot.cogs.keys() if cog not in['jishaku']]
        matches = [cog for cog in all_cogs if current.lower() in cog.lower()]
        return [app_commands.Choice(name=cog, value=cog) for cog in matches[:25]]
    
    async def min_rank_autocomplete(self, interaction: discord.Interaction, current: str):
        ''''get all min ranks and return them as a choice'''
        all_ranks = [rank.get("name", "Unknown") for rank in self.bot.permission_tiers]
        matches = [rank for rank in all_ranks if current.lower() in rank.lower()]
        return [app_commands.Choice(name=rank, value=rank) for rank in matches[:25]]

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
                )
            ]
        )

        await interaction.response.send_modal(modal)
        await modal.wait()

        results = await permission_tiers.find_one({"guild_id": interaction.guild.id, "name": modal.tier_name.value})
        if results:
            return await interaction.followup.send(f"It looks like theres already a tier named `{modal.tier_name.value}`", ephemeral=True)

        view = RoleView(self.bot, min_values=1, max_values=25)
        embed = discord.Embed(title="Roles", description="Please input the roles for this permission tier", color=discord.Color.light_grey())
        await interaction.followup.send(view=view, embed=embed, ephemeral=True)

        await view.wait()

        perms_tier_doc = {
            "guild_id": interaction.guild.id,
            "name": modal.tier_name.value,
            "rank": int(modal.tier_rank.value),
            "role_ids": [int(role.id) for role in view.roles]
        }
        await permission_tiers.insert_one(perms_tier_doc)

        self.manage_permissions_tiers_view.items.append(perms_tier_doc)

        self.manage_permissions_tiers_view.update_buttons()
        new_embed = self.manage_permissions_tiers_view.create_record_embed()

        await interaction.edit_original_response(view=self.manage_permissions_tiers_view, embed=new_embed, content=None)
    
    async def PT_edit_record(self, interaction: discord.Interaction):
        if not self.manage_permissions_tiers_view.items or self.manage_permissions_tiers_view.current_index >= len(self.manage_permissions_tiers_view.items):
            return await interaction.response.send_message("No record to edit.", ephemeral=True)
        
        embed = discord.Embed(
            title="Record Edit",
            description="You can only edit the roles, if you would like to edit the name or rank please delete and re-add",
            color=discord.Color.light_grey()
        )
        view = RoleView(self.bot, min_values=1, max_values=25)
        cancel_button = CustomButton(label="Cancel", style=discord.ButtonStyle.red, row=2)
        view.add_item(cancel_button)
        await interaction.response.edit_message(embed=embed, view=view)
        await view.wait()

        if view.roles and not cancel_button.status:
            roles = [int(role.id) for role in view.roles]
            current_record = self.manage_permissions_tiers_view.items[self.manage_permissions_tiers_view.current_index]
            await permission_tiers.update_one({"guild_id": interaction.guild.id, "name": current_record.get("name"), "rank": int(current_record.get("rank"))}, {"$set": {"role_ids": roles}})

            self.manage_permissions_tiers_view.items[self.manage_permissions_tiers_view.current_index]["role_ids"] = roles

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
                self.bot.permission_rules.remove(current_record)
            elif self.manage_perm_type == "overrides":
                await permission_overrides.delete_one(current_record)
                self.bot.permission_overrides.remove(current_record)

        self.manage_rules_view.current_index = 0
        self.manage_rules_view.update_buttons()
        embed = self.manage_rules_view.create_record_embed()

        await interaction.edit_original_response(embed=embed, view=self.manage_rules_view)


    permissions = app_commands.Group(name="permissions", description="Manage permissions for commands and features.")
    
    set_permissions = app_commands.Group(name="set", description="Set permissions for commands and features.", parent=permissions)

    override_permissions = app_commands.Group(name="override", description="Override permissions for commands and features.", parent=permissions)

    permission_tiers = app_commands.Group(name="tiers", description="Manage permission tiers.", parent=permissions)


    @permission_tiers.command(name="manage", description="Manage permission tier.", extras={'category': 'Permissions'})
    async def manage_permissions_tiers(self, interaction: discord.Interaction):
        self.manage_permissions_tiers_view = PaginatorView(self.bot, interaction.user, self.bot.permission_tiers)

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
    
    @permissions.command(name="manage", description="Manage all permission rules and overrides", extras={'category': 'Permissions'})
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

    @set_permissions.command(name="command", description="Set the permissions for a command.", extras={'category': 'Permissions'})
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

        cached_rule = next(
           ( 
                rule for rule in self.bot.permission_rules
                if rule["guild_id"] == interaction.guild.id
                and rule["scope_type"] == "command"
                and rule["scope_key"] == command
            ),
            None
        )

        if cached_rule:

            await permission_rules.update_one(
                {"guild_id": interaction.guild.id, "scope_type": "command", "scope_key": command},
                {"$set": {"min_rank": tier_info.get("rank")}}
            )
            cached_rule["min_rank"] = tier_info["rank"]

        else:
            await permission_rules.insert_one(perm_rules_doc)
            self.bot.permission_rules.append(perm_rules_doc)

        await interaction.response.send_message(f"Set minimum rank for command `{command}` to `{min_rank}`.", ephemeral=True)

    @set_permissions.command(name="feature", description="Set the permissions for a feature.", extras={'category': 'Permissions'})
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

        cached_rule = next(
           ( 
                rule for rule in self.bot.permission_rules
                if rule["guild_id"] == interaction.guild.id
                and rule["scope_type"] == "feature"
                and rule["scope_key"] == feature
            ),
            None
        )

        if cached_rule:
            await permission_rules.update_one(
                {"guild_id": interaction.guild.id, "scope_type": "feature", "scope_key": feature},
                {"$set": {"min_rank": tier_info.get("rank")}}
            )
            cached_rule["min_rank"] = tier_info["rank"]
        else:
            await permission_rules.insert_one(perm_rules_doc)
            self.bot.permission_rules.append(perm_rules_doc)

        await interaction.response.send_message(f"Set minimum rank for feature `{feature}` to `{min_rank}`.", ephemeral=True)

    @override_permissions.command(name="command", description="Override permissions for a command.", extras={'category': 'Permissions'})
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

        cached_rule = next(
           ( 
                rule for rule in self.bot.permission_overrides
                if rule["guild_id"] == interaction.guild.id
                and rule["scope_type"] == "command"
                and rule["scope_key"] == command
                and rule["target_type"] == perm_override_doc["target_type"]
                and rule["target_id"] == perm_override_doc["target_id"]
            ),
            None
        )
        
        if cached_rule:
            await permission_overrides.update_one(
                {"guild_id": interaction.guild.id, "scope_type": "command", "scope_key": command, "target_type": perm_override_doc["target_type"], "target_id": perm_override_doc["target_id"]},
                {"$set": {"effect": effect}}
            )
            cached_rule["effect"] = effect
        else:
            await permission_overrides.insert_one(perm_override_doc)
            self.bot.permission_overrides.append(perm_override_doc)

        await interaction.followup.send(f"Overwrote permissions for command `{command}` for {scope_type} `{perm_override_doc['target_id']}` with effect `{effect}`.", ephemeral=True)

    @override_permissions.command(name="feature", description="Override permissions for a feature.", extras={'category': 'Permissions'})
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

        cached_rule = next(
           ( 
                rule for rule in self.bot.permission_overrides
                if rule["guild_id"] == interaction.guild.id
                and rule["scope_type"] == "feature"
                and rule["scope_key"] == feature
                and rule["target_type"] == perm_override_doc["target_type"]
                and rule["target_id"] == perm_override_doc["target_id"]
            ),
            None
        )
        
        if cached_rule:
            await permission_overrides.update_one(
                {"guild_id": interaction.guild.id, "scope_type": "feature", "scope_key": feature, "target_type": perm_override_doc["target_type"], "target_id": perm_override_doc["target_id"]},
                {"$set": {"effect": effect}}
            )
            cached_rule["effect"] = effect
        else:
            await permission_overrides.insert_one(perm_override_doc)
            self.bot.permission_overrides.append(perm_override_doc)

        await interaction.followup.send(f"Overwrote permissions for feature `{feature}` for {scope_type} `{perm_override_doc['target_id']}` with effect `{effect}`.", ephemeral=True)
        


async def setup(bot: commands.Bot):
    await bot.add_cog(Permissions(bot))