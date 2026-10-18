# Freelance Assistant Bot

Telegram-бот для учета мелких фриланс-заданий и генерации черновиков текстов через OpenAI.

## 1. Получение ключей

### Токен Telegram-бота
1. Откройте Telegram, найдите `@BotFather`.
2. Отправьте `/newbot`.
3. Введите имя бота (например, `My Freelance Assistant`).
4. Введите юзернейм (должен заканчиваться на `bot`, например, `my_freelance_bot`).
5. Скопируйте полученный **токен** (длинная строка с двоеточием).

### Ваш Telegram ID (OWNER_ID)
1. Напишите боту `@userinfobot`.
2. Он пришлет ваш ID (число). Скопируйте его.

### Ключ OpenAI
1. Зайдите на [platform.openai.com](https://platform.openai.com/).
2. Зарегистрируйтесь/войдите.
3. Перейдите в раздел **API Keys** -> **Create new secret key**.
4. Скопируйте ключ (начинается на `sk-...`). Пополните баланс на $1-2.

## 2. Загрузка на GitHub
1. Зайдите на github.com (через браузер телефона).
2. Нажмите **New repository**, назовите `freelance-bot`, сделайте **Public**, нажмите **Create**.
3. Нажмите **uploading an existing file**.
4. Загрузите все файлы из этого проекта, **кроме** `.env` (файл `.env.example` загрузить можно).
5. Нажмите **Commit changes**.

## 3. Деплой на Render.com
1. Зайдите на [render.com](https://render.com/), зарегистрируйтесь через GitHub.
2. Нажмите **New +** -> **Web Service**.
3. Подключите ваш GitHub репозиторий `freelance-bot`.
4. Заполните настройки:
   - **Name**: `freelance-bot`
   - **Region**: выберите ближайший (например, Frankfurt).
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Instance Type**: `Free`
5. Прокрутите до **Environment Variables**. Добавьте три переменные:
   - `BOT_TOKEN` = ваш токен от BotFather
   - `OPENAI_API_KEY` = ваш ключ OpenAI
   - `OWNER_ID` = ваш Telegram ID (число)
6. Нажмите **Create Web Service**.
7. Дождитесь окончания деплоя (зеленая надпись `Live`).

## 4. Борьба с засыпанием Render (Keep-Alive)
На бесплатном тарифе Render сервис "засыпает" через 15 минут бездействия. Чтобы бот работал 24/7:
1. В коде уже есть файл `keep_alive.py`, который запускает веб-сервер на порту 8080.
2. Render автоматически определяет веб-сервис по наличию открытого порта. 
3. Зайдите на [uptimerobot.com](https://uptimerobot.com/), зарегистрируйтесь бесплатно.
4. Нажмите **Add New Monitor**.
   - **Monitor Type**: `HTTP(s)`
   - **Friendly Name**: `Freelance Bot`
   - **URL**: скопируйте ссылку на ваш сервис из Render (вида `https://freelance-bot-xxxx.onrender.com`)
   - **Monitoring Interval**: `10 minutes`
5. Нажмите **Create Monitor**. UptimeRobot будет пинговать бота каждые 10 минут, не давая ему заснуть.

## 5. Проверка
1. Откройте Telegram, найдите своего бота по юзернейму.
2. Нажмите **Start** (или отправьте `/start`).
3. Появится меню с кнопками. Если бот не отвечает — проверьте логи в Render (вкладка **Logs**).