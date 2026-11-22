#!/usr/bin/env python3
"""
TikTok Bot – GUI. Paste links, click Download. / Wklej linki, kliknij Pobierz.

Run / Uruchom:   python tiktok_gui.py   (macOS/Linux: python3 tiktok_gui.py)
"""

import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from tiktok_bot import TIKTOK_RE, detect_lang, impersonate_target

TEXT = {
    "en": {
        "title": "TikTok Bot – download without watermark",
        "paste": "Paste TikTok links (videos or profiles), one per line:",
        "paste_btn": "Paste from clipboard",
        "clear": "Clear",
        "folder": "Save to:",
        "browse": "Change…",
        "cookies": "Browser cookies:",
        "none": "none",
        "download": "Download",
        "stop": "Stop",
        "open": "Open folder",
        "ready": "Ready.",
        "no_links": "No TikTok links found – paste a link first.",
        "start": "Downloading {n} link(s)…",
        "item": "Video {i}",
        "done": "Done. Downloaded: {ok}, errors: {err}.",
        "stopped": "Stopped.",
        "no_ytdlp": "yt-dlp is missing. In the terminal run:  pip3 install -r requirements.txt",
        "skip": "already downloaded – skipped",
        "hint": "Tip: if TikTok blocks downloads, pick your browser under “Browser cookies”.",
    },
    "pl": {
        "title": "TikTok Bot – pobieranie bez znaku wodnego",
        "paste": "Wklej linki do TikToka (filmy lub profile), jeden w linii:",
        "paste_btn": "Wklej ze schowka",
        "clear": "Wyczyść",
        "folder": "Zapisz do:",
        "browse": "Zmień…",
        "cookies": "Ciasteczka z przeglądarki:",
        "none": "brak",
        "download": "Pobierz",
        "stop": "Zatrzymaj",
        "open": "Otwórz folder",
        "ready": "Gotowy.",
        "no_links": "Nie znaleziono linków do TikToka – najpierw wklej link.",
        "start": "Pobieram {n} link(ów)…",
        "item": "Film {i}",
        "done": "Gotowe. Pobrano: {ok}, błędy: {err}.",
        "stopped": "Zatrzymano.",
        "no_ytdlp": "Brak yt-dlp. W terminalu wpisz:  pip3 install -r requirements.txt",
        "skip": "już pobrany – pominięto",
        "hint": "Wskazówka: jeśli TikTok blokuje pobieranie, wybierz przeglądarkę w polu „Ciasteczka”.",
    },
}

BROWSERS = ["chrome", "firefox", "edge", "brave", "safari"]
ANSI = re.compile(r"\x1b\[[0-9;]*m")


