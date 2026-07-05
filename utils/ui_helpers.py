import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.status import Status
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from .ansi_colors import fg, style

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title, subtitle=""):
    console.print(Panel(f"[bold cyan]{subtitle}[/]", title=f"[bold yellow]{title}[/]"))

def menu_prompt(prompt_text, valid_range=None):
    while True:
        choice = console.input(f"[bold yellow]{prompt_text}[/]: ")
        try:
            val = int(choice)
            if valid_range is None or val in valid_range:
                return val
            console.print("[red]Invalid selection.[/red]")
        except ValueError:
            console.print("[red]Please enter a number.[/red]")

def confirm(question):
    answer = console.input(f"[bold yellow]{question} (y/n)[/]: ").lower()
    return answer.startswith('y')

def wait_for_enter():
    console.input(f"\n[dim]Press Enter to continue...[/dim]")

# Integration für Fortschritt und Status
def show_progress(iterable, description="Processing..."):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description, total=len(iterable))
        for item in iterable:
            yield item
            progress.advance(task)

class SimpleProgressBar:
    def __init__(self, total, description="Progress"):
        self.progress = Progress()
        self.task = self.progress.add_task(description, total=total)
        self.progress.start()

    def update(self, n=1):
        self.progress.update(self.task, advance=n)

    def close(self):
        self.progress.stop()

def show_menu_generic(title_key, subtitle_key, options, device_manager, adb):
    """
    Renders a generic menu in the terminal using i18n keys.
    :param title_key: i18n key for the title
    :param subtitle_key: i18n key for the subtitle
    :param options: list of tuples (emoji, label_key, callback)
    :param device_manager: DeviceManager instance
    :param adb: ADBHandler instance
    """
    from utils.i18n import get_text
    while True:
        clear_screen()
        print_header(get_text(title_key), get_text(subtitle_key))
        
        for i, (emoji, label_key, _) in enumerate(options, 1):
            print(f"{i:2d}. {emoji} {get_text(label_key)}")
        print(" 0. ❌ " + get_text("back"))
        
        choice = menu_prompt(get_text("choose_option"), range(0, len(options) + 1))
        if choice == 0:
            break
        else:
            callback = options[choice - 1][2]
            try:
                callback(device_manager, adb)
            except Exception as e:
                console.print(f"[red]Fehler bei der Ausführung: {e}[/red]")
                wait_for_enter()

