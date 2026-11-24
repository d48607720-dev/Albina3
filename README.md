# Albina × David — Samarkand invite mini-app 💌

Telegram Mini App + bot, ready for Railway. The bot is private to Albina's Telegram ID. The app sends completed answers and the chosen date/time to David's Telegram ID. The invitee can submit at most **2 times**.

## 1. Create the bot
1. Open [@BotFather](https://t.me/BotFather), run `/newbot`.
2. Choose a name, e.g. **«Открытка для Альбины»**.
3. Choose username ending in `bot`, e.g. `albina_walk_invite_bot` (if available).
4. Copy the token.

## 2. Upload to GitHub
Create a repository, e.g. `albina-samarkand-invite`, upload all project files, then connect that repo in Railway.

## 3. Railway setup
Create a Railway project from GitHub and add a **Volume** mounted at `/data` (keeps the two-use limit after redeploys). Add these Variables:

- `BOT_TOKEN` — token from BotFather
- `DAVID_TELEGRAM_ID` — `7948603698`
- `ALBINA_TELEGRAM_ID` — `8660771174`
- `WEBAPP_URL` — Railway public HTTPS domain, e.g. `https://your-app.up.railway.app`
- `WEBHOOK_SECRET` — any long random string
- `DB_PATH` — `/data/submissions.db`

Generate a public domain in Railway. Set `WEBAPP_URL` to that exact HTTPS domain. If first deploy happens before the domain exists, add the variable and redeploy.

## 4. Telegram Mini App domain
In BotFather:
- `/setdomain` → select your bot → enter the Railway hostname only, e.g. `your-app.up.railway.app`.
- Send `/start` to your bot from Albina's Telegram account.

The app validates Telegram's signed `initData` on every API request. It will reject anyone except Telegram ID `8660771174`.

## 5. Test
1. Open the bot as Albina and press **Открыть открытку**.
2. Complete the questionnaire and send.
3. David should receive the result at Telegram ID `7948603698`.
4. A third submission is blocked. SQLite persists on the Railway volume.

## Included
- Animated envelope/card opening
- 10 light questions + 10 more personal questions
- A clear no-pressure disclaimer
- Samarkand parks, walk locations, cafes and restaurants
- Date and time picker, comment field
- Maximum two submissions per Albina account
- Telegram ID validation and private result delivery

Venue names are suggestions, not reservations. Check current hours/availability before going.
