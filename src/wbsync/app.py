from __future__ import annotations

import csv
import ctypes
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


APP_NAME = "WBSync"
DATA_VERSION = 1


COLORS = {
    "ink": "#151821",
    "ink_2": "#232838",
    "paper": "#f4f1ea",
    "surface": "#ffffff",
    "surface_2": "#f8fafc",
    "line": "#d9dee8",
    "muted": "#667085",
    "text": "#111827",
    "text_soft": "#475467",
    "teal": "#008c83",
    "teal_dark": "#006a63",
    "teal_soft": "#dff5f2",
    "blue": "#3164d4",
    "violet": "#7a4dd8",
    "orange": "#f08a24",
    "red": "#d92d20",
    "green": "#168a4a",
    "yellow": "#f2c94c",
    "shadow": "#eef0f4",
}

TASK_STATUSES = ["未着手", "進行中", "レビュー", "完了", "保留"]
TICKET_STATUSES = ["未対応", "対応中", "レビュー", "完了", "保留"]
PRIORITIES = ["高", "中", "低"]

STATUS_COLORS = {
    "未着手": "#8792a2",
    "未対応": "#8792a2",
    "進行中": COLORS["blue"],
    "対応中": COLORS["blue"],
    "レビュー": COLORS["violet"],
    "完了": COLORS["green"],
    "保留": COLORS["orange"],
}

PRIORITY_COLORS = {
    "高": COLORS["red"],
    "中": COLORS["orange"],
    "低": COLORS["teal"],
}

VIEW_TITLES = {
    "wbs": ("WBS Studio", "工程を階層で組み立て、進捗と担当を管理"),
    "tickets": ("Ticket Board", "対応状況をKanbanで整理し、WBSへ紐付け"),
    "gantt": ("Timeline", "期間と進捗を横断して確認"),
}


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def default_data_path() -> Path:
    return app_dir() / "wbsync_project.json"


