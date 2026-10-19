import ssl
import certifi
import os
import asyncio
import logging

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from crypto import (
    CryptoAPIError,
    fetch_coin_price,
    fetch_market_data,
    format_market_cap,
    format_price,
)

# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ALERT_CHANNEL_ID = os.getenv("ALERT_CHANNEL_ID")

ALERT_THRESHOLD = 5.0
MONITOR_INTERVAL_MINUTES = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# Discord bot setup
# --------------------------------------------------

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)

# Track the last alert direction for each coin.
last_alerts = {}


# --------------------------------------------------
# Events
# --------------------------------------------------

@bot.event
async def on_ready():
    logger.info("Bot is online as %s", bot.user)

    if not monitor_market.is_running():
        monitor_market.start()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"Missing argument: `{error.param.name}`. "
            "Use `!helpcrypto` to see available commands."
        )
        return

    if isinstance(error, commands.BadArgument):
        await ctx.send(
            "Invalid argument. Please check the command format."
        )
        return

    logger.error(
        "Command error in %s: %s",
        ctx.command,
        error,
        exc_info=error,
    )

    await ctx.send(
        "Something went wrong while running that command. "
        "Please try again."
    )


# --------------------------------------------------
# Basic commands
# --------------------------------------------------

@bot.command()
async def ping(ctx):
    """Check whether the bot is online."""
    await ctx.send(
        "Pong! Crypto Monitor Bot is online."
    )


@bot.command(name="helpcrypto")
async def helpcrypto_command(ctx):
    """Display all available crypto commands."""
    await ctx.send(
        "**Crypto Monitor Bot Commands**\n\n"
        "`!ping` — Check bot status\n"
        "`!price bitcoin` — Get Bitcoin's price\n"
        "`!price ethereum usd` — Get Ethereum's price in USD\n"
        "`!top` — Show the top 10 cryptocurrencies\n"
        "`!top 15` — Show the top 15 cryptocurrencies\n"
        "`!gainers` — Show the biggest 24-hour gainers\n"
        "`!marketcap bitcoin` — Show Bitcoin's market cap\n"
        "`!helpcrypto` — Show this help message"
    )


# --------------------------------------------------
# Price command
# --------------------------------------------------

@bot.command(name="price")
async def price_command(
    ctx,
    coin_id: str,
    currency: str = "usd",
):
    """
    Get a cryptocurrency's current price.

    Examples:
        !price bitcoin
        !price ethereum usd
        !price solana eur
    """
    try:
        result = await asyncio.to_thread(
            fetch_coin_price,
            coin_id,
            currency,
        )

        change = result["change_24h"]

        if change is None:
            change_text = "Unavailable"
        else:
            change_text = f"{change:+.2f}%"

        await ctx.send(
            f"**{result['id'].title()}**\n"
            f"Price: {format_price(result['price'], currency)}\n"
            f"24-hour change: {change_text}"
        )

    except (CryptoAPIError, ValueError) as error:
        await ctx.send(f"Couldn't get that price: {error}")


# --------------------------------------------------
# Top cryptocurrencies
# --------------------------------------------------

@bot.command(name="top")
async def top_command(ctx, limit: int = 10):
    """
    Display cryptocurrencies ranked by market cap.

    Examples:
        !top
        !top 15
    """
    if not 1 <= limit <= 15:
        await ctx.send(
            "Please choose a number between 1 and 15."
        )
        return

    try:
        coins = await asyncio.to_thread(
            fetch_market_data,
            limit,
        )

        lines = [
            "**Top Cryptocurrencies by Market Cap**"
        ]

        for index, coin in enumerate(coins, start=1):
            change = coin.get(
                "price_change_percentage_24h"
            )

            change_text = (
                f"{change:+.2f}%"
                if change is not None
                else "N/A"
            )

            lines.append(
                f"`{index:>2}.` **{coin['name']}** "
                f"({coin['symbol'].upper()}) — "
                f"{format_price(coin['current_price'])} "
                f"| 24h: {change_text}"
            )

        # Discord messages have a 2,000-character limit.
        message = "\n".join(lines)

        if len(message) <= 2000:
            await ctx.send(message)
        else:
            await ctx.send(lines[0])
            for line in lines[1:]:
                await ctx.send(line)

    except (CryptoAPIError, ValueError) as error:
        await ctx.send(
            f"Market data is unavailable: {error}"
        )


# --------------------------------------------------
# Biggest gainers
# --------------------------------------------------

