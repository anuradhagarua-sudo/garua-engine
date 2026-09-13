import traceback
import sys

# 1. Load Kivy FIRST so we can paint errors to the screen
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock

CRASH_ERROR = ""
SUCCESS_LOAD = False

try:
    # 2. Try loading all the tricky web and API libraries
    import csv, datetime, io, json, logging, math, os, random, re, threading, time, urllib.parse, webbrowser
    from flask import Flask, jsonify, render_template_string, request
    from kiteconnect import KiteTicker
    import pytz
    import requests
    import websocket
    
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except Exception:
        pass

    # --- ALL ORIGINAL ALGO LOGIC GOES HERE ---
    IST = pytz.timezone("Asia/Kolkata")
    stealth_ws = None
    EVENT_LOG = []
    SYSTEM_START_TIME = time.time()
    FLASK_PORT = random.randint(6000, 9000)

    API_CONFIG = {"user_id": "", "enc_token": "", "is_connected": False}
    KITE_SESSION = requests.Session()
    DIAGNOSTICS = {"ws_status": "DISCONNECTED", "rest_history_status": "WAITING"}

    def log_event(msg):
        ts = datetime.datetime.now(IST).strftime("%H:%M:%S")
        EVENT_LOG.append(f"[{ts}] {msg}")
        if len(EVENT_LOG) > 20: EVENT_LOG.pop(0)

    INSTRUMENT_MAP, ACTIVE_POSITIONS, STRATEGY_LEGS = {}, {}, []
    LIVE_MASTER_UND_LTP = 0.0

    def fetch_instrument_tokens():
        global INSTRUMENT_MAP
        while True:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                req = requests.get("https://api.kite.trade/instruments", headers=headers, timeout=15)
                reader = csv.DictReader(io.StringIO(req.text))
                t_INSTRUMENT_MAP = {}
                for row in reader:
                    name = row.get("name", "").strip()
                    if not name: continue
                    exch = row.get("exchange", "")
                    tsym = row.get("tradingsymbol", "")
                    try: token = int(row.get("instrument_token", 0))
                    except: continue
                    t_INSTRUMENT_MAP[f"{exch}:{tsym}"] = token
                INSTRUMENT_MAP = t_INSTRUMENT_MAP
                log_event(f"Database Ready: {len(INSTRUMENT_MAP)} tokens loaded.")
                break
            except Exception as e:
                time.sleep(5)

    def portfolio_sync_thread():
        global ACTIVE_POSITIONS
        while True:
            time.sleep(10)
            if not API_CONFIG["is_connected"]: continue
            try:
                res = KITE_SESSION.get("https://kite.zerodha.com/oms/portfolio/positions")
                if res.status_code == 200:
                    pass # Sync logic omitted for brevity in crash tester
            except: pass

    app = Flask(__name__)
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    HTML_TEMPLATE = """
    <!DOCTYPE html><html lang="en" data-bs-theme="dark"><head><title>Garua Algo</title></head>
    <body style="background-color:#0b0c10; color:#66fcf1; font-family:sans-serif; text-align:center; padding-top:50px;">
        <h2>Garua Engine Server is Active!</h2>
        <p>Your background Flask and KiteConnect systems are successfully running.</p>
    </body></html>
    """

    @app.route("/")
    def home(): return render_template_string(HTML_TEMPLATE)

    @app.route("/api/data")
    def api_data(): return jsonify({"server_time": datetime.datetime.now(IST).strftime("%H:%M:%S")})

    def run_flask():
        app.run(host="127.0.0.1", port=FLASK_PORT, debug=False, use_reloader=False)

    SUCCESS_LOAD = True

except Exception as e:
    # 3. IF ANYTHING FAILS, CATCH THE ERROR EXACTLY
    CRASH_ERROR = traceback.format_exc()
    SUCCESS_LOAD = False


class AlgoWebApp(App):
    def build(self):
        # IF IT CRASHED: Display the red error screen
        if not SUCCESS_LOAD:
            layout = BoxLayout(orientation="vertical", padding=20)
            sv = ScrollView()
            # Binds the text to wrap inside the screen boundaries
            lbl = Label(
                text=f"FATAL BOOT ERROR:\n\n{CRASH_ERROR}", 
                color=(1, 0.2, 0.2, 1), 
                font_size='14sp',
                size_hint_y=None,
                halign="left",
                valign="top"
            )
            lbl.bind(width=lambda *x: lbl.setter('text_size')(lbl, (lbl.width, None)), texture_size=lambda *x: lbl.setter('height')(lbl, lbl.texture_size[1]))
            sv.add_widget(lbl)
            layout.add_widget(Label(text="Garua Engine Crash Reporter", font_size='20sp', size_hint_y=0.1, color=(1,1,0,1)))
            layout.add_widget(sv)
            return layout

        # IF SUCCESSFUL: Display the normal launcher
        threading.Thread(target=fetch_instrument_tokens, daemon=True).start()
        threading.Thread(target=portfolio_sync_thread, daemon=True).start()
        threading.Thread(target=run_flask, daemon=True).start()

        layout = BoxLayout(orientation="vertical", padding=30, spacing=20)
        self.lbl = Label(text="Garua Engine V25.8\nBooting Server...", halign="center", font_size="22sp", color=(0.05, 0.8, 0.94, 1))
        self.btn = Button(text="OPEN ALGO COMMAND CENTER", size_hint=(1, 0.25), disabled=True, background_color=(0, 0.7, 0, 1), font_size="18sp", bold=True)
        self.btn.bind(on_press=self.open_ui)
        layout.add_widget(self.lbl)
        layout.add_widget(self.btn)
        Clock.schedule_once(self.ready, 4)
        return layout

    def ready(self, dt):
        self.lbl.text = f"Garua Engine V25.8\nServer Active on Port {FLASK_PORT}\n\nClick below to open the Live Dashboard."
        self.btn.disabled = False

    def open_ui(self, inst):
        try: webbrowser.open(f"http://127.0.0.1:{FLASK_PORT}")
        except Exception: self.lbl.text = f"Could not launch browser natively.\nOpen Chrome to:\nhttp://127.0.0.1:{FLASK_PORT}"

if __name__ == "__main__":
    AlgoWebApp().run()
