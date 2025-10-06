# NTU SoC Reservation Bot

An automated Python bot for making reservations on NTU SoC websites. This bot uses Selenium WebDriver to automate the booking process and can be scheduled to run at specific times.

## Features

- 🤖 **Automated Login**: Securely logs into the reservation system
- 📅 **Smart Scheduling**: Can be scheduled to run at specific times/days
- ⚙️ **Configurable**: Highly customizable through configuration files
- 🌐 **Headless Mode**: Can run without opening browser window

## Installation

1. **Clone or download this repository**

2. **Run the setup script**:
   ```bash
   source init.sh
   ```

3. **Activate the environment**:
   ```bash
   source env.sh
   ```

## Configuration

### 1. Environment Variables (.env)

Edit the `.env` file with your credentials:

```env
URL="https://soc.ee.ntu.edu.tw/www/"
EMAIL=""
PASSWORD=""
```

### 2. Bot Configuration (config.json)

Customize your reservation preferences in `config.json`:

```json
{
    "NumBots": 3,
    "Headless": false,
    "WaitTimeout": 420,
    "Time": "2025-10-06 10:00:00",
    "Event": "114年度 SoC中心徵才說明會-群聯電子", 
    "Dietary": "葷食"
}
```
* `NumBots`: The number of robots to make the reservation
* `Headless`: `true` for no GUI, `false` for showing the window
* `WaitTimeout`: Maximum wait time in seconds for web elements to become available. If exceeded, the operation fails and the browser closes
* `Time`: The scheduled reservation time
* `Event`: The event name on NTU SoC Website, see the example below
* `Dietary`: "葷食" or "素食"

![Event Name Example](images/event.png)

*Example picture demonstrating how to find the event name. The highlighted text -114年度 SoC中心徵才說明會-群聯電子- is the event name. Remember to change the event name before running the bot*
## Usage

###  Step 1. Activate conda environment

```bash
# Activate environment
source env.sh
```
### Step 2. Customize configurations
Edit the `config.json` to specify your reservation details:
```json
{
    "NumBots": 3,
    "Headless": false,
    "WaitTimeout": 420,
    "Time": "2025-10-06 10:00:00",
    "Event": "114年度 SoC中心徵才說明會-群聯電子", 
    "Dietary": "葷食"
}
```

### Step 3. Run the bot
```
python Bot.py
```

## Project Structure

```
NTU_SoC_Bot/
├── Bot.py              # Main bot script
├── requirements.txt    # Python dependencies
├── config.json         # Bot configuration
├── .env                # Your credentials (created by init.sh)
├── init.sh             # Setup script
├── env.sh              # Environment activation script
└── README.md           # This file
```


## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you've run `init.sh` and activated the environment with `source env.sh`

2. **Login failures**: 
   - Check your credentials in `.env`
   - Verify the login URL is correct
   - Update login form selectors if the website structure changed

3. **Element not found errors**:
   - The website structure may have changed
   - Update the CSS selectors/XPath expressions in the code
   - Use browser developer tools to inspect elements

4. **Chrome driver issues**:
   - The bot automatically downloads the appropriate ChromeDriver
   - Make sure Chrome browser is installed

### Debug Mode

To run in debug mode (with visible browser):

```python
bot = Bot(headless=False)
```

## Legal and Ethical Considerations

⚠️ **Important**: 
- Only use this bot for legitimate reservations
- Respect the website's terms of service
- Don't overload the server with excessive requests
- Ensure you have permission to automate interactions with the target website

## Contributing

Feel free to submit issues and enhancement requests!

## License

Use responsibly and in accordance with your institution's policies.

---
