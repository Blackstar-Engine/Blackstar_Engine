from discord.ext import commands

class PermissionDenied(commands.CheckFailure):
    def __init__(self, reason: str = "generic"):
        self.reason = reason
        super().__init__(f"Permission denied: {reason}")