#!/usr/bin/python3

import os
import sys
import requests
import urllib3
import random
import time
import json
import telebot
import sqlite3
from telebot import TeleBot
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs, urlencode, urlunsplit, quote, urlsplit
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from colorama import Fore, Style, init
from prompt_toolkit import prompt, PromptSession
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.shortcuts import radiolist_dialog, button_dialog
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.text import Text
from rich.style import Style as RichStyle
from queue import Queue
from threading import Lock
import logging
from datetime import datetime, timedelta
import re
import threading

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger('WDM').setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize colorama
init(autoreset=True)

# Custom color definitions
VENUS_COLORS = {
    'primary': '\033[38;2;255;105;180m',  # Hot Pink
    'secondary': '\033[38;2;147;112;219m',  # Medium Purple
    'success': '\033[38;2;50;205;50m',  # Lime Green
    'warning': '\033[38;2;255;215;0m',  # Gold
    'error': '\033[38;2;255;69;0m',  # Red-Orange
    'info': '\033[38;2;135;206;250m',  # Light Sky Blue
    'reset': '\033[0m'
}

# User agents for requests
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
]

class VenusXSS:
    def __init__(self):
        self.console = Console()
        self.driver_pool = Queue()
        self.driver_lock = Lock()
        self.bot_token = "7950078899:AAFIfRbMwkQvAh11fahmC6i9mntWRJSlpdc"
        self.bot = TeleBot(self.bot_token)
        self.chat_id = None

        # Set up bot commands in menu
        try:
            commands = [
                telebot.types.BotCommand("start", "Start the bot and get welcome message"),
                telebot.types.BotCommand("id", "Get your Chat ID for XSS notifications")
            ]
            self.bot.set_my_commands(commands)
        except Exception as e:
            self.print_status(f"Failed to set bot commands: {str(e)}", "warning")

        # Import additional webdriver managers
        from webdriver_manager.firefox import GeckoDriverManager
        from webdriver_manager.microsoft import EdgeChromiumDriverManager

        # Add Telegram bot command handlers
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            welcome_text = (
                "🌟 <b>Welcome to Venus XSS Scanner Bot!</b>\n\n"
                "I will send you:\n"
                "✅ Real-time XSS notifications\n"
                "📊 Scan progress updates\n"
                "📝 Final vulnerability reports\n\n"
                "Use these commands:\n"
                "/start - Show this welcome message\n"
                "/id - Get your Chat ID for notifications"
            )
            try:
                # Send welcome message with custom keyboard
                markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add(
                    telebot.types.KeyboardButton("/start"),
                    telebot.types.KeyboardButton("/id")
                )
                self.bot.reply_to(message, welcome_text, parse_mode='HTML', reply_markup=markup)
            except Exception as e:
                self.print_status(f"Error in welcome message: {str(e)}", "error")

        @self.bot.message_handler(commands=['id'])
        def send_chat_id(message):
            chat_id = message.chat.id
            try:
                response_text = (
                    "🆔 <b>Your Chat ID:</b>\n\n"
                    f"<code>{chat_id}</code>\n\n"
                    "Copy this ID and paste it in the Venus XSS Scanner when prompted to receive:\n"
                    "• Real-time vulnerability notifications\n"
                    "• Scan progress updates\n"
                    "• Final scan reports"
                )
                self.bot.reply_to(message, response_text, parse_mode='HTML')
            except Exception as e:
                self.print_status(f"Error sending chat ID: {str(e)}", "error")

        # Start the bot in a separate thread
        bot_thread = threading.Thread(target=self.bot.polling, daemon=True)
        bot_thread.start()

        self.scan_state = {
            'vulnerability_found': False,
            'vulnerable_urls': [],
            'total_found': 0,
            'total_scanned': 0,
            'scan_start_time': None,
            'scan_end_time': None,
            'error_count': 0,
            'warnings': []
        }
        self.report_data = {
            'scan_date': None,
            'targets': [],
            'findings': [],
            'statistics': {}
        }

        # Initialize webdriver pool
        try:
            self.setup_webdriver_pool()
        except Exception as e:
            self.print_status(f"Warning: Failed to initialize default webdriver pool: {str(e)}", "warning")

    def __del__(self):
        """Cleanup method to ensure all drivers are properly closed"""
        self.cleanup_drivers()

    def show_bot_info(self):
        """Display bot information to the user"""
        print(f"\n{VENUS_COLORS['primary']}╭─ Telegram Notifications ─────────────────────────────╮")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}To receive scan results and notifications:")
        print(f"{VENUS_COLORS['primary']}│")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}1. Open Telegram and search: {VENUS_COLORS['secondary']}@VenusXSS_bot")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}2. Start the bot with {VENUS_COLORS['secondary']}/start")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}3. Get your Chat ID with {VENUS_COLORS['secondary']}/id")
        print(f"{VENUS_COLORS['primary']}│")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}You'll receive:")
        print(f"{VENUS_COLORS['primary']}│ • Real-time vulnerability notifications")
        print(f"{VENUS_COLORS['primary']}│ • Scan progress updates")
        print(f"{VENUS_COLORS['primary']}│ • Final scan reports")
        print(f"{VENUS_COLORS['primary']}╰───────────────────────────────────────────────────────╯")

    def set_chat_id(self, chat_id):
        """Set the chat ID for notifications"""
        if chat_id and chat_id.isdigit():
            self.chat_id = chat_id
            try:
                self.bot.send_message(
                    chat_id,
                    "✅ <b>Connected to Venus XSS Scanner!</b>\n\nYou will now receive scan notifications.",
                    parse_mode='HTML'
                )
                return True
            except Exception as e:
                self.print_status(f"Failed to send test message: {str(e)}", "error")
                return False
        return False

    def main(self):
        self.display_intro()
        self.show_bot_info()

        # Ask for chat ID
        print(f"\n{VENUS_COLORS['primary']}╭─ Setup ────────────────────────────────────────────╮")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Enter your Telegram Chat ID to receive notifications")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}(or press Enter to skip)")
        print(f"{VENUS_COLORS['primary']}╰───────────────────────────────────────────────────────╯")

        chat_id = input(f"{VENUS_COLORS['secondary']}➜ Chat ID (optional): {VENUS_COLORS['reset']}")
        if chat_id:
            if self.set_chat_id(chat_id):
                self.print_status("Telegram notifications enabled!", "success")
            else:
                self.print_status("Invalid Chat ID. Continuing without notifications.", "warning")
        else:
            self.print_status("Continuing without Telegram notifications.", "info")

        urls = self.prompt_for_urls()
        payload_file = self.prompt_for_valid_file_path("Enter payload file path: ")
        timeout = self.show_timeout_menu()

        self.clear_screen()
        self.print_status("Starting scan...", "info")
        if self.chat_id:
            self.send_telegram_message("🚀 Starting new XSS scan...")

        all_vulnerable_urls = []
        total_scanned = 0
        self.scan_state['scan_start_time'] = time.time()
        total_urls = len(urls)
        payloads = self.load_payloads(payload_file)
        total_combinations = len(urls) * len(payloads)
        scanned_combinations = 0
        start_time = time.time()

        print(f"\n{VENUS_COLORS['primary']}╭─ Scan Progress ─────────────────────────────────────╮")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Total URLs to scan: {VENUS_COLORS['secondary']}{total_urls}")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Total payloads: {VENUS_COLORS['secondary']}{len(payloads)}")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Total combinations: {VENUS_COLORS['secondary']}{total_combinations}")
        print(f"{VENUS_COLORS['primary']}╰───────────────────────────────────────────────────────╯\n")

        try:
            for url in urls:
                self.print_scanning_url(url)
                vulnerable_urls, scanned = self.run_scan([url], payload_file, timeout)
                all_vulnerable_urls.extend(vulnerable_urls)
                total_scanned += scanned
                scanned_combinations += len(payloads)
                
                # Calculate progress and time estimates
                progress = (scanned_combinations / total_combinations) * 100
                remaining_urls = total_urls - (scanned_combinations // len(payloads))
                elapsed_time = time.time() - start_time
                avg_time_per_url = elapsed_time / (scanned_combinations / len(payloads)) if scanned_combinations > 0 else 0
                estimated_remaining_time = avg_time_per_url * remaining_urls

                # Create progress bar
                bar_width = 40
                filled = int(progress * bar_width / 100)
                bar = f"[{'=' * filled}{' ' * (bar_width - filled)}]"

                # Print progress information
                print(f"\r{VENUS_COLORS['primary']}Progress: {VENUS_COLORS['info']}{bar} {progress:.1f}%", end='')
                print(f" | {VENUS_COLORS['info']}URLs: {scanned_combinations//len(payloads)}/{total_urls}", end='')
                print(f" | {VENUS_COLORS['success']}Found: {len(all_vulnerable_urls)}", end='')
                print(f" | {VENUS_COLORS['warning']}ETA: {int(estimated_remaining_time)}s{VENUS_COLORS['reset']}    ", end='')
                sys.stdout.flush()

                # Print detailed status every 5 URLs
                if scanned_combinations % (len(payloads) * 5) == 0:
                    print(f"\n{VENUS_COLORS['info']}Detailed Status:")
                    print(f"├─ Scanned URLs: {scanned_combinations//len(payloads)}/{total_urls}")
                    print(f"├─ Vulnerabilities found: {len(all_vulnerable_urls)}")
                    print(f"├─ Elapsed time: {int(elapsed_time)}s")
                    print(f"└─ Estimated time remaining: {int(estimated_remaining_time)}s\n")

        except KeyboardInterrupt:
            print("\n")  # Add newline for clean display
            self.print_status("Scan interrupted by the user.", "error")
            if self.chat_id:
                self.send_telegram_message("⚠️ Scan interrupted by user.")
            self.print_scan_summary(self.scan_state['total_found'], total_scanned, self.scan_state['scan_start_time'])
            sys.exit()

        print("\n")  # Add newline for clean display
        scan_duration = int(time.time() - self.scan_state['scan_start_time'])
        self.scan_state['scan_end_time'] = time.time()

        report_file = self.generate_report(all_vulnerable_urls, total_scanned)
        self.print_scan_summary(self.scan_state['total_found'], total_scanned, self.scan_state['scan_start_time'])
        self.print_status(f"Scan report saved to: {report_file}", "success")

        if self.chat_id:
            summary_msg = (
                "🏁 <b>Scan Completed</b>\n\n"
                f"📊 Results:\n"
                f"• URLs Scanned: {total_scanned}\n"
                f"• Vulnerabilities Found: {len(all_vulnerable_urls)}\n"
                f"• Duration: {scan_duration} seconds\n"
                f"• Errors: {self.scan_state['error_count']}"
            )
            self.send_telegram_message(summary_msg)
        else:
            self.print_status("\nTip: Start @VenusXSS_bot on Telegram to receive notifications next time!", "info")

        sys.exit()

    def display_intro(self):
        self.clear_screen()

        # Modern banner design
        banner = """
╭──────────────────────────────────────────────────╮
│                                                  │
│  ██╗   ██╗███████╗███╗   ██╗██╗   ██╗███████╗  │
│  ██║   ██║██╔════╝████╗  ██║██║   ██║██╔════╝  │
│  ██║   ██║█████╗  ██╔██╗ ██║██║   ██║███████╗  │
│  ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║██║   ██║╚════██║  │
│   ╚████╔╝ ███████╗██║ ╚████║╚██████╔╝███████║  │
│    ╚═══╝  ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝  │
│                                                  │
╰──────────────────────────────────────────────────╯
"""

        # Print banner with gradient effect
        for line in banner.split('\n'):
            if '█' in line:
                print(f"{VENUS_COLORS['primary']}{line}{VENUS_COLORS['reset']}")
            else:
                print(f"{VENUS_COLORS['secondary']}{line}{VENUS_COLORS['reset']}")

        # Print subtitle with animation effect
        subtitle = "Advanced XSS Vulnerability Scanner"
        print(f"\n{VENUS_COLORS['info']}{' ' * ((80 - len(subtitle)) // 2)}{subtitle}{VENUS_COLORS['reset']}\n")

        # Print version and author info
        version_info = "Version 1.0 | Developed by Venus Security"
        print(f"{VENUS_COLORS['secondary']}{' ' * ((80 - len(version_info)) // 2)}{version_info}{VENUS_COLORS['reset']}\n")

    def print_status(self, message, status_type="info"):
        status_icons = {
            "info": "ℹ",
            "success": "✓",
            "warning": "⚠",
            "error": "✗"
        }
        color = VENUS_COLORS[status_type]
        icon = status_icons.get(status_type, "ℹ")
        print(f"{color}[{icon}] {message}{VENUS_COLORS['reset']}")

    def print_vulnerability(self, url, alert_text):
        print(f"\n{VENUS_COLORS['success']}╭─ Vulnerability Found ────────────────────────────────╮")
        print(f"{VENUS_COLORS['success']}│ {VENUS_COLORS['info']}URL: {VENUS_COLORS['secondary']}{url}")
        print(f"{VENUS_COLORS['success']}│ {VENUS_COLORS['info']}Alert: {VENUS_COLORS['secondary']}{alert_text}")
        print(f"{VENUS_COLORS['success']}╰───────────────────────────────────────────────────────╯{VENUS_COLORS['reset']}\n")

        # Send to Telegram
        message = f"🔥 <b>XSS Vulnerability Found!</b>\n\n"
        message += f"🌐 <b>URL:</b> <code>{url}</code>\n"
        message += f"⚠️ <b>Alert:</b> <code>{alert_text}</code>"
        self.send_telegram_message(message)

    def print_scanning_url(self, url):
        response_code = self.check_url_response(url)
        status_color = {
            200: VENUS_COLORS['success'],
            301: VENUS_COLORS['warning'],
            302: VENUS_COLORS['warning'],
            403: VENUS_COLORS['error'],
            404: VENUS_COLORS['error'],
            500: VENUS_COLORS['error'],
            'default': VENUS_COLORS['info']
        }
        
        status_text = {
            200: "OK",
            301: "Moved Permanently",
            302: "Found/Redirect",
            403: "Forbidden",
            404: "Not Found",
            500: "Server Error",
            'default': "Unknown"
        }

        # Get color and text based on response code
        if isinstance(response_code, int):
            color = status_color.get(response_code, status_color['default'])
            status = status_text.get(response_code, str(response_code))
        else:
            color = VENUS_COLORS['error']
            status = str(response_code)

        print(f"\n{VENUS_COLORS['primary']}╭─ Scanning ───────────────────────────────────────────╮")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Target: {VENUS_COLORS['secondary']}{url}")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Status: {color}{status} ({response_code if isinstance(response_code, int) else 'Error'})")
        print(f"{VENUS_COLORS['primary']}╰───────────────────────────────────────────────────────╯{VENUS_COLORS['reset']}\n")

        # Send to Telegram if enabled
        if self.chat_id:
            status_emoji = "✅" if isinstance(response_code, int) and response_code == 200 else "⚠️"
            message = f"{status_emoji} <b>Scanning URL</b>\n\n"
            message += f"🌐 <b>URL:</b> <code>{url}</code>\n"
            message += f"📊 <b>Status:</b> <code>{status} ({response_code if isinstance(response_code, int) else 'Error'})</code>"
            self.send_telegram_message(message)

    def print_scan_summary(self, total_found, total_scanned, start_time):
        print(f"\n{VENUS_COLORS['primary']}╭─ Scan Summary ───────────────────────────────────────╮")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Vulnerabilities Found: {VENUS_COLORS['success']}{total_found}")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}URLs Scanned: {VENUS_COLORS['secondary']}{total_scanned}")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Scan Duration: {VENUS_COLORS['secondary']}{int(time.time() - start_time)} seconds")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Errors: {VENUS_COLORS['error']}{self.scan_state['error_count']}")

        if self.scan_state['warnings']:
            print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Warnings: {VENUS_COLORS['warning']}{len(self.scan_state['warnings'])}")
            print(f"{VENUS_COLORS['primary']}╰─ Warnings ───────────────────────────────────────────╯")
            for warning in self.scan_state['warnings']:
                print(f"{VENUS_COLORS['warning']}  • {warning}")
        else:
            print(f"{VENUS_COLORS['primary']}╰───────────────────────────────────────────────────────╯{VENUS_COLORS['reset']}")

    def check_url_response(self, url):
        """Check URL response code before scanning"""
        try:
            headers = {'User-Agent': self.get_random_user_agent()}
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            return response.status_code
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"

    def check_vulnerability(self, url, payload, vulnerable_urls, total_scanned, timeout):
        driver = self.get_driver()
        try:
            payload_urls = self.generate_payload_urls(url, payload)
            if not payload_urls:
                return

            for payload_url in payload_urls:
                try:
                    # Check response code before testing payload
                    response_code = self.check_url_response(payload_url)
                    if isinstance(response_code, str):  # Error occurred
                        self.print_status(f"Error accessing {payload_url}: {response_code}", "error")
                        continue
                    elif response_code >= 400:  # Client or Server Error
                        self.print_status(f"Skipping {payload_url} - Response code: {response_code}", "warning")
                        continue

                    driver.get(payload_url)
                    total_scanned[0] += 1

                    try:
                        alert = WebDriverWait(driver, timeout).until(EC.alert_is_present())
                        alert_text = alert.text

                        if alert_text:
                            self.print_vulnerability(payload_url, alert_text)
                            vulnerable_urls.append({
                                'url': payload_url,
                                'payload': payload,
                                'alert_text': alert_text,
                                'response_code': response_code,
                                'timestamp': datetime.now().isoformat()
                            })
                            self.scan_state['vulnerability_found'] = True
                            self.scan_state['vulnerable_urls'].append(payload_url)
                            self.scan_state['total_found'] += 1
                            alert.accept()
                        else:
                            self.print_status(f"Not Vulnerable: {payload_url} (Status: {response_code})", "info")

                    except TimeoutException:
                        self.print_status(f"Not Vulnerable: {payload_url} (Status: {response_code})", "info")

                except UnexpectedAlertPresentException:
                    pass
                except WebDriverException as e:
                    self.scan_state['warnings'].append(f"WebDriver error for {payload_url}: {str(e)}")
        finally:
            self.return_driver(driver)

    def get_random_user_agent(self):
        return random.choice(USER_AGENTS)

    def create_driver(self):
        """Create a WebDriver instance with automatic browser selection and fallback"""
        browsers = [
            {
                'name': 'Chrome',
                'options': webdriver.ChromeOptions,
                'service': Service,
                'driver': webdriver.Chrome,
                'manager': ChromeDriverManager
            },
            {
                'name': 'Firefox',
                'options': webdriver.FirefoxOptions,
                'service': Service,
                'driver': webdriver.Firefox,
                'manager': GeckoDriverManager
            },
            {
                'name': 'Edge',
                'options': webdriver.EdgeOptions,
                'service': Service,
                'driver': webdriver.Edge,
                'manager': EdgeChromiumDriverManager
            },
            {
                'name': 'Safari',
                'options': None,
                'service': None,
                'driver': webdriver.Safari,
                'manager': None
            }
        ]

        last_exception = None
        for browser in browsers:
            try:
                self.print_status(f"Attempting to initialize {browser['name']} driver...", "info")

                # Configure browser options
                options = None
                if browser['options']:
                    options = browser['options']()
                    options.add_argument("--headless")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--disable-gpu")
                    options.add_argument("--disable-extensions")
                    options.add_argument("--disable-browser-side-navigation")
                    options.add_argument("--disable-infobars")
                    options.add_argument("--disable-notifications")
                    options.add_argument("--disable-web-security")
                    options.add_argument("--ignore-certificate-errors")
                    options.add_argument(f"user-agent={self.get_random_user_agent()}")
                    options.page_load_strategy = 'eager'

                # Special handling for different browsers
                if browser['name'] == 'Safari':
                    driver = browser['driver']()
                else:
                    service = browser['service'](browser['manager']().install())
                    driver = browser['driver'](service=service, options=options)

                self.print_status(f"Successfully initialized {browser['name']} driver!", "success")
                return driver

            except Exception as e:
                last_exception = e
                self.print_status(f"Failed to initialize {browser['name']} driver: {str(e)}", "warning")
                continue

        # If all browsers fail
        error_msg = "Failed to initialize any web driver. Please ensure at least one of these browsers is installed:"
        self.print_status(error_msg, "error")
        for browser in browsers:
            self.print_status(f"• {browser['name']}", "error")
        raise Exception(f"No available web drivers. Last error: {str(last_exception)}")

    def setup_webdriver_pool(self, pool_size=3):
        """Initialize a pool of web drivers"""
        for _ in range(pool_size):
            try:
                driver = self.create_driver()
                self.driver_pool.put(driver)
            except Exception as e:
                self.print_status(f"Failed to create driver for pool: {str(e)}", "error")
                break

    def cleanup_drivers(self):
        """Clean up all web drivers in the pool"""
        while not self.driver_pool.empty():
            try:
                driver = self.driver_pool.get_nowait()
                driver.quit()
            except:
                pass

    def get_driver(self):
        try:
            return self.driver_pool.get_nowait()
        except:
            with self.driver_lock:
                return self.create_driver()

    def return_driver(self, driver):
        self.driver_pool.put(driver)

    def generate_payload_urls(self, url, payload):
        url_combinations = []
        try:
            scheme, netloc, path, query_string, fragment = urlsplit(url)
            if not scheme:
                scheme = 'http'

            # Handle URL parameters
            query_params = parse_qs(query_string, keep_blank_values=True)
            for key in query_params.keys():
                modified_params = query_params.copy()
                modified_params[key] = [payload]
                modified_query_string = urlencode(modified_params, doseq=True)
                modified_url = urlunsplit((scheme, netloc, path, modified_query_string, fragment))
                url_combinations.append(modified_url)

            # Handle path-based injection
            path_parts = path.split('/')
            for i in range(len(path_parts)):
                if path_parts[i]:
                    modified_path = '/'.join(path_parts[:i] + [payload] + path_parts[i+1:])
                    modified_url = urlunsplit((scheme, netloc, modified_path, query_string, fragment))
                    url_combinations.append(modified_url)

            # Handle fragment-based injection
            if fragment:
                modified_url = urlunsplit((scheme, netloc, path, query_string, payload))
                url_combinations.append(modified_url)

            return url_combinations
        except Exception as e:
            self.scan_state['warnings'].append(f"Error generating payload URLs for {url}: {str(e)}")
            return []

    def encode_payload(self, payload, encoding_type="all"):
        """Encode payload using various WAF bypass techniques"""
        encodings = {
            "html": {
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#x27;",
                "/": "&#x2F;",
            },
            "hex": lambda x: "".join([f"%{ord(i):02x}" for i in x]),
            "unicode": lambda x: "".join([f"\\u00{ord(i):02x}" for i in x]),
            "decimal": lambda x: "".join([f"&#x{ord(i):02x};" for i in x]),
            "octal": lambda x: "".join([f"\\{ord(i):03o}" for i in x]),
            "double_encode": lambda x: "".join([f"%%{ord(i):02x}" for i in x])
        }

        # WAF bypass techniques
        waf_bypass = {
            "case_swapping": lambda x: "".join(c.swapcase() if c.isalpha() else c for c in x),
            "space_substitution": lambda x: x.replace(" ", "/**/"),
            "keyword_splitting": lambda x: x.replace("script", "scr'+'ipt"),
            "tag_splitting": lambda x: x.replace("<script", "<scr\nript"),
            "quotes_substitution": lambda x: x.replace('"', '`').replace("'", "`"),
            "add_nullbyte": lambda x: x + "\0",
        }

        def html_encode(text):
            for char, encoded in encodings["html"].items():
                text = text.replace(char, encoded)
            return text

        if encoding_type == "all":
            # Try different combinations of encodings
            encoded_payloads = []
            
            # Base payload
            encoded_payloads.append(payload)
            
            # HTML encoding
            encoded_payloads.append(html_encode(payload))
            
            # URL encoding
            encoded_payloads.append(encodings["hex"](payload))
            
            # Unicode encoding
            encoded_payloads.append(encodings["unicode"](payload))
            
            # Double encoding
            encoded_payloads.append(encodings["double_encode"](payload))
            
            # Mixed techniques
            for bypass_name, bypass_func in waf_bypass.items():
                encoded_payloads.append(bypass_func(payload))
                # Combine with encodings
                encoded_payloads.append(bypass_func(html_encode(payload)))
                encoded_payloads.append(bypass_func(encodings["hex"](payload)))

            # Advanced WAF bypass combinations
            advanced_payloads = [
                payload.replace("script", "scr`+`ipt"),
                payload.replace("script", "\\x73cript"),
                payload.replace("alert", "\\x61lert"),
                payload.replace("alert", "al\tert"),
                payload.replace("alert", "al`+`ert"),
                payload.replace("<", "\\x3c").replace(">", "\\x3e"),
                payload.replace("script", "sCr"+"\u0130"+"pt"),
                payload.replace("<", "&lt;").replace(">", "&gt;"),
                payload.replace("script", "scr\u0131pt"),
                payload.replace("on", "ｏｎ"),
                f"{payload}<!---->",
                f"{payload}//",
                f"{payload}/**/",
                f"{payload}%%0a",
            ]
            encoded_payloads.extend(advanced_payloads)

            return list(set(encoded_payloads))  # Remove duplicates
        else:
            # Single encoding type
            if encoding_type in encodings:
                if isinstance(encodings[encoding_type], dict):
                    return html_encode(payload)
                return encodings[encoding_type](payload)
            elif encoding_type in waf_bypass:
                return waf_bypass[encoding_type](payload)
            return payload

    def generate_waf_bypass_payloads(self, base_payload):
        """Generate WAF bypass variations of a payload"""
        variations = []
        
        # Basic character mutations
        variations.extend([
            base_payload.replace("script", "scr`ipt"),
            base_payload.replace("script", "scr%00ipt"),
            base_payload.replace("script", "scr\nipt"),
            base_payload.replace("script", "scr/**/ipt"),
            base_payload.replace("alert", "al\u0065rt"),
            base_payload.replace("alert", "al`+`ert"),
            base_payload.replace("alert", "\\x61lert"),
        ])
        
        # Protocol bypass
        if "javascript:" in base_payload:
            variations.extend([
                base_payload.replace("javascript:", "javascript&colon;"),
                base_payload.replace("javascript:", "javascript&#58;"),
                base_payload.replace("javascript:", "javascript&#x3A;"),
            ])
        
        # Event handler bypass
        events = ["onload", "onerror", "onmouseover"]
        for event in events:
            if event in base_payload:
                variations.extend([
                    base_payload.replace(event, f"{event.replace('on', 'ON')}"),
                    base_payload.replace(event, f"{event.replace('on', '%6f%6e')}"),
                    base_payload.replace(event, f"{event.replace('on', '&#x6f;&#x6e;')}"),
                ])
        
        return variations

    def load_payloads(self, payload_file):
        """Load and process payloads with WAF bypass variations"""
        try:
            with open(payload_file, "r") as file:
                base_payloads = [line.strip() for line in file if line.strip()]

            all_payloads = []
            for base_payload in base_payloads:
                # Add original payload
                all_payloads.append(base_payload)
                
                # Add encoded variations
                encoded_variations = self.encode_payload(base_payload)
                all_payloads.extend(encoded_variations)
                
                # Add WAF bypass variations
                waf_variations = self.generate_waf_bypass_payloads(base_payload)
                all_payloads.extend(waf_variations)

            # Remove duplicates while preserving order
            unique_payloads = list(dict.fromkeys(all_payloads))
            
            self.print_status(f"Loaded {len(base_payloads)} base payloads and generated {len(unique_payloads)} WAF bypass variations", "info")
            return unique_payloads

        except Exception as e:
            self.print_status(f"Error loading payloads: {e}", "error")
            sys.exit()

    def run_scan(self, urls, payload_file, timeout):
        payloads = self.load_payloads(payload_file)
        vulnerable_urls = []
        total_scanned = [0]
        start_time = time.time()

        for _ in range(3):
            self.driver_pool.put(self.create_driver())

        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = []
                for url in urls:
                    for payload in payloads:
                        futures.append(
                            executor.submit(
                                self.check_vulnerability,
                                url,
                                payload,
                                vulnerable_urls,
                                total_scanned,
                                timeout
                            )
                        )

                total_futures = len(futures)
                completed_futures = 0

                for future in as_completed(futures):
                    try:
                        future.result(timeout)
                        completed_futures += 1
                        
                        # Calculate progress
                        progress = (completed_futures / total_futures) * 100
                        elapsed_time = time.time() - start_time
                        remaining_time = (elapsed_time / completed_futures) * (total_futures - completed_futures) if completed_futures > 0 else 0

                        # Print detailed status
                        print(f"\n{VENUS_COLORS['primary']}╭─ Scan Status ──────────────────────────────────────╮")
                        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Progress: {VENUS_COLORS['secondary']}{progress:.1f}%")
                        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Payloads tested: {VENUS_COLORS['secondary']}{completed_futures}/{total_futures}")
                        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Vulnerabilities found: {VENUS_COLORS['success']}{len(vulnerable_urls)}")
                        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Elapsed time: {VENUS_COLORS['secondary']}{int(elapsed_time)}s")
                        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Estimated remaining: {VENUS_COLORS['warning']}{int(remaining_time)}s")
                        print(f"{VENUS_COLORS['primary']}╰───────────────────────────────────────────────────────╯")

                    except Exception as e:
                        print(Fore.RED + f"[!] Error during scan: {e}")
                        self.scan_state['error_count'] += 1

        finally:
            while not self.driver_pool.empty():
                driver = self.driver_pool.get()
                driver.quit()

            return vulnerable_urls, total_scanned[0]

    def generate_report(self, vulnerable_urls, total_scanned):
        self.report_data['scan_date'] = datetime.now().isoformat()
        self.report_data['targets'] = self.scan_state['vulnerable_urls']
        self.report_data['findings'] = vulnerable_urls
        self.report_data['statistics'] = {
            'total_scanned': total_scanned,
            'total_vulnerabilities': len(vulnerable_urls),
            'error_count': self.scan_state['error_count'],
            'scan_duration': int(time.time() - self.scan_state['scan_start_time']),
            'warnings': self.scan_state['warnings'],
            'response_codes': {}  # Will store count of different response codes
        }

        # Count response codes
        for vuln in vulnerable_urls:
            code = vuln.get('response_code', 'unknown')
            self.report_data['statistics']['response_codes'][str(code)] = \
                self.report_data['statistics']['response_codes'].get(str(code), 0) + 1

        # Generate default filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_json = f"xss_scan_report_{timestamp}.json"
        default_txt = f"xss_vulnerabilities_{timestamp}.txt"

        print(f"\n{VENUS_COLORS['primary']}╭─ Save Scan Report ─────────────────────────────────────╮")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Default JSON report: {VENUS_COLORS['secondary']}{default_json}")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Default TXT report: {VENUS_COLORS['secondary']}{default_txt}")
        print(f"{VENUS_COLORS['primary']}╰───────────────────────────────────────────────────────╯")

        save = input(f"\n{VENUS_COLORS['secondary']}➜ Save reports? (Y/n): {VENUS_COLORS['reset']}").lower()

        if save != 'n':
            try:
                # Save JSON report
                with open(default_json, 'w') as f:
                    json.dump(self.report_data, f, indent=4)
                self.print_status(f"JSON report saved as: {default_json}", "success")

                # Save TXT report with only vulnerable URLs
                if vulnerable_urls:
                    with open(default_txt, 'w') as f:
                        f.write("Venus XSS - Vulnerable URLs Report\n")
                        f.write("=" * 50 + "\n\n")
                        for vuln in vulnerable_urls:
                            f.write(f"URL: {vuln['url']}\n")
                            f.write(f"Response Code: {vuln.get('response_code', 'unknown')}\n")
                            f.write(f"Alert: {vuln['alert_text']}\n")
                            f.write(f"Payload: {vuln['payload']}\n")
                            f.write("-" * 50 + "\n")
                    self.print_status(f"TXT report saved as: {default_txt}", "success")

                    # Send reports to Telegram if enabled
                    if self.chat_id:
                        self.send_telegram_file(default_txt, "📝 XSS Vulnerabilities Report")
            except Exception as e:
                self.print_status(f"Error saving reports: {str(e)}", "error")
                return None

            return default_json
        else:
            self.print_status("Reports not saved.", "info")
            return None

    def get_file_path(self, prompt_text):
        completer = PathCompleter()
        print(f"\n{VENUS_COLORS['primary']}╭─ Input Required ─────────────────────────────────────╮")
        print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}{prompt_text}")
        print(f"{VENUS_COLORS['primary']}╰───────────────────────────────────────────────────────╯")
        return input(f"{VENUS_COLORS['secondary']}➜ {VENUS_COLORS['reset']}").strip()

    def print_menu(self, title, options):
        print(f"\n{VENUS_COLORS['primary']}╭─ {title} ────────────────────────────────────────╮")
        for idx, option in enumerate(options, 1):
            print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}[{idx}] {VENUS_COLORS['secondary']}{option}")
        print(f"{VENUS_COLORS['primary']}╰───────────────────────────────────────────────────╯{VENUS_COLORS['reset']}")
        return input(f"\n{VENUS_COLORS['info']}Select an option (1-{len(options)}): {VENUS_COLORS['reset']}")

    def show_url_input_menu(self):
        options = [
            "Load URLs from a file",
            "Enter a single URL",
            "Exit"
        ]
        while True:
            choice = self.print_menu("URL Input Method", options)
            if choice == "1":
                return self.get_file_path("Enter the path to your URL file")
            elif choice == "2":
                print(f"\n{VENUS_COLORS['primary']}╭─ Input Required ─────────────────────────────────────╮")
                print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Enter your target URL")
                print(f"{VENUS_COLORS['primary']}╰───────────────────────────────────────────────────────╯")
                return input(f"{VENUS_COLORS['secondary']}➜ {VENUS_COLORS['reset']}").strip()
            elif choice == "3":
                self.print_status("Exiting...", "info")
                sys.exit(0)
            else:
                self.print_status("Invalid option. Please try again.", "error")

    def prompt_for_urls(self):
        while True:
            try:
                url_input = self.show_url_input_menu()
                if not url_input:
                    self.print_status("Please provide a URL or file path", "error")
                    continue

                if os.path.isfile(url_input):
                    with open(url_input) as file:
                        urls = [line.strip() for line in file if line.strip()]
                    return urls
                else:
                    return [url_input]

            except Exception as e:
                self.print_status(f"Error: {str(e)}", "error")
                input(f"{VENUS_COLORS['warning']}Press Enter to continue...{VENUS_COLORS['reset']}")
                self.clear_screen()
                self.display_intro()

    def show_payload_menu(self):
        options = [
            "Load payloads from a file",
            "Use default XSS payloads",
            "Exit"
        ]
        while True:
            choice = self.print_menu("Payload Input Method", options)
            if choice == "1":
                return self.get_file_path("Enter payload file path: ")
            elif choice == "2":
                default_payload_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "default_xss_payloads.txt")
                if not os.path.exists(default_payload_path):
                    self.print_status("Default payload file not found. Please make sure default_xss_payloads.txt exists in the same directory.", "error")
                    continue
                return default_payload_path
            elif choice == "3":
                self.print_status("Exiting...", "info")
                sys.exit(0)
            else:
                self.print_status("Invalid option. Please try again.", "error")

    def prompt_for_valid_file_path(self, prompt_text):
        while True:
            try:
                file_path = self.show_payload_menu()
                if not file_path:
                    self.print_status("Payload file is required", "error")
                    continue
                if os.path.isfile(file_path):
                    return file_path
                else:
                    self.print_status("File not found", "error")
            except Exception as e:
                self.print_status(f"Error: {str(e)}", "error")
                input(f"{VENUS_COLORS['warning']}Press Enter to continue...{VENUS_COLORS['reset']}")
                self.clear_screen()
                self.display_intro()

    def show_timeout_menu(self):
        options = [
            "0.5 seconds (Default)",
            "1.0 seconds",
            "2.0 seconds",
            "Custom value",
            "Exit"
        ]
        timeout_values = [0.5, 1.0, 2.0]
        while True:
            choice = self.print_menu("Select Timeout Duration", options)
            if choice in ["1", "2", "3"]:
                return timeout_values[int(choice) - 1]
            elif choice == "4":
                try:
                    print(f"\n{VENUS_COLORS['primary']}╭─ Input Required ─────────────────────────────────────╮")
                    print(f"{VENUS_COLORS['primary']}│ {VENUS_COLORS['info']}Enter custom timeout value in seconds")
                    print(f"{VENUS_COLORS['primary']}╰───────────────────────────────────────────────────────╯")
                    custom_timeout = float(input(f"{VENUS_COLORS['secondary']}➜ {VENUS_COLORS['reset']}"))
                    if custom_timeout > 0:
                        return custom_timeout
                    else:
                        self.print_status("Timeout must be greater than 0", "error")
                except ValueError:
                    self.print_status("Invalid timeout value, using default (0.5)", "warning")
                    return 0.5
            elif choice == "5":
                self.print_status("Exiting...", "info")
                sys.exit(0)
            else:
                self.print_status("Invalid option. Please try again.", "error")

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def send_telegram_message(self, message):
        """Send a message via Telegram bot"""
        if self.chat_id:
            try:
                self.bot.send_message(self.chat_id, message, parse_mode='HTML')
                return True
            except Exception as e:
                self.print_status(f"Failed to send Telegram message: {str(e)}", "error")
                return False
        return False

    def send_telegram_file(self, file_path, caption=""):
        """Send a file via Telegram bot"""
        if self.chat_id:
            try:
                with open(file_path, 'rb') as file:
                    self.bot.send_document(self.chat_id, file, caption=caption)
                return True
            except Exception as e:
                self.print_status(f"Failed to send file via Telegram: {str(e)}", "error")
                return False
        return False

if __name__ == "__main__":
    try:
        validator = VenusXSS()
        validator.main()
    except KeyboardInterrupt:
        print(f"{VENUS_COLORS['error']}[!] Scan interrupted by the user. Exiting...")
        sys.exit()