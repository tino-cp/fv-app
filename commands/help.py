import discord
from discord.ext import commands
from discord.ui import View, Button

class JumpButton(Button):
    def __init__(self, page_index, label, parent_view, row):
        super().__init__(label=label, style=discord.ButtonStyle.primary, row=row)
        self.page_index = page_index
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.parent_view.ctx.author:
            await interaction.response.send_message("You're not allowed to control this help menu.", ephemeral=True)
            return

        self.parent_view.current_page = self.page_index
        self.parent_view.update_buttons()
        await interaction.response.edit_message(embed=self.parent_view.pages[self.page_index], view=self.parent_view)

class HelpView(View):
    def __init__(self, ctx, pages, section_labels, timeout=120):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.pages = pages
        self.section_labels = section_labels
        self.current_page = 0
        self.message = None
        self.update_buttons()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)
            await self.ctx.send("Help menu timed out to save memory. Use `!help` again to reopen.", delete_after=10)

    def update_buttons(self):
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.pages) - 1

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, row=0)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("You're not allowed to control this help menu.", ephemeral=True)
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("You're not allowed to control this help menu.", ephemeral=True)
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    # Dynamically add jump buttons for each page
    def add_jump_buttons(self):
        for idx, label in enumerate(self.section_labels):
            short_label = f"{idx+1} - {label[:10]}"
            row = (idx // 5) + 1
            self.add_item(JumpButton(idx, short_label, self, row))


@commands.command(name="help", aliases=['h'])
async def show_help(ctx):
    sections = [
        (
            "General",
            "`!regs` - Link to regulations\n"
            "`!df` - Downforce settings\n"
            "`!lapchecks` - Roll lap-check chances\n"
            "`!fastestLap (track)` - Fastest lap on selected track\n"
            "`!lapCount (time)` / `!lc (time)` - Lap count for a set time",
            "General"
        ),
        (
            "Weather & Race",
            "`!race <league> <round>` - Race start weather\n"
            "`!weather` - Live conditions\n"
            "`!rain` - Rain forecast (5 intervals)",
            "Weather"
        ),
        (
            "Results",
            "`!results <race>` - Race results summary\n"
            "Examples: `!results F1_R1`, `!results F2_R3`\n"
            "`!standings <F1><c>` - Standings (c for constructor)\n"
            "Example: `!standings F2c`",
            "Results"
        ),
        (
            "Penalty Points",
            "`!pp [league]` - Driver penalty points\n"
            "`!lw [league]` - Lag warnings\n"
            "`!rep [league]` - Reprimands\n"
            "`!pens` - Summary of all penalties across leagues",
            "Penalty records"
        ),
        (
            "Trainee Stewards",
            "`!suggestion <reason>` - Suggest a penalty\n"
            "`!approve` - Approve suggestion\n"
            "`!deny` - Deny suggestion\n"
            "`!listSuggestions` - Export all suggestions",
            "Trainee stewards"
        ),
        (
            "Protests",
            "`!protest <team>` - File a protest\n"
            "`!protests` - Check protest count\n"
            "`!revertProtest <team>` - Revert a protest",
            "Protests"
        ),
        (
            "FIA Penalties",
            "`!rpo [sprint]` - Start timer (60/90min)\n"
            "`!cancel` - Cancel timer\n"
            "`!pen sug`, `!pen pov <name>` - Rename thread\n"
            "`!pen <type> <name> <reason>` - Apply verdict",
            "Concluding penalties"
        ),
        (
            "Logs",
            "`!pen getLogs`, `!pen clearLogs` - Logs\n"
            "`!pen filterLogs`, `!pen sortLogs` - Organize logs",
            "Logs"
        ),
        (
            "Attendance",
            "`!RA <track>` - Standard attendance form\n"
            "`!RAFVEC` - Vector GP attendance\n"
            "`!RAMOTOVGP` - Motov GP attendance\n"
            "`!reset F1/F2` - Reset league attendance",
            "Attendance"
        ),
    ]

    pages = []
    labels = []

    for index, (title, content, button_label) in enumerate(sections, 1):
        embed = discord.Embed(
            title=f"Bot Help – {title} ({index}/{len(sections)})",
            description=content,
            color=discord.Color.gold()
        )
        embed.set_footer(text="Menu will time out after 2 minutes")
        pages.append(embed)
        labels.append(button_label)

    view = HelpView(ctx, pages, labels)
    view.add_jump_buttons()
    view.message = await ctx.send(embed=pages[0], view=view)
