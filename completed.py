import os
import random
import aiohttp
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from keep_alive import keep_alive

# =========================
# LOAD ENV
# =========================

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1546218403264729108

# =========================
# DISCORD SETUP
# =========================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# =========================
# FALLBACK PRICES
# =========================

FALLBACK_PRICES = {
    "bitcoin": 75000,
    "ethereum": 2100,
    "solana": 85,
    "litecoin": 70,
    "tether": 1
}

# =========================
# CRYPTO DATA
# =========================

CRYPTOS = [
    {
        "name": "Litecoin",
        "symbol": "LTC",
        "coingecko": "litecoin",
        "explorer": "Blockcypher",
        "button_url": "https://live.blockcypher.com/ltc/tx/",
        "image": "https://media.discordapp.net/attachments/1507379117589528686/1509317373151281172/Groupe_22.png?format=webp&quality=lossless"
    },

    {
        "name": "Solana",
        "symbol": "SOL",
        "coingecko": "solana",
        "explorer": "Solscan",
        "button_url": "https://solscan.io/tx/",
        "image": "https://media.discordapp.net/attachments/1507379117589528686/1509317427081515148/image.png?format=webp&quality=lossless"
    },

    {
        "name": "Bitcoin",
        "symbol": "BTC",
        "coingecko": "bitcoin",
        "explorer": "Mempool",
        "button_url": "https://mempool.space/tx/",
        "image": "https://media.discordapp.net/attachments/1507379117589528686/1509317448304951296/Groupe_14.png?format=webp&quality=lossless"
    },

    {
        "name": "Ethereum",
        "symbol": "ETH",
        "coingecko": "ethereum",
        "explorer": "Etherscan",
        "button_url": "https://etherscan.io/tx/",
        "image": "https://media.discordapp.net/attachments/1507379117589528686/1509317470060679218/Groupe_21.png?format=webp&quality=lossless"
    },

    {
        "name": "USDT [ERC-20]",
        "symbol": "USDT",
        "coingecko": "tether",
        "explorer": "Etherscan",
        "button_url": "https://etherscan.io/tx/",
        "image": "https://media.discordapp.net/attachments/1500924796261761219/1543693344331276399/image.png?ex=6a95cbf5&is=6a947a75&hm=e9c74305945f26304b077371c1a6ea62fdbae898bfac14d054040266433c7cd7&=&format=webp&quality=lossless"
    }
]

# =========================
# RANDOM TX HASH
# =========================

def random_tx():
    chars = "abcdef0123456789"
    return "0x" + "".join(
        random.choice(chars)
        for _ in range(64)
    )

# =========================
# GET LIVE PRICE
# =========================

async def get_live_price(coin_id):

    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        f"?ids={coin_id}&vs_currencies=usd"
    )

    try:

        async with aiohttp.ClientSession() as session:

            async with session.get(
                url,
                timeout=10
            ) as response:

                data = await response.json()

                if (
                    coin_id in data and
                    "usd" in data[coin_id]
                ):
                    return float(
                        data[coin_id]["usd"]
                    )

                print(
                    f"Missing price for {coin_id}"
                )

    except Exception as e:

        print(
            f"Price error for {coin_id}: {e}"
        )

    return FALLBACK_PRICES[coin_id]

# =========================
# GENERATE EMBED
# =========================

async def generate_embed():

    crypto = random.choice(CRYPTOS)

    # LIVE PRICE
    price = await get_live_price(
        crypto["coingecko"]
    )

    # RANDOM USD
    usd = round(
        random.uniform(1, 10000),
        2
    )

    # DECIMALS
    decimals = (
        6 if crypto["symbol"] == "USDT"
        else 8
    )

    # CONVERT
    crypto_amount = usd / price

    # TX HASH
    tx_hash = random_tx()

    # EMBED
    embed = discord.Embed(
        title=f"{crypto['name']} Deal Complete",
        color=0x52F85A
    )

    # AMOUNT
    embed.add_field(
        name="Amount",
        value=(
            f"`{crypto_amount:.{decimals}f}` "
            f"{crypto['symbol']} "
            f"(${usd:,.2f} USD)"
        ),
        inline=False
    )

    # SENDER
    embed.add_field(
        name="Sender",
        value="`Anonymous`",
        inline=True
    )

    # RECEIVER
    embed.add_field(
        name="Receiver",
        value="`Anonymous`",
        inline=True
    )

    # TRANSACTION
    embed.add_field(
        name="Transaction",
        value=(
            f"{tx_hash[:6]}...{tx_hash[-6:]} "
            f"([View Transaction]"
            f"({crypto['button_url']}{tx_hash}))"
        ),
        inline=False
    )

    # THUMBNAIL
    if crypto["image"]:

        embed.set_thumbnail(
            url=crypto["image"]
        )

    # BUTTON
    view = discord.ui.View()

    view.add_item(
        discord.ui.Button(
            label=f"View on {crypto['explorer']}",
            url=(
                f"{crypto['button_url']}"
                f"{tx_hash}"
            )
        )
    )

    return embed, view

# =========================
# AUTO SEND LOOP
# =========================

@tasks.loop(minutes=1)
async def auto_send():

    channel = bot.get_channel(
        CHANNEL_ID
    )

    if not channel:

        print("Channel not found.")
        return

    try:

        embed, view = await generate_embed()

        await channel.send(
            embed=embed,
            view=view
        )

        print("Auto embed sent.")

    except Exception as e:

        print(f"Auto send error: {e}")

# =========================
# /SEND COMMAND
# =========================

@bot.tree.command(
    name="send",
    description="Send one demo deal embed"
)
async def send(
    interaction: discord.Interaction
):

    try:

        embed, view = await generate_embed()

        await interaction.channel.send(
            embed=embed,
            view=view
        )

        await interaction.response.send_message(
            "Sent.",
            ephemeral=True
        )

    except Exception as e:

        await interaction.response.send_message(
            f"Error: {e}",
            ephemeral=True
        )

# =========================
# READY
# =========================

@bot.event
async def on_ready():

    await bot.tree.sync()

    print(
        f"Logged in as {bot.user}"
    )

    if not auto_send.is_running():

        auto_send.start()

# =========================
# RUN BOT
# =========================

keep_alive()
bot.run(TOKEN)
