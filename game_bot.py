import json
import hashlib
from datetime import datetime
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Bot config
TOKEN = "7657071291:AAGDd2qjNpE0MtX2J9DNCidu2GuHfySKXK8"  # Token từ @BotFather
DATA_FILE = "data.json"
KEYS_FILE = "keys.json"
WEBHOOK_URL = "YOUR_RENDER_URL_HERE"  # VD: https://vua-thoat-hiem.onrender.com/webhook
ROOMS = {
    "1": "Nhà kho", "2": "Văn phòng", "3": "Hầm mộ", "4": "Tàu vũ trụ",
    "5": "Lâu đài", "6": "Rừng ma", "7": "Thành phố bỏ hoang", "8": "Đền cổ"
}

app = Flask(__name__)
bot = Bot(TOKEN)
application = Application.builder().token(TOKEN).build()

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_keys():
    try:
        with open(KEYS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Chào mừng đến với *Vua Thoát Hiểm Elite*! 🔥\n"
        "👉 Vui lòng nhập key và UID bằng lệnh:\n/key <key> <uid>",
        parse_mode="Markdown"
    )

async def key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("❌ Dùng: /key <key> <uid>")
        return

    key, uid = args
    keys = load_keys()
    hashed_key = hashlib.sha256(key.encode()).hexdigest()
    data = load_data()

    if hashed_key not in keys:
        await update.message.reply_text("❌ Key không tồn tại hoặc đã bị xóa!")
        return

    expiry = datetime.fromisoformat(keys[hashed_key]["expiry"])
    if datetime.now() > expiry:
        await update.message.reply_text("❌ Key đã hết hạn!")
        return

    if hashed_key in data and data[hashed_key]["uid"] != uid:
        await update.message.reply_text("❌ Key đã được dùng bởi UID khác!")
        return

    data[hashed_key] = {"uid": uid, "active": True}
    save_data(data)
    msg = (
        f"✅ Kích hoạt thành công!\n🔑 Key: {key}\n🆔 UID: {uid}\n\n"
        "🔥 Chào mừng đến với *Vua Thoát Hiểm Elite*! 🔥\n"
        "Dùng các lệnh:\n👉 /bet <số/tên> để đặt cược\n👉 /killer <số/tên> để chọn killer\n"
        "👉 /submit để xác nhận\n\nPhòng:\n" +
        "\n".join(f"{k}. {v}" for k, v in ROOMS.items())
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    keys = load_keys()
    active_key = None
    for hashed_key, info in data.items():
        if info["active"] and hashed_key in keys:
            active_key = hashed_key
            break

    if not active_key or datetime.now() > datetime.fromisoformat(keys[active_key]["expiry"]):
        await update.message.reply_text("❌ Key đã bị xóa hoặc hết hạn! Nhập key mới bằng /key")
        return

    args = context.args
    if not args:
        await update.message.reply_text("❌ Dùng: /bet <số/tên>")
        return

    choice = args[0].lower()
    room = next((v for k, v in ROOMS.items() if choice == k or choice == v.lower()), None)
    if not room:
        await update.message.reply_text("❌ Phòng không hợp lệ! Chọn số 1-8 hoặc tên phòng.")
        return

    data[active_key]["bet"] = room
    save_data(data)
    await update.message.reply_text(f"✅ Đã đặt cược: {room}")

# Webhook endpoint
@app.route("/webhook", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(), bot)
    await application.process_update(update)
    return "OK"

def main():
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("key", key))
    application.add_handler(CommandHandler("bet", bet))
    # Thêm handler cho /killer, /submit nếu cần
    application.run_webhook(
        listen="0.0.0.0",
        port=8443,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8443)