@bot.command(name="gainers")
async def gainers_command(ctx, limit: int = 10):
    """
    Display the biggest 24-hour gainers among the
    top 100 cryptocurrencies by market cap.

    Examples:
        !gainers
        !gainers 5
    """
    if not 1 <= limit <= 15:
        await ctx.send(
            "Please choose a number between 1 and 15."
        )
        return

    try:
        coins = await asyncio.to_thread(
            fetch_market_data,
            100,
        )

        coins = [
            coin
            for coin in coins
            if coin.get(
                "price_change_percentage_24h"
            ) is not None
        ]

        coins.sort(
            key=lambda coin: coin[
                "price_change_percentage_24h"
            ],
            reverse=True,
        )

        lines = [
            "**24-Hour Crypto Gainers**",
            "_Among the top 100 coins by market cap_",
        ]

        for coin in coins[:limit]:
            change = coin[
                "price_change_percentage_24h"
            ]

            lines.append(
                f"**{coin['name']}** "
                f"({coin['symbol'].upper()}) — "
                f"{change:+.2f}%"
            )

        await ctx.send("\n".join(lines))

    except (CryptoAPIError, ValueError) as error:
        await ctx.send(
            f"Market data is unavailable: {error}"
        )


# --------------------------------------------------
# Market capitalization command
# --------------------------------------------------

@bot.command(name="marketcap")
async def marketcap_command(ctx, coin_id: str):
    """
    Display market cap and rank for a coin.

    Example:
        !marketcap bitcoin
    """
    try:
        coins = await asyncio.to_thread(
            fetch_market_data,
            100,
        )

        coin = next(
            (
                item
                for item in coins
                if item["id"] == coin_id.lower()
            ),
            None,
        )

        if coin is None:
            await ctx.send(
                "Coin not found in the top 100. "
                "Try `!top` or use a valid CoinGecko coin ID."
            )
            return

        market_cap = format_market_cap(
            coin.get("market_cap")
        )

        rank = coin.get("market_cap_rank", "N/A")

        await ctx.send(
            f"**{coin['name']} "
            f"({coin['symbol'].upper()})**\n"
            f"Market cap: {market_cap}\n"
            f"Market-cap rank: {rank}"
        )

    except (CryptoAPIError, ValueError) as error:
        await ctx.send(
            f"Market data is unavailable: {error}"
        )


# --------------------------------------------------
# Automatic market alerts
# --------------------------------------------------

@tasks.loop(minutes=MONITOR_INTERVAL_MINUTES)
async def monitor_market():
    """
    Check the top 20 coins every 10 minutes.

    Alert when the reported 24-hour change reaches
    +5% or -5%. This is a 24-hour change threshold,
    not a 5% move since the previous check.
    """
    if not ALERT_CHANNEL_ID:
        return

    try:
        channel_id = int(ALERT_CHANNEL_ID)

        channel = bot.get_channel(channel_id)

        if channel is None:
            channel = await bot.fetch_channel(
                channel_id
            )

        coins = await asyncio.to_thread(
            fetch_market_data,
            20,
        )

        current_alerts = {}

        for coin in coins:
            change = coin.get(
                "price_change_percentage_24h"
            )

            if change is None:
                continue

            coin_id = coin["id"]

            if change >= ALERT_THRESHOLD:
                direction = "up"
            elif change <= -ALERT_THRESHOLD:
                direction = "down"
            else:
                continue

            current_alerts[coin_id] = direction

            # Avoid repeating the same-direction alert
            # on every monitoring cycle.
            if last_alerts.get(coin_id) == direction:
                continue

            arrow = (
                "📈" if direction == "up" else "📉"
            )

            message = (
                f"{arrow} **{coin['name']} "
                f"({coin['symbol'].upper()})** "
                f"is at {change:+.2f}% over 24 hours.\n"
                f"Current price: "
                f"{format_price(coin['current_price'])}"
            )

            try:
                await channel.send(message)
            except discord.HTTPException:
                logger.exception(
                    "Could not send alert for %s",
                    coin_id,
                )

        # Update alert history after processing the coins.
        last_alerts.clear()
        last_alerts.update(current_alerts)

    except (CryptoAPIError, ValueError) as error:
        logger.warning(
            "Market monitoring error: %s",
            error,
        )

    except discord.HTTPException:
        logger.exception(
            "Could not access the alert channel."
        )

    except Exception:
        logger.exception(
            "Unexpected error during market monitoring."
        )


@monitor_market.before_loop
async def before_monitor_market():
    """Wait until Discord is ready before monitoring."""
    await bot.wait_until_ready()


# --------------------------------------------------
# Start the bot
# --------------------------------------------------


# --------------------------------------------------
# Start the bot
# --------------------------------------------------

async def main():
    if not TOKEN:
        raise RuntimeError(
            "DISCORD_BOT_TOKEN is missing from your .env file."
        )

    ssl_context = ssl.create_default_context(
        cafile=certifi.where()
    )

    connector = discord.http.aiohttp.TCPConnector(
        ssl=ssl_context
    )

    async with bot:
        # Configure the bot's HTTP client to use
        # the trusted certificate bundle.
        bot.http.connector = connector
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
