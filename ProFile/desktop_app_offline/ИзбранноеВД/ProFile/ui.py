import os, json, tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import webbrowser, sys, ctypes, ctypes.wintypes

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_PATH = os.path.join(DATA_DIR, "users.json")
BOARDS_PATH = os.path.join(DATA_DIR, "boards.json")
ITEMS_PATH = os.path.join(DATA_DIR, "items.json")
TOKEN_FILE = os.path.join(BASE_DIR, ".user_token")
BG_IMG = os.path.join(BASE_DIR, "bg.png")

WM_DROPFILES = 0x0233

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_PATH):
        with open(USERS_PATH, "w", encoding="utf-8") as f:
            json.dump({"users": [], "_seq": {"users": 1}}, f, ensure_ascii=False, indent=2)
    if not os.path.exists(BOARDS_PATH):
        with open(BOARDS_PATH, "w", encoding="utf-8") as f:
            json.dump({"boards": [], "_seq": {"boards": 1}}, f, ensure_ascii=False, indent=2)
    if not os.path.exists(ITEMS_PATH):
        with open(ITEMS_PATH, "w", encoding="utf-8") as f:
            json.dump({"items": [], "_seq": {"items": 1}}, f, ensure_ascii=False, indent=2)

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(p, data):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_token():
    if os.path.exists(TOKEN_FILE):
        try:
            return open(TOKEN_FILE, "r", encoding="utf-8").read().strip()
        except:
            return ""
    return ""

def set_token(tok):
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(tok or "")

def bootstrap_user():
    ensure_dirs()
    users = load_json(USERS_PATH)
    if users["users"]:
        tok = users["users"][0]["token"]
        set_token(tok)
        return
    tok = "local_"+str(users["_seq"]["users"])
    uid = users["_seq"]["users"]
    users["_seq"]["users"] += 1
    users["users"].append({"id": uid, "username": "local_user", "password": "local_pw", "token": tok})
    save_json(USERS_PATH, users)
    boards = load_json(BOARDS_PATH)
    bid = boards["_seq"]["boards"]
    boards["_seq"]["boards"] += 1
    boards["boards"].append({"id": bid, "user_id": uid, "name": "Моя доска"})
    save_json(BOARDS_PATH, boards)
    set_token(tok)

def current_user():
    tok = get_token()
    users = load_json(USERS_PATH)["users"]
    for u in users:
        if u["token"] == tok:
            return u
    return None

def list_boards():
    u = current_user()
    if not u:
        return []
    bs = load_json(BOARDS_PATH)["boards"]
    return [b for b in bs if b["user_id"] == u["id"]]

def create_board(name):
    u = current_user()
    if not u:
        return None
    data = load_json(BOARDS_PATH)
    bid = data["_seq"]["boards"]
    data["_seq"]["boards"] += 1
    data["boards"].append({"id": bid, "user_id": u["id"], "name": name})
    save_json(BOARDS_PATH, data)
    return {"id": bid, "name": name}

def rename_board(bid, new_name):
    u = current_user()
    if not u:
        return False
    data = load_json(BOARDS_PATH)
    changed = False
    for b in data["boards"]:
        if b["id"] == bid and b["user_id"] == u["id"]:
            b["name"] = new_name
            changed = True
            break
    if changed:
        save_json(BOARDS_PATH, data)
    return changed

def delete_board(bid):
    u = current_user()
    if not u:
        return False
    boards = load_json(BOARDS_PATH)
    items = load_json(ITEMS_PATH)
    before_b = len(boards["boards"])
    boards["boards"] = [b for b in boards["boards"] if not (b["id"] == bid and b["user_id"] == u["id"])]
    if len(boards["boards"]) == before_b:
        return False
    items["items"] = [it for it in items["items"] if not (it["board_id"] == bid and it["user_id"] == u["id"])]
    save_json(BOARDS_PATH, boards)
    save_json(ITEMS_PATH, items)
    return True

def list_items(board_id):
    u = current_user()
    if not u:
        return []
    data = load_json(ITEMS_PATH)["items"]
    arr = [it for it in data if it["user_id"] == u["id"] and it["board_id"] == board_id]
    arr.sort(key=lambda x: x["id"], reverse=True)
    return arr

def add_item(board_id, title, typ="link", url=None, tags=None, path=None):
    u = current_user()
    if not u:
        return None
    data = load_json(ITEMS_PATH)
    iid = data["_seq"]["items"]
    data["_seq"]["items"] += 1
    item = {"id": iid, "user_id": u["id"], "board_id": board_id, "title": title, "type": typ, "url": url, "tags": tags, "path": path}
    data["items"].append(item)
    save_json(ITEMS_PATH, data)
    return item