class StopDownload(Exception):
    pass


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.lang = detect_lang()
        self.events: queue.Queue = queue.Queue()
        self.worker: threading.Thread | None = None
        self.stop_flag = threading.Event()
        self.folder = tk.StringVar(value=str(Path.home() / "Downloads" / "TikTok"))
        self.cookies = tk.StringVar()
        self.status = tk.StringVar()
        self.progress = tk.DoubleVar()
        self.build()
        self.apply_lang()
        self.root.after(100, self.poll)

    # ---------- UI ----------
    def build(self):
        r = self.root
        r.minsize(620, 520)
        pad = {"padx": 10, "pady": 4}

        top = ttk.Frame(r)
        top.pack(fill="x", **pad)
        self.lbl_paste = ttk.Label(top)
        self.lbl_paste.pack(side="left")
        self.lang_btn = ttk.Button(top, width=4, command=self.toggle_lang)
        self.lang_btn.pack(side="right")

        self.links = tk.Text(r, height=8, wrap="none", font=("Menlo", 12) if sys.platform == "darwin" else None)
        self.links.pack(fill="both", expand=False, **pad)

        row = ttk.Frame(r)
        row.pack(fill="x", **pad)
        self.btn_paste = ttk.Button(row, command=self.paste)
        self.btn_paste.pack(side="left")
        self.btn_clear = ttk.Button(row, command=lambda: self.links.delete("1.0", "end"))
        self.btn_clear.pack(side="left", padx=6)

        opts = ttk.Frame(r)
        opts.pack(fill="x", **pad)
        self.lbl_folder = ttk.Label(opts)
        self.lbl_folder.grid(row=0, column=0, sticky="w")
        ttk.Entry(opts, textvariable=self.folder).grid(row=0, column=1, sticky="ew", padx=6)
        self.btn_browse = ttk.Button(opts, command=self.choose_folder)
        self.btn_browse.grid(row=0, column=2)
        self.lbl_cookies = ttk.Label(opts)
        self.lbl_cookies.grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.cmb_cookies = ttk.Combobox(opts, textvariable=self.cookies, state="readonly", width=12)
        self.cmb_cookies.grid(row=1, column=1, sticky="w", padx=6, pady=(6, 0))
        opts.columnconfigure(1, weight=1)

        actions = ttk.Frame(r)
        actions.pack(fill="x", **pad)
        self.btn_download = ttk.Button(actions, command=self.start)
        self.btn_download.pack(side="left")
        self.btn_stop = ttk.Button(actions, command=self.stop, state="disabled")
        self.btn_stop.pack(side="left", padx=6)
        self.btn_open = ttk.Button(actions, command=self.open_folder)
        self.btn_open.pack(side="right")

        ttk.Progressbar(r, variable=self.progress, maximum=100).pack(fill="x", **pad)
        ttk.Label(r, textvariable=self.status).pack(anchor="w", padx=10)

        self.log = tk.Text(r, height=10, state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True, padx=10, pady=(4, 10))

    def t(self, key, **kw):
        return TEXT[self.lang][key].format(**kw)

    def apply_lang(self):
        self.root.title(self.t("title"))
        self.lbl_paste.config(text=self.t("paste"))
        self.lang_btn.config(text="EN" if self.lang == "pl" else "PL")
        self.btn_paste.config(text=self.t("paste_btn"))
        self.btn_clear.config(text=self.t("clear"))
        self.lbl_folder.config(text=self.t("folder"))
        self.btn_browse.config(text=self.t("browse"))
        self.lbl_cookies.config(text=self.t("cookies"))
        current = self.cookies.get()
        values = [self.t("none")] + BROWSERS
        self.cmb_cookies.config(values=values)
        self.cookies.set(current if current in BROWSERS else values[0])
        self.btn_download.config(text=self.t("download"))
        self.btn_stop.config(text=self.t("stop"))
        self.btn_open.config(text=self.t("open"))
        if not self.worker:
            self.status.set(self.t("ready"))
            self.write_log(self.t("hint"), clear=True)

    def toggle_lang(self):
        self.lang = "en" if self.lang == "pl" else "pl"
        self.apply_lang()

    def write_log(self, line, clear=False):
        self.log.config(state="normal")
        if clear:
            self.log.delete("1.0", "end")
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    # ---------- actions ----------
    def paste(self):
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            return
        current = self.links.get("1.0", "end").strip()
        self.links.insert("end", ("\n" if current else "") + text.strip())

    def choose_folder(self):
        path = filedialog.askdirectory(initialdir=self.folder.get())
        if path:
            self.folder.set(path)

    def open_folder(self):
        folder = Path(self.folder.get())
        folder.mkdir(parents=True, exist_ok=True)
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        elif sys.platform.startswith("win"):
            subprocess.Popen(["explorer", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])

    def start(self):
        urls = list(dict.fromkeys(TIKTOK_RE.findall(self.links.get("1.0", "end"))))
        if not urls:
            self.status.set(self.t("no_links"))
            return
        try:
            import yt_dlp  # noqa: F401
        except ImportError:
            self.status.set(self.t("no_ytdlp"))
            return
        self.stop_flag.clear()
        self.btn_download.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.progress.set(0)
        self.write_log(self.t("start", n=len(urls)), clear=True)
        cookies = self.cookies.get() if self.cookies.get() in BROWSERS else None
        self.worker = threading.Thread(target=self.run, args=(urls, Path(self.folder.get()), cookies), daemon=True)
        self.worker.start()

    def stop(self):
        self.stop_flag.set()

    # ---------- worker thread ----------
    def run(self, urls, folder, cookies):
        import yt_dlp

        stats = {"ok": 0, "err": 0, "n": 0}
        app = self

        class Logger:
            def debug(self, msg):
                if msg.startswith("[download]") and "%" in msg:
                    return  # progress handled by hook
                if "has already been recorded in the archive" in msg:
                    app.events.put(("log", "↷ " + app.t("skip")))
                elif msg.startswith("[download] Downloading item"):
                    app.events.put(("log", ANSI.sub("", msg)))

            def info(self, msg):
                self.debug(msg)

            def warning(self, msg):
                pass

            def error(self, msg):
                stats["err"] += 1
                app.events.put(("log", "✗ " + ANSI.sub("", msg)))

        def hook(d):
            if self.stop_flag.is_set():
                raise StopDownload()
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                pct = d.get("downloaded_bytes", 0) * 100 / total if total else 0
                self.events.put(("progress", pct, d.get("filename", "")))
            elif d["status"] == "finished":
                stats["ok"] += 1
                self.events.put(("log", "✓ " + Path(d.get("filename", "")).name))

        folder.mkdir(parents=True, exist_ok=True)
        opts = {
            "outtmpl": str(folder / "%(uploader)s_%(id)s.%(ext)s"),
            "format": "bestvideo*+bestaudio/best",
            "merge_output_format": "mp4",
            "download_archive": str(folder / "archive.txt"),
            "ignoreerrors": True,
            "retries": 5,
            "sleep_interval": 1,
            "max_sleep_interval": 3,
            "logger": Logger(),
            "progress_hooks": [hook],
            "noprogress": True,
        }
        target = impersonate_target()
        if target:
            opts["impersonate"] = target
        if cookies:
            opts["cookiesfrombrowser"] = (cookies,)

        stopped = False
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                for url in urls:
                    if self.stop_flag.is_set():
                        stopped = True
                        break
                    self.events.put(("log", "→ " + url))
                    ydl.download([url])
        except StopDownload:
            stopped = True
        except Exception as e:  # noqa: BLE001
            stats["err"] += 1
            self.events.put(("log", "✗ " + str(e)))
        if self.stop_flag.is_set():
            stopped = True
        self.events.put(("finished", stopped, stats["ok"], stats["err"]))

    # ---------- UI updates from the queue ----------
    def poll(self):
        try:
            while True:
                ev = self.events.get_nowait()
                if ev[0] == "log":
                    self.write_log(ev[1])
                elif ev[0] == "progress":
                    self.progress.set(ev[1])
                    self.status.set(f"{ev[1]:.0f}%  {Path(ev[2]).name}")
                elif ev[0] == "finished":
                    _, stopped, ok, err = ev
                    msg = self.t("stopped") if stopped else self.t("done", ok=ok, err=err)
                    self.status.set(msg)
                    self.write_log(msg)
                    self.progress.set(0 if stopped else 100)
                    self.btn_download.config(state="normal")
                    self.btn_stop.config(state="disabled")
                    self.worker = None
        except queue.Empty:
            pass
        self.root.after(100, self.poll)


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("aqua" if sys.platform == "darwin" else "clam")
    except tk.TclError:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
