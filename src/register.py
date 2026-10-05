"""NTU SoC registration with HTTP and early-login Selenium strategies.

Default is observation only; --submit schedules one registration attempt.
--submit-once sends one real HTTP registration attempt immediately after login.
Never persist credentials, cookies, raw responses, or personal profiles.
"""
import argparse
from datetime import datetime, timedelta
import json
import os
import shutil
import sys
from pathlib import Path
import time
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent.parent
CODES = {"INSERT", "RJ", "OVER", "NAVA", "OUT", "PASS", "NLOG", "NON", "WP", "NOEC"}
FIELDS = ("id", "title", "non", "savanon", "sava", "ujoin", "s_sdate", "special")
MEAL_LABELS = {"葷食": "non-vegetarian", "素食": "vegetarian"}
CONFIG_DEFAULTS = {"Timezone": "Asia/Taipei", "PrepareSeconds": 180,
                   "PollSeconds": 1, "ObserveSeconds": 30, "RequestTimeout": 15}


def load_config(path):
    return {**CONFIG_DEFAULTS, **json.loads(Path(path).read_text(encoding="utf-8"))}


def console_event(row):
    """Keep original API data on disk; display English meal labels in the terminal."""
    display = dict(row)
    if "activity" in row:
        activity = dict(row["activity"])
        special = activity.pop("special", "") or ""
        options = special.split("#", 1)
        activity["meal_options"] = ([MEAL_LABELS.get(v, "custom option")
                                      for v in options[1].split("*")]
                                     if len(options) == 2 else [])
        display["activity"] = activity
    return display


def code(text):
    first = text.strip().split("|", 1)[0]
    return first if first in CODES else "UNKNOWN"


def joined(item):
    return item.get("ujoin") not in (None, False, 0, "", "0", "false")


def payload(item, dietary):
    if str(item.get("id", "")) in ("", "137"):
        raise ValueError("Missing activity ID or activity requires extra profile confirmation")
    result = {"aid": str(item["id"]), "t": "non"}
    special = item.get("special") or ""
    if special:
        parts = special.split("#", 1)
        if len(parts) != 2 or dietary not in parts[1].split("*"):
            raise ValueError("Activity choices do not match Dietary; inspect activity before submitting")
        result["special"] = dietary
    return result


def wait_until(target, rec=None, phase="Waiting for registration"):
    next_notice = 0.0
    next_display = 0.0
    interactive = sys.stdout.isatty()
    line_active = False
    try:
        while True:
            now = datetime.now(target.tzinfo)
            remaining = (target - now).total_seconds()
            if remaining <= 0:
                return
            # Finish the status line before the final second and before normal events.
            if remaining <= 1 and line_active:
                print(flush=True)
                line_active = False
            tick = time.monotonic()
            notice_due = tick >= next_notice
            if rec is not None and remaining > 1 and (notice_due or (interactive and tick >= next_display)):
                seconds = int(remaining + 0.999)
                days, seconds = divmod(seconds, 86400)
                hours, seconds = divmod(seconds, 3600)
                minutes, seconds = divmod(seconds, 60)
                countdown = f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
                if notice_due:
                    rec.state["status"] = "waiting"
                    rec.emit("heartbeat", console=False, phase=phase,
                             remaining_seconds=round(remaining, 1),
                             next_action_at=target.isoformat(), pid=os.getpid())
                    next_notice = time.monotonic() + 60
                message = (f"[{now:%H:%M:%S}] {phase} | Remaining: {countdown} | "
                           f"Next: {target:%Y-%m-%d %H:%M:%S %Z}")
                if interactive:
                    # Keep the text within one physical terminal row, including in tmux.
                    width = max(1, shutil.get_terminal_size().columns - 1)
                    print("\r\033[2K" + message[:width], end="", flush=True)
                    line_active = True
                else:
                    # Redirected logs should have readable lines, not terminal escapes.
                    print(message, flush=True)
                next_display = time.monotonic() + 1
                continue
            time.sleep(min(remaining, 0.2))
    finally:
        if line_active:
            print(flush=True)


