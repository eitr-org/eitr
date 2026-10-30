#!/usr/bin/env python3
"""Read subscription limits without starting a conversation or changing accounts."""
import eitr_bootstrap
from eitr_i18n import tr
from eitr_assistants import executable
from eitr_ai_accounts import rows as account_rows, environment as account_environment, CONFIGURATION

import concurrent.futures
import datetime as dt
import email.utils
import json
import os
from pathlib import Path
import select
import subprocess
import time
import sys
import urllib.error
import urllib.request


COOLDOWNS = {}


class UsageRateLimit(RuntimeError):
    def __init__(self, message, headers):
        super().__init__(message)
        try:
            self.delay = max(300, float(headers.get('Retry-After', 300)))
        except (TypeError, ValueError):
            try:
                self.delay = max(300, email.utils.parsedate_to_datetime(headers['Retry-After']).timestamp() - time.time())
            except (KeyError, TypeError, ValueError):
                self.delay = 300


def cli_binary(name):
    """The real installed tool; Eitr's first-use launchers would only ask to install it."""
    found = executable(name)
    return str(found) if found else None


def codex_binary():
    binary = cli_binary("codex")
    if not binary:
        raise RuntimeError(tr('Codex CLI is not installed'))
    return binary


def read_credentials(path):
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def grok_credentials(environment=None):
    environment = os.environ if environment is None else environment
    directory = Path(environment.get("GROK_HOME") or Path.home() / ".grok")
    path = Path(environment.get("GROK_AUTH_PATH") or directory / "auth.json")
    return read_credentials(path)


def available_providers():
    providers = []
    claude = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    if cli_binary("claude") and (read_credentials(claude / ".credentials.json").get("claudeAiOauth", {}).get("accessToken")
                                 or os.environ.get("ANTHROPIC_API_KEY")):
        providers.append("Claude")
    binary = cli_binary("codex")
    if binary:
        home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
        auth = read_credentials(home / "auth.json")
        configured = bool(auth.get("OPENAI_API_KEY") or (auth.get("tokens") or {}).get("access_token"))
        if not configured:
            # The CLI also understands keyring-backed credentials. Never print its output.
            try:
                env = os.environ.copy()
                env["PATH"] = str(Path(binary).parent) + os.pathsep + env.get("PATH", "")
                configured = subprocess.run([binary, "login", "status"], env=env,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3).returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                configured = False
        if configured:
            providers.append("Codex")
    if cli_binary("grok") and (os.environ.get("XAI_API_KEY") or any(
            isinstance(auth, dict) and auth.get("key") for auth in grok_credentials().values())):
        providers.append("Grok")
    return providers


def grok_windows(payload):
    config = payload.get("config") or {}
    used = config.get("creditUsagePercent")
    if used is None:
        limit = (config.get("monthlyLimit") or {}).get("val", 0)
        if limit > 0:
            used = (config.get("used") or {}).get("val", 0) * 100 / limit
    if used is None:
        return []
    period = config.get("currentPeriod") or {}
    kind = period.get("type", "")
    label = "Weekly" if "WEEKLY" in kind else "Monthly" if "MONTHLY" in kind else "Usage"
    reset = period.get("end") or config.get("billingPeriodEnd")
    if isinstance(reset, str):
        reset = dt.datetime.fromisoformat(reset.replace("Z", "+00:00")).timestamp()
    return [{"label": label, "used": used, "reset": reset}]


def grok_usage(environment=None):
    # Official Grok Build auth store / read-only billing contract. Never refresh or
    # mutate credentials, and never forward enterprise tokens to a first-party host.
    credentials = [auth for auth in grok_credentials(environment).values() if isinstance(auth, dict)
                   and auth.get("key") and auth.get("oidc_issuer") == "https://auth.x.ai"
                   and not auth.get("team_id")]
    if len(credentials) != 1:
        raise RuntimeError(tr('Grok subscription usage requires one personal Grok login; API/enterprise limits are not supported'))
    auth = credentials[0]
    request = urllib.request.Request("https://cli-chat-proxy.grok.com/v1/billing?format=credits", headers={
        "Authorization": "Bearer " + auth["key"], "X-XAI-Token-Auth": "xai-grok-cli",
        "x-userid": auth.get("user_id", ""), "Accept": "application/json",
    })
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, file_pointer, code, message, headers, new_url):
            return None

    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=10) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        message = tr('Grok usage returned HTTP {code}; retry later or sign in again', code=f'{exc.code}')
        raise (UsageRateLimit(message, exc.headers) if exc.code == 429 else RuntimeError(message)) from None
    return {"name": "Grok", "windows": grok_windows(payload), "plan": payload.get("subscriptionTier")}


