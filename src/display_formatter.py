"""
Display Formatter
Handles terminal output formatting with Corporate Blue color scheme
"""

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich import box
from rich.text import Text
from typing import List, Dict
import yaml
from datetime import datetime


class DisplayFormatter:
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize display formatter with Corporate Blue theme"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['display']
        
        self.console = Console()
        
        # Corporate Blue Color Palette
        self.colors = {
            'header': '#00D7FF',           # Bright Cyan
            'up': '#5FD75F',               # Soft Green
            'down': '#D75F5F',             # Muted Red
            'client_name': '#D0D0D0',      # Light Gray
            'ip': '#87AFFF',               # Sky Blue
            'border': '#585858',           # Dark Gray
            'info': '#5FAFFF',             # Bright Blue
            'warning': '#FFD75F',          # Soft Yellow
            'error': '#FF5F5F',            # Soft Red
            'success': '#5FD787',          # Mint Green
            'command': '#AF87FF',          # Soft Purple
            'timestamp': '#87D7D7',        # Aqua
        }
    
    def show_header(self, pop_name: str, client_count: int, timestamp: str = None):
        """Display header with POP information"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%H:%M:%S")
        
        header_text = Text()
        header_text.append("📡 Network Monitor\n", style=f"bold {self.colors['header']}")
        header_text.append(f"POP: ", style=self.colors['info'])
        header_text.append(f"{pop_name}\n", style=f"bold {self.colors['header']}")
        header_text.append(f"Clients: ", style=self.colors['info'])
        header_text.append(f"{client_count}", style="bold white")
        header_text.append(f"  •  Last Update: ", style=self.colors['info'])
        header_text.append(timestamp, style=self.colors['timestamp'])
        
        panel = Panel(
            header_text,
            box=box.DOUBLE,
            border_style=self.colors['border'],
            padding=(1, 2)
        )
        self.console.print(panel)
        self.console.print()
    
    def show_monitoring_header(self, pop_name: str, up_count: int, down_count: int, timestamp: str):
        """Display monitoring header with status summary"""
        header_text = Text()
        header_text.append("🔄 Monitoring: ", style=self.colors['info'])
        header_text.append(f"{pop_name}\n", style=f"bold {self.colors['header']}")
        header_text.append(f"Last Update: ", style=self.colors['info'])
        header_text.append(f"{timestamp}", style=self.colors['timestamp'])
        header_text.append(f"  •  ", style="dim")
        header_text.append(f"UP: ", style=self.colors['success'])
        header_text.append(f"{up_count}", style=f"bold {self.colors['up']}")
        header_text.append(f"  •  ", style="dim")
        header_text.append(f"DOWN: ", style=self.colors['error'])
        header_text.append(f"{down_count}", style=f"bold {self.colors['down']}")
        
        panel = Panel(
            header_text,
            box=box.ROUNDED,
            border_style=self.colors['header'],
            padding=(0, 2)
        )
        self.console.print(panel)
        self.console.print()
    
    def show_progress(self, total: int):
        """Create and return a progress bar"""
        return Progress(
            SpinnerColumn(style=self.colors['info']),
            TextColumn("[progress.description]{task.description}", style=self.colors['info']),
            BarColumn(complete_style=self.colors['success'], finished_style=self.colors['up']),
            TaskProgressColumn(style=self.colors['info']),
            console=self.console
        )
    
    def show_results_table(self, results: List[Dict[str, any]]):
        """Display results in a formatted table with Corporate Blue theme"""
        table = Table(
            box=box.SIMPLE_HEAVY,
            show_header=True,
            header_style=f"bold {self.colors['header']}",
            border_style=self.colors['border']
        )
        
        table.add_column("No.", style="dim white", width=6, justify="right")
        table.add_column("Client Name", style=self.colors['client_name'], width=40)
        table.add_column("Base IP", style=self.colors['ip'], width=18)
        table.add_column("Status", width=10, justify="center")
        table.add_column("Latency", width=12, justify="right")
        
        for idx, result in enumerate(results, 1):
            status = result['status']
            
            # Colorize status
            if status == 'UP':
                status_text = f"[{self.colors['up']}]🟢 UP[/{self.colors['up']}]"
            elif status == 'DOWN':
                status_text = f"[{self.colors['down']}]🔴 DOWN[/{self.colors['down']}]"
            else:
                status_text = f"[{self.colors['warning']}]⚠️  ERR[/{self.colors['warning']}]"
            
            # Latency formatting
            latency = result.get('latency')
            if latency is not None:
                if latency < 50:
                    latency_text = f"[{self.colors['success']}]{latency} ms[/{self.colors['success']}]"
                elif latency < 100:
                    latency_text = f"[{self.colors['warning']}]{latency} ms[/{self.colors['warning']}]"
                else:
                    latency_text = f"[{self.colors['error']}]{latency} ms[/{self.colors['error']}]"
            else:
                latency_text = f"[dim]-[/dim]"
            
            table.add_row(
                str(idx),
                result['client_name'][:38],
                result['ip_address'],
                status_text,
                latency_text
            )
        
        self.console.print(table)
    
    def show_summary(self, results: List[Dict[str, any]], elapsed_time: float):
        """Display summary statistics"""
        total = len(results)
        up_count = sum(1 for r in results if r['status'] == 'UP')
        down_count = sum(1 for r in results if r['status'] == 'DOWN')
        error_count = sum(1 for r in results if r['status'] == 'ERROR')
        
        summary = Text()
        summary.append("✓ UP: ", style=self.colors['success'])
        summary.append(f"{up_count}", style=f"bold {self.colors['up']}")
        summary.append("  |  ", style="dim")
        summary.append("✗ DOWN: ", style=self.colors['error'])
        summary.append(f"{down_count}", style=f"bold {self.colors['down']}")
        
        if error_count > 0:
            summary.append("  |  ", style="dim")
            summary.append("⚠ ERROR: ", style=self.colors['warning'])
            summary.append(f"{error_count}", style=f"bold {self.colors['warning']}")
        
        summary.append("  |  ", style="dim")
        summary.append("⏱ Time: ", style=self.colors['info'])
        summary.append(f"{elapsed_time:.1f}s", style=f"bold {self.colors['timestamp']}")
        
        panel = Panel(
            summary,
            box=box.ROUNDED,
            border_style=self.colors['success'] if down_count == 0 else self.colors['warning'],
            padding=(0, 2)
        )
        
        self.console.print()
        self.console.print(panel)
    
    def show_command_menu(self):
        """Display interactive command menu"""
        menu = Text()
        menu.append("Commands: ", style=f"bold {self.colors['header']}")
        menu.append("\n")
        menu.append("  ↓ or R", style=f"bold {self.colors['command']}")
        menu.append(" - Re-ping now\n", style=self.colors['client_name'])
        menu.append("  A", style=f"bold {self.colors['command']}")
        menu.append(" - Auto-refresh mode\n", style=self.colors['client_name'])
        menu.append("  N", style=f"bold {self.colors['command']}")
        menu.append(" - Search new POP\n", style=self.colors['client_name'])
        menu.append("  Q", style=f"bold {self.colors['command']}")
        menu.append(" - Quit", style=self.colors['client_name'])
        
        panel = Panel(
            menu,
            box=box.ROUNDED,
            border_style=self.colors['info'],
            padding=(0, 2)
        )
        
        self.console.print()
        self.console.print(panel)
    
    def show_auto_refresh_header(self, pop_name: str, interval: int, next_refresh: int):
        """Display auto-refresh mode header"""
        header = Text()
        header.append("🔄 Auto-Refresh: ", style=f"bold {self.colors['success']}")
        header.append(f"{pop_name}\n", style=f"bold {self.colors['header']}")
        header.append(f"Interval: ", style=self.colors['info'])
        header.append(f"{interval}s", style="bold white")
        header.append(f"  •  Next refresh: ", style=self.colors['info'])
        header.append(f"{next_refresh}s", style=f"bold {self.colors['warning']}")
        header.append(f"\nPress ", style="dim")
        header.append("Ctrl+C", style=f"bold {self.colors['command']}")
        header.append(" to stop", style="dim")
        
        panel = Panel(
            header,
            box=box.DOUBLE,
            border_style=self.colors['success'],
            padding=(0, 2)
        )
        
        self.console.print(panel)
        self.console.print()
    
    def clear_screen(self):
        """Clear the terminal screen"""
        self.console.clear()
    
    def show_error(self, message: str):
        """Display error message"""
        self.console.print(f"[{self.colors['error']}]❌ {message}[/{self.colors['error']}]")
    
    def show_warning(self, message: str):
        """Display warning message"""
        self.console.print(f"[{self.colors['warning']}]⚠️  {message}[/{self.colors['warning']}]")
    
    def show_success(self, message: str):
        """Display success message"""
        self.console.print(f"[{self.colors['success']}]✓ {message}[/{self.colors['success']}]")
    
    def show_info(self, message: str):
        """Display info message"""
        self.console.print(f"[{self.colors['info']}]ℹ {message}[/{self.colors['info']}]")

