"""
Auto Ping - ISP Network Monitoring System
Hybrid interactive mode with auto-refresh
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from google_sheets_handler import GoogleSheetsHandler
from ping_engine import PingEngine
from display_formatter import DisplayFormatter

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings


class AutoPingMonitor:
    """Main monitoring system with interactive mode"""
    
    def __init__(self):
        self.display = DisplayFormatter()
        self.sheets = GoogleSheetsHandler()
        self.ping_engine = PingEngine()
        self.current_pop = None
        self.current_clients = None
        self.last_results = None
    
    def run_ping(self, clients):
        """Execute ping for all clients"""
        progress = self.display.show_progress(len(clients))
        task = progress.add_task("[#5FAFFF]Pinging...", total=len(clients))
        
        start_time = time.time()
        
        def progress_callback(current, total):
            progress.update(task, completed=current)
        
        with progress:
            results = self.ping_engine.ping_all_sync(clients, progress_callback)
        
        elapsed_time = time.time() - start_time
        
        return results, elapsed_time
    
    def display_results(self, results, elapsed_time, pop_name):
        """Display ping results"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        up_count = sum(1 for r in results if r['status'] == 'UP')
        down_count = sum(1 for r in results if r['status'] == 'DOWN')
        
        self.display.show_monitoring_header(pop_name, up_count, down_count, timestamp)
        self.display.show_results_table(results)
        self.display.show_summary(results, elapsed_time)
    
    def interactive_menu(self):
        """Show interactive menu and handle commands"""
        self.display.show_command_menu()
        
        # Custom style for prompt
        prompt_style = Style.from_dict({
            'prompt': '#00D7FF bold',
        })
        
        while True:
            try:
                command = prompt(
                    f"\n{self.current_pop} > ",
                    style=prompt_style
                ).strip().upper()
                
                if command in ['↓', 'R', '']:
                    # Re-ping
                    return 'repinga'
                elif command == 'A':
                    # Auto-refresh mode
                    return 'auto'
                elif command == 'N':
                    # New POP
                    return 'new'
                elif command == 'Q':
                    # Quit
                    return 'quit'
                else:
                    self.display.show_warning(f"Unknown command: {command}")
                    self.display.show_info("Use: ↓/R (re-ping), A (auto-refresh), N (new POP), Q (quit)")
            
            except KeyboardInterrupt:
                return 'quit'
    
    def auto_refresh_mode(self):
        """Auto-refresh mode with countdown"""
        # Get interval
        try:
            interval_input = input(f"Auto-refresh interval (seconds) [30]: ").strip()
            interval = int(interval_input) if interval_input else 30
            
            if interval < 5:
                self.display.show_warning("Minimum interval is 5 seconds")
                interval = 5
        except ValueError:
            interval = 30
        
        print()
        self.display.show_info(f"Starting auto-refresh every {interval}s (Press Ctrl+C to stop)")
        time.sleep(2)
        
        try:
            while True:
                # Clear and show results
                self.display.clear_screen()
                
                # Run ping
                results, elapsed_time = self.run_ping(self.current_clients)
                self.last_results = results
                
                print()
                self.display_results(results, elapsed_time, self.current_pop)
                
                # Countdown
                for remaining in range(interval, 0, -1):
                    self.display.console.print(
                        f"\r[#5FAFFF]Next refresh in: [bold #FFD75F]{remaining}s[/bold #FFD75F]  "
                        f"[dim](Press Ctrl+C to stop)[/dim][/#5FAFFF]",
                        end=""
                    )
                    time.sleep(1)
                
                print("\n")
        
        except KeyboardInterrupt:
            print("\n")
            self.display.show_info("Auto-refresh stopped")
            time.sleep(1)
            
            # Show results one more time
            self.display.clear_screen()
            self.display_results(self.last_results, 0, self.current_pop)
    
    def select_pop(self):
        """Search and select a POP"""
        # Fetch available POPs
        self.display.show_info("Loading POPs from Google Sheets...")
        all_pops = self.sheets.get_all_pops()
        
        if not all_pops:
            self.display.show_error("No POPs found in Google Sheets")
            return None
        
        # Create autocomplete
        pop_completer = WordCompleter(
            all_pops,
            ignore_case=True,
            sentence=True,
            match_middle=True
        )
        
        prompt_style = Style.from_dict({
            'prompt': '#00D7FF bold',
        })
        
        print()
        
        # Get POP name with autocomplete
        pop_name = prompt(
            "🔍 Enter POP name (start typing for suggestions): ",
            completer=pop_completer,
            style=prompt_style,
            complete_while_typing=True
        ).strip()
        
        if not pop_name:
            self.display.show_warning("No POP name entered")
            return None
        
        print()
        
        # Fetch clients for selected POP
        self.display.show_info(f"Fetching clients for POP: {pop_name}")
        clients = self.sheets.get_clients_by_pop(pop_name)
        
        if not clients:
            self.display.show_error(f"No clients found for POP: {pop_name}")
            self.display.show_warning("Check if POP name is correct")
            
            # Suggest similar POPs
            similar = [p for p in all_pops if pop_name.lower() in p.lower()]
            if similar:
                print()
                self.display.console.print("[#FFD75F]Did you mean:[/#FFD75F]")
                for s in similar[:5]:
                    print(f"  • {s}")
            
            return None
        
        return pop_name, clients
    
    def run(self):
        """Main execution loop"""
        try:
            while True:
                # Select POP
                result = self.select_pop()
                if result is None:
                    return
                
                pop_name, clients = result
                self.current_pop = pop_name
                self.current_clients = clients
                
                print()
                self.display.show_header(pop_name, len(clients))
                
                # Initial ping
                self.display.show_info(f"Starting ping for {len(clients)} clients...")
                print()
                
                results, elapsed_time = self.run_ping(clients)
                self.last_results = results
                
                print()
                self.display_results(results, elapsed_time, pop_name)
                
                # Interactive loop for this POP
                while True:
                    action = self.interactive_menu()
                    
                    if action == 'repinga':
                        # Re-ping
                        self.display.clear_screen()
                        self.display.show_header(pop_name, len(clients))
                        self.display.show_info("Re-pinging...")
                        print()
                        
                        results, elapsed_time = self.run_ping(clients)
                        self.last_results = results
                        
                        print()
                        self.display_results(results, elapsed_time, pop_name)
                    
                    elif action == 'auto':
                        # Auto-refresh mode
                        self.auto_refresh_mode()
                    
                    elif action == 'new':
                        # Search new POP
                        self.display.clear_screen()
                        break
                    
                    elif action == 'quit':
                        # Exit
                        print()
                        self.display.show_success("Goodbye!")
                        return
        
        except KeyboardInterrupt:
            print("\n")
            self.display.show_info("Exiting...")
            sys.exit(0)
        
        except Exception as e:
            self.display.show_error(f"Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Entry point"""
    monitor = AutoPingMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
