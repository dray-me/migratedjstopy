#!/usr/bin/env python3
"""
Discobase CLI - Python equivalent of cli.js
Interactive project generator for Cogs, Events, and Commands with builder support.
"""
import os
import sys
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import pyfiglet

console = Console()

# Base Cog template
COG_TEMPLATE = '''import discord
from discord import app_commands
from discord.ext import commands

class {class_name}(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="{command_name}", 
        description="{description}"
    )
    async def {command_name}(self, ctx):
        """{description}"""
        await ctx.reply("Hello from your new {class_name} Cog!")

async def setup(bot):
    await bot.add_cog({class_name}(bot))
'''

# Cog template with embed builder
COG_EMBED_TEMPLATE = '''import discord
from discord import app_commands
from discord.ext import commands

class {class_name}(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="{command_name}", 
        description="{description}"
    )
    async def {command_name}(self, ctx):
        """{description}"""
        # Example: Create an embed
        embed = discord.Embed(
            title="Title",
            description="Description",
            color=discord.Color.blue()
        )
        embed.add_field(name="Field 1", value="Value 1", inline=True)
        embed.add_field(name="Field 2", value="Value 2", inline=True)
        embed.set_footer(text="Footer text")
        
        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog({class_name}(bot))
'''

# Cog template with button builder
COG_BUTTON_TEMPLATE = '''import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

class {class_name}(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="{command_name}", 
        description="{description}"
    )
    async def {command_name}(self, ctx):
        """{description}"""
        # Example: Create a button
        button = Button(
            label="Click Me",
            style=discord.ButtonStyle.primary,
            custom_id="button_id"
        )
        
        async def button_callback(interaction):
            await interaction.response.send_message("Button clicked!", ephemeral=True)
        
        button.callback = button_callback
        
        view = View()
        view.add_item(button)
        
        await ctx.reply("Message with button:", view=view)

async def setup(bot):
    await bot.add_cog({class_name}(bot))
'''

# Cog template with select menu builder
COG_SELECT_TEMPLATE = '''import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View

class {class_name}(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="{command_name}", 
        description="{description}"
    )
    async def {command_name}(self, ctx):
        """{description}"""
        # Example: Create a select menu
        select = Select(
            placeholder="Make a selection",
            options=[
                discord.SelectOption(label="Option 1", value="option1", description="Description 1"),
                discord.SelectOption(label="Option 2", value="option2", description="Description 2"),
                discord.SelectOption(label="Option 3", value="option3", description="Description 3"),
            ],
            custom_id="select_id"
        )
        
        async def select_callback(interaction):
            await interaction.response.send_message(f"You selected: {select.values[0]}", ephemeral=True)
        
        select.callback = select_callback
        
        view = View()
        view.add_item(select)
        
        await ctx.reply("Select an option:", view=view)

async def setup(bot):
    await bot.add_cog({class_name}(bot))
'''

# Cog template with modal builder
COG_MODAL_TEMPLATE = '''import discord
from discord import app_commands
from discord.ext import commands

class {class_name}Modal(discord.ui.Modal, title="{class_name} Modal"):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.TextInput(
            label="Input Label",
            placeholder="Enter something...",
            custom_id="input_id"
        ))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"You entered: {self.children[0].value}", ephemeral=True)

class {class_name}(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="{command_name}", 
        description="{description}"
    )
    async def {command_name}(self, ctx):
        """{description}"""
        # Example: Show a modal
        modal = {class_name}Modal()
        await ctx.interaction.response.send_modal(modal)

async def setup(bot):
    await bot.add_cog({class_name}(bot))
'''

# Event template
EVENT_TEMPLATE = '''import discord
from discord.ext import commands
from core.logger import logger

class {class_name}Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def {event_name}(self, *args, **kwargs):
        """Logic for the {event_name} event."""
        logger.info(f"Event {event_name} triggered!")
        # Add your event handling logic here

async def setup(bot):
    await bot.add_cog({class_name}Event(bot))
'''

def print_banner():
    banner = pyfiglet.figlet_format("Discobase CLI", font="slant")
    console.print(Panel(Text(banner, style="bold cyan"), subtitle="[white]Project Generator (Python Version)[/white]", border_style="blue"))

def get_template(template_type, class_name, command_name, description):
    """Get the appropriate template based on builder selection."""
    templates = {
        "basic": COG_TEMPLATE,
        "embed": COG_EMBED_TEMPLATE,
        "button": COG_BUTTON_TEMPLATE,
        "select": COG_SELECT_TEMPLATE,
        "modal": COG_MODAL_TEMPLATE,
    }
    return templates.get(template_type, COG_TEMPLATE).format(
        class_name=class_name,
        command_name=command_name,
        description=description
    )

def main():
    print_banner()
    
    choice = questionary.select(
        "📂 What would you like to generate?",
        choices=[
            "Command (Hybrid Cog)",
            "Event Listener",
            "Exit"
        ]
    ).ask()
    
    if choice == "Exit" or choice is None:
        return

    name = questionary.text(f"📝 Enter the name of the {choice}:").ask()
    if not name:
        return

    description = ""
    template_type = "basic"
    
    if "Command" in choice:
        description = questionary.text("📜 Enter a description for the command:", default="A new command.").ask()
        
        # Ask about builders
        use_builders = questionary.confirm("🛠️ Do you want to use Discord.py builders in this command?").ask()
        
        if use_builders:
            builder_choice = questionary.select(
                "📦 Select a builder to include:",
                choices=[
                    questionary.Choice("EmbedBuilder", value="embed"),
                    questionary.Choice("ButtonBuilder & View", value="button"),
                    questionary.Choice("StringSelectMenuBuilder", value="select"),
                    questionary.Choice("ModalBuilder & TextInput", value="modal"),
                    questionary.Choice("None - Basic command", value="basic"),
                ]
            ).ask()
            template_type = builder_choice
        
        template = get_template(template_type, name.capitalize(), name.lower(), description)
        folder = "cogs"
    else:
        template = EVENT_TEMPLATE.format(class_name=name.capitalize(), event_name=f"on_{name.lower()}")
        folder = "cogs"

    # Create folder if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)
        console.print(f"[bold green]📁 Created folder: {folder}[/bold green]")

    file_path = os.path.join(folder, f"{name.lower()}.py")
    if os.path.exists(file_path):
        console.print(f"[bold red]❌ Error:[/bold red] File {file_path} already exists!")
        return

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(template)

    console.print(f"\n[bold green]✅ Success:[/bold green] Created {choice} at [cyan]{file_path}[/cyan]")
    
    if template_type != "basic" and "Command" in choice:
        console.print(f"[bold blue]ℹ️ Info:[/bold blue] Included {template_type} builder template")
    console.print()

if __name__ == "__main__":
    main()
