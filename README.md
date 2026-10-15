# NTU SoC Registration Bot

Schedule registration for an event on the [NTU SoC website](https://soc.ee.ntu.edu.tw/www/).

Follow steps 1–7 for your first run. For each later event, update `config.json` in **step 4**, then use the **single check-and-launch command in step 5**. It checks all methods and starts them together; you do not need to run each method separately. Run commands from the project root.

The default workflow uses these three methods:

| Method | Behavior | Requirements |
| --- | --- | --- |
| HTTP | Logs in early and sends one registration request at opening | Python; no browser |
| Early-login Selenium | Logs in early, then uses the website controls at opening | Python and Chrome |
| Legacy Selenium | Starts browser login and interaction at opening; uses `NumBots` concurrent browsers | Python and Chrome; system time zone must match the event |

HTTP and early-login Selenium use `src/register.py` and save structured results. Legacy Selenium uses `src/Bot.py`. The default workflow runs all three through Bash and tmux on macOS, Linux, or Windows WSL. Native Windows users can use the optional individual Python commands below.

## Step 1: Prepare your computer

Install Miniconda or Anaconda, then open a terminal in this project directory. Check that conda is available:

```text
conda --version
```

| Platform | Terminal and setup |
| --- | --- |
| macOS | Terminal with zsh or Bash; execute `.sh` scripts normally, but do not source Bash scripts into zsh |
| Linux | Bash |
| Windows with WSL | Bash inside WSL; install conda and any required Chrome/tmux inside WSL, independently of Windows |
| Native Windows | Anaconda/Miniconda PowerShell prompt; use the Python command column in steps 5–7 |

For Selenium, install Chrome. Open `chrome://version` in Chrome to check its version and executable path, or use the appropriate terminal command:

| Platform | Chrome version check |
| --- | --- |
| macOS | `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version` |
| Linux / WSL | `google-chrome --version` (sometimes named `google-chrome-stable`) |
| Windows | Open `chrome://version` in Chrome |

For a per-user macOS installation, replace `/Applications` with `$HOME/Applications`. A `google-chrome: command not found` error on macOS does **not** mean Chrome is missing: that is a Linux command name. The Python code starts Chrome through `webdriver.Chrome(...)`, with discovery and driver management handled by [Selenium Manager](https://www.selenium.dev/documentation/selenium_manager/). Initial driver setup may need internet access. HTTP mode never starts Chrome.

For the default workflow, also install tmux in macOS/Linux/WSL and check `tmux -V`. Native PowerShell does not run the Bash/tmux workflow.

## Step 2: Install the Python environment

### macOS, Linux, or WSL

```bash
./init.sh
conda activate SoC
```

The installer creates `SoC` with Python 3.13.7 if needed, installs `requirements.txt`, and creates `.env` if missing. It preserves existing credentials. Rerun it when you need to reinstall dependencies; it does not install Chrome or tmux or start registration.

If activation asks for shell initialization, run `conda init zsh` or `conda init bash` for your shell, then reopen the terminal. Bash users can alternatively activate with `source scripts/env.sh`; do not source this script or `init.sh` into zsh.

### Native Windows

```powershell
conda create -n SoC python=3.13.7 -y
conda activate SoC
python -m pip install -r requirements.txt
python -m pip install tzdata
```

Skip the create command if `SoC` already exists. `tzdata` provides time-zone rules such as `Asia/Taipei`, which Windows usually does not supply to Python. Native Windows instructions have not been runtime-validated.

For every new terminal, activate `SoC` before using direct Python commands. The shell launchers select the environment automatically.

## Step 3: Enter your credentials

Create or edit `.env` in the project root:

```dotenv
URL="https://soc.ee.ntu.edu.tw/www/"
EMAIL="your-email"
PASSWORD="your-password"
```

Keep an existing working `.env`. It is ignored by Git; do not share credentials in logs or issue reports.

## Step 4: Configure your event

Edit `config.json` in the project root:

- `Time`: **registration opening time**, not the event start time, in `YYYY-MM-DD HH:MM:SS` format.
- `Event`: the complete title, exactly as shown on the website.
- `Dietary`: `葷食` (non-vegetarian) or `素食` (vegetarian). The website requires these Chinese values.

The example below is historical. **Replace its past date and event before scheduling.**

```json
{
    "NumBots": 5,
    "Headless": true,
    "WaitTimeout": 420,
    "Time": "2026-10-05 10:00:00",
    "Event": "115年度 SoC中心徵才說明會-瑞鼎科技",
    "Dietary": "葷食",
    "Timezone": "Asia/Taipei",
    "PrepareSeconds": 180,
    "PollSeconds": 1,
    "ObserveSeconds": 30,
    "RequestTimeout": 15
}
```

For your first run, leave the other values unchanged unless you need different behavior. JSON does not allow a trailing comma after the final property.

![Example event title on the website](images/event.png)

| Setting | Purpose | Applies to |
| --- | --- | --- |
| `Headless` | `true` hides Chrome; `false` shows it | Both Selenium methods |
| `NumBots` | Number of concurrent legacy browsers | **Legacy Selenium only** |
| `WaitTimeout` | Maximum element wait in seconds | **Legacy Selenium only** |
| `Timezone` | Time zone; default `Asia/Taipei` | HTTP and early-login Selenium |
| `PrepareSeconds` | Preparation lead time; 180 seconds = 3 minutes | HTTP and early-login Selenium |
| `PollSeconds` | Status polling interval; default 1 second, minimum 0.5 | HTTP and early-login Selenium |
| `ObserveSeconds` | Status polling window after opening; default 30 seconds | HTTP and early-login Selenium |
| `RequestTimeout` | Request or submission wait timeout; default 15 seconds | HTTP and early-login Selenium |
| `EventId` | Optional activity ID; the event title is still checked | HTTP and early-login Selenium |

Legacy Selenium uses the computer's local time zone. When running all methods, the system time zone must match the configured opening time. The new runner supplies defaults for its additional settings when loading an older configuration. `NumBots: 5` does not start five HTTP or early-login Selenium instances.

Configuration is read at startup. Restart a waiting process after changing it. See Optional commands for an alternative configuration; the all-methods launcher always reads the root-level `config.json`.

## Step 5: Check and launch with one command

After setup and event configuration, run this once on macOS, Linux, or WSL:

```bash
./scripts/test_all.sh && ./scripts/run_all.sh
```

**This is the default workflow; no separate per-method commands are needed.** `test_all.sh` checks all three methods without registering. Only if every check passes does `&&` start `run_all.sh`, which schedules **real registration** for all three in tmux. If a check fails, resolve it before retrying.

Expect three `PASS` results. HTTP and early-login Selenium log in and read the activity; verify that it matches your intended event. The legacy check only validates imports, configuration, and initialization offline; **it does not validate legacy browser login or submission**. Check logs are saved in `runs/check_all_<time>_<id>/`, including `results.txt`.

To check setup without scheduling registration, run only `./scripts/test_all.sh`. If those checks have already passed for the current configuration, run only `./scripts/run_all.sh` to schedule. Do not run it again after the combined command has already launched the session.

For a single method or native Windows without WSL, use [Individual methods](#individual-methods) instead.

## Step 6: Monitor or cancel registration

The command in step 5 already starts the scheduled runners; there is nothing else to launch.

**Start before the preparation time and keep the computer awake and online.** With `PrepareSeconds: 180` and a 10:00 opening:

```text
Before 09:57  Launch the runner
09:57        HTTP / early-login Selenium begin preparation
09:59:50     Recheck the session
10:00        HTTP submits; early-login Selenium refreshes and interacts
```

HTTP and early-login Selenium stop if scheduled preparation misses the opening time.

The new runner displays a countdown every second in an interactive terminal and records a heartbeat every 60 seconds. Redirected output prints waiting updates every 60 seconds. Each launch handles one event, not a recurring schedule.

### Running all three with tmux

`run_all.sh` creates a `soc-all` session with `http`, `selenium`, and `legacy` windows. It rejects past opening times, a mismatched system time zone, and an existing `soc-all` session, but does not detect separately started runners.

The methods share an account and have no coordination lock: they may submit independently, and their sessions may interact. Running all three does not guarantee better results. `NumBots: 5` creates five legacy browsers in addition to the early-login Selenium browser and HTTP process.

```bash
tmux attach -t soc-all
```

- Select a window: press `Ctrl+b`, release, then `w`.
- Detach and leave it running: press `Ctrl+b`, release, then `d`.
- Switch from another tmux session: `tmux switch-client -t soc-all`.
- Cancel all methods: `tmux kill-session -t soc-all`.

Detached sessions survive closing the terminal. Each window closes when its process exits; the session closes after the last one. No cleanup script is needed, but a stuck process is not forcibly stopped. Unsaved terminal output disappears on closure; saved run records remain. Closure alone does not mean registration succeeded.

Stopping a process does not undo an accepted registration. Check the website before restarting after an uncertain outcome.

## Step 7: Review the result

| macOS / Linux / WSL | Direct Python (all platforms) |
| --- | --- |
| `./scripts/report.sh` | `python src/register.py report` |

Read the status and server response together: **`registered_confirmed` + `INSERT`** means this request added the registration and a later query confirmed it. With `RJ`, the account was already registered. For `unknown` or an interrupted submission, check the website before trying again.

Legacy Selenium does not produce this report. Its success message reflects UI actions, not confirmed server acceptance.

Each HTTP or early-login Selenium run saves `runs/<start-time>_<mode>/`:

- `summary.json`: configuration, activity, status, response code, and timing.
- `events.jsonl`: timestamped progress, session checks, requests, responses, and sanitized errors.

Records update during execution. Their directory date is the process start date, which can precede the opening by several days. A saved `waiting` status does not prove the process is still running; check the latest heartbeat and process status.

### Status and response reference

| Status | Meaning |
| --- | --- |
| `registered_confirmed` | A subsequent query found the account registered; attribution requires the response code |
| `accepted_unverified` | Received `INSERT` or `RJ`, but readback did not confirm registration |
| `rejected` | Received a known rejection (`OVER`, `NAVA`, or `OUT`) |
| `unknown` | Submission outcome could not be determined |
| `observed_only` | Read-only observation completed |
| `already_registered_before_run` / `already_registered_before_submit` | Registration was already present; no new submission was made |
| `not_open_or_full` | Selenium could not proceed with an open registration state |
| `submission_pending` | Submission was about to happen; if interrupted, query status before trying again |
| `starting` / `waiting` / `preparing` / `waiting_for_target` / `observing` / `ready_to_submit` | Intermediate execution states |
| `error` / `interrupted` | Execution failed or was interrupted; inspect the last events |

| Server response | Meaning |
| --- | --- |
| `INSERT` | This request added a registration |
| `RJ` | The account was already registered |
| `OVER` | Capacity reached |
| `NAVA` | Requested attendance method unavailable |
| `OUT` | Outside the registration period |
| `UNKNOWN` | Unrecognized or unavailable response; not proof of rejection |

The runner performs at most three readback checks after a submission, including after an uncertain timeout. It does not retry the registration POST. If several methods run together, a readback with `ujoin: 1` alone cannot identify the winner; use `INSERT` versus `RJ`. A timeout followed by successful readback remains ambiguous about attribution.

`submit_offset_ms` measures the local submission start relative to the target, not arrival at the server. HTTP measures just before the client call; Selenium measures jQuery `ajaxSend`. Selenium's `response_ms` can include dismissing the native alert, so it is not directly equivalent to HTTP network latency. For `immediate_submit`, the target is invocation time, not the event opening time. Server Date headers are recorded for diagnosis, not automatic clock synchronization.

The new runner does not save credentials, cookies, raw responses, profiles, or full pages. Legacy Selenium (`src/Bot.py`) can still save HTML and screenshots; those files and `runs/` are ignored by Git. Sessions are not reused across executions.

## Optional commands

### Individual methods

Use these only if you want one method or are running native Windows without WSL. They are alternatives to step 5, not additional steps. Choose one method, run its check, then schedule it after confirming the result:

| Method | Check without registering | Schedule real registration |
| --- | --- | --- |
| HTTP | `python src/register.py http --now` | `python src/register.py http --submit` |
| Early-login Selenium | `python src/register.py early-selenium --now` | `python src/register.py early-selenium --submit` |
| Legacy Selenium | No standalone live observation mode | `python src/Bot.py` |

Activate `SoC` first. Successful observation normally ends with `observed_only` or `already_registered_before_run`; `session_check` should report `PASS`. `--now` also works with a past opening time.

On macOS/Linux/WSL, the equivalent launchers are `./scripts/run_http.sh`, `./scripts/run_selenium.sh`, and `./scripts/run_legacy.sh`. Add `--now` to either of the first two for a check without registration.

Individual methods run in the foreground: keep the terminal open, or press `Ctrl+C` to stop. Legacy Selenium can start immediately when its configured time is already past, so check its date carefully.

### Other actions

For HTTP and early-login Selenium, the shell launchers default to `--submit`; direct Python commands without an action flag only observe at the configured opening time. `--submit`, `--now`, and `--submit-once` are mutually exclusive.

| Task | Command (activate `SoC` first) |
| --- | --- |
| Observe at opening without registering | `python src/register.py http` or `python src/register.py early-selenium` |
| Submit one real HTTP request immediately | `python src/register.py http --submit-once` |
| Use another configuration | `python src/register.py http --now --config /path/to/config.json` |
| Show available options | `python src/register.py --help` |

`--submit-once` is HTTP-only and ignores the scheduled time. It is **not a simulation**. Already-registered activities are skipped; a timeout or `OUT` response does not trigger a retry.

Shell interpreter selection is: `PYTHON` environment variable, active `SoC`, `conda run -n SoC`, then `python` on PATH. To use a custom environment:

```bash
PYTHON=/path/to/venv/bin/python ./scripts/run_http.sh --now
```

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `Permission denied` for a shell script | Run `chmod +x init.sh scripts/*.sh` |
| `conda: command not found` | Install or initialize conda, then reopen the terminal |
| `ModuleNotFoundError` | Activate `SoC` and run `python -m pip install -r requirements.txt`; `missing_module` identifies the package |
| `google-chrome: command not found` | Use your platform's Chrome check in step 1 |
| Chrome or driver startup failure | Check Chrome installation, driver compatibility, and network access for downloads; set `Headless: false` to inspect the browser |
| `ZoneInfoNotFoundError` | In the active environment, run `python -m pip install tzdata` |
| Login or session failure | Check `.env` and the recorded response codes |
| Opening time is in the past | Update `Time`; use `--now` only for immediate observation |
| Activity not found | Verify the complete title; optionally set `EventId` (the title is still checked) |
| `Session soc-all already exists` | Inspect it with `tmux attach -t soc-all` before starting another run |
| No new waiting output | Check the heartbeat timestamp and whether Python is still running using your system's process monitor |
| tmux session disappeared | Review the report and logs; all processes may have exited |

When reporting a problem, include the sanitized error and outcome without credentials or personal data.

## Limits and project files

Only the NTU SoC HTTPS site is supported. Activity 137 requires extra profile confirmation and is unsupported by the new runner. Unsupported meal formats also stop execution. Website changes may require adapter updates.

A recorded run on 2026-10-05 returned `INSERT` for HTTP and `RJ` for early-login Selenium. This confirms those request paths worked then; it does not establish that Selenium would have secured a place independently. Historical evidence remains in local `runs/` records.

| Path | Purpose |
| --- | --- |
| `config.json` / `.env` | Event settings / local credentials |
| `requirements.txt` / `init.sh` | Python dependencies / installer entry point |
| `src/register.py` | HTTP, early-login Selenium, and reports |
| `src/Bot.py` | Legacy Selenium |
| `scripts/` | Setup, environment activation, launchers, checks, and reports |
| `runs/` | Local logs and results; ignored by Git |

Older root-level launch commands have moved to `scripts/`, and Python entry points to `src/`. `init.sh` remains at the root. For Python imports, use `from src import Bot, register`; the legacy `Bot`, `job`, and `multi_thread_run` APIs remain available.

Use the tool only for registrations you are authorized to make, follow the website's rules, and avoid excessive requests.
