
"""Простой клиент для отправки и чтения почты по SMTP/IMAP (интерактивный режим)."""

from __future__ import annotations

import email
import imaplib
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from getpass import getpass
from typing import Iterable, Optional, Sequence, Tuple


# ===== Класс (как в твоём варианте) =====

@dataclass
class MailClient:
    """Клиент почты с методами отправки (SMTP) и получения (IMAP)."""

    username: str
    password: str
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    imap_server: str = "imap.gmail.com"
    imap_port: int = 993
    smtp_use_tls: bool = True
    timeout: int = 60

    # ---------- SMTP ----------
    def send_email(
        self,
        recipients: Sequence[str],
        subject: str,
        body: str,
        *,
        cc: Sequence[str] | None = None,
        bcc: Sequence[str] | None = None,
        attachments: Iterable[Tuple[str, bytes, str]] | None = None,
    ) -> None:
        """Отправить письмо.

        attachments: итерируемый набор кортежей (filename, content_bytes, mime_type)
                     например: [("readme.txt", b"...", "text/plain")]
        """
        cc = cc or []
        bcc = bcc or []
        attachments = attachments or []

        msg = EmailMessage()
        msg["From"] = self.username
        msg["To"] = ", ".join(recipients)
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg["Subject"] = subject
        msg.set_content(body)

        for filename, content, mime_type in attachments:
            maintype, subtype = mime_type.split("/", 1)
            msg.add_attachment(
                content,
                maintype=maintype,
                subtype=subtype,
                filename=filename,
            )

        all_rcpts = list(recipients) + list(cc) + list(bcc)

        with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout) as s:
            s.ehlo()
            if self.smtp_use_tls:
                s.starttls()
                s.ehlo()
            s.login(self.username, self.password)
            s.send_message(msg, from_addr=self.username, to_addrs=all_rcpts)

    # ---------- IMAP ----------
    def fetch_latest(
        self,
        mailbox: str = "INBOX",
        *,
        subject: Optional[str] = None,
        unread_only: bool = False,
    ) -> Optional[email.message.Message]:
        """Получить последнее письмо по критериям (или None, если не найдено)."""
        with imaplib.IMAP4_SSL(self.imap_server, self.imap_port) as imap:
            imap.login(self.username, self.password)
            imap.select(mailbox)

            criteria = ["ALL"]
            if unread_only:
                criteria.append("UNSEEN")
            if subject:
                safe_subject = subject.replace('"', r"\"")
                criteria.append(f'(HEADER Subject "{safe_subject}")')

            search_query = " ".join(criteria)
            status, data = imap.uid("search", None, search_query)
            if status != "OK" or not data or not data[0]:
                return None

            latest_uid = data[0].split()[-1]
            status, fetched = imap.uid("fetch", latest_uid, "(RFC822)")
            if status != "OK" or not fetched or not fetched[0]:
                return None

            raw_email = fetched[0][1]
            return email.message_from_bytes(raw_email)

    # ---------- Helpers ----------
    @staticmethod
    def extract_text(msg: email.message.Message) -> str:
        """Достать текстовую часть письма (text/plain) без вложений."""
        parts: list[str] = []
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                disp = part.get("Content-Disposition", "")
                if ctype == "text/plain" and "attachment" not in disp:
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    if payload is not None:
                        parts.append(payload.decode(charset, errors="replace"))
        else:
            charset = msg.get_content_charset() or "utf-8"
            payload = msg.get_payload(decode=True)
            if payload is not None:
                parts.append(payload.decode(charset, errors="replace"))
        return "\n".join(parts).strip()


# ===== Утилиты для интерактива =====

def ask_str(prompt: str, default: str | None = None, required: bool = False) -> str:
    """Строковый вопрос с дефолтом. Повторяет, если требуется и пусто."""
    while True:
        suffix = f" [{default}]" if default is not None else ""
        val = input(f"{prompt}{suffix}: ").strip()
        if not val and default is not None:
            return default
        if val or not required:
            return val
        print("Поле обязательно, повторите ввод.")


