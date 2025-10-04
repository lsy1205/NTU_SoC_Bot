# NTU SoC Reservation Bot

An automated Python bot for making reservations on NTU SoC websites. This bot uses Selenium WebDriver to automate the booking process and can be scheduled to run at specific times.

## Features

- 🤖 **Automated Login**: Securely logs into the reservation system
- 📅 **Smart Scheduling**: Can be scheduled to run at specific times/days
- 🔄 **Retry Logic**: Automatically retries failed reservation attempts
- ⚡ **Availability Checking**: Checks slot availability before booking
- 📊 **Logging**: Comprehensive logging for monitoring and debugging
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
# Login credentials
USERNAME=your_ntu_username
PASSWORD=your_password

# Bot settings
MAX_RETRIES=3
RETRY_DELAY=5
HEADLESS_MODE=true
```

### 2. Bot Configuration (config.json)

Customize your reservation preferences in `config.json`:

```json
{
  "scheduling": {
    "auto_book": false,
    "schedule_days": ["monday", "thursday"],
    "schedule_time": "10:00"
  }
}
```

## Usage

### Basic Usage

```bash
# Activate environment
source env.sh

# Run the bot
python Bot.py
```

### Customizing Reservations

Edit the `main()` function in `Bot.py` to specify your reservation details:

```python
reservation_details = {
    'date': '2025-10-11',        # YYYY-MM-DD format
    'time': '14:00',             # HH:MM format  
    'facility': 'Study Room 1',  # Room/facility name
    'purpose': 'Group Study'     # Purpose of booking
}
```

### Scheduling (Optional)

To enable automatic scheduling, uncomment the scheduling section in the `main()` function:

```python
# Schedule reservation attempts
schedule.every().monday.at("09:00").do(schedule_reservation_job)
schedule.every().wednesday.at("09:00").do(schedule_reservation_job)
```

## Customization for Different Websites

The bot is designed to be adaptable. To use it with your specific booking website:

1. **Update the login selectors** in the `login()` method:
   ```python
   username_field = self.wait.until(
       EC.presence_of_element_located((By.NAME, "username"))  # Update selector
   )
   ```

2. **Modify the reservation form selectors** in `make_reservation()`:
   ```python
   date_field = self.wait.until(
       EC.element_to_be_clickable((By.NAME, "date"))  # Update selector
   )
   ```

3. **Update the availability check logic** in `check_availability()` based on your site's implementation.

## Project Structure

```
NTU_SoC_Bot/
├── Bot.py              # Main bot script
├── requirements.txt    # Python dependencies
├── config.json        # Bot configuration
├── .env.example       # Environment template
├── .env               # Your credentials (created by init.sh)
├── init.sh            # Setup script
├── env.sh             # Environment activation script
├── README.md          # This file
└── reservation_bot.log # Log file (created when bot runs)
```

## Logging

The bot creates detailed logs in `reservation_bot.log`. Log levels include:
- INFO: General information and successful operations
- ERROR: Failed operations and errors
- WARNING: Potential issues

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
bot = ReservationBot(headless=False)
```

## Legal and Ethical Considerations

⚠️ **Important**: 
- Only use this bot for legitimate reservations
- Respect the website's terms of service
- Don't overload the server with excessive requests
- Use appropriate delays between requests
- Ensure you have permission to automate interactions with the target website

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is for educational purposes. Use responsibly and in accordance with your institution's policies.

---