def resource_path(name: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / name
    return Path(__file__).resolve().parents[2] / name


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_today() -> str:
    return date.today().isoformat()


def parse_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def safe_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return parse_date(value)
    except ValueError:
        return None


def code_key(code: str) -> tuple:
    parts: list[int | str] = []
    for part in str(code).split("."):
        parts.append(int(part) if part.isdigit() else part)
    return tuple(parts)


def display_task(task: dict | None) -> str:
    if not task:
        return ""
    code = task.get("code", "")
    title = task.get("title", "")
    return f"{code}  {title}".strip()


def clamp_int(value: str, low: int = 0, high: int = 100) -> int:
    try:
        number = int(str(value).strip())
    except ValueError as exc:
        raise ValueError("数値を入力してください。") from exc
    if number < low or number > high:
        raise ValueError(f"{low} から {high} の範囲で入力してください。")
    return number


def create_sample_data() -> dict:
    today = date.today()
    return {
        "version": DATA_VERSION,
        "meta": {
            "project_name": "新規プロジェクト",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "tasks": [
            {
                "id": "task-001",
                "parent_id": "",
                "code": "1",
                "title": "要件定義",
                "owner": "PM",
                "status": "進行中",
                "start": today.isoformat(),
                "end": (today + timedelta(days=5)).isoformat(),
                "progress": 45,
                "memo": "スコープと成果物を確定する",
            },
            {
                "id": "task-002",
                "parent_id": "task-001",
                "code": "1.1",
                "title": "業務フロー整理",
                "owner": "PM",
                "status": "進行中",
                "start": today.isoformat(),
                "end": (today + timedelta(days=2)).isoformat(),
                "progress": 60,
                "memo": "",
            },
            {
                "id": "task-003",
                "parent_id": "task-001",
                "code": "1.2",
                "title": "画面要件",
                "owner": "Design",
                "status": "未着手",
                "start": (today + timedelta(days=2)).isoformat(),
                "end": (today + timedelta(days=5)).isoformat(),
                "progress": 0,
                "memo": "",
            },
            {
                "id": "task-004",
                "parent_id": "",
                "code": "2",
                "title": "実装",
                "owner": "Dev",
                "status": "未着手",
                "start": (today + timedelta(days=6)).isoformat(),
                "end": (today + timedelta(days=17)).isoformat(),
                "progress": 0,
                "memo": "",
            },
            {
                "id": "task-005",
                "parent_id": "",
                "code": "3",
                "title": "テスト・リリース",
                "owner": "QA",
                "status": "未着手",
                "start": (today + timedelta(days=18)).isoformat(),
                "end": (today + timedelta(days=25)).isoformat(),
                "progress": 0,
                "memo": "",
            },
        ],
        "tickets": [
            {
                "id": "ticket-001",
                "key": "T-001",
                "title": "主要画面の項目を洗い出す",
                "assignee": "Design",
                "status": "対応中",
                "priority": "高",
                "due": (today + timedelta(days=3)).isoformat(),
                "task_id": "task-003",
                "memo": "",
            },
            {
                "id": "ticket-002",
                "key": "T-002",
                "title": "CSV出力列を確定する",
                "assignee": "PM",
                "status": "未対応",
                "priority": "中",
                "due": (today + timedelta(days=4)).isoformat(),
                "task_id": "task-001",
                "memo": "",
            },
        ],
    }


def rounded_rect(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, radius: int = 10, **kwargs) -> int:
    radius = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    points = [
        x1 + radius,
        y1,
        x2 - radius,
        y1,
        x2,
        y1,
        x2,
        y1 + radius,
        x2,
        y2 - radius,
        x2,
        y2,
        x2 - radius,
        y2,
        x1 + radius,
        y2,
        x1,
        y2,
        x1,
        y2 - radius,
        x1,
        y1 + radius,
        x1,
        y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class FlatButton(tk.Button):
    def __init__(
        self,
        master: tk.Widget,
        text: str,
        command=None,
        *,
        kind: str = "secondary",
        width: int | None = None,
        padx: int = 14,
        pady: int = 8,
        font_size: int = 10,
    ):
        palettes = {
            "primary": (COLORS["teal"], "#ffffff", COLORS["teal_dark"], COLORS["teal"]),
            "secondary": (COLORS["surface"], COLORS["text"], "#edf2f7", COLORS["line"]),
            "dark": (COLORS["ink_2"], "#ffffff", "#30384b", COLORS["ink_2"]),
            "danger": (COLORS["red"], "#ffffff", "#b42318", COLORS["red"]),
            "quiet": (COLORS["surface_2"], COLORS["text_soft"], "#edf2f7", COLORS["surface_2"]),
        }
        bg, fg, active_bg, border = palettes[kind]
        super().__init__(
            master,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            bd=0,
            relief="flat",
            cursor="hand2",
            font=("Yu Gothic UI", font_size, "bold"),
            padx=padx,
            pady=pady,
            width=width or 0,
            highlightthickness=1,
            highlightbackground=border,
            highlightcolor=border,
        )


class MetricTile(tk.Frame):
    def __init__(self, master: tk.Widget, label: str, value: str, accent: str):
        super().__init__(master, bg=COLORS["surface"], highlightthickness=1, highlightbackground=COLORS["line"])
        tk.Frame(self, bg=accent, width=4).pack(side="left", fill="y")
        body = tk.Frame(self, bg=COLORS["surface"])
        body.pack(side="left", fill="both", expand=True, padx=14, pady=10)
        tk.Label(body, text=label, bg=COLORS["surface"], fg=COLORS["muted"], font=("Yu Gothic UI", 9, "bold")).pack(
            anchor="w"
        )
        tk.Label(body, text=value, bg=COLORS["surface"], fg=COLORS["text"], font=("Yu Gothic UI", 21, "bold")).pack(
            anchor="w"
        )


class ScrollFrame(tk.Frame):
    def __init__(self, master: tk.Widget, *, bg: str = COLORS["surface"]):
        super().__init__(master, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.inner.bind("<Configure>", self._sync_region)
        self.canvas.bind("<Configure>", self._sync_width)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _sync_region(self, _event: tk.Event | None = None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _sync_width(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self.winfo_containing(event.x_root, event.y_root) in self._descendants():
            self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def _descendants(self) -> set[tk.Widget]:
        widgets = {self, self.canvas, self.inner}
        stack = list(self.inner.winfo_children())
        while stack:
            item = stack.pop()
            widgets.add(item)
            stack.extend(item.winfo_children())
        return widgets


class WBSyncApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.apply_app_identity()
        self.apply_window_icon()
        self.geometry("1380x820")
        self.minsize(1120, 680)
        self.configure(bg=COLORS["paper"])

        self.project_path = default_data_path()
        self.data = self.load_or_seed_data()
        self.current_view = "wbs"
        self.search_var = tk.StringVar()
        self.ticket_status_filter = tk.StringVar(value="すべて")
        self.gantt_zoom = tk.StringVar(value="週")
        self.selected_ticket_id_value = ""
        self.dirty = False

        self.configure_styles()
        self.build_shell()
        self.show_view("wbs")
        self.refresh_all()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def apply_app_identity(self) -> None:
        if sys.platform != "win32":
            return
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("WBSync.ProjectControl")
        except Exception:
            pass

    def apply_window_icon(self) -> None:
        self._icon_images = []
        ico_path = resource_path("assets/generated/icon.ico")
        if ico_path.exists():
            try:
                self.iconbitmap(default=str(ico_path))
            except tk.TclError:
                pass
        for name in [
            "assets/generated/window_icon_16.png",
            "assets/generated/window_icon_24.png",
            "assets/generated/window_icon_32.png",
            "assets/generated/window_icon_48.png",
            "assets/generated/window_icon_64.png",
            "assets/generated/window_icon_128.png",
            "assets/generated/window_icon_256.png",
            "assets/brand/Icon.png",
        ]:
            png_path = resource_path(name)
            if not png_path.exists():
                continue
            try:
                self._icon_images.append(tk.PhotoImage(file=str(png_path)))
            except tk.TclError:
                continue
        if self._icon_images:
            self.iconphoto(True, *self._icon_images)

    def apply_icon_to_window(self, window: tk.Toplevel) -> None:
        ico_path = resource_path("assets/generated/icon.ico")
        if ico_path.exists():
            try:
                window.iconbitmap(default=str(ico_path))
            except tk.TclError:
                pass
        if getattr(self, "_icon_images", None):
            try:
                window.iconphoto(False, *self._icon_images)
            except tk.TclError:
                pass

    def configure_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", font=("Yu Gothic UI", 10), background=COLORS["paper"])
        style.configure("WBSync.Treeview", rowheight=38, borderwidth=0, background=COLORS["surface"], fieldbackground=COLORS["surface"])
        style.configure(
            "WBSync.Treeview.Heading",
            font=("Yu Gothic UI", 10, "bold"),
            foreground=COLORS["text_soft"],
            background="#ece7dd",
            relief="flat",
        )
        style.map("WBSync.Treeview", background=[("selected", COLORS["teal_soft"])], foreground=[("selected", COLORS["text"])])
        style.configure("TEntry", padding=8, fieldbackground="#ffffff")
        style.configure("TCombobox", padding=7, fieldbackground="#ffffff")
        style.configure("Vertical.TScrollbar", background="#d7dce5", troughcolor=COLORS["surface"])
        style.configure("Horizontal.TScrollbar", background="#d7dce5", troughcolor=COLORS["surface"])

    def build_shell(self) -> None:
        self.chrome = tk.Frame(self, bg=COLORS["ink"], height=86)
        self.chrome.pack(fill="x")
        self.chrome.pack_propagate(False)

        brand = tk.Frame(self.chrome, bg=COLORS["ink"])
        brand.pack(side="left", padx=24, pady=13)
        tk.Label(brand, text=APP_NAME, bg=COLORS["ink"], fg="#ffffff", font=("Yu Gothic UI", 21, "bold")).pack(anchor="w")
        self.path_label = tk.Label(
            brand,
            text="",
            bg=COLORS["ink"],
            fg="#aeb7c7",
            font=("Yu Gothic UI", 9),
        )
        self.path_label.pack(anchor="w")

        self.nav_bar = tk.Frame(self.chrome, bg=COLORS["ink"])
        self.nav_bar.pack(side="left", padx=24, pady=22)
        self.nav_buttons: dict[str, tk.Button] = {}
        for view, label in [("wbs", "WBS Studio"), ("tickets", "Ticket Board"), ("gantt", "Timeline")]:
            btn = tk.Button(
                self.nav_bar,
                text=label,
                command=lambda name=view: self.show_view(name),
                bg=COLORS["ink"],
                fg="#cfd5e2",
                activebackground=COLORS["ink_2"],
                activeforeground="#ffffff",
                bd=0,
                relief="flat",
                cursor="hand2",
                font=("Yu Gothic UI", 10, "bold"),
                padx=16,
                pady=9,
                highlightthickness=1,
                highlightbackground=COLORS["ink"],
            )
            btn.pack(side="left", padx=4)
            self.nav_buttons[view] = btn

        actions = tk.Frame(self.chrome, bg=COLORS["ink"])
        actions.pack(side="right", padx=22, pady=20)
        FlatButton(actions, "CSV出力", self.export_all_csv, kind="dark").pack(side="right", padx=(8, 0))
        FlatButton(actions, "保存", self.save_project, kind="dark").pack(side="right", padx=(8, 0))
        FlatButton(actions, "開く", self.open_project, kind="dark").pack(side="right", padx=(8, 0))
        FlatButton(actions, "新規", self.new_project, kind="dark").pack(side="right", padx=(8, 0))

        self.title_band = tk.Frame(self, bg=COLORS["paper"], height=92)
        self.title_band.pack(fill="x")
        self.title_band.pack_propagate(False)
        title_left = tk.Frame(self.title_band, bg=COLORS["paper"])
        title_left.pack(side="left", padx=28, pady=17)
        self.view_title = tk.Label(title_left, text="", bg=COLORS["paper"], fg=COLORS["text"], font=("Yu Gothic UI", 24, "bold"))
        self.view_title.pack(anchor="w")
        self.view_subtitle = tk.Label(title_left, text="", bg=COLORS["paper"], fg=COLORS["muted"], font=("Yu Gothic UI", 10))
        self.view_subtitle.pack(anchor="w")

        title_right = tk.Frame(self.title_band, bg=COLORS["paper"])
        title_right.pack(side="right", padx=28, pady=18)
        self.updated_label = tk.Label(
            title_right,
            text="",
            bg=COLORS["paper"],
            fg=COLORS["text_soft"],
            font=("Yu Gothic UI", 9),
        )
        self.updated_label.pack(anchor="e")

        self.content = tk.Frame(self, bg=COLORS["paper"])
        self.content.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        self.frames: dict[str, tk.Frame] = {}
        self.build_wbs_view()
        self.build_ticket_view()
        self.build_gantt_view()

    def panel(self, master: tk.Widget, *, bg: str = COLORS["surface"]) -> tk.Frame:
        return tk.Frame(master, bg=bg, highlightthickness=1, highlightbackground=COLORS["line"])

    def build_wbs_view(self) -> None:
        frame = tk.Frame(self.content, bg=COLORS["paper"])
        self.frames["wbs"] = frame

        self.metrics_frame = tk.Frame(frame, bg=COLORS["paper"])
        self.metrics_frame.pack(fill="x", pady=(0, 14))

        split = tk.Frame(frame, bg=COLORS["paper"])
        split.pack(fill="both", expand=True)
        split.grid_columnconfigure(0, weight=7, minsize=690)
        split.grid_columnconfigure(1, weight=3, minsize=320)
        split.grid_rowconfigure(0, weight=1)

        left = self.panel(split)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        right = self.panel(split)
        right.grid(row=0, column=1, sticky="nsew")

        toolbar = tk.Frame(left, bg=COLORS["surface"])
        toolbar.pack(fill="x", padx=16, pady=16)
        tk.Label(toolbar, text="Work Breakdown", bg=COLORS["surface"], fg=COLORS["text"], font=("Yu Gothic UI", 15, "bold")).pack(
            side="left"
        )
        FlatButton(toolbar, "追加", lambda: self.open_task_dialog(), kind="primary").pack(side="right", padx=(8, 0))
        FlatButton(toolbar, "子を追加", self.add_child_task, kind="secondary").pack(side="right", padx=(8, 0))
        FlatButton(toolbar, "編集", self.edit_selected_task, kind="secondary").pack(side="right", padx=(8, 0))
        FlatButton(toolbar, "削除", self.delete_selected_task, kind="danger").pack(side="right", padx=(8, 0))

        table_shell = tk.Frame(left, bg=COLORS["surface"])
        table_shell.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        columns = ("status", "start", "end", "progress", "owner")
        self.wbs_tree = ttk.Treeview(table_shell, columns=columns, show="tree headings", selectmode="browse", style="WBSync.Treeview")
        self.wbs_tree.heading("#0", text="WBS")
        self.wbs_tree.heading("status", text="状態")
        self.wbs_tree.heading("start", text="開始")
        self.wbs_tree.heading("end", text="終了")
        self.wbs_tree.heading("progress", text="進捗")
        self.wbs_tree.heading("owner", text="担当")
        self.wbs_tree.column("#0", width=390, minwidth=260)
        self.wbs_tree.column("status", width=105, anchor="center")
        self.wbs_tree.column("start", width=108, anchor="center")
        self.wbs_tree.column("end", width=108, anchor="center")
        self.wbs_tree.column("progress", width=84, anchor="e")
        self.wbs_tree.column("owner", width=120)
        self.wbs_tree.tag_configure("complete", foreground=COLORS["green"])
        self.wbs_tree.tag_configure("hold", foreground=COLORS["orange"])
        self.wbs_tree.tag_configure("review", foreground=COLORS["violet"])
        ybar = ttk.Scrollbar(table_shell, orient="vertical", command=self.wbs_tree.yview)
        xbar = ttk.Scrollbar(table_shell, orient="horizontal", command=self.wbs_tree.xview)
        self.wbs_tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        self.wbs_tree.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        table_shell.grid_columnconfigure(0, weight=1)
        table_shell.grid_rowconfigure(0, weight=1)
        self.wbs_tree.bind("<<TreeviewSelect>>", lambda _event: self.refresh_task_inspector())
        self.wbs_tree.bind("<Double-1>", lambda _event: self.edit_selected_task())

        self.inspector_header = tk.Frame(right, bg=COLORS["ink_2"], height=68)
        self.inspector_header.pack(fill="x")
        self.inspector_header.pack_propagate(False)
        tk.Label(
            self.inspector_header,
            text="Selected Work",
            bg=COLORS["ink_2"],
            fg="#ffffff",
            font=("Yu Gothic UI", 13, "bold"),
        ).pack(anchor="w", padx=16, pady=(13, 0))
        tk.Label(
            self.inspector_header,
            text="選択中のWBS詳細",
            bg=COLORS["ink_2"],
            fg="#bfc7d7",
            font=("Yu Gothic UI", 9),
        ).pack(anchor="w", padx=16)

        self.task_inspector = tk.Frame(right, bg=COLORS["surface"])
        self.task_inspector.pack(fill="both", expand=True)

    def build_ticket_view(self) -> None:
        frame = tk.Frame(self.content, bg=COLORS["paper"])
        self.frames["tickets"] = frame

        panel = self.panel(frame)
        panel.pack(fill="both", expand=True)

        toolbar = tk.Frame(panel, bg=COLORS["surface"])
        toolbar.pack(fill="x", padx=16, pady=16)
        tk.Label(toolbar, text="Kanban", bg=COLORS["surface"], fg=COLORS["text"], font=("Yu Gothic UI", 15, "bold")).pack(side="left")

        search = ttk.Entry(toolbar, textvariable=self.search_var, width=28)
        search.pack(side="left", padx=(18, 8))
        search.bind("<KeyRelease>", lambda _event: self.refresh_tickets())

        status_filter = ttk.Combobox(
            toolbar,
            textvariable=self.ticket_status_filter,
            values=["すべて", *TICKET_STATUSES],
            width=10,
            state="readonly",
        )
        status_filter.pack(side="left")
        status_filter.bind("<<ComboboxSelected>>", lambda _event: self.refresh_tickets())

        FlatButton(toolbar, "追加", self.open_ticket_dialog, kind="primary").pack(side="right", padx=(8, 0))
        FlatButton(toolbar, "編集", self.edit_selected_ticket, kind="secondary").pack(side="right", padx=(8, 0))
        FlatButton(toolbar, "削除", self.delete_selected_ticket, kind="danger").pack(side="right", padx=(8, 0))

        self.kanban = tk.Frame(panel, bg=COLORS["surface"])
        self.kanban.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def build_gantt_view(self) -> None:
        frame = tk.Frame(self.content, bg=COLORS["paper"])
        self.frames["gantt"] = frame

        panel = self.panel(frame)
        panel.pack(fill="both", expand=True)

        toolbar = tk.Frame(panel, bg=COLORS["surface"])
        toolbar.pack(fill="x", padx=16, pady=16)
        tk.Label(toolbar, text="Schedule Map", bg=COLORS["surface"], fg=COLORS["text"], font=("Yu Gothic UI", 15, "bold")).pack(
            side="left"
        )
        ttk.Combobox(toolbar, textvariable=self.gantt_zoom, values=["日", "週", "月"], width=8, state="readonly").pack(
            side="left", padx=(16, 8)
        )
        self.gantt_zoom.trace_add("write", lambda *_args: self.refresh_gantt())
        FlatButton(toolbar, "CSV出力", self.export_gantt_csv, kind="secondary").pack(side="right", padx=(8, 0))
        FlatButton(toolbar, "再描画", self.refresh_gantt, kind="secondary").pack(side="right", padx=(8, 0))

        canvas_shell = tk.Frame(panel, bg=COLORS["surface"])
        canvas_shell.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.gantt_canvas = tk.Canvas(canvas_shell, bg=COLORS["surface_2"], highlightthickness=0)
        ybar = ttk.Scrollbar(canvas_shell, orient="vertical", command=self.gantt_canvas.yview)
        xbar = ttk.Scrollbar(canvas_shell, orient="horizontal", command=self.gantt_canvas.xview)
        self.gantt_canvas.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        self.gantt_canvas.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        canvas_shell.grid_columnconfigure(0, weight=1)
        canvas_shell.grid_rowconfigure(0, weight=1)
        self.gantt_canvas.bind("<MouseWheel>", self.on_gantt_mousewheel)

    def show_view(self, name: str) -> None:
        self.current_view = name
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True)

        title, subtitle = VIEW_TITLES[name]
        self.view_title.configure(text=title)
        self.view_subtitle.configure(text=subtitle)
        for key, button in self.nav_buttons.items():
            active = key == name
            button.configure(
                bg=COLORS["teal"] if active else COLORS["ink"],
                fg="#ffffff" if active else "#cfd5e2",
                highlightbackground=COLORS["teal"] if active else COLORS["ink"],
            )
        if name == "gantt":
            self.after(50, self.refresh_gantt)

    def load_or_seed_data(self) -> dict:
        path = default_data_path()
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as f:
                    return self.normalize_data(json.load(f))
            except (OSError, json.JSONDecodeError):
                messagebox.showwarning(APP_NAME, "保存済みデータを読み込めなかったため、新規データで開始します。")
        return create_sample_data()

    def normalize_data(self, data: dict) -> dict:
        data.setdefault("version", DATA_VERSION)
        data.setdefault("meta", {})
        data["meta"].setdefault("project_name", "新規プロジェクト")
        data["meta"].setdefault("updated_at", datetime.now().isoformat(timespec="seconds"))
        data.setdefault("tasks", [])
        data.setdefault("tickets", [])
        for task in data["tasks"]:
            task.setdefault("id", self.next_task_id())
            task.setdefault("parent_id", "")
            task.setdefault("code", "")
            task.setdefault("title", "")
            task.setdefault("owner", "")
            task.setdefault("status", "未着手")
            task.setdefault("start", iso_today())
            task.setdefault("end", iso_today())
            task.setdefault("progress", 0)
            task.setdefault("memo", "")
        for ticket in data["tickets"]:
            ticket.setdefault("id", self.next_ticket_id())
            ticket.setdefault("key", self.next_ticket_key())
            ticket.setdefault("title", "")
            ticket.setdefault("assignee", "")
            ticket.setdefault("status", "未対応")
            ticket.setdefault("priority", "中")
            ticket.setdefault("due", iso_today())
            ticket.setdefault("task_id", "")
            ticket.setdefault("memo", "")
        return data

    def tasks(self) -> list[dict]:
        return self.data["tasks"]

    def tickets(self) -> list[dict]:
        return self.data["tickets"]

    def task_by_id(self, task_id: str) -> dict | None:
        return next((task for task in self.tasks() if task.get("id") == task_id), None)

    def ticket_by_id(self, ticket_id: str) -> dict | None:
        return next((ticket for ticket in self.tickets() if ticket.get("id") == ticket_id), None)

    def next_task_id(self) -> str:
        numbers = []
        for task in self.data.get("tasks", []) if hasattr(self, "data") else []:
            raw = str(task.get("id", "")).replace("task-", "")
            if raw.isdigit():
                numbers.append(int(raw))
        return f"task-{(max(numbers) + 1 if numbers else 1):03d}"

    def next_ticket_id(self) -> str:
        numbers = []
        for ticket in self.data.get("tickets", []) if hasattr(self, "data") else []:
            raw = str(ticket.get("id", "")).replace("ticket-", "")
            if raw.isdigit():
                numbers.append(int(raw))
        return f"ticket-{(max(numbers) + 1 if numbers else 1):03d}"

    def next_ticket_key(self) -> str:
        numbers = []
        for ticket in self.data.get("tickets", []) if hasattr(self, "data") else []:
            raw = str(ticket.get("key", "")).replace("T-", "")
            if raw.isdigit():
                numbers.append(int(raw))
        return f"T-{(max(numbers) + 1 if numbers else 1):03d}"

    def next_code(self, parent_id: str = "") -> str:
        siblings = [task for task in self.tasks() if task.get("parent_id", "") == parent_id]
        next_number = len(siblings) + 1
        if parent_id:
            parent = self.task_by_id(parent_id)
            prefix = parent.get("code", "") if parent else ""
            return f"{prefix}.{next_number}" if prefix else str(next_number)
        return str(next_number)

    def task_depth(self, task: dict) -> int:
        depth = 0
        current = task
        seen: set[str] = set()
        while current.get("parent_id"):
            parent_id = current.get("parent_id", "")
            if parent_id in seen:
                break
            seen.add(parent_id)
            parent = self.task_by_id(parent_id)
            if not parent:
                break
            depth += 1
            current = parent
        return depth

    def ordered_tasks(self) -> list[dict]:
        by_parent: dict[str, list[dict]] = {}
        for task in self.tasks():
            by_parent.setdefault(task.get("parent_id", ""), []).append(task)
        for siblings in by_parent.values():
            siblings.sort(key=lambda item: (code_key(item.get("code", "")), item.get("title", "")))

        result: list[dict] = []

        def walk(parent_id: str) -> None:
            for task in by_parent.get(parent_id, []):
                result.append(task)
                walk(task.get("id", ""))

        walk("")
        result_ids = {task.get("id") for task in result}
        dangling = [task for task in self.tasks() if task.get("id") not in result_ids]
        result.extend(sorted(dangling, key=lambda item: (code_key(item.get("code", "")), item.get("title", ""))))
        return result

    def descendants_of(self, task_id: str) -> set[str]:
        descendants: set[str] = set()

        def walk(parent_id: str) -> None:
            for task in self.tasks():
                if task.get("parent_id") == parent_id and task.get("id") not in descendants:
                    descendants.add(task["id"])
                    walk(task["id"])

        walk(task_id)
        return descendants

    def refresh_all(self) -> None:
        self.refresh_chrome()
        self.refresh_metrics()
        self.refresh_wbs()
        self.refresh_task_inspector()
        self.refresh_tickets()
        self.refresh_gantt()

    def refresh_chrome(self) -> None:
        self.path_label.configure(text=str(self.project_path))
        updated_at = self.data.get("meta", {}).get("updated_at", "")
        self.updated_label.configure(text=f"最終更新: {updated_at}" if updated_at else "")

    def refresh_metrics(self) -> None:
        for child in self.metrics_frame.winfo_children():
            child.destroy()
        total = len(self.tasks())
        done = sum(1 for task in self.tasks() if task.get("status") == "完了")
        active = sum(1 for task in self.tasks() if task.get("status") == "進行中")
        progress_values = [int(task.get("progress", 0)) for task in self.tasks()]
        avg_progress = round(sum(progress_values) / len(progress_values)) if progress_values else 0
        open_tickets = sum(1 for ticket in self.tickets() if ticket.get("status") != "完了")
        values = [
            ("WBS", str(total), COLORS["teal"]),
            ("進行中", str(active), COLORS["blue"]),
            ("平均進捗", f"{avg_progress}%", COLORS["violet"]),
            ("未完了チケット", str(open_tickets), COLORS["orange"]),
            ("完了", str(done), COLORS["green"]),
        ]
        for idx, (label, value, accent) in enumerate(values):
            tile = MetricTile(self.metrics_frame, label, value, accent)
            tile.grid(row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else 10, 0))
            self.metrics_frame.grid_columnconfigure(idx, weight=1, uniform="metric")

    def refresh_wbs(self) -> None:
        selected = self.wbs_tree.selection()
        opened = {iid for iid in self.wbs_tree.get_children("") if self.wbs_tree.item(iid, "open")}
        for iid in self.wbs_tree.get_children(""):
            self.wbs_tree.delete(iid)

        for task in self.ordered_tasks():
            parent_id = task.get("parent_id", "")
            parent_iid = parent_id if parent_id and self.wbs_tree.exists(parent_id) else ""
            status = task.get("status", "")
            tags = []
            if status == "完了":
                tags.append("complete")
            elif status == "保留":
                tags.append("hold")
            elif status == "レビュー":
                tags.append("review")
            self.wbs_tree.insert(
                parent_iid,
                "end",
                iid=task["id"],
                text=display_task(task),
                values=(
                    status,
                    task.get("start", ""),
                    task.get("end", ""),
                    f"{int(task.get('progress', 0))}%",
                    task.get("owner", ""),
                ),
                tags=tags,
            )
            if task["id"] in opened:
                self.wbs_tree.item(task["id"], open=True)
        if selected and self.wbs_tree.exists(selected[0]):
            self.wbs_tree.selection_set(selected[0])
        for iid in self.wbs_tree.get_children(""):
            self.wbs_tree.item(iid, open=True)

    def refresh_task_inspector(self) -> None:
        for child in self.task_inspector.winfo_children():
            child.destroy()
        task = self.task_by_id(self.selected_task_id() or "")
        if not task:
            tk.Label(
                self.task_inspector,
                text="WBSを選択してください",
                bg=COLORS["surface"],
                fg=COLORS["muted"],
                font=("Yu Gothic UI", 12, "bold"),
            ).pack(anchor="w", padx=18, pady=18)
            return

        body = tk.Frame(self.task_inspector, bg=COLORS["surface"])
        body.pack(fill="both", expand=True, padx=18, pady=18)
        status = task.get("status", "")
        tk.Label(body, text=task.get("code", ""), bg=COLORS["surface"], fg=STATUS_COLORS.get(status, COLORS["teal"]), font=("Yu Gothic UI", 12, "bold")).pack(anchor="w")
        tk.Label(body, text=task.get("title", ""), bg=COLORS["surface"], fg=COLORS["text"], font=("Yu Gothic UI", 18, "bold"), wraplength=300, justify="left").pack(anchor="w", pady=(2, 10))

        self._inspector_line(body, "状態", status, STATUS_COLORS.get(status, COLORS["text"]))
        self._inspector_line(body, "担当", task.get("owner", "") or "-", COLORS["text_soft"])
        self._inspector_line(body, "期間", f"{task.get('start', '')} - {task.get('end', '')}", COLORS["text_soft"])
        self._inspector_line(body, "進捗", f"{int(task.get('progress', 0))}%", COLORS["text_soft"])

        progress_shell = tk.Canvas(body, height=14, bg=COLORS["surface"], highlightthickness=0)
        progress_shell.pack(fill="x", pady=(2, 18))
        progress_shell.update_idletasks()
        width = max(260, progress_shell.winfo_width())
        rounded_rect(progress_shell, 0, 2, width - 2, 12, 6, fill="#e7ebf1", outline="")
        progress = max(0, min(100, int(task.get("progress", 0))))
        rounded_rect(progress_shell, 0, 2, int((width - 2) * progress / 100), 12, 6, fill=COLORS["teal"], outline="")

        memo = task.get("memo", "")
        if memo:
            tk.Label(body, text="メモ", bg=COLORS["surface"], fg=COLORS["muted"], font=("Yu Gothic UI", 9, "bold")).pack(anchor="w")
            tk.Label(body, text=memo, bg=COLORS["surface_2"], fg=COLORS["text_soft"], font=("Yu Gothic UI", 10), wraplength=300, justify="left", padx=10, pady=9).pack(fill="x", pady=(5, 16))

        linked = [ticket for ticket in self.tickets() if ticket.get("task_id") == task.get("id")]
        tk.Label(body, text=f"関連チケット {len(linked)}件", bg=COLORS["surface"], fg=COLORS["text"], font=("Yu Gothic UI", 11, "bold")).pack(anchor="w", pady=(4, 8))
        for ticket in linked[:6]:
            self._small_ticket(body, ticket)

    def _inspector_line(self, master: tk.Widget, label: str, value: str, color: str) -> None:
        row = tk.Frame(master, bg=COLORS["surface"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, bg=COLORS["surface"], fg=COLORS["muted"], font=("Yu Gothic UI", 9, "bold"), width=8, anchor="w").pack(side="left")
        tk.Label(row, text=value, bg=COLORS["surface"], fg=color, font=("Yu Gothic UI", 10, "bold"), anchor="w").pack(side="left", fill="x", expand=True)

    def _small_ticket(self, master: tk.Widget, ticket: dict) -> None:
        card = tk.Frame(master, bg=COLORS["surface_2"], highlightthickness=1, highlightbackground=COLORS["line"])
        card.pack(fill="x", pady=4)
        tk.Label(card, text=f"{ticket.get('key', '')}  {ticket.get('title', '')}", bg=COLORS["surface_2"], fg=COLORS["text"], font=("Yu Gothic UI", 9, "bold"), wraplength=280, justify="left").pack(anchor="w", padx=10, pady=(8, 1))
        tk.Label(card, text=f"{ticket.get('status', '')} / {ticket.get('priority', '')}", bg=COLORS["surface_2"], fg=COLORS["muted"], font=("Yu Gothic UI", 8)).pack(anchor="w", padx=10, pady=(0, 8))

    def refresh_tickets(self) -> None:
        for child in self.kanban.winfo_children():
            child.destroy()
        query = self.search_var.get().strip().lower()
        filter_status = self.ticket_status_filter.get()
        statuses = TICKET_STATUSES if filter_status == "すべて" else [filter_status]
        for idx in range(len(TICKET_STATUSES)):
            self.kanban.grid_columnconfigure(idx, weight=0, uniform="")

        for col_idx, status in enumerate(statuses):
            self.kanban.grid_columnconfigure(col_idx, weight=1, uniform="kanban")
            column = tk.Frame(self.kanban, bg=COLORS["surface_2"], highlightthickness=1, highlightbackground=COLORS["line"])
            column.grid(row=0, column=col_idx, sticky="nsew", padx=(0 if col_idx == 0 else 10, 0))
            self.kanban.grid_rowconfigure(0, weight=1)

            header = tk.Frame(column, bg=STATUS_COLORS.get(status, COLORS["teal"]))
            header.pack(fill="x")
            column_tickets = [ticket for ticket in self.tickets() if ticket.get("status") == status]
            filtered = []
            for ticket in column_tickets:
                haystack = " ".join(
                    [
                        ticket.get("key", ""),
                        ticket.get("title", ""),
                        ticket.get("assignee", ""),
                        ticket.get("memo", ""),
                    ]
                ).lower()
                if not query or query in haystack:
                    filtered.append(ticket)
            tk.Label(header, text=status, bg=STATUS_COLORS.get(status, COLORS["teal"]), fg="#ffffff", font=("Yu Gothic UI", 11, "bold")).pack(side="left", padx=12, pady=10)
            tk.Label(header, text=str(len(filtered)), bg=STATUS_COLORS.get(status, COLORS["teal"]), fg="#ffffff", font=("Yu Gothic UI", 10, "bold")).pack(side="right", padx=12)

            scroller = ScrollFrame(column, bg=COLORS["surface_2"])
            scroller.pack(fill="both", expand=True, padx=8, pady=8)
            for ticket in sorted(filtered, key=lambda item: (item.get("due", ""), item.get("key", ""))):
                self._ticket_card(scroller.inner, ticket)

    def _ticket_card(self, master: tk.Widget, ticket: dict) -> None:
        selected = ticket.get("id") == self.selected_ticket_id_value
        border = COLORS["teal"] if selected else COLORS["line"]
        card = tk.Frame(master, bg=COLORS["surface"], highlightthickness=2 if selected else 1, highlightbackground=border)
        card.pack(fill="x", padx=2, pady=5)

        top = tk.Frame(card, bg=COLORS["surface"])
        top.pack(fill="x", padx=10, pady=(9, 3))
        priority = ticket.get("priority", "中")
        tk.Label(top, text=ticket.get("key", ""), bg=COLORS["surface"], fg=COLORS["muted"], font=("Yu Gothic UI", 9, "bold")).pack(side="left")
        tk.Label(top, text=priority, bg=PRIORITY_COLORS.get(priority, COLORS["teal"]), fg="#ffffff", font=("Yu Gothic UI", 8, "bold"), padx=8, pady=2).pack(side="right")

        tk.Label(
            card,
            text=ticket.get("title", ""),
            bg=COLORS["surface"],
            fg=COLORS["text"],
            font=("Yu Gothic UI", 10, "bold"),
            wraplength=210,
            justify="left",
        ).pack(anchor="w", padx=10, pady=(2, 7))

        task = self.task_by_id(ticket.get("task_id", ""))
        meta = f"{ticket.get('assignee', '-') or '-'} / {ticket.get('due', '')}"
        if task:
            meta = f"{meta}\n{task.get('code', '')} {task.get('title', '')}"
        tk.Label(
            card,
            text=meta,
            bg=COLORS["surface"],
            fg=COLORS["text_soft"],
            font=("Yu Gothic UI", 8),
            wraplength=210,
            justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 9))

        for widget in (card, *card.winfo_children()):
            widget.bind("<Button-1>", lambda _event, tid=ticket.get("id", ""): self.select_ticket(tid))
            widget.bind("<Double-1>", lambda _event, tid=ticket.get("id", ""): self.edit_ticket_by_id(tid))

    def select_ticket(self, ticket_id: str) -> None:
        self.selected_ticket_id_value = ticket_id
        self.refresh_tickets()

    def refresh_gantt(self) -> None:
        if not hasattr(self, "gantt_canvas"):
            return
        canvas = self.gantt_canvas
        canvas.delete("all")
        tasks_with_dates = []
        for task in self.ordered_tasks():
            start = safe_date(task.get("start"))
            end = safe_date(task.get("end"))
            if not start or not end:
                continue
            if end < start:
                start, end = end, start
            tasks_with_dates.append((task, start, end))

        if not tasks_with_dates:
            canvas.create_text(30, 30, anchor="nw", text="日付が設定されたWBSを追加してください。", fill=COLORS["muted"], font=("Yu Gothic UI", 12))
            canvas.configure(scrollregion=(0, 0, 1000, 540))
            return

        min_start = min(start for _task, start, _end in tasks_with_dates) - timedelta(days=2)
        max_end = max(end for _task, _start, end in tasks_with_dates) + timedelta(days=4)
        today = date.today()
        min_start = min(min_start, today - timedelta(days=1))
        max_end = max(max_end, today + timedelta(days=1))

        zoom = self.gantt_zoom.get()
        pixels_per_day = {"日": 34, "週": 13, "月": 6}.get(zoom, 13)
        row_h = 42
        header_h = 78
        left_w = 330
        total_days = (max_end - min_start).days + 1
        chart_w = left_w + total_days * pixels_per_day + 100
        chart_h = header_h + len(tasks_with_dates) * row_h + 70

        canvas.create_rectangle(0, 0, chart_w, chart_h, fill=COLORS["surface_2"], outline="")
        canvas.create_rectangle(0, 0, chart_w, header_h, fill=COLORS["ink_2"], outline="")
        canvas.create_rectangle(0, header_h, left_w, chart_h, fill=COLORS["surface"], outline="")
        canvas.create_text(22, 23, anchor="nw", text="WBS", fill="#ffffff", font=("Yu Gothic UI", 13, "bold"))

        label_step = 1 if zoom == "日" else 7 if zoom == "週" else 30
        current = min_start
        while current <= max_end:
            offset_days = (current - min_start).days
            x = left_w + offset_days * pixels_per_day
            if current.weekday() >= 5:
                canvas.create_rectangle(x, header_h, x + pixels_per_day, chart_h, fill="#f4eadb", outline="")
            canvas.create_line(x, header_h, x, chart_h - 38, fill="#dfe5ef")
            if offset_days % label_step == 0:
                label = current.strftime("%m/%d") if zoom != "月" else current.strftime("%Y/%m")
                canvas.create_text(x + 5, 24, anchor="nw", text=label, fill="#dce3ef", font=("Yu Gothic UI", 9, "bold"))
            current += timedelta(days=1)

        if min_start <= today <= max_end:
            today_x = left_w + (today - min_start).days * pixels_per_day
            canvas.create_line(today_x, 0, today_x, chart_h - 38, fill=COLORS["red"], width=2)
            canvas.create_text(today_x + 7, 51, anchor="nw", text="Today", fill="#ffffff", font=("Yu Gothic UI", 9, "bold"))

        for idx, (task, start, end) in enumerate(tasks_with_dates):
            y = header_h + idx * row_h
            row_fill = "#ffffff" if idx % 2 == 0 else "#f8fafc"
            canvas.create_rectangle(0, y, chart_w, y + row_h, fill=row_fill, outline="")
            canvas.create_line(0, y + row_h, chart_w, y + row_h, fill="#edf1f6")
            depth = self.task_depth(task)
            canvas.create_text(
                22 + depth * 18,
                y + 11,
                anchor="nw",
                text=display_task(task)[:38],
                fill=COLORS["text"],
                font=("Yu Gothic UI", 10, "bold" if depth == 0 else "normal"),
            )
            owner = task.get("owner", "")
            if owner:
                canvas.create_text(270, y + 12, anchor="nw", text=owner[:10], fill=COLORS["muted"], font=("Yu Gothic UI", 9))

            x1 = left_w + (start - min_start).days * pixels_per_day
            x2 = left_w + ((end - min_start).days + 1) * pixels_per_day
            bar = STATUS_COLORS.get(task.get("status"), COLORS["teal"])
            rounded_rect(canvas, int(x1), y + 12, int(x2), y + 30, 8, fill="#dfe6f0", outline="")
            progress = max(0, min(100, int(task.get("progress", 0))))
            progress_x = int(x1 + (x2 - x1) * progress / 100)
            if progress_x > x1:
                rounded_rect(canvas, int(x1), y + 12, progress_x, y + 30, 8, fill=bar, outline="")
            canvas.create_text(int(x2) + 8, y + 10, anchor="nw", text=f"{progress}%", fill=COLORS["muted"], font=("Yu Gothic UI", 9, "bold"))

        canvas.create_line(left_w, 0, left_w, chart_h, fill=COLORS["line"])
        canvas.configure(scrollregion=(0, 0, chart_w, chart_h))

    def on_gantt_mousewheel(self, event: tk.Event) -> None:
        direction = -1 if event.delta > 0 else 1
        self.gantt_canvas.yview_scroll(direction * 3, "units")

    def selected_task_id(self) -> str | None:
        selected = self.wbs_tree.selection()
        return selected[0] if selected else None

    def selected_ticket_id(self) -> str | None:
        return self.selected_ticket_id_value or None

    def add_child_task(self) -> None:
        task_id = self.selected_task_id()
        if not task_id:
            messagebox.showinfo(APP_NAME, "親にするWBSを選択してください。")
            return
        self.open_task_dialog(parent_id=task_id)

    def edit_selected_task(self) -> None:
        task_id = self.selected_task_id()
        if not task_id:
            messagebox.showinfo(APP_NAME, "編集するWBSを選択してください。")
            return
        task = self.task_by_id(task_id)
        if task:
            self.open_task_dialog(task=task)

    def delete_selected_task(self) -> None:
        task_id = self.selected_task_id()
        if not task_id:
            messagebox.showinfo(APP_NAME, "削除するWBSを選択してください。")
            return
        task = self.task_by_id(task_id)
        if not task:
            return
        descendants = self.descendants_of(task_id)
        affected = {task_id, *descendants}
        count = 1 + len(descendants)
        if not messagebox.askyesno(APP_NAME, f"{display_task(task)} を削除しますか？\n子WBSを含めて {count} 件が削除されます。"):
            return
        self.data["tasks"] = [item for item in self.tasks() if item.get("id") not in affected]
        for ticket in self.tickets():
            if ticket.get("task_id") in affected:
                ticket["task_id"] = ""
        self.mark_changed()

    def edit_selected_ticket(self) -> None:
        ticket_id = self.selected_ticket_id()
        if not ticket_id:
            messagebox.showinfo(APP_NAME, "編集するチケットを選択してください。")
            return
        self.edit_ticket_by_id(ticket_id)

    def edit_ticket_by_id(self, ticket_id: str) -> None:
        ticket = self.ticket_by_id(ticket_id)
        if ticket:
            self.open_ticket_dialog(ticket=ticket)

    def delete_selected_ticket(self) -> None:
        ticket_id = self.selected_ticket_id()
        if not ticket_id:
            messagebox.showinfo(APP_NAME, "削除するチケットを選択してください。")
            return
        ticket = self.ticket_by_id(ticket_id)
        if not ticket:
            return
        if not messagebox.askyesno(APP_NAME, f"{ticket.get('key')} を削除しますか？"):
            return
        self.data["tickets"] = [item for item in self.tickets() if item.get("id") != ticket_id]
        self.selected_ticket_id_value = ""
        self.mark_changed()

    def task_parent_choices(self, current_task_id: str = "") -> tuple[list[str], dict[str, str]]:
        blocked = {current_task_id}
        if current_task_id:
            blocked |= self.descendants_of(current_task_id)
        labels = ["なし"]
        mapping = {"なし": ""}
        for task in self.ordered_tasks():
            if task.get("id") in blocked:
                continue
            label = display_task(task)
            labels.append(label)
            mapping[label] = task["id"]
        return labels, mapping

    def open_task_dialog(self, task: dict | None = None, parent_id: str = "") -> None:
        is_edit = task is not None
        dialog = self.dialog_shell("WBS編集" if is_edit else "WBS追加")
        container = dialog.body

        current_parent = task.get("parent_id", "") if task else parent_id
        parent_labels, parent_map = self.task_parent_choices(task.get("id", "") if task else "")
        parent_label = next((label for label, value in parent_map.items() if value == current_parent), "なし")

        values = {
            "parent": tk.StringVar(value=parent_label),
            "code": tk.StringVar(value=task.get("code", "") if task else self.next_code(parent_id)),
            "title": tk.StringVar(value=task.get("title", "") if task else ""),
            "owner": tk.StringVar(value=task.get("owner", "") if task else ""),
            "status": tk.StringVar(value=task.get("status", "未着手") if task else "未着手"),
            "start": tk.StringVar(value=task.get("start", iso_today()) if task else iso_today()),
            "end": tk.StringVar(value=task.get("end", iso_today()) if task else iso_today()),
            "progress": tk.StringVar(value=str(task.get("progress", 0)) if task else "0"),
        }

        widgets = [
            ("親WBS", ttk.Combobox(container, textvariable=values["parent"], values=parent_labels, state="readonly", width=44)),
            ("WBSコード", ttk.Entry(container, textvariable=values["code"], width=46)),
            ("タイトル", ttk.Entry(container, textvariable=values["title"], width=46)),
            ("担当", ttk.Entry(container, textvariable=values["owner"], width=46)),
            ("状態", ttk.Combobox(container, textvariable=values["status"], values=TASK_STATUSES, state="readonly", width=44)),
            ("開始日", ttk.Entry(container, textvariable=values["start"], width=46)),
            ("終了日", ttk.Entry(container, textvariable=values["end"], width=46)),
            ("進捗(%)", ttk.Spinbox(container, from_=0, to=100, increment=5, textvariable=values["progress"], width=44)),
        ]
        for row_idx, (label, widget) in enumerate(widgets):
            self.form_row(container, label, widget, row_idx)

        tk.Label(container, text="メモ", bg=COLORS["surface"], fg=COLORS["muted"], font=("Yu Gothic UI", 9, "bold")).grid(row=8, column=0, sticky="nw", padx=18, pady=(9, 5))
        memo = tk.Text(container, height=4, width=46, bd=1, relief="solid", highlightthickness=0, font=("Yu Gothic UI", 10))
        memo.grid(row=8, column=1, sticky="ew", padx=18, pady=(9, 5))
        memo.insert("1.0", task.get("memo", "") if task else "")

        footer = tk.Frame(container, bg=COLORS["surface"])
        footer.grid(row=9, column=0, columnspan=2, sticky="ew", padx=18, pady=18)
        FlatButton(footer, "キャンセル", dialog.destroy, kind="secondary").pack(side="right", padx=(8, 0))

        def save() -> None:
            title = values["title"].get().strip()
            code = values["code"].get().strip()
            if not title:
                messagebox.showerror(APP_NAME, "タイトルを入力してください。", parent=dialog)
                return
            if not code:
                messagebox.showerror(APP_NAME, "WBSコードを入力してください。", parent=dialog)
                return
            try:
                start = parse_date(values["start"].get())
                end = parse_date(values["end"].get())
                progress = clamp_int(values["progress"].get())
            except ValueError as exc:
                messagebox.showerror(APP_NAME, str(exc), parent=dialog)
                return
            if end < start:
                messagebox.showerror(APP_NAME, "終了日は開始日以降にしてください。", parent=dialog)
                return

            payload = {
                "parent_id": parent_map.get(values["parent"].get(), ""),
                "code": code,
                "title": title,
                "owner": values["owner"].get().strip(),
                "status": values["status"].get(),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "progress": progress,
                "memo": memo.get("1.0", "end").strip(),
            }
            if is_edit and task:
                task.update(payload)
            else:
                payload["id"] = self.next_task_id()
                self.tasks().append(payload)
            dialog.destroy()
            self.mark_changed()

        FlatButton(footer, "保存", save, kind="primary").pack(side="right")
        if container.first_widget:
            container.first_widget.focus_set()
        self.center_dialog(dialog)

    def open_ticket_dialog(self, ticket: dict | None = None) -> None:
        is_edit = ticket is not None
        dialog = self.dialog_shell("チケット編集" if is_edit else "チケット追加")
        container = dialog.body

        task_labels = ["未紐付け"] + [display_task(task) for task in self.ordered_tasks()]
        task_map = {"未紐付け": ""}
        for task in self.ordered_tasks():
            task_map[display_task(task)] = task["id"]
        current_task_id = ticket.get("task_id", "") if ticket else ""
        current_task_label = next((label for label, value in task_map.items() if value == current_task_id), "未紐付け")

        values = {
            "key": tk.StringVar(value=ticket.get("key", "") if ticket else self.next_ticket_key()),
            "title": tk.StringVar(value=ticket.get("title", "") if ticket else ""),
            "assignee": tk.StringVar(value=ticket.get("assignee", "") if ticket else ""),
            "status": tk.StringVar(value=ticket.get("status", "未対応") if ticket else "未対応"),
            "priority": tk.StringVar(value=ticket.get("priority", "中") if ticket else "中"),
            "due": tk.StringVar(value=ticket.get("due", iso_today()) if ticket else iso_today()),
            "task": tk.StringVar(value=current_task_label),
        }
        widgets = [
            ("チケット番号", ttk.Entry(container, textvariable=values["key"], width=46)),
            ("タイトル", ttk.Entry(container, textvariable=values["title"], width=46)),
            ("担当", ttk.Entry(container, textvariable=values["assignee"], width=46)),
            ("状態", ttk.Combobox(container, textvariable=values["status"], values=TICKET_STATUSES, state="readonly", width=44)),
            ("優先度", ttk.Combobox(container, textvariable=values["priority"], values=PRIORITIES, state="readonly", width=44)),
            ("期限", ttk.Entry(container, textvariable=values["due"], width=46)),
            ("WBS", ttk.Combobox(container, textvariable=values["task"], values=task_labels, state="readonly", width=44)),
        ]
        for row_idx, (label, widget) in enumerate(widgets):
            self.form_row(container, label, widget, row_idx)

        tk.Label(container, text="メモ", bg=COLORS["surface"], fg=COLORS["muted"], font=("Yu Gothic UI", 9, "bold")).grid(row=7, column=0, sticky="nw", padx=18, pady=(9, 5))
        memo = tk.Text(container, height=5, width=46, bd=1, relief="solid", highlightthickness=0, font=("Yu Gothic UI", 10))
        memo.grid(row=7, column=1, sticky="ew", padx=18, pady=(9, 5))
        memo.insert("1.0", ticket.get("memo", "") if ticket else "")

        footer = tk.Frame(container, bg=COLORS["surface"])
        footer.grid(row=8, column=0, columnspan=2, sticky="ew", padx=18, pady=18)
        FlatButton(footer, "キャンセル", dialog.destroy, kind="secondary").pack(side="right", padx=(8, 0))

        def save() -> None:
            key = values["key"].get().strip()
            title = values["title"].get().strip()
            if not key:
                messagebox.showerror(APP_NAME, "チケット番号を入力してください。", parent=dialog)
                return
            if not title:
                messagebox.showerror(APP_NAME, "タイトルを入力してください。", parent=dialog)
                return
            try:
                due = parse_date(values["due"].get())
            except ValueError:
                messagebox.showerror(APP_NAME, "期限は YYYY-MM-DD 形式で入力してください。", parent=dialog)
                return
            payload = {
                "key": key,
                "title": title,
                "assignee": values["assignee"].get().strip(),
                "status": values["status"].get(),
                "priority": values["priority"].get(),
                "due": due.isoformat(),
                "task_id": task_map.get(values["task"].get(), ""),
                "memo": memo.get("1.0", "end").strip(),
            }
            if is_edit and ticket:
                ticket.update(payload)
            else:
                payload["id"] = self.next_ticket_id()
                self.tickets().append(payload)
                self.selected_ticket_id_value = payload["id"]
            dialog.destroy()
            self.mark_changed()

        FlatButton(footer, "保存", save, kind="primary").pack(side="right")
        if container.first_widget:
            container.first_widget.focus_set()
        self.center_dialog(dialog)

    def dialog_shell(self, title: str) -> tk.Toplevel:
        dialog = tk.Toplevel(self)
        dialog.title(title)
        self.apply_icon_to_window(dialog)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(bg=COLORS["paper"])
        dialog.resizable(False, False)
        shell = self.panel(dialog)
        shell.pack(fill="both", expand=True, padx=18, pady=18)
        header = tk.Frame(shell, bg=COLORS["ink_2"], height=58)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=title, bg=COLORS["ink_2"], fg="#ffffff", font=("Yu Gothic UI", 13, "bold")).pack(anchor="w", padx=18, pady=17)
        body = tk.Frame(shell, bg=COLORS["surface"])
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(1, weight=1)
        body.first_widget = None
        dialog.body = body
        return dialog

    def form_row(self, master: tk.Widget, label: str, widget: tk.Widget, row: int) -> None:
        tk.Label(master, text=label, bg=COLORS["surface"], fg=COLORS["muted"], font=("Yu Gothic UI", 9, "bold")).grid(
            row=row, column=0, sticky="w", padx=18, pady=(13 if row == 0 else 8, 4)
        )
        widget.grid(row=row, column=1, sticky="ew", padx=18, pady=(13 if row == 0 else 8, 4))
        if row == 0:
            master.first_widget = widget

    def center_dialog(self, dialog: tk.Toplevel) -> None:
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = self.winfo_rootx() + (self.winfo_width() - width) // 2
        y = self.winfo_rooty() + (self.winfo_height() - height) // 2
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")

    def mark_changed(self) -> None:
        self.dirty = True
        self.data["meta"]["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self.save_project(silent=True)
        self.refresh_all()

    def save_project(self, silent: bool = False) -> bool:
        try:
            self.project_path.parent.mkdir(parents=True, exist_ok=True)
            with self.project_path.open("w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            self.dirty = False
            if not silent:
                messagebox.showinfo(APP_NAME, f"保存しました。\n{self.project_path}")
            return True
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"保存できませんでした。\n{exc}")
            return False

    def save_project_as(self) -> None:
        path = filedialog.asksaveasfilename(
            title="プロジェクトを保存",
            defaultextension=".json",
            filetypes=[("WBSync Project", "*.json"), ("All files", "*.*")],
            initialfile=self.project_path.name,
            initialdir=str(self.project_path.parent),
        )
        if not path:
            return
        self.project_path = Path(path)
        self.save_project()
        self.refresh_all()

    def open_project(self) -> None:
        path = filedialog.askopenfilename(
            title="プロジェクトを開く",
            filetypes=[("WBSync Project", "*.json"), ("All files", "*.*")],
            initialdir=str(self.project_path.parent),
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.data = self.normalize_data(json.load(f))
            self.project_path = Path(path)
            self.selected_ticket_id_value = ""
            self.dirty = False
            self.refresh_all()
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_NAME, f"読み込めませんでした。\n{exc}")

    def new_project(self) -> None:
        if not messagebox.askyesno(APP_NAME, "現在の内容を保存して新規プロジェクトを作成しますか？"):
            return
        self.save_project(silent=True)
        self.data = {
            "version": DATA_VERSION,
            "meta": {
                "project_name": "新規プロジェクト",
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            },
            "tasks": [],
            "tickets": [],
        }
        self.project_path = default_data_path()
        self.selected_ticket_id_value = ""
        self.mark_changed()

    def export_all_csv(self) -> None:
        folder = filedialog.askdirectory(title="CSV出力先を選択")
        if not folder:
            return
        output_dir = Path(folder)
        stamp = now_stamp()
        paths = [
            self.write_tasks_csv(output_dir / f"wbs_{stamp}.csv"),
            self.write_tickets_csv(output_dir / f"tickets_{stamp}.csv"),
            self.write_gantt_csv(output_dir / f"gantt_{stamp}.csv"),
        ]
        messagebox.showinfo(APP_NAME, "CSVを出力しました。\n" + "\n".join(str(path) for path in paths))

    def export_gantt_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            title="ガントCSVを出力",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("All files", "*.*")],
            initialfile=f"gantt_{now_stamp()}.csv",
        )
        if not path:
            return
        written = self.write_gantt_csv(Path(path))
        messagebox.showinfo(APP_NAME, f"CSVを出力しました。\n{written}")

    def write_tasks_csv(self, path: Path) -> Path:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "parent_id", "code", "title", "owner", "status", "start", "end", "progress", "memo"])
            for task in self.ordered_tasks():
                writer.writerow(
                    [
                        task.get("id", ""),
                        task.get("parent_id", ""),
                        task.get("code", ""),
                        task.get("title", ""),
                        task.get("owner", ""),
                        task.get("status", ""),
                        task.get("start", ""),
                        task.get("end", ""),
                        task.get("progress", ""),
                        task.get("memo", ""),
                    ]
                )
        return path

    def write_tickets_csv(self, path: Path) -> Path:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "key", "title", "assignee", "status", "priority", "due", "task_code", "task_title", "memo"])
            for ticket in sorted(self.tickets(), key=lambda item: item.get("key", "")):
                task = self.task_by_id(ticket.get("task_id", ""))
                writer.writerow(
                    [
                        ticket.get("id", ""),
                        ticket.get("key", ""),
                        ticket.get("title", ""),
                        ticket.get("assignee", ""),
                        ticket.get("status", ""),
                        ticket.get("priority", ""),
                        ticket.get("due", ""),
                        task.get("code", "") if task else "",
                        task.get("title", "") if task else "",
                        ticket.get("memo", ""),
                    ]
                )
        return path

    def write_gantt_csv(self, path: Path) -> Path:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["code", "title", "owner", "status", "start", "end", "duration_days", "progress"])
            for task in self.ordered_tasks():
                start = safe_date(task.get("start"))
                end = safe_date(task.get("end"))
                duration = ""
                if start and end:
                    duration = abs((end - start).days) + 1
                writer.writerow(
                    [
                        task.get("code", ""),
                        task.get("title", ""),
                        task.get("owner", ""),
                        task.get("status", ""),
                        task.get("start", ""),
                        task.get("end", ""),
                        duration,
                        task.get("progress", ""),
                    ]
                )
        return path

    def on_close(self) -> None:
        if self.dirty:
            if not self.save_project(silent=True):
                if not messagebox.askyesno(APP_NAME, "保存に失敗しています。終了しますか？"):
                    return
        self.destroy()


def main() -> None:
    app = WBSyncApp()
    app.mainloop()


if __name__ == "__main__":
    main()
