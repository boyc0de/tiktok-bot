# TikTok Bot

**English** | [Polski](README.pl.md)

A simple Python bot that downloads TikTok videos **without the watermark** (using [yt-dlp](https://github.com/yt-dlp/yt-dlp)) and saves them to `~/Downloads/TikTok`.

## Installation

```bash
git clone https://github.com/boyc0de/tiktok-bot.git
cd tiktok-bot
pip install -r requirements.txt
```
(on macOS/Linux use `pip3` and `python3`)

## GUI (window)

```bash
python tiktok_gui.py
```
Paste links (videos or profiles), optionally pick your browser under **Browser cookies**, and click **Download**. The **PL/EN** button switches the language.

## Command line

| What | Command |
|---|---|
| One or more videos | `python tiktok_bot.py <link> [<link> ...]` |
| Whole profile | `python tiktok_bot.py https://www.tiktok.com/@username` |
| Links from `links.txt` | `python tiktok_bot.py` |
| Download copied links (clipboard) | `python tiktok_bot.py --watch` |
| When TikTok blocks requests | add `--cookies chrome` (or `firefox`, `edge`, `brave`) |
| Message language | `--lang en` or `--lang pl` (default: system language) |

Already downloaded videos are skipped (`archive.txt`).

## Troubleshooting

- **"Unexpected response from webpage request"** – update: `pip install -U --pre "yt-dlp[default,curl-cffi]"` and run with `--cookies chrome` (open tiktok.com in that browser first).
- **No sound** – install ffmpeg (`brew install ffmpeg` / `winget install ffmpeg`).

## Note

Videos belong to their creators. Download for personal use only and don't re-upload other people's content without permission.
