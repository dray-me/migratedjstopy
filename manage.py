#!/usr/bin/env python3
"""
Discobase Manager - Python equivalent of manage.js
Project management TUI for enabling/disabling/toggling Cogs.
"""
import os
import sys
import subprocess
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import pyfiglet
import re

console = Console()

def print_banner():
    banner = pyfiglet.figlet_format("Discobase Manager", font="slant")
    console.print(Panel(Text(banner, style="bold magenta"), subtitle="[white]Project Administration (Python Version)[/white]", border_style="magenta"))

def list_cogs():
    """Lists all Cog files in the cogs/ directory."""
    cogs_dir = os.path.join(os.getcwd(), 'cogs')
    if not os.path.exists(cogs_dir):
        return []
    return [f for f in os.listdir(cogs_dir) if f.endswith('.py') and not f.startswith('__')]

def get_cog_status(filename):
    """Check if a cog is enabled or disabled."""
    file_path = os.path.join(os.getcwd(), 'cogs', filename)
    if not os.path.exists(file_path):
        return "unknown"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for disabled attribute
        match = re.search(r'^disabled\s*=\s*(True|False)', content, re.MULTILINE | re.IGNORECASE)
        if match:
            return "disabled" if match.group(1).lower() == "true" else "enabled"
        return "enabled"  # Default if no disabled attribute
    except Exception:
        return "unknown"

def toggle_cog_state(filename, disable=True):
    """Adds or modifies the 'disabled' attribute in a Cog file."""
    file_path = os.path.join(os.getcwd(), 'cogs', filename)
    if not os.path.exists(file_path):
        return False
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if 'disabled =' already exists
        if re.search(r"^disabled\s*=\s*(True|False)", content, re.MULTILINE | re.IGNORECASE):
            new_content = re.sub(
                r"^disabled\s*=\s*(True|False)",
                f"disabled = {disable}",
                content,
                flags=re.MULTILINE | re.IGNORECASE
            )
        else:
            # Insert at the top of the file before imports
            new_content = f"disabled = {disable}\n\n" + content
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return False

def open_in_editor(file_path):
    """Open file in default editor."""
    try:
        if sys.platform == 'win32':
            os.startfile(file_path)
        elif sys.platform == 'darwin':
            subprocess.call(['open', file_path])
        else:
            subprocess.call(['xdg-open', file_path])
        return True
    except Exception as e:
        console.print(f"[bold red]Error opening editor:[/bold red] {e}")
        return False

def delete_cog(filename):
    """Delete a cog file."""
    file_path = os.path.join(os.getcwd(), 'cogs', filename)
    if not os.path.exists(file_path):
        return False
    
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        console.print(f"[bold red]Error deleting file:[/bold red] {e}")
        return False

def main_menu():
    print_banner()
    
    choice = questionary.select(
        "🛠️  What would you like to do?",
        choices=[
            "📁 Manage Cogs (Commands/Events)",
            "➕ Create New (Generator)",
            "🚪 Exit"
        ]
    ).ask()
    
    if choice == "Exit" or choice is None:
        return
    elif "Create New" in choice:
        # Run the CLI generator
        import cli
        cli.main()
        return main_menu()
    elif "Manage Cogs" in choice:
        cog_menu()

def cog_menu():
    cogs = list_cogs()
    if not cogs:
        console.print("[bold yellow]⚠️ No Cogs found in the cogs/ directory.[/bold yellow]")
        return main_menu()

    # Show cogs with their status
    cog_choices = []
    for cog in cogs:
        status = get_cog_status(cog)
        status_icon = "🟢" if status == "enabled" else "🔴" if status == "disabled" else "⚪"
        cog_choices.append(questionary.Choice(f"{status_icon} {cog}", value=cog))
    
    cog_choices.append(questionary.Choice("⬅️ Back", value="back"))

    cog_choice = questionary.select(
        "📄 Select a Cog to manage:",
        choices=cog_choices
    ).ask()

    if cog_choice == "back" or cog_choice is None:
        return main_menu()

    # Get current status
    current_status = get_cog_status(cog_choice)
    
    # Build action choices based on status
    action_choices = [
        questionary.Choice("✏️ Edit", value="edit"),
    ]
    
    if current_status == "enabled":
        action_choices.append(questionary.Choice("⏸️ Pause/Disable", value="disable"))
    elif current_status == "disabled":
        action_choices.append(questionary.Choice("▶️ Resume/Enable", value="enable"))
    else:
        action_choices.append(questionary.Choice("⏸️ Pause/Disable", value="disable"))
    
    action_choices.extend([
        questionary.Choice("🗑️ Delete", value="delete"),
        questionary.Choice("⬅️ Back", value="back")
    ])

    action = questionary.select(
        f"⚙️ Action for {cog_choice}:",
        choices=action_choices
    ).ask()

    if action == "edit":
        file_path = os.path.join(os.getcwd(), 'cogs', cog_choice)
        console.print(f"[bold blue]ℹ️ Opening {cog_choice} in editor...[/bold blue]")
        if open_in_editor(file_path):
            console.print(f"[bold green]✅ Opened {cog_choice} in default editor[/bold green]")
        else:
            console.print(f"[bold yellow]⚠️ Could not open editor. File location: {file_path}[/bold yellow]")
            
    elif action == "enable":
        if toggle_cog_state(cog_choice, False):
            console.print(f"[bold green]✅ Success:[/bold green] {cog_choice} is now [bold green]ENABLED[/bold green].")
            console.print("[bold blue]ℹ️ The cog will be loaded on next bot restart or hot-reload.[/bold blue]")
        else:
            console.print(f"[bold red]❌ Failed to enable {cog_choice}[/bold red]")
            
    elif action == "disable":
        if toggle_cog_state(cog_choice, True):
            console.print(f"[bold yellow]⚠️ Success:[/bold yellow] {cog_choice} is now [bold yellow]DISABLED[/bold yellow].")
            console.print("[bold blue]ℹ️ The cog will be skipped on next bot restart or hot-reload.[/bold blue]")
        else:
            console.print(f"[bold red]❌ Failed to disable {cog_choice}[/bold red]")
            
    elif action == "delete":
        confirm = questionary.confirm(f"🗑️ Are you sure you want to delete {cog_choice}? This cannot be undone!").ask()
        if confirm:
            if delete_cog(cog_choice):
                console.print(f"[bold red]🗑️ Success:[/bold red] {cog_choice} has been deleted.")
            else:
                console.print(f"[bold red]❌ Failed to delete {cog_choice}[/bold red]")
    elif action == "back":
        pass

    # Return to cog menu
    cog_menu()

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]👋 Goodbye![/bold yellow]")
        sys.exit(0)