class Record:
    def __init__(self, mode, cfg, submit, target):
        self.start = time.perf_counter()
        self.target = target
        self.directory = ROOT / "runs" / (datetime.now().strftime("%Y%m%d_%H%M%S_%f") + "_" + mode)
        self.directory.mkdir(parents=True, mode=0o700)
        self.state = {"mode": mode, "submit": submit, "config": cfg, "status": "starting"}
        self.emit("start", mode=mode, submit=submit)

    def emit(self, event, *, console=True, **values):
        now = datetime.now(self.target.tzinfo)
        row = {"time": now.isoformat(timespec="milliseconds"),
               "elapsed_ms": round((time.perf_counter() - self.start) * 1000, 2),
               "target_offset_ms": round((now - self.target).total_seconds() * 1000, 2),
               "event": event, **values}
        if event == "request_start" and values.get("endpoint") == "fn/actjoin.php":
            self.state["submit_offset_ms"] = row["target_offset_ms"]
        if event == "request_end" and values.get("endpoint") == "fn/actjoin.php":
            self.state["response_ms"] = values["duration_ms"]
        if event == "browser_response":
            self.state["submit_offset_ms"] = round(values["sent"] - self.target.timestamp() * 1000, 2)
            self.state["response_ms"] = values["received"] - values["sent"]
        with (self.directory / "events.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        self.state.update(last_event=row)
        tmp = self.directory / "summary.tmp"
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.directory / "summary.json")
        if console:
            print(json.dumps(console_event(row), ensure_ascii=False), flush=True)

    def snapshot(self, item):
        safe = {k: item[k] for k in FIELDS if k in item}
        self.state["activity"] = safe
        self.emit("activity", activity=safe)


class Transport:
    def __init__(self, base, timeout, rec, browser=None):
        self.base, self.timeout, self.rec, self.browser = base, timeout, rec, browser
        self.session = None
        if browser is None:
            import requests
            self.session = requests.Session()
            self.session.headers.update({"Referer": base, "X-Requested-With": "XMLHttpRequest"})

    def request(self, method, path, data=None):
        started = time.perf_counter()
        self.rec.emit("request_start", method=method, endpoint=path)
        try:
            if self.browser:
                result = self.browser.execute_async_script("""
                    const [method, url, data, timeout, done] = arguments;
                    const controller = new AbortController();
                    const timer = setTimeout(() => controller.abort(), timeout * 1000);
                    let options = {method, credentials:'same-origin', cache:'no-store',
                                   signal:controller.signal};
                    let dest = url;
                    if (method === 'GET' && data) dest += '?' + new URLSearchParams(data);
                    else if (data) options.body = new URLSearchParams(data);
                    fetch(dest, options).then(async r => {
                        const text = await r.text(); clearTimeout(timer);
                        done({status:r.status, text, date:r.headers.get('Date')});
                    }).catch(() => {clearTimeout(timer); done({status:0, text:''});});
                """, method, urljoin(self.base, path), data, self.timeout)
            else:
                response = self.session.request(method, urljoin(self.base, path),
                    params=data if method == "GET" else None,
                    data=data if method != "GET" else None, timeout=self.timeout,
                    allow_redirects=False)
                result = {"status": response.status_code, "text": response.text,
                          "date": response.headers.get("Date")}
            self.rec.emit("request_end", endpoint=path, http_status=result["status"],
                          duration_ms=round((time.perf_counter()-started)*1000, 2),
                          server_date=result.get("date"))
            if not 200 <= result["status"] < 300:
                raise RuntimeError("Unexpected HTTP status")
            return result["text"]
        except Exception as exc:
            self.rec.emit("request_error", endpoint=path, error_type=type(exc).__name__)
            raise

    def get(self, params):
        value = json.loads(self.request("GET", "fn/getdata.php", params))
        if not isinstance(value, dict):
            raise ValueError("Activity API schema changed")
        return value

    def detail(self, aid):
        item = self.get({"scope": "item", "type": "activity", "id": aid}).get("item")
        if not isinstance(item, dict) or str(item.get("id")) != str(aid):
            raise ValueError("Unexpected activity detail")
        self.rec.snapshot(item)
        return item

    def discover(self, cfg):
        if cfg.get("EventId"):
            item = self.detail(cfg["EventId"])
        else:
            home = self.get({"scope": "home"})
            candidates = {}
            for section, kind in (("jobs", "job"), ("socs", "soc")):
                items = home.get(section, [])
                more = home.get(section + "_more", False)
                for _ in range(100):
                    for item in items:
                        if item.get("title") == cfg["Event"]:
                            candidates[str(item["id"])] = item
                    if candidates or not more:
                        break
                    offset = len(home.get(section, [])) if _ == 0 else offset + len(items)
                    page = self.get({"scope": "more", "kind": kind, "offset": offset, "limit": 5})
                    items, more = page.get("items", []), page.get("more", False)
                    if not items:
                        break
            if len(candidates) != 1:
                raise ValueError("Expected one exact event title; configure EventId if necessary")
            item = self.detail(next(iter(candidates)))
        if item.get("title") != cfg["Event"]:
            raise ValueError("EventId/title mismatch")
        return item

    def check_session(self):
        result = code(self.request("POST", "fn/checksession.php"))
        self.rec.emit("session_check", result=result)
        if result != "PASS":
            raise RuntimeError("Session is not authenticated")