def ask_int(prompt: str, default: int) -> int:
    while True:
        s = input(f"{prompt} [{default}]: ").strip()
        if not s:
            return default
        try:
            return int(s)
        except ValueError:
            print("Введите целое число.")


def ask_bool(prompt: str, default: bool = True) -> bool:
    d = "Y/n" if default else "y/N"
    while True:
        s = input(f"{prompt} ({d}): ").strip().lower()
        if not s:
            return default
        if s in {"y", "yes", "д", "да"}:
            return True
        if s in {"n", "no", "н", "нет"}:
            return False
        print("Ответьте 'y' или 'n'.")


def parse_emails(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def read_multiline(prompt: str) -> str:
    print(prompt + " (окончание — одиночная строка с точкой '.')")
    lines: list[str] = []
    while True:
        line = input()
        if line == ".":
            break
        lines.append(line)
    return "\n".join(lines)


# ===== Точка входа (интерактивная сессия) =====

if __name__ == "__main__":
    print("Настроим подключение к почтовому серверу.\n"
          "Для Gmail рекомендуется App Password (при включённой 2FA).")

    username = ask_str("Email (логин)", required=True)
    password = getpass("Пароль (символы скрыты): ").strip()
    while not password:
        print("Пароль обязателен.")
        password = getpass("Пароль (символы скрыты): ").strip()

    smtp_server = ask_str("SMTP сервер", default="smtp.gmail.com")
    smtp_port = ask_int("SMTP порт", default=587)
    imap_server = ask_str("IMAP сервер", default="imap.gmail.com")
    imap_port = ask_int("IMAP порт", default=993)
    use_tls = ask_bool("Использовать STARTTLS для SMTP?", default=True)
    timeout = ask_int("Таймаут (сек)", default=60)

    client = MailClient(
        username=username,
        password=password,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        imap_server=imap_server,
        imap_port=imap_port,
        smtp_use_tls=use_tls,
        timeout=timeout,
    )

    # Один и тот же client используется во всех действиях, пока программа не завершится.
    while True:
        print("\n=== Почтовый клиент ===")
        print("1) Отправить письмо")
        print("2) Получить последнее письмо")
        print("0) Выход")

        choice = input("Выберите пункт: ").strip()
        if choice == "1":
            to = parse_emails(ask_str("Кому (email, через запятую)", required=True))
            cc = parse_emails(ask_str("Копия (опционально)", default=""))
            bcc = parse_emails(ask_str("Скрытая копия (опционально)", default=""))
            subject = ask_str("Тема", required=True)
            body = read_multiline("Текст письма")

            try:
                client.send_email(
                    recipients=to,
                    subject=subject,
                    body=body,
                    cc=cc,
                    bcc=bcc,
                )
                print("Письмо отправлено.")
            except smtplib.SMTPAuthenticationError:
                print("Ошибка аутентификации SMTP. Проверьте логин/пароль "
                      "(для Gmail — App Password).")
            except smtplib.SMTPException as exc:
                print(f"Ошибка SMTP: {exc}")

        elif choice == "2":
            mailbox = ask_str("Папка", default="INBOX")
            subj = ask_str("Фильтр по теме (пусто = без фильтра)", default="")
            unread_only = ask_bool("Только непрочитанные?", default=False)

            try:
                msg = client.fetch_latest(
                    mailbox=mailbox,
                    subject=subj or None,
                    unread_only=unread_only,
                )
            except imaplib.IMAP4.error as exc:
                print(f"Ошибка IMAP: {exc}")
                continue

            if msg is None:
                print("Писем по заданным критериям не найдено.")
            else:
                print("\n— From:", msg.get("From", ""))
                print("— Subject:", msg.get("Subject", ""))
                print("— Date:", msg.get("Date", ""))
                print("— Body:\n" + MailClient.extract_text(msg))

        elif choice == "0":
            print("До встречи!")
            break
        else:
            print("Неверный пункт меню.")
