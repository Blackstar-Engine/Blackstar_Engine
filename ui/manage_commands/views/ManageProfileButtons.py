import discord
from utils.constants import profiles, departments
from ui.manage_commands.modals.EditProfile import EditProfileModal
from ui.manage_commands.views.ConfirmRemoval import ConfirmRemovalView
from ui.manage_commands.views.ProfileManageUnits import ProfileManageUnitsView
from ui.manage_commands.views.DemoteUnit import DemoteUnitView
from utils.utils import interaction_check, fetch_unit_options

class ManageProfileButtons(discord.ui.View):
    def __init__(self, bot, user, profile, embed, options):
        super().__init__(timeout=None)
        self.bot = bot
        self.profile = profile
        self.user = user
        self.embed: discord.Embed = embed
        self.main_message: discord.Message = None

        self.dept_role_select.options = options
    
    @discord.ui.select(
        placeholder="Select a Role",
        min_values=1,
        max_values=1,
        options=[]
    )
    async def dept_role_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        value = select.values[0]

        select.values.clear()

        await interaction.edit_original_response(view=self)

        if value == "no_units":
            return
        
        department = self.profile["unit"][value]

        embed = discord.Embed(
            title="Unit Information",
            description=f"**Unit Name: ** {value}\n**Rank: ** {department.get('rank')}\n**Current Points: ** {department.get('current_points')}\n**Total Points: ** {department.get('total_points')}",
            color=discord.Color.light_grey()
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.gray, row=2)
    async def manage_profile_edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        interaction_check(self.user, interaction.user)

        modal = EditProfileModal(self.bot, self.profile, self.embed)
        await interaction.response.send_modal(modal)
        await modal.wait()

        self.profile["roblox_name"] = modal.roblox_name.value
        self.profile["timezone"] = modal.timezone.value
        self.profile["codename"] = modal.codename.value
        self.profile["status"] = modal.status.value

    @discord.ui.button(label="Manage Units", style=discord.ButtonStyle.gray, row=2)
    async def manage_profile_units(self, interaction: discord.Interaction, button: discord.ui.Button):
        interaction_check(self.user, interaction.user)

        self.profile = await profiles.find_one({"_id": self.profile["_id"]})

        results = await departments.find().to_list(length=None)

        user_units = []
        units = dict(self.profile.get("unit", {}))

        for unit, data in units.items():
            if data.get("is_active"):
                user_units.append(unit)

        user_private_units = set(self.profile.get("private_unit", []))

        normal_unit_results = []
        private_unit_results = []

        for result in results:
            unit_name = result.get("display_name")
            is_private = result.get("is_private", False)

            option = discord.SelectOption(label=unit_name)

            if is_private:
                if unit_name in user_private_units:
                    option.default = True
                private_unit_results.append(option)
            else:
                if unit_name in user_units:
                    option.default = True
                normal_unit_results.append(option)

        view = ProfileManageUnitsView(
            self.bot,
            self.profile,
            self.user,
            normal_unit_results,
            private_unit_results
        )

        embed = discord.Embed(
            title="Units Selection",
            description="Please select all units you want this user to be a part of",
            color=discord.Color.light_grey()
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await view.wait()

        # 🔄 Reload profile after submit
        self.profile = await profiles.find_one({"_id": self.profile["_id"]})

        private_units = ", ".join(self.profile.get("private_unit", [])) or ""

        self.embed.description = (
            f"**Codename:** {self.profile.get('codename')}\n"
            f"**Roblox Name:** {self.profile.get('r_name')}\n"
            f"**Timezone:** {self.profile.get('timezone')}\n"
            f"**Private Unit(s):** {private_units}\n"
            f"**Join Date:** {self.profile.get('join_date')}\n"
            f"**Status:** {self.profile.get('status').title()}"
        )

        options = fetch_unit_options(self.profile)

        manage_profile_view = ManageProfileButtons(self.bot, self.user, self.profile, self.embed, options)

        message = await self.main_message.edit(embed=self.embed, view=manage_profile_view)

        manage_profile_view.main_message = message

    @discord.ui.button(label="Demote", style=discord.ButtonStyle.blurple, row=2)
    async def demote_user_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        interaction_check(self.user, interaction.user)

        embed = discord.Embed(title="", description="Please select what department you want to demote them from!", color=discord.Color.dark_embed())
        view = DemoteUnitView(self.profile)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red, row=3)
    async def manage_profile_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        interaction_check(self.user, interaction.user)

        result = ConfirmRemovalView(self.bot, self.profile, 0)
        embed = discord.Embed(
            title="Confirm Deletion",
            description="Are you sure you would like to remove this profile?",
            color=discord.Color.yellow()
        )

        await interaction.response.send_message(embed=embed, view=result, ephemeral=True)
        await result.wait()

        if result.status == 1:
            await profiles.delete_one(self.profile)
            await self.main_message.edit(content="Profile was deleted", embed=None, view=None)
            self.stop()