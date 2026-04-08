import pendulum
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
import pyfiglet
import os

console = Console()

class Logger:
    @staticmethod
    def success(message: str):
        Logger._log("SUCCESS", message, "green", "bold")

    @staticmethod
    def info(message: str):
        Logger._log("INFO", message, "blue", "bold")

    @staticmethod
    def warning(message: str):
        Logger._log("WARNING", message, "yellow", "bold")

    @staticmethod
    def error(message: str):
        Logger._log("ERROR", message, "red", "bold")

    @staticmethod
    def system(message: str):
        Logger._log("SYSTEM", message, "cyan", "bold")

    @staticmethod
    def _log(prefix: str, message: str, color: str, style: str = ""):
        timestamp = pendulum.now().format('HH:mm:ss')
        
        # Create a text object for the log
        text = Text()
        text.append(f"[{timestamp}] ", style="bright_black")
        text.append(f" {prefix} ", style=f"white on {color} {style}")
        text.append(" │ ", style="bright_black")
        text.append(message, style=color)
        
        console.print(text)

    @staticmethod
    def print_banner():
        # Generate ASCII Art
        banner_text = pyfiglet.figlet_format("Discobase", font="slant")
        
        # Create a stylized panel for the banner
        panel = Panel(
            Text(banner_text, style="bold cyan"),
            subtitle="[bold white]The Ultimate Discord Bot Toolkit (Python Reborn)[/bold white]",
            subtitle_align="center",
            border_style="bright_magenta",
            expand=False
        )
        
        console.print("\n")
        console.print(panel)
        console.print("\n")

    @staticmethod
    def section_header(title: str, icon: str, color: str):
        table = Table.grid(expand=True)
        table.add_column(justify="center")
        
        header_text = Text()
        header_text.append(f" {icon} ", style=f"bold {color}")
        header_text.append(title.upper(), style=f"bold {color}")
        header_text.append(f" {icon} ", style=f"bold {color}")
        
        console.print("\n")
        console.print(Panel(header_text, border_style="bright_black", padding=(1, 5)))
        console.print("\n")

# Global logger instance
logger = Logger()
