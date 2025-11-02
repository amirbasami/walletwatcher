import os
from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
SECRET = os.getenv("WEBHOOK_SECRET", "super-secret-path")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده.")

app = FastAPI()
tg_app: Application | None = None

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("WalletWatcher ✅ روی Render + Webhook بالا هستم.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message and update.effective_message.text:
        await update.effective_message.reply_text(update.effective_message.text)

async def build_app() -> Application:
    a = Application.builder().token(TOKEN).build()
    a.add_handler(CommandHandler("start", start_cmd))
    a.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    await a.initialize()
    return a

@app.on_event("startup")
async def on_startup():
    global tg_app
    tg_app = await build_app()

@app.get("/")
async def root():
    return {"ok": True}

@app.post(f"/webhook/{SECRET}")
async def webhook(request: Request):
    global tg_app
    if tg_app is None:
        tg_app = await build_app()
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(400, "invalid json")
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}
