import customtkinter as ctk
from collections import deque
from datetime import datetime

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG       = "#0F1117"
SURFACE  = "#161B22"
SURFACE2 = "#1C2128"
BORDER   = "#30363D"
TEXT     = "#E6EDF3"
TEXT_DIM = "#7D8590"
ACCENT   = "#388BFD"

LEVEL_COLORS = {
    "safe":      {"bg": "#0D2818", "fg": "#57A87A", "border": "#1D4D30"},
    "potential": {"bg": "#221C08", "fg": "#B8932A", "border": "#4A3C10"},
    "likely":    {"bg": "#221408", "fg": "#C07030", "border": "#4A2C10"},
    "danger":    {"bg": "#220C0C", "fg": "#B84040", "border": "#4A1818"},
}

AE_LEVEL_COLORS = {
    "normal":     "#57A87A",
    "elevated":   "#B8932A",
    "suspicious": "#C07030",
    "severe":     "#B84040",
}

RF_LABELS  = ["safe", "potential", "likely", "danger"]
RF_DISPLAY = ["Safe", "Potential", "Likely", "Danger"]
AE_LABELS  = ["normal", "elevated", "suspicious", "severe"]

BASELINE_WINDOW = 20
FONT = "Consolas"


class SectionCard(ctk.CTkFrame):
    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, fg_color=SURFACE, corner_radius=8,
                         border_width=1, border_color=BORDER, **kwargs)
        if title:
            ctk.CTkLabel(self, text=title, font=(FONT, 10),
                         text_color=TEXT_DIM).pack(anchor="w", padx=16, pady=(12, 0))


class RiskRow(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=SURFACE2, corner_radius=6,
                         border_width=1, border_color=BORDER, **kwargs)
        self._tiles = {}
        for col, (key, disp) in enumerate(zip(RF_LABELS, RF_DISPLAY)):
            tile = ctk.CTkFrame(self, fg_color="transparent", corner_radius=5)
            tile.grid(row=0, column=col, padx=4, pady=4, sticky="nsew")
            self.grid_columnconfigure(col, weight=1)
            lbl = ctk.CTkLabel(tile, text=disp, font=(FONT, 13, "bold"),
                               text_color=TEXT_DIM)
            lbl.pack(expand=True, fill="both", padx=2, pady=8)
            self._tiles[key] = (tile, lbl)

    def set_level(self, level: str):
        for key, (tile, lbl) in self._tiles.items():
            if key == level:
                c = LEVEL_COLORS[key]
                tile.configure(fg_color=c["bg"], border_width=1, border_color=c["border"])
                lbl.configure(text_color=c["fg"])
            else:
                tile.configure(fg_color="transparent", border_width=0)
                lbl.configure(text_color=TEXT_DIM)