def login_browser(base, email, password, cfg, rec):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    options = webdriver.ChromeOptions()
    if cfg.get("Headless", True):
        options.add_argument("--headless=new")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    try:
        rec.emit("browser_started")
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(cfg["RequestTimeout"] + 5)
        driver.get(base)
        rec.emit("browser_page_loaded")
        wait = WebDriverWait(driver, 30, poll_frequency=0.1)
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loader")))
        driver.execute_script("""
            window.__loginCodes = [];
            window.__loginShown = false;
            $('#loginpanel').one('shown.bs.modal', function(){window.__loginShown = true;});
            $(document).ajaxComplete(function(e,x,s) {
                if (s.url.includes('fn/login.php') || s.url.includes('fn/checksession.php'))
                    window.__loginCodes.push(x.responseText.trim().split('|')[0]);
            });
        """)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-target='#loginpanel']"))).click()
        wait.until(lambda d: d.execute_script("return window.__loginShown"))
        rec.emit("browser_login_panel_opened")
        wait.until(EC.visibility_of_element_located((By.ID, "login_email"))).send_keys(email)
        driver.find_element(By.ID, "login_pw").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "#loginpanel .modal-footer .btn-primary").click()
        rec.emit("browser_login_sent")
        wait.until(lambda d: d.execute_script("""
            const s = angular.element(document.querySelector('[ng-controller]')).scope();
            return s && s.loginc === true;
        """))
        rec.emit("browser_authenticated")
        return driver
    except Exception:
        try:
            results = driver.execute_script("return window.__loginCodes || []")
            rec.emit("browser_login_diagnostic", results=[code(v) for v in results])
        except Exception:
            pass
        driver.quit()
        raise


