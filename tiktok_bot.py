#!/usr/bin/env python3
"""
TikTok Bot – download TikTok videos WITHOUT watermark / pobieranie filmów z TikToka BEZ znaku wodnego.

Install / Instalacja:
    pip install -r requirements.txt

Usage / Użycie:
    python tiktok_bot.py <link> [<link> ...]          # video(s) / film(y)
    python tiktok_bot.py https://www.tiktok.com/@user # whole profile / cały profil
    python tiktok_bot.py                              # links from links.txt / linki z links.txt
    python tiktok_bot.py --watch                      # watch clipboard / obserwuj schowek
    python tiktok_bot.py --cookies chrome <link>      # use browser cookies / ciasteczka z przeglądarki
    python tiktok_bot.py --lang en|pl ...             # language / język (default: system)

Videos are saved to / Filmy trafiają do:  ~/Downloads/TikTok
"""

import locale
import os
import re
import sys
import time
from pathlib import Path

OUTPUT_DIR = Path.home() / "Downloads" / "TikTok"
LINKS_FILE = Path(__file__).with_name("links.txt")
TIKTOK_RE = re.compile(r"https?://(?:www\.|vm\.|vt\.|m\.)?tiktok\.com/[^\s\"'<>]+")

MESSAGES = {
    "en": {
        "no_ytdlp": "yt-dlp is missing. Install it:  pip install -r requirements.txt",
        "no_curl": "Note: curl_cffi is missing – install: pip install -U \"yt-dlp[default,curl-cffi]\"",
        "no_links": "No links to download.",
        "start": "Downloading {n} link(s) to: {dir}\n",
        "done": "\nDone. Files are in: {dir}",
        "links_created": "Created {file} – paste links into it (one per line) and run again.",
        "links_header": "# Paste TikTok links here, one per line\n",
        "no_pyperclip": "--watch mode needs pyperclip:  pip install pyperclip",
        "watching": "Watching the clipboard – copy TikTok links (Ctrl/Cmd+C). Stop: Ctrl+C in the terminal.\n",
        "stopped": "\nStopped.",
        "cookies_arg": "Name a browser, e.g.:  --cookies chrome",
    },
    "pl": {
        "no_ytdlp": "Brak yt-dlp. Zainstaluj:  pip install -r requirements.txt",
        "no_curl": "Uwaga: brak curl_cffi – zainstaluj: pip install -U \"yt-dlp[default,curl-cffi]\"",
        "no_links": "Brak linków do pobrania.",
        "start": "Pobieram {n} link(ów) do: {dir}\n",
        "done": "\nGotowe. Pliki są w: {dir}",
        "links_created": "Utworzyłem {file} – wklej do niego linki (jeden w linii) i uruchom ponownie.",
        "links_header": "# Wklej tu linki do TikToków, jeden w linii\n",
        "no_pyperclip": "Tryb --watch wymaga pyperclip:  pip install pyperclip",
        "watching": "Obserwuję schowek – kopiuj linki do TikToków (Ctrl/Cmd+C). Zakończ: Ctrl+C w terminalu.\n",
        "stopped": "\nZakończono.",
        "cookies_arg": "Podaj przeglądarkę, np.:  --cookies chrome",
    },
}

LANG = "en"
COOKIES_BROWSER = None


def detect_lang() -> str:
    for value in (os.environ.get("LANG", ""), (locale.getlocale()[0] or "")):
        if value.lower().startswith("pl") or "polish" in value.lower():
            return "pl"
    return "en"


def t(key: str, **kw) -> str:
    return MESSAGES[LANG][key].format(**kw)


def pop_option(args: list[str], name: str) -> str | None:
    if name not in args:
        return None
    i = args.index(name)
    if i + 1 >= len(args):
        sys.exit(t("cookies_arg") if name == "--cookies" else f"{name} en|pl")
    value = args[i + 1]
    del args[i:i + 2]
    return value


def impersonate_target():
    """Pretend to be real Chrome (needs curl_cffi) so TikTok doesn't block requests."""
    try:
        import curl_cffi  # noqa: F401
        from yt_dlp.networking.impersonate import ImpersonateTarget
        return ImpersonateTarget.from_str("chrome")
    except Exception:
        return None


def make_downloader():
    import yt_dlp

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    opts = {
        "outtmpl": str(OUTPUT_DIR / "%(uploader)s_%(id)s.%(ext)s"),
        # best quality; yt-dlp prefers the no-watermark version by default
        "format": "bestvideo*+bestaudio/best",
        "merge_output_format": "mp4",
        "download_archive": str(OUTPUT_DIR / "archive.txt"),  # skip already downloaded
        "ignoreerrors": True,
        "retries": 5,
        "sleep_interval": 1,
        "max_sleep_interval": 3,
        "no_warnings": True,
    }
    target = impersonate_target()
    if target:
        opts["impersonate"] = target
    else:
        print(t("no_curl"))
    if COOKIES_BROWSER:
        opts["cookiesfrombrowser"] = (COOKIES_BROWSER,)
    return yt_dlp.YoutubeDL(opts)


def download(urls: list[str]) -> None:
    urls = list(dict.fromkeys(u.strip() for u in urls if u.strip()))
    if not urls:
        print(t("no_links"))
        return
    print(t("start", n=len(urls), dir=OUTPUT_DIR))
    with make_downloader() as ydl:
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {url}")
            ydl.download([url])
    print(t("done", dir=OUTPUT_DIR))


def read_links_file() -> list[str]:
    if not LINKS_FILE.exists():
        LINKS_FILE.write_text(t("links_header"), encoding="utf-8")
        print(t("links_created", file=LINKS_FILE))
        return []
    return TIKTOK_RE.findall(LINKS_FILE.read_text(encoding="utf-8"))


def watch_clipboard() -> None:
    try:
        import pyperclip
    except ImportError:
        sys.exit(t("no_pyperclip"))
    print(t("watching"))
    seen, last = set(), ""
    try:
        while True:
            clip = pyperclip.paste() or ""
            if clip != last:
                last = clip
                new = [u for u in TIKTOK_RE.findall(clip) if u not in seen]
                if new:
                    seen.update(new)
                    download(new)
            time.sleep(1)
    except KeyboardInterrupt:
        print(t("stopped"))


def main() -> None:
    global LANG, COOKIES_BROWSER
    args = sys.argv[1:]
    LANG = detect_lang()
    lang = pop_option(args, "--lang")
    if lang in MESSAGES:
        LANG = lang
    COOKIES_BROWSER = pop_option(args, "--cookies")

    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        sys.exit(t("no_ytdlp"))

    if "--watch" in args:
        watch_clipboard()
    elif args:
        download(args)
    else:
        download(read_links_file())


if __name__ == "__main__":
    main()
