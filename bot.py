#paper trading
import logging
import re
import telebot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, MessageHandler, CallbackQueryHandler, filters
)
import requests
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram & Birdeye Setup
# Telegram Bot Configuration
BOT_TOKEN=8022122944:AAGM0SxZAwF5V6gJg-yDVHNPls05lKoWMoo
ADMIN_ID=5950741458

# Birdeye API Configuration
BIRDEYE_API_KEY=cf6800ffe5754d46af1f2f3dda65ab31
bot = telebot.TeleBot(BOT_TOKEN)

# Referral Links
TROJAN_REF_LINK = "https://t.me/solana_trojanbot?start=r-abhyudday"
GMGN_REF_LINK = "https://t.me/GMGN_sol_bot?start=i_NEu2DbZx"

# Validate required environment variables
if not all([BOT_TOKEN, BIRDEYE_API_KEY, ADMIN_ID]):
    raise ValueError("Missing required environment variables. Please check your .env file.")

USERS = {}
logging.basicConfig(level=logging.INFO)

def is_solana_address(text):
    return bool(re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", text.strip()))

async def get_token_price(token_address):
    url = f"https://public-api.birdeye.so/defi/price?address={token_address}"
    headers = {
        "accept": "application/json",
        "x-chain": "solana",
        "X-API-KEY": BIRDEYE_API_KEY
    }
    response = await asyncio.to_thread(requests.get, url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return float(data["data"]["value"])
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in USERS:
        USERS[uid] = {
            'balance': 10000.0,
            'holdings': {},
            'realized_pnl': 0.0,
            'history': [],
            'context': {}
        }

    welcome_text = (
        "👋 Welcome to the Memecoin Paper Trading Bot!\n\n"
        "🎯 Practice trading Solana memecoins risk-free with paper money.\n"
        "💰 Start with $10,000 virtual balance\n\n"
        "🚀 Ready to trade with real money?\n"
        "Get MAX trading fee rebates with our partner bots:\n"
        "• Trojan Bot: Advanced trading features\n"
        "• GMGN Sniper: Fast and reliable trading\n\n"
        "Choose an action below:"
    )

    keyboard = [
        [InlineKeyboardButton("🟢 Buy", callback_data="menu_buy"),
         InlineKeyboardButton("🔴 Sell", callback_data="menu_sell")],
        [InlineKeyboardButton("💰 Balance", callback_data="menu_balance"),
         InlineKeyboardButton("📈 PnL", callback_data="menu_pnl")],
        [InlineKeyboardButton("🔁 Copy Trade", callback_data="menu_copy_trade"),
         InlineKeyboardButton("🔎 Check Wallet PnL", callback_data="menu_check_wallet_pnl")],
        [InlineKeyboardButton("👤 Track Wallet", callback_data="menu_track_wallet")],
        [InlineKeyboardButton("🚀 Trade with Trojan Bot", url=TROJAN_REF_LINK)],
        [InlineKeyboardButton("⚡ Trade with GMGN Sniper", url=GMGN_REF_LINK)]
    ]
    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_buy_start(query, context):
    USERS[query.from_user.id]['context'] = {'mode': 'buy'}
    await query.message.reply_text("🔍 Enter the Solana token contract address to buy:")

async def handle_sell_start(query, context):
    uid = query.from_user.id
    user = USERS.get(uid)
    tokens = list(user['holdings'].keys())
    if not tokens:
        await query.message.reply_text("📭 No tokens to sell.")
        return
    keyboard = [[InlineKeyboardButton(token, callback_data=f"sell_token:{token}")] for token in tokens]
    await query.message.reply_text("📉 Choose token to sell:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_token_selected_for_sell(query, context):
    uid = query.from_user.id
    token = query.data.split(":")[1]
    USERS[uid]['context'] = {'mode': 'sell', 'token': token}
    await query.message.reply_text("💸 Enter the % of token to sell:")

async def handle_buy_token(update, context, ca, usd_amount):
    uid = update.effective_user.id
    user = USERS[uid]
    price = await get_token_price(ca)
    if not price:
        await update.message.reply_text("❌ Token price fetch failed.")
        return

    qty = usd_amount / price
    user['balance'] -= usd_amount

    holding = user['holdings'].get(ca)
    if holding:
        total_cost = holding['qty'] * holding['avg_price'] + usd_amount
        new_qty = holding['qty'] + qty
        holding['avg_price'] = total_cost / new_qty
        holding['qty'] = new_qty
    else:
        user['holdings'][ca] = {'qty': qty, 'avg_price': price}

    user['history'].append(f"🟢 Bought {qty:.4f} of {ca} at ${price:.4f}")
    
    success_msg = (
        f"✅ Bought {qty:.4f} of {ca} at ${price:.4f}\n\n"
        f"🚀 Ready to trade with real money?\n"
        f"Get MAX trading fee rebates and instant execution:\n"
        f"• Trojan Bot: Advanced trading with limit orders\n"
        f"• GMGN Sniper: Lightning-fast MEV protection"
    )
    keyboard = [
        [InlineKeyboardButton("🚀 Trade with Trojan Bot", url=TROJAN_REF_LINK)],
        [InlineKeyboardButton("⚡ Trade with GMGN Sniper", url=GMGN_REF_LINK)]
    ]
    await update.message.reply_text(success_msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_sell_token(update, context, token, percent):
    uid = update.effective_user.id
    user = USERS[uid]
    holding = user['holdings'].get(token)
    if not holding:
        await update.message.reply_text("❌ You don't own this token.")
        return

    price = await get_token_price(token)
    if not price:
        await update.message.reply_text("❌ Token price fetch failed.")
        return

    qty_to_sell = holding['qty'] * (percent / 100)
    if qty_to_sell <= 0 or qty_to_sell > holding['qty']:
        await update.message.reply_text("❗ Invalid sell percentage.")
        return

    usd_value = qty_to_sell * price
    pnl = (price - holding['avg_price']) * qty_to_sell
    user['balance'] += usd_value
    user['realized_pnl'] += pnl
    holding['qty'] -= qty_to_sell

    if holding['qty'] <= 0.00001:
        del user['holdings'][token]

    user['history'].append(f"🔴 Sold {qty_to_sell:.4f} of {token} at ${price:.4f} | PnL: ${pnl:.2f}")
    
    success_msg = (
        f"✅ Sold {qty_to_sell:.4f} of {token} at ${price:.4f}\n"
        f"💵 PnL: ${pnl:.2f}\n\n"
        f"🚀 Want faster execution and better prices?\n"
        f"Trade with our partner bots and get:\n"
        f"• MAX trading fee rebates\n"
        f"• MEV protection\n"
        f"• Advanced trading features"
    )
    keyboard = [
        [InlineKeyboardButton("🚀 Trade with Trojan Bot", url=TROJAN_REF_LINK)],
        [InlineKeyboardButton("⚡ Trade with GMGN Sniper", url=GMGN_REF_LINK)]
    ]
    await update.message.reply_text(success_msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_balance(query, context):
    uid = query.from_user.id
    user = USERS[uid]
    balance = user['balance']

    msg = (
        f"💵 Cash: ${balance:.2f}\n"
        f"📦 Holdings Value: Click to Check token PnL\n\n"
        f"🚀 Ready to trade with real money?\n"
        f"Get MAX trading fee rebates with our partner bots:\n"
        f"• Trojan Bot: Advanced trading features\n"
        f"• GMGN Sniper: Fast and reliable trading"
    )
    keyboard = [
        [InlineKeyboardButton("📈 View Token PnL", callback_data="menu_pnl")],
        [InlineKeyboardButton("🚀 Trade with Trojan Bot", url=TROJAN_REF_LINK)],
        [InlineKeyboardButton("⚡ Trade with GMGN Sniper", url=GMGN_REF_LINK)]
    ]
    await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_pnl_tokens(query, context):
    uid = query.from_user.id
    user = USERS.get(uid)
    tokens = list(user['holdings'].keys())
    if not tokens:
        await query.message.reply_text("📭 No active positions.")
        return
    keyboard = [[InlineKeyboardButton(token, callback_data=f"pnl:{token}")] for token in tokens]
    await query.message.reply_text("📈 Click on a token to view PnL:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_token_pnl(query, context):
    uid = query.from_user.id
    token = query.data.split(":")[1]
    user = USERS.get(uid)
    holding = user['holdings'][token]
    price = await get_token_price(token)
    if not price:
        await query.message.reply_text("❌ Couldn't fetch price.")
        return

    qty = holding['qty']
    avg = holding['avg_price']
    pnl = (price - avg) * qty
    msg = (
        f"📊 Token: {token}\n"
        f"• Qty: {qty:.4f}\n"
        f"• Avg Price: ${avg:.4f}\n"
        f"• Current Price: ${price:.4f}\n"
        f"• PnL: ${pnl:.2f}"
    )
    await query.message.reply_text(msg)

async def handle_coming_soon(query, context, feature):
    msg = (
        f"🚧 {feature} feature is under construction.\n\n"
        f"🚀 In the meantime, start trading with real money!\n"
        f"Get MAX trading fee rebates with our partner bots:\n"
        f"• Trojan Bot: Advanced trading features\n"
        f"• GMGN Sniper: Fast and reliable trading"
    )
    keyboard = [
        [InlineKeyboardButton("🚀 Trade with Trojan Bot", url=TROJAN_REF_LINK)],
        [InlineKeyboardButton("⚡ Trade with GMGN Sniper", url=GMGN_REF_LINK)]
    ]
    await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != ADMIN_ID:
        await update.message.reply_text("🚫 You are not authorized to use this command.")
        return
    if not context.args:
        await update.message.reply_text("📝 Usage: /broadcast Your message here")
        return
    message = ' '.join(context.args)
    sent = 0
    for user_id in USERS:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"{message}")
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ Message sent to {sent} users.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    user = USERS.get(uid)
    if not user:
        await start(update, context)
        return

    ctx = user['context']
    if 'mode' in ctx:
        if ctx['mode'] == 'buy':
            if is_solana_address(text):
                ctx['ca'] = text
                await update.message.reply_text("💵 How much USD to invest?")
            elif 'ca' in ctx:
                try:
                    usd = float(text)
                    await handle_buy_token(update, context, ctx['ca'], usd)
                    user['context'] = {}
                except:
                    await update.message.reply_text("❌ Enter a valid USD amount.")
            return
        elif ctx['mode'] == 'sell' and 'token' in ctx:
            try:
                percent = float(text)
                await handle_sell_token(update, context, ctx['token'], percent)
                user['context'] = {}
            except:
                await update.message.reply_text("❌ Enter a valid percentage.")
            return

    if is_solana_address(text):
        keyboard = [
            [InlineKeyboardButton("🟢 Buy", callback_data=f"ca_buy:{text}"),
             InlineKeyboardButton("🔴 Sell", callback_data=f"ca_sell:{text}")]
        ]
        await update.message.reply_text("Detected token address. Choose action:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await start(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_buy":
        await handle_buy_start(query, context)
    elif data == "menu_sell":
        await handle_sell_start(query, context)
    elif data.startswith("sell_token:"):
        await handle_token_selected_for_sell(query, context)
    elif data == "menu_balance":
        await show_balance(query, context)
    elif data == "menu_pnl":
        await show_pnl_tokens(query, context)
    elif data.startswith("pnl:"):
        await show_token_pnl(query, context)
    elif data.startswith("ca_buy:"):
        ca = data.split(":")[1]
        USERS[query.from_user.id]['context'] = {'mode': 'buy', 'ca': ca}
        await query.message.reply_text("💵 How much USD to invest?")
    elif data.startswith("ca_sell:"):
        token = data.split(":")[1]
        USERS[query.from_user.id]['context'] = {'mode': 'sell', 'token': token}
        await query.message.reply_text("💸 Enter the % of token to sell:")
    elif data == "menu_copy_trade":
        await handle_coming_soon(query, context, "Copy Trade")
    elif data == "menu_check_wallet_pnl":
        await handle_coming_soon(query, context, "Check Wallet PnL")
    elif data == "menu_track_wallet":
        await handle_coming_soon(query, context, "Track Wallet")

# Main Setup
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    print("Bot running...")
    app.run_polling()
