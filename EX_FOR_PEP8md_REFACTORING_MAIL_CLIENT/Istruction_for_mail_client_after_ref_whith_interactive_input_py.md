# Mail Client (Interactive)

Интерактивный клиент для отправки и получения писем по SMTP/IMAP.  
Настройки (логин, пароль, сервера) запрашиваются один раз при старте и хранятся **в памяти сессии**.

> Требования: Python **3.10+**. Внешние зависимости не нужны (используется стандартная библиотека).

---

## Скачивание и установка

Поддерживаются два способа: через `git clone` или скачивание ZIP-архива.

### Способ 1 — `git clone` (рекомендуется)

**GitHub**
```bash
# macOS / Linux
git clone https://github.com/<ВАШ-ЛОГИН>/<ИМЯ-РЕПОЗИТОРИЯ>.git
cd <ИМЯ-РЕПОЗИТОРИЯ>
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
```

```powershell
# Windows (PowerShell)
git clone https://github.com/<ВАШ-ЛОГИН>/<ИМЯ-РЕПОЗИТОРИЯ>.git
cd <ИМЯ-РЕПОЗИТОРИЯ>
py -3 -m venv venv
.env\Scripts\Activate.ps1
py -3 -m pip install --upgrade pip
```

**Bitbucket**
```bash
# macOS / Linux
git clone https://bitbucket.org/<ВАШ-ЛОГИН>/<ИМЯ-РЕПОЗИТОРИЯ>.git
cd <ИМЯ-РЕПОЗИТОРИЯ>
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
```

```powershell
# Windows (PowerShell)
git clone https://bitbucket.org/<ВАШ-ЛОГИН>/<ИМЯ-РЕПОЗИТОРИЯ>.git
cd <ИМЯ-РЕПОЗИТОРИЯ>
py -3 -m venv venv
.env\Scripts\Activate.ps1
py -3 -m pip install --upgrade pip
```

> Если активация venv блокируется на Windows, временно разрешите:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Либо активируйте через CMD: `.env\Scriptsctivate.bat`.

### Способ 2 — ZIP-архив

1. Откройте страницу репозитория (GitHub/Bitbucket).  
2. Нажмите **Code** → **Download ZIP**.  
3. Распакуйте архив.  
4. Создайте и активируйте виртуальное окружение:

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
```

**Windows (PowerShell)**
```powershell
py -3 -m venv venv
.env\Scripts\Activate.ps1
py -3 -m pip install --upgrade pip
```

---

## Запуск

Интерактивная версия (запрашивает настройки и хранит их в памяти сессии):
```bash
# Находясь в корне репозитория и с активированным venv
python mail_client_interactive.py
```

Скрипт запросит:
- Email (логин)  
- Пароль (символы скрыты)  
- SMTP/IMAP сервера и порты (по умолчанию: `smtp.gmail.com:587` / `imap.gmail.com:993`)  
- Использование STARTTLS для SMTP (по умолчанию — да)  
- Таймаут в секундах

Затем появится меню:
1. Отправить письмо  
2. Получить последнее письмо  
0. Выход

---

## Замечания по безопасности (Gmail)

- Включите 2FA и используйте **App Password** вместо обычного пароля.  
- Включите IMAP в настройках Gmail.  
- Не храните пароль в коде или репозитории.

---

## Типичные ошибки

- **SMTPAuthenticationError** — неправильный логин/пароль или требуется App Password.  
- **IMAP ошибки** — проверьте сервер/порт и название папки (`INBOX`).  
- Пустое тело письма — у некоторых писем только `text/html`; метод извлекает `text/plain`.

---

## Лицензия

Добавьте файл LICENSE при необходимости (MIT/Apache-2.0/BSD и т.п.).
