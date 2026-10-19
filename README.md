# Crypto Monitor Bot

A Python-powered Discord bot for tracking cryptocurrency prices, monitoring market trends, and receiving automated alerts.

## Features

- **Price Tracking:** Check current cryptocurrency prices.
- **Market Rankings:** View cryptocurrencies ranked by market capitalization.
- **Gainers:** Find coins with the strongest reported 24-hour price changes.
- **Market Cap Lookup:** Check market capitalization for supported coins.
- **Automated Alerts:** Receive alerts when monitored coins meet configured 24-hour price-change thresholds.
- **Discord Integration:** Access features through simple Discord commands.

## Tech Stack

- Python
- discord.py
- CoinGecko API
- Requests
- python-dotenv

## Setup

1. Clone this repository:

   ```bash
   git clone https://github.com/siddhantsinhal1812/Crypto_Bot.git
   cd Crypto_Bot
   ```

2. Create and activate a virtual environment.

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project directory:

   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token
   COINGECKO_API_KEY=your_coingecko_api_key
   ALERT_CHANNEL_ID=your_discord_channel_id
   ```

   Keep your actual credentials private. Never commit your `.env` file.

5. Run the bot:

   ```bash
   python bot.py
   ```

## Discord Commands

| Command | Description |
|---|---|
| `!ping` | Check whether the bot responds |
| `!price bitcoin` | Check Bitcoin's price |
| `!top 10` | View leading cryptocurrencies |
| `!gainers 10` | View leading gainers |
| `!marketcap bitcoin` | Look up market capitalization |
| `!helpcrypto` | View bot commands |

## Future Improvements

- Technical-indicator analysis
- Historical backtesting
- Liquidity and volume filters
- Expanded coin coverage

## Disclaimer

This project is for educational purposes and does not provide financial advice.