def rename_item(item_id, new_title):
    u = current_user()
    if not u:
        return False
    data = load_json(ITEMS_PATH)
    ok = False
    for it in data["items"]:
        if it["id"] == item_id and it["user_id"] == u["id"]:
            it["title"] = new_title
            ok = True
            break
    if ok:
        save_json(ITEMS_PATH, data)
    return ok

def move_item(item_id, new_board_id):
    u = current_user()
    if not u:
        return False
    data = load_json(ITEMS_PATH)
    changed = False
    for it in data["items"]:
        if it["id"] == item_id and it["user_id"] == u["id"]:
            it["board_id"] = new_board_id
            changed = True
            break
    if changed:
        save_json(ITEMS_PATH, data)
    return changed

def delete_item(item_id):
    u = current_user()
    if not u:
        return False
    data = load_json(ITEMS_PATH)
    before = len(data["items"])
    data["items"] = [it for it in data["items"] if not (it["id"] == item_id and it["user_id"] == u["id"])]
    if len(data["items"]) != before:
        save_json(ITEMS_PATH, data)
        return True
    return False

class Loader:
    def __init__(self, root):
        self.root = root
        self.top = None
    def show(self, text="Загрузка..."):
        if self.top:
            return
        self.top = tk.Toplevel(self.root)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x, y = self.root.winfo_rootx(), self.root.winfo_rooty()
        self.top.geometry(f"{w}x{h}+{x}+{y}")
        try:
            self.top.attributes("-alpha", 0.15)
        except:
            pass
        veil = tk.Frame(self.top)
        veil.place(relx=0, rely=0, relwidth=1, relheight=1)
        card = tk.Frame(self.top, bd=0, highlightthickness=1, highlightbackground="#eaeaea")
        card.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(card, text=text, font=("Segoe UI", 11, "bold")).pack(padx=16, pady=(14, 6))
        pb = ttk.Progressbar(card, mode="indeterminate", length=220)
        pb.pack(padx=16, pady=(0, 14))
        pb.start(8)
        self.top.update()
    def hide(self):
        if self.top:
            self.top.destroy()
            self.top = None

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Избранное Pro — Local (Modern Files v2)")
        self.geometry("1150x720")
        self.minsize(980, 560)
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except:
            pass
        style.configure("Modern.TButton", padding=(10,6))
        root_bg = tk.Frame(self, bg="#eef1f5")
        root_bg.pack(fill="both", expand=True)
        try:
            self._bg_img = tk.PhotoImage(file=BG_IMG)
            bg_label = tk.Label(root_bg, image=self._bg_img, bg="#eef1f5")
            bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
            bg_label.lower()
        except Exception:
            pass
        top = tk.Frame(root_bg, pady=10, padx=16, bg="#eef1f5")
        top.pack(fill="x", side="top")
        tk.Label(top, text="Избранное", font=("Segoe UI", 20, "bold"), bg="#eef1f5").pack(side="left")
        tk.Label(top, text="локальное хранилище идей", font=("Segoe UI", 10), bg="#eef1f5", fg="#6b7280").pack(side="left", padx=(10, 0))
        self.search_var = tk.StringVar()
        ent = ttk.Entry(top, textvariable=self.search_var, width=46)
        ent.pack(side="right")
        ent.bind("<KeyRelease>", lambda e: self.refresh_items())
        center = tk.Frame(root_bg, padx=16, pady=16, bg="#eef1f5")
        center.pack(fill="both", expand=True)
        left = tk.Frame(center, bg="#ffffff", bd=0, highlightthickness=1, highlightbackground="#e5e7eb")
        right = tk.Frame(center, bg="#ffffff", bd=0, highlightthickness=1, highlightbackground="#e5e7eb")
        left.pack(side="left", fill="y", padx=(0, 12))
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))
        li = tk.Frame(left, bg="#ffffff")
        li.pack(fill="both", expand=True, padx=12, pady=12)
        hdr_l = tk.Frame(li, bg="#ffffff")
        hdr_l.pack(fill="x")
        tk.Label(hdr_l, text="Доски", font=("Segoe UI", 12, "bold"), bg="#ffffff").pack(side="left")
        lb_btns = tk.Frame(hdr_l, bg="#ffffff"); lb_btns.pack(side="right")
        ttk.Button(lb_btns, text="Создать", style="Modern.TButton", command=self.add_board).pack(side="left", padx=(0,6))
        ttk.Button(lb_btns, text="Переименовать", style="Modern.TButton", command=self.rename_board_action).pack(side="left", padx=(0,6))
        ttk.Button(lb_btns, text="Удалить", style="Modern.TButton", command=self.delete_board_action).pack(side="left")
        self.boards_list = tk.Listbox(li, height=22, exportselection=False, activestyle="dotbox")
        self.boards_list.pack(fill="both", expand=True, pady=(8,0))
        self.boards_list.bind("<<ListboxSelect>>", self.on_board_change)
        ri = tk.Frame(right, bg="#ffffff")
        ri.pack(fill="both", expand=True, padx=12, pady=12)
        hdr = tk.Frame(ri, bg="#ffffff")
        hdr.pack(fill="x")
        tk.Label(hdr, text="Элементы", font=("Segoe UI", 12, "bold"), bg="#ffffff").pack(side="left")
        btns = tk.Frame(hdr, bg="#ffffff"); btns.pack(side="right")
        ttk.Button(btns, text="Добавить ссылку", style="Modern.TButton", command=self.add_link).pack(side="left", padx=(0,6))
        ttk.Button(btns, text="Добавить файл", style="Modern.TButton", command=self.add_file).pack(side="left")
        cols = ("title", "type", "tags")
        self.items = ttk.Treeview(ri, columns=cols, show="headings", selectmode="browse")
        self.items.heading("title", text="Название")
        self.items.heading("type", text="Тип")
        self.items.heading("tags", text="Теги")
        self.items.column("title", width=680, anchor="w")
        self.items.column("type", width=120, anchor="w")
        self.items.column("tags", width=200, anchor="w")
        self.items.pack(side="left", fill="both", expand=True, pady=(8, 0))
        self.items.bind("<Double-1>", self.on_item_double)
        scr = ttk.Scrollbar(ri, orient="vertical", command=self.items.yview)
        self.items.configure(yscroll=scr.set)
        scr.pack(side="left", fill="y", pady=(8, 0))
        dnd_state = {"start_iid": None}
        def on_tv_button1(e):
            sel = self.items.selection()
            if sel:
                dnd_state["start_iid"] = int(sel[0])
        def on_tv_release(e):
            if dnd_state["start_iid"] is None:
                return
            x, y = self.winfo_pointerx(), self.winfo_pointery()
            target = self.winfo_containing(x, y)
            if target is self.boards_list or (hasattr(target, "master") and target.master is self.boards_list):
                try:
                    idx = self.boards_list.nearest(self.boards_list.winfo_pointery() - self.boards_list.winfo_rooty())
                    if idx is not None and idx >= 0:
                        b = self.boards[idx]
                        self.move_item_to_board(dnd_state["start_iid"], b["id"])
                except Exception:
                    pass
            dnd_state["start_iid"] = None
        self.items.bind("<Button-1>", on_tv_button1)
        self.items.bind("<ButtonRelease-1>", on_tv_release)
        bottom = tk.Frame(root_bg, padx=16, pady=12, bg="#eef1f5")
        bottom.pack(fill="x", side="bottom")
        ttk.Button(bottom, text="Переименовать", style="Modern.TButton", command=self.rename_item_action).pack(side="left", padx=6)
        ttk.Button(bottom, text="Удалить", style="Modern.TButton", command=self.delete_item).pack(side="left", padx=6)
        self.loader = Loader(self)
        self.after(100, self.startup)
        self._orig_wndproc = None
        self._setup_file_drop()

    def _setup_file_drop(self):
        if sys.platform != "win32":
            return
        hwnd = self.winfo_id()
        ctypes.windll.shell32.DragAcceptFiles(ctypes.wintypes.HWND(hwnd), True)
        WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.wintypes.HWND, ctypes.wintypes.UINT, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
        def py_wndproc(hWnd, msg, wParam, lParam):
            if msg == WM_DROPFILES:
                hdrop = wParam
                count = ctypes.windll.shell32.DragQueryFileW(ctypes.wintypes.HANDLE(hdrop), 0xFFFFFFFF, None, 0)
                paths = []
                for i in range(count):
                    length = ctypes.windll.shell32.DragQueryFileW(hdrop, i, None, 0) + 1
                    buf = ctypes.create_unicode_buffer(length)
                    ctypes.windll.shell32.DragQueryFileW(hdrop, i, buf, length)
                    paths.append(buf.value)
                ctypes.windll.shell32.DragFinish(hdrop)
                self._handle_files_dropped(paths)
                return 0
            return ctypes.windll.user32.CallWindowProcW(self._orig_wndproc, hWnd, msg, wParam, lParam)
        self._proc = WNDPROC(py_wndproc)
        self._orig_wndproc = ctypes.windll.user32.SetWindowLongPtrW(ctypes.wintypes.HWND(hwnd), -4, self._proc)

    def _handle_files_dropped(self, paths):
        b = self.selected_board()
        if not b:
            return
        cnt = 0
        for p in paths:
            if os.path.isfile(p):
                title = os.path.basename(p)
                add_item(b["id"], title, "file", path=p)
                cnt += 1
        if cnt > 0:
            self.refresh_items()

    def guarded(self, fn, text="Загрузка..."):
        def wrap(*a, **kw):
            self.after(0, lambda: self.loader.show(text))
            try:
                return fn(*a, **kw)
            finally:
                self.after(0, self.loader.hide)
        return wrap

    def startup(self):
        bootstrap_user()
        self.refresh_boards()

    def refresh_boards(self):
        arr = list_boards()
        self.boards = arr
        self.boards_list.delete(0, tk.END)
        for b in self.boards:
            self.boards_list.insert(tk.END, b["name"])
        if self.boards:
            self.boards_list.select_set(0)
            self.on_board_change(None)

    def selected_board(self):
        if not getattr(self, "boards", None):
            return None
        sel = self.boards_list.curselection()
        if not sel:
            return None
        return self.boards[sel[0]]

    def on_board_change(self, _):
        self.refresh_items()

    def refresh_items(self):
        self.items.delete(*self.items.get_children())
        b = self.selected_board()
        if not b:
            return
        arr = list_items(b["id"])
        q = self.search_var.get().strip().lower()
        for it in arr:
            if q and q not in (it["title"] + " " + (it.get("tags") or "") + " " + (it.get("url") or "") + " " + (it.get("path") or "")).lower():
                continue
            self.items.insert("", tk.END, iid=str(it["id"]), values=(it["title"], it["type"], it.get("tags") or ""))

    def add_board(self):
        name = simpledialog.askstring("Новая доска", "Название:")
        if not name:
            return
        @self.guarded
        def go():
            create_board(name)
            self.refresh_boards()
        go()

    def rename_board_action(self):
        b = self.selected_board()
        if not b:
            return
        new_name = simpledialog.askstring("Переименовать доску", "Новое имя:", initialvalue=b["name"])
        if not new_name:
            return
        @self.guarded
        def go():
            ok = rename_board(b["id"], new_name)
            if ok:
                self.refresh_boards()
            else:
                messagebox.showerror("Ошибка", "Не удалось переименовать")
        go()

    def delete_board_action(self):
        b = self.selected_board()
        if not b:
            return
        if not messagebox.askyesno("Удалить доску", "Удалить доску и её элементы?"):
            return
        @self.guarded
        def go():
            ok = delete_board(b["id"])
            if ok:
                self.refresh_boards()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить доску")
        go()

    def selected_item_id(self):
        sel = self.items.selection()
        if not sel:
            return None
        return int(sel[0])

    def rename_item_action(self):
        iid = self.selected_item_id()
        if not iid:
            return
        title = self.items.item(self.items.selection()[0], "values")[0]
        new_title = simpledialog.askstring("Переименовать", "Новое название:", initialvalue=title)
        if not new_title:
            return
        @self.guarded
        def go():
            ok = rename_item(iid, new_title)
            if ok:
                self.refresh_items()
            else:
                messagebox.showerror("Ошибка", "Не удалось переименовать")
        go()

    def add_link(self):
        b = self.selected_board()
        if not b:
            return
        url = simpledialog.askstring("Ссылка", "Вставьте URL:")
        if not url:
            return
        title = simpledialog.askstring("Название", "Название (можно #теги):", initialvalue=url[:50]) or url[:50]
        @self.guarded
        def go():
            add_item(b["id"], title, "link", url=url)
            self.refresh_items()
        go()

    def add_file(self):
        b = self.selected_board()
        if not b:
            return
        paths = filedialog.askopenfilenames(title="Выберите файлы")
        if not paths:
            return
        @self.guarded
        def go():
            for p in paths:
                add_item(b["id"], os.path.basename(p), "file", path=p)
            self.refresh_items()
        go()

    def on_item_double(self, e):
        iid = self.selected_item_id()
        if not iid:
            return
        b = self.selected_board()
        if not b:
            return
        arr = list_items(b["id"])
        it = next((x for x in arr if x["id"] == iid), None)
        if not it:
            return
        if it["type"] == "link" and it.get("url"):
            webbrowser.open(it["url"])
        elif it["type"] == "file" and it.get("path"):
            p = it["path"]
            if os.path.exists(p):
                try:
                    os.startfile(p)
                except Exception as e:
                    messagebox.showerror("Открыть", str(e))
            else:
                messagebox.showwarning("Открыть", "Файл не найден на диске")

    def move_item_to_board(self, item_id, board_id):
        @self.guarded
        def go():
            ok = move_item(item_id, board_id)
            if ok:
                self.refresh_items()
            else:
                messagebox.showerror("Ошибка", "Не удалось перенести")
        go()

    def delete_item(self):
        iid = self.selected_item_id()
        if not iid:
            return
        if not messagebox.askyesno("Удаление", "Удалить выбранный элемент?"):
            return
        @self.guarded
        def go():
            ok = delete_item(iid)
            if ok:
                self.refresh_items()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить")
        go()

def run_ui():
    App().mainloop()
