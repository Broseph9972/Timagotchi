# Demonstrates: Background process management with WiFi connection and git maintenance
import subprocess
import threading
import time
def _attempt_wifi_connect(self, ssid, password):
    self.display.show_message("WiFi", f"Connecting to\n{ssid}...", (100, 200, 255), self.nav_items, self.nav_selected_index, self._get_wifi_connected())
    try:
        if password:
            result = subprocess.run(
                ['nmcli', 'device', 'wifi', 'connect', ssid, 'password', password],
                capture_output=True,
                text=True,
                timeout=10
            )
        else:
            result = subprocess.run(
                ['nmcli', 'device', 'wifi', 'connect', ssid],
                capture_output=True,
                text=True,
                timeout=10
            )
        if result.returncode == 0:
            self._wifi_state = True
            self._wifi_checked_at = time.time()
            if password:
                self.wifi_history[ssid] = password
                self._save_wifi_history()
            time.sleep(1)
            self.display.show_message("WiFi", f"Connected to\n{ssid}!", (100, 255, 100), self.nav_items, self.nav_selected_index, True)
            time.sleep(2)
        else:
            error_msg = result.stderr.strip()[:50] if result.stderr else "Connection failed"
            self.display.show_message("WiFi", f"Error:\n{error_msg}", (255, 100, 100), self.nav_items, self.nav_selected_index, self._get_wifi_connected())
            time.sleep(2)
    except Exception as e:
        self.display.show_message("WiFi", f"Error: {str(e)[:40]}", (255, 100, 100), self.nav_items, self.nav_selected_index, self._get_wifi_connected())
        time.sleep(2)
    self.current_screen = "wifi"
    self.show_wifi_menu()
def start_boot_git_maintenance_background(self):
    try:
        worker = threading.Thread(target=self._boot_git_maintenance_worker, daemon=True)
        worker.start()
    except Exception as exc:
        print(f"[Boot Git] Failed to start background maintenance: {exc}")
def _boot_git_maintenance_worker(self):
    try:
        repo_dir = self._get_repo_dir()
        git_check = subprocess.run(['git', '--version'], capture_output=True, text=True, timeout=5)
        if git_check.returncode != 0:
            print("[Boot Git] git not installed; skipping integrity check.")
            return
        try:
            subprocess.run(['git', 'config', '--global', '--add', 'safe.directory', repo_dir], capture_output=True, text=True, timeout=5)
        except Exception:
            pass
        fsck_result = self._git_run(['fsck', '--full', '--no-progress'], repo_dir=repo_dir, timeout=45)
        fsck_output = ((fsck_result.stdout or '') + '\n' + (fsck_result.stderr or '')).lower() if fsck_result else ''
        if self._git_output_indicates_corruption(fsck_output):
            print("[Boot Git] Repository corruption detected. Running background auto-repair...")
            repaired = self._repair_repo_in_background(repo_dir)
            if repaired:
                print("[Boot Git] Auto-repair completed successfully.")
            else:
                print("[Boot Git] Auto-repair failed. Manual re-clone may be required.")
        else:
            print("[Boot Git] Repository integrity check passed.")
    except subprocess.TimeoutExpired:
        print("[Boot Git] Integrity check timed out; skipping this boot.")
    except Exception as exc:
        print(f"[Boot Git] Background maintenance error: {exc}")
