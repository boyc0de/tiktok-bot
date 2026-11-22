# TikTok Bot

[English](README.md) | **Polski**

Prosty bot w Pythonie, który pobiera filmy z TikToka **bez znaku wodnego** (przez [yt-dlp](https://github.com/yt-dlp/yt-dlp)) i zapisuje je w folderze `Pobrane/TikTok` (`~/Downloads/TikTok`).

## Instalacja

```bash
git clone https://github.com/boyc0de/tiktok-bot.git
cd tiktok-bot
pip install -r requirements.txt
```
(na macOS/Linuksie: `pip3` i `python3`)

## Okienko (GUI)

```bash
python tiktok_gui.py
```
Wklej linki (filmy lub profile), opcjonalnie wybierz przeglądarkę w polu **Ciasteczka z przeglądarki** i kliknij **Pobierz**. Przycisk **EN/PL** zmienia język.

## Wiersz poleceń

| Co | Komenda |
|---|---|
| Jeden lub kilka filmów | `python tiktok_bot.py <link> [<link> ...]` |
| Cały profil | `python tiktok_bot.py https://www.tiktok.com/@nazwa` |
| Linki z pliku `links.txt` | `python tiktok_bot.py` |
| Pobieraj skopiowane linki (schowek) | `python tiktok_bot.py --watch` |
| Gdy TikTok blokuje | dodaj `--cookies chrome` (lub `firefox`, `edge`, `brave`) |
| Język komunikatów | `--lang pl` lub `--lang en` (domyślnie: język systemu) |

Już pobrane filmy są pomijane (`archive.txt`).

## Rozwiązywanie problemów

- **„Unexpected response from webpage request”** – zaktualizuj: `pip install -U --pre "yt-dlp[default,curl-cffi]"` i uruchom z `--cookies chrome` (najpierw otwórz tiktok.com w tej przeglądarce).
- **Brak dźwięku** – zainstaluj ffmpeg (`brew install ffmpeg` / `winget install ffmpeg`).

## Uwaga

Prawa do filmów należą do ich autorów. Pobieraj na własny użytek i nie publikuj ponownie cudzych treści bez zgody.