def browser_submit(driver, item, dietary, rec, timeout):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import NoAlertPresentException
    driver.execute_script("""
        window.__registration = {};
        $(document).ajaxSend(function(e,x,s) {
            if (s.url.split('?')[0].endsWith('fn/actjoin.php'))
                window.__registration.sent = Date.now();
        });
        $(document).ajaxComplete(function(e,x,s) {
            if (s.url.split('?')[0].endsWith('fn/actjoin.php')) {
                window.__registration.received = Date.now();
                window.__registration.code = x.responseText.trim().split('|')[0];
                window.__registration.status = x.status;
            }
        });
        const item = arguments[0];
        const scope = angular.element(document.querySelector('[ng-controller]')).scope();
        scope.$apply(function(){scope.sa = item;});
        window.__activityShown = $('#actpanel').hasClass('show');
        $('#actpanel').one('shown.bs.modal', function(){window.__activityShown = true;});
        $('#actpanel').modal('show');
    """, item)
    wait = WebDriverWait(driver, timeout, poll_frequency=0.1)
    wait.until(lambda d: d.execute_script("return window.__activityShown"))
    rec.emit("browser_click_start")
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#actpanel button[ng-click=\"actjoin(sa,'non')\"]"))).click()
    if item.get("special"):
        wait.until(EC.element_to_be_clickable((By.XPATH,
            "//button[@ng-click='specialp(i)' and normalize-space(.)='" + dietary + "']"))).click()
    def completed(d):
        try:
            d.switch_to.alert.accept()
        except NoAlertPresentException:
            pass
        result = d.execute_script("return window.__registration")
        return result if "received" in result else False
    result = wait.until(completed)
    result["code"] = code(result["code"])
    rec.emit("browser_response", **result)
    return result["code"]


def run(args, cfg, target, rec):
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    base = (os.environ.get("URL") or "https://soc.ee.ntu.edu.tw/www/").rstrip("/") + "/"
    if urlparse(base).scheme != "https" or urlparse(base).hostname != "soc.ee.ntu.edu.tw":
        raise ValueError("This adapter supports only the NTU SoC HTTPS site")
    email, password = os.environ.get("EMAIL"), os.environ.get("PASSWORD")
    if not email or not password:
        raise ValueError("EMAIL and PASSWORD are required")
    immediate = args.now or getattr(args, "submit_once", False)
    if not immediate:
        wait_until(target - timedelta(seconds=cfg["PrepareSeconds"]), rec, "Waiting to log in")
    driver, client = None, None
    try:
        rec.state["status"] = "preparing"
        rec.emit("prepare_start")
        if args.mode == "early-selenium":
            driver = login_browser(base, email, password, cfg, rec)
        client = Transport(base, cfg["RequestTimeout"], rec, driver)
        if not driver:
            result = code(client.request("POST", "fn/login.php",
                                        {"login_email": email, "login_pw": password}))
            rec.emit("login_result", result=result)
            if result != "PASS":
                raise RuntimeError("Login failed")
        client.check_session()
        item = client.discover(cfg)
        form = payload(item, cfg["Dietary"])
        if joined(item):
            rec.state["status"] = "already_registered_before_run"
            rec.emit("finished")
            return
        rec.emit("prepared", activity_id=item["id"])
        if not immediate:
            rec.state["status"] = "waiting_for_target"
            rec.emit("waiting_for_target")
            wait_until(target - timedelta(seconds=10), rec, "Ready; waiting to check session")
            client.check_session()
            if datetime.now(target.tzinfo) >= target:
                raise RuntimeError("Preparation missed target; reschedule instead of silently submitting late")
            wait_until(target, rec, "Session valid; waiting for registration")
        rec.state["status"] = "observing" if not args.submit else "ready_to_submit"
        rec.emit("target_reached")
        if args.mode == "early-selenium" or not args.submit:
            deadline = time.monotonic() + cfg["ObserveSeconds"]
            while True:
                item = client.detail(item["id"])
                if args.now:
                    break
                if joined(item) or str(item.get("non")) == "1":
                    break
                if str(item.get("savanon")) == "9" or str(item.get("sava")) == "8":
                    break
                if time.monotonic() >= deadline:
                    break
                time.sleep(cfg["PollSeconds"])
        if not args.submit:
            rec.state["status"] = "observed_only"
            rec.emit("finished")
            return
        if joined(item):
            rec.state["status"] = "already_registered_before_submit"
            rec.emit("finished")
            return
        if driver and str(item.get("non")) != "1":
            rec.state["status"] = "not_open_or_full"
            rec.emit("finished")
            return
        # Revalidate choices after the early-Selenium refresh.
        form = payload(item, cfg["Dietary"])
        rec.state["status"] = "submission_pending"
        rec.emit("submit_intent", activity_id=item["id"])
        response_code = "UNKNOWN"
        try:
            if driver:
                response_code = browser_submit(driver, item, cfg["Dietary"], rec, cfg["RequestTimeout"])
            else:
                response_code = code(client.request("POST", "fn/actjoin.php", form))
        except Exception as exc:
            rec.emit("submission_uncertain", error_type=type(exc).__name__)
        rec.state["response_code"] = response_code
        rec.emit("registration_response", result=response_code)
        # Never retry a registration POST, even after timeout. Read back only.
        confirmed = False
        for attempt in range(3):
            try:
                confirmed = joined(client.detail(item["id"]))
            except Exception as exc:
                rec.emit("verification_error", error_type=type(exc).__name__)
            if confirmed:
                break
            if attempt < 2:
                time.sleep(cfg["PollSeconds"])
        rec.state["status"] = ("registered_confirmed" if confirmed else
            "accepted_unverified" if response_code in ("INSERT", "RJ") else
            "rejected" if response_code in ("OVER", "NAVA", "OUT") else "unknown")
        rec.emit("finished")
    finally:
        if client and client.session:
            client.session.close()
        if driver:
            try:
                driver.quit()
            except Exception as exc:
                rec.emit("browser_cleanup_error", error_type=type(exc).__name__)