class App(ctk.CTk):
    def __init__(self, results_queue, stop_event=None, models_ready=None):
        super().__init__()
        self.results_queue = results_queue
        self.stop_event    = stop_event
        self.models_ready  = models_ready
        self.is_paused     = False
        self.flow_count    = 0
        self._baseline_buf = deque(maxlen=BASELINE_WINDOW)
        self._recent       = deque(maxlen=12)

        self.title("NIDS")
        self.geometry("900x490")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self._build_ui()

        # auto-start: if models already ready, go live immediately
        # if still loading, poll until ready then go live automatically
        if self.models_ready and self.models_ready.is_set():
            self._start_live()
        elif self.models_ready:
            self._poll_ready()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent", height=48)
        hdr.pack(fill="x", padx=24, pady=(16, 0))
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="NIDS", font=(FONT, 20, "bold"),
                     text_color=TEXT).pack(side="left", anchor="center")
        ctk.CTkLabel(hdr, text="Network Intrusion Detection System",
                     font=(FONT, 11), text_color=TEXT_DIM).pack(
                         side="left", anchor="center", padx=(10, 0), pady=(4, 0))

        sf = ctk.CTkFrame(hdr, fg_color="transparent")
        sf.pack(side="right", anchor="center")
        self.status_dot = ctk.CTkLabel(sf, text="●", font=(FONT, 13),
                                        text_color=TEXT_DIM)
        self.status_dot.pack(side="left")
        self.status_lbl = ctk.CTkLabel(sf, text="IDLE", font=(FONT, 11),
                                        text_color=TEXT_DIM)
        self.status_lbl.pack(side="left", padx=(4, 0))

        ctk.CTkFrame(self, fg_color=BORDER, height=1).pack(
            fill="x", padx=24, pady=(10, 0))

        # Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=12)

        left  = ctk.CTkFrame(body, fg_color="transparent")
        right = ctk.CTkFrame(body, fg_color="transparent", width=220)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        self._build_rf_card(left)
        self._build_ae_card(left)
        self._build_activity_strip(left)
        self._build_right_column(right)

    def _build_rf_card(self, parent):
        card = SectionCard(parent, title="ATTACK RISK")
        card.pack(fill="x", pady=(0, 8))
        self.risk_row = RiskRow(card, height=50)
        self.risk_row.pack(fill="x", padx=12, pady=(6, 12))

    def _build_ae_card(self, parent):
        card = SectionCard(parent, title="ANOMALOUS BEHAVIOUR")
        card.pack(fill="x", pady=(0, 8))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=(6, 14))

        score_row = ctk.CTkFrame(inner, fg_color="transparent")
        score_row.pack(fill="x", pady=(0, 8))

        self.ae_pct_label = ctk.CTkLabel(score_row, text="—",
                                          font=(FONT, 38, "bold"), text_color=TEXT)
        self.ae_pct_label.pack(side="left")

        right_labels = ctk.CTkFrame(score_row, fg_color="transparent")
        right_labels.pack(side="left", padx=(12, 0), pady=(10, 0))

        self.ae_level_label = ctk.CTkLabel(right_labels, text="",
                                            font=(FONT, 13), text_color=TEXT_DIM)
        self.ae_level_label.pack(anchor="w")

        self.ae_baseline_label = ctk.CTkLabel(right_labels, text="",
                                               font=(FONT, 11), text_color=TEXT_DIM)
        self.ae_baseline_label.pack(anchor="w", pady=(3, 0))

        self._track = ctk.CTkFrame(inner, fg_color=SURFACE2, height=7,
                                    corner_radius=4, border_width=1, border_color=BORDER)
        self._track.pack(fill="x")
        self._track.pack_propagate(False)
        self.ae_bar = ctk.CTkFrame(self._track, fg_color=ACCENT,
                                    height=7, corner_radius=4, width=4)
        self.ae_bar.place(x=0, y=0, relheight=1)

    def _build_activity_strip(self, parent):
        card = SectionCard(parent, title="RECENT FLOWS")
        card.pack(fill="x")

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(8, 14))

        self._dot_widgets = []
        for i in range(12):
            sq = ctk.CTkFrame(row, width=26, height=26, corner_radius=4,
                              fg_color=SURFACE2, border_width=1, border_color=BORDER)
            sq.pack(side="left", padx=3)
            sq.pack_propagate(False)
            self._dot_widgets.append(sq)

    def _build_right_column(self, parent):
        stats = SectionCard(parent, title="SESSION")
        stats.pack(fill="x", pady=(0, 8))

        g = ctk.CTkFrame(stats, fg_color="transparent")
        g.pack(fill="x", padx=16, pady=(6, 14))

        def stat(row, label, attr):
            ctk.CTkLabel(g, text=label, font=(FONT, 11),
                         text_color=TEXT_DIM).grid(row=row, column=0, sticky="w", pady=3)
            val = ctk.CTkLabel(g, text="—", font=(FONT, 12, "bold"), text_color=TEXT)
            val.grid(row=row, column=1, sticky="e", padx=(12, 0), pady=3)
            setattr(self, attr, val)

        stat(0, "Flows",    "stat_flows")
        stat(1, "Updated",  "stat_time")
        stat(2, "Risk",     "stat_rf")
        stat(3, "Anomaly",  "stat_ae")
        stat(4, "Baseline", "stat_baseline")
        g.grid_columnconfigure(1, weight=1)

        # only a pause button — no start button needed
        btn_card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=8,
                                border_width=1, border_color=BORDER)
        btn_card.pack(fill="x")

        btn_inner = ctk.CTkFrame(btn_card, fg_color="transparent")
        btn_inner.pack(fill="x", padx=14, pady=14)

        self.pause_btn = ctk.CTkButton(
            btn_inner, text="PAUSE",
            font=(FONT, 12),
            fg_color=SURFACE2, hover_color=BORDER,
            text_color=TEXT_DIM, corner_radius=6, height=34,
            border_width=1, border_color=BORDER,
            state="disabled", command=self._on_pause
        )
        self.pause_btn.pack(fill="x")

    def _poll_ready(self):
        # keep polling until models are loaded, then go live automatically
        if self.models_ready.is_set():
            self._start_live()
        else:
            self.status_dot.configure(text_color=TEXT_DIM)
            self.status_lbl.configure(text="LOADING")
            self.after(200, self._poll_ready)

    def _start_live(self):
        # called automatically — either on open if ready, or once loading finishes
        self.is_paused = False
        self.pause_btn.configure(state="normal", text="PAUSE", text_color=TEXT)
        self.status_dot.configure(text_color=AE_LEVEL_COLORS["normal"])
        self.status_lbl.configure(text="LIVE", text_color=AE_LEVEL_COLORS["normal"])
        if self.stop_event:
            self.stop_event.clear()
        self.poll_results()

    def _on_pause(self):
        if self.is_paused:
            self.is_paused = False
            self.pause_btn.configure(text="PAUSE")
            self.status_dot.configure(text_color=AE_LEVEL_COLORS["normal"])
            self.status_lbl.configure(text="LIVE", text_color=AE_LEVEL_COLORS["normal"])
            if self.stop_event:
                self.stop_event.clear()
        else:
            self.is_paused = True
            self.pause_btn.configure(text="RESUME")
            self.status_dot.configure(text_color=TEXT_DIM)
            self.status_lbl.configure(text="PAUSED", text_color=TEXT_DIM)
            if self.stop_event:
                self.stop_event.set()

    def poll_results(self):
        wait_time = 1000
        if not self.is_paused:
            try:
                if not self.results_queue.empty():
                    result = self.results_queue.get_nowait()
                    if result is not None:
                        if result['type'] == 'flow':
                            ae_percent, ae_category, rf_category = result['payload']
                            self._update(ae_percent, ae_category, rf_category)
                        if result['type'] == 'alert':
                            self.show_alert(result['payload'])
                            wait_time = 10
            except Exception:
                pass
        self.after(wait_time, self.poll_results)

    def show_alert(self, alert):
        print('Alert pinged in dashboard...')
        alert_type = alert.get('type', '')
        message = alert.get('message', '')
        severity = alert.get('severity', 0)

        color = {
            1: LEVEL_COLORS['potential']['fg'],
            2: LEVEL_COLORS['likely']['fg'],
            3: LEVEL_COLORS['danger']['fg'],
            4: '#FF0000'
        }.get(severity, TEXT_DIM)

        self.status_lbl.configure(text=f'ALERT: {alert_type.replace('_', ' ')}', text_color=color)
        self.status_dot.configure(text_color=color)

    def _update(self, ae_percent: int, ae_category: int, rf_category: int):
        self.flow_count += 1
        rf_level = RF_LABELS[rf_category]
        ae_level = AE_LABELS[ae_category]
        ae_pct   = max(0, min(ae_percent, 100))

        self._baseline_buf.append(ae_pct)
        baseline = int(sum(self._baseline_buf) / len(self._baseline_buf))
        self._recent.appendleft(ae_level)

        self.risk_row.set_level(rf_level)

        ae_color = AE_LEVEL_COLORS[ae_level]
        self.ae_pct_label.configure(text=f"{ae_pct}%", text_color=ae_color)
        self.ae_level_label.configure(text=f"· {ae_level.upper()}", text_color=ae_color)

        if len(self._baseline_buf) >= 5:
            delta = ae_pct - baseline
            sign  = "+" if delta >= 0 else ""
            self.ae_baseline_label.configure(
                text=f"baseline {baseline}%   ({sign}{delta}% from avg)",
                text_color=TEXT_DIM
            )
        else:
            self.ae_baseline_label.configure(
                text=f"building baseline  {len(self._baseline_buf)}/{BASELINE_WINDOW}",
                text_color=TEXT_DIM
            )

        self.after(10, lambda: self._resize_bar(ae_pct, ae_color))
        self._refresh_dots()

        self.stat_flows.configure(text=str(self.flow_count))
        self.stat_time.configure(text=datetime.now().strftime("%H:%M:%S"))
        self.stat_rf.configure(text=rf_level.upper(),
                               text_color=LEVEL_COLORS[rf_level]["fg"])
        self.stat_ae.configure(text=ae_level.upper(), text_color=ae_color)
        self.stat_baseline.configure(
            text=f"{baseline}%" if len(self._baseline_buf) >= 5 else "—"
        )

    def _refresh_dots(self):
        for i, sq in enumerate(self._dot_widgets):
            if i < len(self._recent):
                color = AE_LEVEL_COLORS[self._recent[i]]
                sq.configure(fg_color=color, border_color=color)
            else:
                sq.configure(fg_color=SURFACE2, border_color=BORDER)

    def _resize_bar(self, pct: int, color: str):
        track_w = self._track.winfo_width()
        if track_w < 2:
            return
        bar_w = max(4, int(track_w * pct / 100))
        self.ae_bar.configure(fg_color=color, width=bar_w)


def dashboard_process(results_queue, stop_event=None, models_ready=None):
    app = App(results_queue, stop_event=stop_event, models_ready=models_ready)
    app.mainloop()