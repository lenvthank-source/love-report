import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init(autoreset=True)

def log_info(message: str):
    print(f"{Fore.CYAN}[INFO]{Style.RESET_ALL} {message}")

def log_success(message: str):
    print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {message}")

def log_warning(message: str):
    print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}")

def log_error(message: str):
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")
