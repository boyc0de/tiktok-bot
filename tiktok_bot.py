#!/usr/bin/env python3
"""
TikTok Bot – pobiera filmy z TikToka BEZ znaku wodnego i zapisuje na dysku.

Wymagania (jednorazowo):
    pip install -r requirements.txt

Użycie:
    python tiktok_bot.py https://www.tiktok.com/@user/video/123...      # jeden lub kilka linków
    python tiktok_bot.py                                                  # linki z pliku links.txt
    python tiktok_bot.py https://www.tiktok.com/@nazwa_uzytkownika        # wszystkie filmy z profilu
    python tiktok_bot.py --watch                                          # pilnuje schowka i pobiera skopiowane linki
    python tiktok_bot.py --cookies chrome <link>                          # gdy TikTok blokuje: użyj ciasteczek z przeglądarki

Filmy trafiają do folderu  Pobrane/TikTok  (Downloads/TikTok).
Już pobrane filmy są pomijane (plik archive.txt).
"""

import re
import sys
import time
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    sys.exit("Brak yt-dlp. Zainstaluj:  pip install -U yt-dlp")

OUTPUT_DIR = Path.home() / "Downloads" / "TikTok"
LINKS_FILE = Path(__file__).with_name("links.txt")
TIKTOK_RE = re.compile(r"https?://(?:www\.|vm\.|vt\.|m\.)?tiktok\.com/[^\s\"'<>]+")


COOKIES_BROWSER = None  # ustawiane opcją --cookies chrome|firefox|edge|brave


def impersonate_target():
    """Udawaj prawdziwego Chrome'a (wymaga curl_cffi), żeby TikTok nie blokował."""
    try:
        import curl_cffi  # noqa: F401
        from yt_dlp.networking.impersonate import ImpersonateTarget
        return ImpersonateTarget.from_str("chrome")
    except Exception:
        return None


def make_downloader() -> yt_dlp.YoutubeDL:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    opts = {
        "outtmpl": str(OUTPUT_DIR / "%(uploader)s_%(id)s.%(ext)s"),
        # najlepsza jakość; yt-dlp domyślnie wybiera wersję bez znaku wodnego
        "format": "bestvideo*+bestaudio/best",
        "merge_output_format": "mp4",
        "download_archive": str(OUTPUT_DIR / "archive.txt"),  # nie pobieraj drugi raz
        "ignoreerrors": True,
        "retries": 5,
        "sleep_interval": 1,          # krótka przerwa między filmami (mniej blokad)
        "max_sleep_interval": 3,
        "quiet": False,
        "no_warnings": True,
    }
    target = impersonate_target()
    if target:
        opts["impersonate"] = target
    else:
        print("Uwaga: brak curl_cffi – zainstaluj: pip install -U \"yt-dlp[default,curl-cffi]\"")
    if COOKIES_BROWSER:
        opts["cookiesfrombrowser"] = (COOKIES_BROWSER,)
    return yt_dlp.YoutubeDL(opts)


def download(urls: list[str]) -> None:
    urls = list(dict.fromkeys(u.strip() for u in urls if u.strip()))  # usuń duplikaty
    if not urls:
        print("Brak linków do pobrania.")
        return
    print(f"Pobieram {len(urls)} link(ów) do: {OUTPUT_DIR}\n")
    with make_downloader() as ydl:
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {url}")
            ydl.download([url])
    print(f"\nGotowe. Pliki są w: {OUTPUT_DIR}")


def read_links_file() -> list[str]:
    if not LINKS_FILE.exists():
        LINKS_FILE.write_text("# Wklej tu linki do TikToków, jeden w linii\n", encoding="utf-8")
        print(f"Utworzyłem {LINKS_FILE} – wklej do niego linki i uruchom ponownie.")
        return []
    text = LINKS_FILE.read_text(encoding="utf-8")
    return TIKTOK_RE.findall(text)


def watch_clipboard() -> None:
    try:
        import pyperclip
    except ImportError:
        sys.exit("Tryb --watch wymaga pyperclip:  pip install pyperclip")
    print("Obserwuję schowek – kopiuj linki do TikToków (Ctrl+C). Zakończ: Ctrl+C w terminalu.\n")
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
        print("\nZakończono.")


def main() -> None:
    global COOKIES_BROWSER
    args = sys.argv[1:]
    if "--cookies" in args:
        i = args.index("--cookies")
        if i + 1 >= len(args):
            sys.exit("Podaj przeglądarkę, np.:  --cookies chrome")
        COOKIES_BROWSER = args[i + 1]
        del args[i:i + 2]
    if "--watch" in args:
        watch_clipboard()
    elif args:
        download(args)
    else:
        download(read_links_file())


if __name__ == "__main__":
    main()