def codex_usage(environment=None):
    binary = codex_binary()
    env = dict(os.environ if environment is None else environment)
    # NVM's CLI launcher uses /usr/bin/env node; desktop sessions omit its bin dir.
    env["PATH"] = str(Path(binary).parent) + os.pathsep + env.get("PATH", "")
    proc = subprocess.Popen(
        [binary, "-s", "read-only", "-a", "on-request", "app-server"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        env=env,
    )
    pending = b""

    def send(payload):
        proc.stdin.write((json.dumps(payload) + "\n").encode())
        proc.stdin.flush()

    def request(identifier, method, params=None):
        nonlocal pending
        send({"id": identifier, "method": method, "params": params or {}})
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            while b"\n" in pending:
                line, pending = pending.split(b"\n", 1)
                message = json.loads(line)
                if message.get("id") == identifier:
                    if "error" in message:
                        raise RuntimeError(tr('Codex usage unavailable; check `codex login status`'))
                    return message.get("result", {})
            if select.select([proc.stdout], [], [], 0.2)[0]:
                chunk = os.read(proc.stdout.fileno(), 65536)
                if not chunk:
                    raise RuntimeError(tr('Codex usage service exited'))
                pending += chunk
        raise RuntimeError(tr('Codex usage request timed out'))

    try:
        request(1, "initialize", {"clientInfo": {"name": "desktop-ai-usage", "version": "1"}})
        send({"method": "initialized", "params": {}})
        response = request(2, "account/rateLimits/read")
        buckets = response.get("rateLimitsByLimitId") or {"codex": response.get("rateLimits", {})}
        windows = []
        for bucket_id, bucket in buckets.items():
            for key in ("primary", "secondary"):
                window = bucket.get(key)
                if not window or window.get("usedPercent") is None:
                    continue
                minutes = window.get("windowDurationMins", 0)
                label = "Weekly" if minutes == 10080 else f"{minutes // 60}h window" if minutes else "Usage"
                if len(buckets) > 1:
                    label = f"{bucket_id} · {label}"
                windows.append({"label": label, "used": window["usedPercent"], "reset": window.get("resetsAt")})
        plan = next((bucket.get("planType") for bucket in buckets.values() if bucket.get("planType")), None)
        return {"name": "Codex", "windows": windows, "plan": plan}
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        proc.stdin.close()
        proc.stdout.close()


def claude_windows(payload):
    windows = []
    for key, label in (("five_hour", "5h window"), ("seven_day_oauth_apps", "Weekly"),
                       ("seven_day", "Weekly"), ("seven_day_sonnet", "Sonnet weekly"),
                       ("seven_day_opus", "Opus weekly")):
        window = payload.get(key)
        if not window or window.get("utilization") is None:
            continue
        if any(w["label"] == label for w in windows):
            continue
        windows.append({"label": label, "used": window["utilization"], "reset": window.get("resets_at")})
    for limit in payload.get("limits") or []:
        if limit.get("percent") is None:
            continue
        scope = limit.get("scope") or {}
        model = scope.get("model") or {}
        name = model.get("display_name")
        kind = limit.get("kind")
        label = "5h window" if kind == "session" else "Weekly" if kind == "weekly_all" else None
        if kind == "weekly_scoped" and name:
            label = name + " weekly"
        if label and not any(w["label"] == label for w in windows):
            windows.append({"label": label, "used": limit["percent"], "reset": limit.get("resets_at")})
    for window in windows:
        if isinstance(window["reset"], str):
            window["reset"] = dt.datetime.fromisoformat(window["reset"].replace("Z", "+00:00")).timestamp()
    return windows


def claude_usage(environment=None):
    environment = os.environ if environment is None else environment
    home = Path(environment.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
    try:
        credentials = json.loads((home / ".credentials.json").read_text())
        token = credentials["claudeAiOauth"]["accessToken"]
    except (OSError, ValueError, KeyError):
        raise RuntimeError(tr('Sign in with `claude` to show subscription usage')) from None
    request = urllib.request.Request("https://api.anthropic.com/api/oauth/usage", headers={
        "Authorization": "Bearer " + token,
        "anthropic-beta": "oauth-2025-04-20", "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        message = tr('Claude usage returned HTTP {code}; retry later or sign in again', code=f'{exc.code}')
        raise (UsageRateLimit(message, exc.headers) if exc.code == 429 else RuntimeError(message)) from None
    windows = claude_windows(payload)
    account = credentials.get("claudeAiOauth", {})
    tier = account.get("rateLimitTier", "")
    plan = account.get("subscriptionType")
    if "20x" in tier:
        plan = "Max 20x"
    elif "5x" in tier:
        plan = "Max 5x"
    return {"name": "Claude", "windows": windows, "plan": plan}


def usage_accounts():
    """Discover configured accounts for installed assistants."""
    return [(identifier, account) for identifier in CONFIGURATION if cli_binary(identifier)
            for account in account_rows(identifier)]


LABELS = {"claude": "Claude", "codex": "Codex", "gemini": "Gemini CLI",
          "grok": "Grok", "copilot": "Copilot", "agy": "Antigravity"}


def collect_account(identifier, account):
    key = (identifier, account["id"])
    if time.monotonic() < COOLDOWNS.get(key, 0):
        return None
    result = {"id": account["id"], "label": account["label"], "windows": []}
    try:
        reader = {"claude": claude_usage, "codex": codex_usage, "grok": grok_usage}.get(identifier)
        if reader:
            result.update(reader(account_environment(identifier, account=account["id"])))
        if result["windows"] and not result.get("error"):
            return result
    except UsageRateLimit as error:
        COOLDOWNS[key] = time.monotonic() + error.delay
    except Exception:
        pass
    return None


def group_results(results):
    grouped = {}
    for identifier, account in results:
        if account is not None:
            provider = grouped.setdefault(identifier, {"name": LABELS[identifier], "accounts": []})
            provider["accounts"].append(account)
    return {"updated": time.time(), "providers": list(grouped.values())}


def collect():
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        jobs = [(identifier, pool.submit(collect_account, identifier, account))
                for identifier, account in usage_accounts()]
        return group_results((identifier, job.result()) for identifier, job in jobs)


if __name__ == "__main__":
    print(json.dumps({"available": available_providers()} if "--detect" in sys.argv else collect()))
