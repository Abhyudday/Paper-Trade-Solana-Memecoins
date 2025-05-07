# Solana Paper Trading Bot

A Telegram bot for paper trading Solana tokens.

## Setup

1. Clone the repository:
```bash
git clone https://github.com/Abhyudday/Solana-Paper-Trading-Bot.git
cd Solana-Paper-Trading-Bot
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Create a `.env` file in the root directory
   - Add the following variables:
     ```
     BOT_TOKEN=your_telegram_bot_token_here
     ADMIN_ID=your_telegram_user_id_here
     BIRDEYE_API_KEY=your_birdeye_api_key_here
     ```
   - Replace the placeholder values with your actual credentials

5. Run the bot:
```bash
python bot.py
```

## Environment Variables

- `BOT_TOKEN`: Your Telegram bot token from [@BotFather](https://t.me/BotFather)
- `ADMIN_ID`: Your Telegram user ID (you can get this from [@userinfobot](https://t.me/userinfobot))
- `BIRDEYE_API_KEY`: Your Birdeye API key from [Birdeye](https://birdeye.so/)

## Features

- Paper trading of Solana tokens
- Real-time price tracking
- Portfolio management
- PnL tracking
- Copy trading (coming soon)
- Wallet tracking (coming soon)

## Security

- Never commit your `.env` file
- Keep your API keys secure
- The bot uses in-memory storage for user data
- No sensitive data is stored permanently

## Contributing

Feel free to open issues and pull requests!

## License

MIT License