def report():
    for path in sorted((ROOT / "runs").glob("*/summary.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        print(path.parent.name, data["status"], data.get("response_code", ""),
              "submit_offset_ms=" + str(data.get("submit_offset_ms", "-")),
              "response_ms=" + str(data.get("response_ms", "-")),
              data["config"]["Event"], sep=" | ")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("early-selenium", "http", "report"))
    parser.add_argument("--config", type=Path, default=ROOT / "config.json")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--submit", action="store_true", help="Schedule one real registration attempt")
    action.add_argument("--now", action="store_true", help="Observe immediately without submitting")
    action.add_argument("--submit-once", action="store_true",
                        help="HTTP only: login and send one real registration attempt now")
    args = parser.parse_args()
    if args.submit_once and args.mode != "http":
        parser.error("--submit-once requires http mode")
    if args.mode == "report":
        report()
        return 0
    args.submit = args.submit or args.submit_once
    cfg = load_config(args.config)
    for name in ("PrepareSeconds", "PollSeconds", "ObserveSeconds", "RequestTimeout"):
        if not isinstance(cfg[name], (int, float)) or cfg[name] <= 0:
            parser.error(name + " must be positive")
    if cfg["PollSeconds"] < 0.5:
        parser.error("PollSeconds must be at least 0.5")
    if cfg["Dietary"] not in ("葷食", "素食"):
        parser.error("Dietary must match a supported meal option in config.json")
    zone = ZoneInfo(cfg.get("Timezone", "Asia/Taipei"))
    target = datetime.strptime(cfg["Time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=zone)
    if args.now or args.submit_once:
        target = datetime.now(zone)
    elif target <= datetime.now(zone):
        parser.error("Time is in the past; update config or use --now to observe")
    rec = Record(args.mode, cfg, args.submit, target)
    rec.state["execution"] = ("immediate_submit" if args.submit_once else
                              "immediate_observe" if args.now else "scheduled")
    rec.state["target_time"] = target.isoformat()
    rec.emit("execution_mode", execution=rec.state["execution"])
    try:
        run(args, cfg, target, rec)
    except (Exception, KeyboardInterrupt) as exc:
        rec.state["status"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "error"
        # Avoid arbitrary exception text, which can contain credentials or responses.
        details = {"error_type": type(exc).__name__}
        if isinstance(exc, ModuleNotFoundError):
            details["missing_module"] = exc.name
            print("Missing Python module:", exc.name, flush=True)
            print("Install project dependencies with: python -m pip install -r requirements.txt", flush=True)
        rec.emit("stopped", **details)
        return 1
    finally:
        print("Saved:", rec.directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
