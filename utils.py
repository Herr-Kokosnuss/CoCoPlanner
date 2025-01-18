import os
import sys
import time
import threading
from threading import Event, Thread

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_centered(text: str):
    """Print text centered in terminal"""
    terminal_width = os.get_terminal_size().columns
    for line in text.split('\n'):
        print(line.center(terminal_width))

def show_progress(message="Loading"):
    """Show a progress indicator"""
    stop_event = Event()
    
    def progress_worker():
        i = 0
        spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        while not stop_event.is_set():
            sys.stdout.write(f'\r{message} {spinner[i]}')
            sys.stdout.flush()
            time.sleep(0.1)
            i = (i + 1) % len(spinner)
        sys.stdout.write('\r' + ' ' * (len(message) + 2) + '\r')
        sys.stdout.flush()

    thread = Thread(target=progress_worker)
    thread.daemon = True
    thread.start()
    
    return stop_event

def get_single_key():
    """Get a single keypress without requiring Enter"""
    try:
        import tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    except ImportError:
        import msvcrt
        return msvcrt.getch().decode() 