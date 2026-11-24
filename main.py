import os, json, hmac, hashlib, time, sqlite3
from urllib.parse import parse_qsl
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DAVID_ID = int(os.getenv("DAVID_TELEGRAM_ID", "7948603698"))
ALBINA_ID = int(os.getenv("ALBINA_TELEGRAM_ID", "8660771174"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "").rstrip("/")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-this-secret")
DB_PATH = os.getenv("DB_PATH", "/data/submissions.db")

if not BOT_TOKEN:
    raise RuntimeError("Set BOT_TOKEN in Railway Variables")
bot = Bot(BOT_TOKEN)
dp = Dispatcher()
app = FastAPI(title="Для Альбины")
app.mount("/static", StaticFiles(directory="static"), name="static")

def db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        payload TEXT NOT NULL
    )""")
    con.commit()
    return con

def validate_init_data(init_data: str):
    if not init_data:
        raise HTTPException(401, "Открой мини-приложение через Telegram")
    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = values.pop("hash", None)
    if not received_hash:
        raise HTTPException(401, "Не удалось проверить Telegram")
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        raise HTTPException(401, "Проверка Telegram не пройдена")
    auth_date = int(values.get("auth_date", "0"))
    if time.time() - auth_date > 86400:
        raise HTTPException(401, "Сессия устарела. Открой приложение заново")
    user = json.loads(values.get("user", "{}"))
    return int(user.get("id", 0)), user

@dp.message(CommandStart())
async def start(message: types.Message):
    if message.from_user.id != ALBINA_ID:
        await message.answer("Это личное приглашение. Оно предназначено для Альбины 🌷")
        return
    if not WEBAPP_URL:
        await message.answer("Ссылка мини-приложения ещё не настроена. Давид скоро всё подключит 💌")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Открыть открытку 💌", web_app=WebAppInfo(url=WEBAPP_URL))
    ]])
    await message.answer(
        "Альбина, тебе пришло маленькое приглашение от Давида. "
        "Открывай, только если есть настроение — никакого давления 🌷",
        reply_markup=keyboard
    )

@app.get("/")
async def index():
    return FileResponse("static/index.html")

@app.get("/api/status")
async def status(request: Request):
    uid, _ = validate_init_data(request.headers.get("X-Telegram-Init-Data", ""))
    if uid != ALBINA_ID:
        raise HTTPException(403, "Это приглашение адресовано Альбине")
    con = db()
    used = con.execute("SELECT COUNT(*) FROM submissions WHERE telegram_id=?", (uid,)).fetchone()[0]
    con.close()
    return {"used": used, "remaining": max(0, 2-used)}

@app.post("/api/submit")
async def submit(request: Request):
    uid, user = validate_init_data(request.headers.get("X-Telegram-Init-Data", ""))
    if uid != ALBINA_ID:
        raise HTTPException(403, "Это приглашение адресовано Альбине")
    payload = await request.json()
    if not payload.get("consent"):
        raise HTTPException(400, "Нужно подтвердить отправку ответа")
    if not payload.get("date") or not payload.get("time"):
        raise HTTPException(400, "Выбери дату и время")
    con = db()
    used = con.execute("SELECT COUNT(*) FROM submissions WHERE telegram_id=?", (uid,)).fetchone()[0]
    if used >= 2:
        con.close()
        raise HTTPException(429, "Лимит в два отправления уже использован 💌")
    created = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    con.execute("INSERT INTO submissions (telegram_id, created_at, payload) VALUES (?,?,?)",
                (uid, created, json.dumps(payload, ensure_ascii=False)))
    con.commit()
    con.close()

    answers = payload.get("answers", [])
    lines = [
        "💌 НОВЫЙ ОТВЕТ ИЗ ОТКРЫТКИ",
        f"От: {user.get('first_name','Альбина')} (Telegram ID: {uid})",
        f"Дата отправки: {created}",
        "",
        "📅 ПРЕДЛОЖЕНИЕ ПО ВСТРЕЧЕ",
        f"Дата: {payload['date']}",
        f"Время: {payload['time']}",
        f"Формат/маршрут: {payload.get('route','Не выбран')}",
        f"Комментарий: {payload.get('comment') or '—'}",
        "",
        "🌿 ОТВЕТЫ НА ВОПРОСЫ"
    ]
    for i, item in enumerate(answers, 1):
        lines.append(f"{i}. {item.get('q','')}\n   ↳ {item.get('a','—')}")
    await bot.send_message(DAVID_ID, "\n".join(lines))
    return {"ok": True, "remaining": 1-used}

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        raise HTTPException(403, "Forbidden")
    update = types.Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})

@app.on_event("startup")
async def startup():
    if WEBAPP_URL:
        await bot.set_webhook(
            url=f"{WEBAPP_URL}/telegram/webhook",
            secret_token=WEBHOOK_SECRET,
            allowed_updates=dp.resolve_used_update_types()
        )

@app.on_event("shutdown")
async def shutdown():
    await bot.session.close()
