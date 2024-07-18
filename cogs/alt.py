import discord
from discord.ext import commands
import json
from datetime import datetime, timezone

def loadConfig():
    try:
        with open('db/alt.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def saveConfig(config):
    with open('db/alt.json', 'w') as f:
        json.dump(config, f)

class AntiAlt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = loadConfig()

    def getGuildConfig(self, guild_id):
        str_guild_id = str(guild_id)
        if str_guild_id not in self.config:
            self.config[str_guild_id] = {"enabled": False, "threshold": 30, "punishment": "kick"}
            saveConfig(self.config)
        return self.config[str_guild_id]

    def isNewUser(self, member: discord.Member):
        guild_config = self.getGuildConfig(member.guild.id)
        account_age = (datetime.now(timezone.utc) - member.created_at).days
        return account_age < guild_config['threshold']

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_config = self.getGuildConfig(member.guild.id)
        if guild_config['enabled'] and self.isNewUser(member):
            try:
                await member.send(f"{member.mention}: you've been {guild_config['punishment']}ed from **{member.guild.name}** because you don't fulfill the minimum account age requirement to join the guild.")
                if guild_config['punishment'] == 'kick':
                    await member.kick(reason=f"{self.bot.user.name} @ anti-alt triggered : potential alt acc")
                else:
                    await member.ban(reason=f"{self.bot.user.name} @ anti-alt triggered : potential alt acc")
            except Exception as e:
                print(e)

    @commands.command(name="antialt")
    @commands.has_permissions(administrator=True)
    async def antialt(self, ctx):
        view = AntiAltView(self, ctx.guild.id, ctx.author)
        embed = discord.Embed(description=">>> Navigate through the buttons below to setup and configure **Anti Alt Module** into the guild.", color=discord.Color.blurple())
        embed.set_author(name=f"Anti-Alt Setup Menu",icon_url=self.bot.user.avatar)
        embed.set_footer(text=f"Requested by {ctx.author.name}",icon_url=self.bot.user.avatar)
        await ctx.send(embed=embed, view=view)

class AntiAltView(discord.ui.View):
    def __init__(self, cog, guild_id, author):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id
        self.author = author

    async def authorCheck(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("You are not authorized to use these buttons.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Enable Anti-Alt", style=discord.ButtonStyle.green)
    async def enable(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_config = self.cog.getGuildConfig(self.guild_id)
        guild_config['enabled'] = True
        saveConfig(self.cog.config)
        await interaction.response.send_message("✅ **Enabled** Anti-Alt For This Server! ( Default Threshold : 30d )")

    @discord.ui.button(label="Disable Anti-Alt", style=discord.ButtonStyle.red)
    async def disable(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_config = self.cog.getGuildConfig(self.guild_id)
        guild_config['enabled'] = False
        saveConfig(self.cog.config)
        await interaction.response.send_message("✅ **Disabled** Anti-Alt For This Server!")

    @discord.ui.button(label="Config Anti-Alt", style=discord.ButtonStyle.blurple)
    async def config(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_config = self.cog.getGuildConfig(self.guild_id)
        status = "enabled" if guild_config['enabled'] else "disabled"
        embed = discord.Embed(color=discord.Color.blurple(), description=f"Below is the information about the config of **Anti-Alt** Module for this guild.\n- Anti-Alt : `{status}`\n- Threshold : `{guild_config['threshold']}` day(s)\n- Punishment : `{guild_config['punishment']}`")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Set Anti-Alt Threshold", style=discord.ButtonStyle.grey)
    async def set_threshold(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(Threshold(self.cog, self.guild_id))

    @discord.ui.button(label="Set Anti-Alt Punishment", style=discord.ButtonStyle.grey)
    async def set_punishment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **punishment** type:", view=PunishmentSelect(self.cog, self.guild_id), ephemeral=True)

class PunishmentSelect(discord.ui.View):
    def __init__(self, cog, guild_id):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id

    @discord.ui.select(
        placeholder="choose punishment type",
        options=[
            discord.SelectOption(label="Kick"),
            discord.SelectOption(label="Ban")
        ]
    )
    async def select_punishment(self, interaction: discord.Interaction, select: discord.ui.Select):
        guild_config = self.cog.getGuildConfig(self.guild_id)
        guild_config['punishment'] = select.values[0].lower()
        saveConfig(self.cog.config)
        await interaction.response.send_message(f"✅ Punishment type set to **{select.values[0]}** for **Anti-Alt** system.", ephemeral=True)

class Threshold(discord.ui.Modal, title="Set Threshold"):
    def __init__(self, cog, guild_id):
        super().__init__()
        self.cog = cog
        self.guild_id = guild_id
        self.threshold = discord.ui.TextInput(label="Threshold (in days)", placeholder="Enter a number between 1 and 3650", min_length=1, max_length=4)
        self.add_item(self.threshold)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            days = int(self.threshold.value)
            if 1 <= days <= 3650:
                guild_config = self.cog.getGuildConfig(self.guild_id)
                guild_config['threshold'] = days
                saveConfig(self.cog.config)
                await interaction.response.send_message(f"✅ **Anti-Alt** threshold set to **{days}** day(s).", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ **Threshold** must be set between 1 to 3650 days.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message(f"❌ Please enter a valid number.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AntiAlt(bot))
