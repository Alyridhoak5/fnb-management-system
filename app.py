import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3, csv, os, math, random
from datetime import datetime, date, timedelta

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "database", "fnb_v7.db")
EXPORT_DIR = os.path.join(APP_DIR, "exports")
RECEIPT_DIR = os.path.join(APP_DIR, "receipts")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(RECEIPT_DIR, exist_ok=True)

BG = "#F4F7FB"
CARD = "#FFFFFF"
NAV = "#09111F"
NAV2 = "#14233A"
TEXT = "#14213D"
MUTED = "#718096"
ACCENT = "#2563EB"
ACCENT2 = "#0EA5E9"
GREEN = "#16A34A"
RED = "#DC2626"
ORANGE = "#F59E0B"
PURPLE = "#7C3AED"
LINE = "#D7E0EC"
SOFT = "#EAF1FF"
DARK_LINE = "#26364D"


def rupiah(n):
    try:
        n = float(n)
    except Exception:
        n = 0
    return "Rp {:,.0f}".format(n).replace(",", ".")


def num(v):
    try:
        return float(v)
    except Exception:
        return 0.0


def fmt_qty(v):
    x = num(v)
    return f"{x:g}"


def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init_db():
    c = db()
    cur = c.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'owner'
    );
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL DEFAULT 0,
        status TEXT DEFAULT 'Aktif'
    );
    CREATE TABLE IF NOT EXISTS ingredients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        unit TEXT NOT NULL,
        stock REAL NOT NULL DEFAULT 0,
        min_stock REAL NOT NULL DEFAULT 0,
        cost REAL NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS bom(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        ingredient_id INTEGER NOT NULL,
        qty REAL NOT NULL,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
        FOREIGN KEY(ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trx_no TEXT,
        created_at TEXT,
        total REAL,
        discount REAL DEFAULT 0,
        payment REAL DEFAULT 0,
        change_amount REAL DEFAULT 0,
        payment_method TEXT DEFAULT 'Cash'
    );
    CREATE TABLE IF NOT EXISTS transaction_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER,
        product_id INTEGER,
        qty INTEGER,
        price REAL,
        subtotal REAL,
        FOREIGN KEY(transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
        FOREIGN KEY(product_id) REFERENCES products(id)
    );
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        amount REAL,
        category TEXT,
        created_at TEXT
    );
    """)
    if not cur.execute("SELECT 1 FROM users LIMIT 1").fetchone():
        cur.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)", ("admin", "admin", "owner"))
    if not cur.execute("SELECT 1 FROM products LIMIT 1").fetchone():
        products = [
            ("Nasi Goreng", "Makanan", 15000), ("Ayam Geprek", "Makanan", 18000),
            ("Mie Goreng", "Makanan", 14000), ("Es Teh", "Minuman", 5000),
            ("Kopi Susu", "Minuman", 12000), ("French Fries", "Snack", 10000),
            ("Chicken Rice Bowl", "Makanan", 22000), ("Matcha Latte", "Minuman", 15000),
            ("Pisang Coklat", "Snack", 9000), ("Lemon Tea", "Minuman", 7000)
        ]
        cur.executemany("INSERT INTO products(name,category,price) VALUES(?,?,?)", products)
    if not cur.execute("SELECT 1 FROM ingredients LIMIT 1").fetchone():
        ingredients = [
            ("Ayam", "pcs", 50, 10, 9000), ("Beras", "kg", 12, 3, 15000),
            ("Mie", "pcs", 60, 10, 3000), ("Minyak", "liter", 10, 2, 18000),
            ("Telur", "pcs", 48, 12, 2500), ("Gula", "kg", 5, 1, 16000),
            ("Teh", "gram", 1000, 200, 120), ("Kopi", "gram", 1000, 200, 180),
            ("Susu", "liter", 10, 2, 18000), ("Kentang", "kg", 8, 2, 14000),
            ("Matcha", "gram", 500, 100, 500), ("Cup", "pcs", 100, 20, 700),
            ("Pisang", "pcs", 40, 8, 2500), ("Coklat", "gram", 1000, 200, 90),
            ("Lemon", "pcs", 30, 6, 2500)
        ]
        cur.executemany("INSERT INTO ingredients(name,unit,stock,min_stock,cost) VALUES(?,?,?,?,?)", ingredients)
    if not cur.execute("SELECT 1 FROM bom LIMIT 1").fetchone():
        p = {r["name"]: r["id"] for r in cur.execute("SELECT id,name FROM products")}
        i = {r["name"]: r["id"] for r in cur.execute("SELECT id,name FROM ingredients")}
        rows = [
            (p["Nasi Goreng"], i["Beras"], .15), (p["Nasi Goreng"], i["Telur"], 1), (p["Nasi Goreng"], i["Minyak"], .02),
            (p["Ayam Geprek"], i["Ayam"], 1), (p["Ayam Geprek"], i["Beras"], .15), (p["Ayam Geprek"], i["Minyak"], .03),
            (p["Mie Goreng"], i["Mie"], 1), (p["Mie Goreng"], i["Telur"], 1), (p["Mie Goreng"], i["Minyak"], .02),
            (p["Es Teh"], i["Teh"], 8), (p["Es Teh"], i["Gula"], .015), (p["Es Teh"], i["Cup"], 1),
            (p["Kopi Susu"], i["Kopi"], 15), (p["Kopi Susu"], i["Susu"], .12), (p["Kopi Susu"], i["Gula"], .01), (p["Kopi Susu"], i["Cup"], 1),
            (p["French Fries"], i["Kentang"], .15), (p["French Fries"], i["Minyak"], .03),
            (p["Chicken Rice Bowl"], i["Ayam"], 1), (p["Chicken Rice Bowl"], i["Beras"], .15), (p["Chicken Rice Bowl"], i["Cup"], 1),
            (p["Matcha Latte"], i["Matcha"], 8), (p["Matcha Latte"], i["Susu"], .15), (p["Matcha Latte"], i["Gula"], .01), (p["Matcha Latte"], i["Cup"], 1),
            (p["Pisang Coklat"], i["Pisang"], 2), (p["Pisang Coklat"], i["Coklat"], 20), (p["Pisang Coklat"], i["Minyak"], .02),
            (p["Lemon Tea"], i["Teh"], 6), (p["Lemon Tea"], i["Lemon"], .25), (p["Lemon Tea"], i["Gula"], .01), (p["Lemon Tea"], i["Cup"], 1)
        ]
        cur.executemany("INSERT INTO bom(product_id,ingredient_id,qty) VALUES(?,?,?)", rows)
    c.commit(); c.close()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("F&B Management System V7 PRO")
        self.geometry("1320x800")
        self.minsize(1120, 700)
        self.configure(bg=BG)
        self.user = None
        self.cart = []
        self.current_nav = None
        self.anim_ids = []
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.style()
        self.show_login()

    def style(self):
        s = ttk.Style(self)
        try: s.theme_use("clam")
        except Exception: pass
        s.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
                    rowheight=36, font=("Segoe UI", 10), borderwidth=0)
        s.configure("Treeview.Heading", background="#EAF0F7", foreground=TEXT,
                    font=("Segoe UI", 10, "bold"), padding=9)
        s.map("Treeview", background=[("selected", "#DCE8FF")], foreground=[("selected", TEXT)])
        s.configure("TEntry", padding=8)
        s.configure("TCombobox", padding=7)
        s.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8)

    def clear(self):
        for aid in self.anim_ids:
            try: self.after_cancel(aid)
            except Exception: pass
        self.anim_ids.clear()
        for w in self.winfo_children(): w.destroy()

    def show_login(self):
        self.user = None
        self.clear(); self.style()
        bg = tk.Canvas(self, bg=BG, highlightthickness=0)
        bg.pack(fill="both", expand=True)
        self.login_canvas = bg
        # subtle animated dots
        dots = []
        for _ in range(22):
            x=random.randint(20,1250); y=random.randint(20,740); r=random.randint(2,5)
            dots.append([x,y,r,random.choice([-1,1])])
            bg.create_oval(x-r,y-r,x+r,y+r,fill="#DCE8FF",outline="")
        def drift():
            if not bg.winfo_exists(): return
            for j,d in enumerate(dots):
                d[1] += d[3]*.35
                if d[1] < 0 or d[1] > max(10,bg.winfo_height()): d[3]*=-1
                x,y,r,_=d; bg.coords(j+1,x-r,y-r,x+r,y+r)
            self.anim_ids.append(self.after(40,drift))
        drift()
        box=tk.Frame(bg,bg=CARD,highlightbackground=LINE,highlightthickness=1)
        box.place(relx=.5,rely=.5,anchor="center",width=470,height=540)
        tk.Label(box,text="F&B",bg=CARD,fg=ACCENT,font=("Segoe UI",40,"bold")).pack(pady=(42,0))
        tk.Label(box,text="MANAGEMENT SYSTEM",bg=CARD,fg=TEXT,font=("Segoe UI",12,"bold")).pack()
        tk.Frame(box,bg=ACCENT,height=3,width=80).pack(pady=17)
        tk.Label(box,text="Selamat datang",bg=CARD,fg=TEXT,font=("Segoe UI",20,"bold")).pack()
        tk.Label(box,text="Masuk untuk mengelola operasional F&B.",bg=CARD,fg=MUTED,font=("Segoe UI",10)).pack(pady=(3,22))
        tk.Label(box,text="Username",bg=CARD,fg=MUTED,font=("Segoe UI",10,"bold")).pack(anchor="w",padx=58)
        u=ttk.Entry(box); u.pack(fill="x",padx=58,pady=(5,14),ipady=2)
        tk.Label(box,text="Password",bg=CARD,fg=MUTED,font=("Segoe UI",10,"bold")).pack(anchor="w",padx=58)
        p=ttk.Entry(box,show="•"); p.pack(fill="x",padx=58,pady=(5,20),ipady=2)
        def login(event=None):
            c=db(); row=c.execute("SELECT * FROM users WHERE username=? AND password=?",(u.get().strip(),p.get())).fetchone(); c.close()
            if row:
                self.user=row; self.build_shell()
            else: messagebox.showerror("Login gagal","Username atau password salah.")
        ttk.Button(box,text="MASUK KE DASHBOARD",command=login).pack(fill="x",padx=58,pady=4)
        ttk.Button(box,text="Buat akun baru",command=self.register).pack(pady=12)
        tk.Label(box,text="Akun demo: admin / admin",bg=CARD,fg=MUTED,font=("Segoe UI",9)).pack(side="bottom",pady=18)
        u.focus(); p.bind("<Return>",login)

    def register(self):
        win=tk.Toplevel(self); win.title("Buat Akun Baru"); win.geometry("420x340"); win.configure(bg=CARD); win.resizable(False,False)
        tk.Label(win,text="Buat akun",bg=CARD,fg=TEXT,font=("Segoe UI",20,"bold")).pack(pady=25)
        f=tk.Frame(win,bg=CARD); f.pack(fill="x",padx=45)
        tk.Label(f,text="Username",bg=CARD,fg=MUTED).pack(anchor="w"); u=ttk.Entry(f); u.pack(fill="x",pady=5)
        tk.Label(f,text="Password",bg=CARD,fg=MUTED).pack(anchor="w"); p=ttk.Entry(f,show="•"); p.pack(fill="x",pady=5)
        tk.Label(f,text="Konfirmasi password",bg=CARD,fg=MUTED).pack(anchor="w"); q=ttk.Entry(f,show="•"); q.pack(fill="x",pady=5)
        def save():
            un=u.get().strip()
            if not un or not p.get(): return messagebox.showwarning("Data belum lengkap","Isi username dan password.",parent=win)
            if p.get()!=q.get(): return messagebox.showwarning("Password","Konfirmasi password tidak sama.",parent=win)
            try:
                c=db(); c.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",(un,p.get(),"owner")); c.commit(); c.close()
                messagebox.showinfo("Berhasil","Akun berhasil dibuat.",parent=win); win.destroy()
            except sqlite3.IntegrityError: messagebox.showerror("Gagal","Username sudah digunakan.",parent=win)
        ttk.Button(win,text="SIMPAN AKUN",command=save).pack(pady=22)

    def build_shell(self):
        self.clear()
        self.nav=tk.Frame(self,bg=NAV,width=245); self.nav.pack(side="left",fill="y"); self.nav.pack_propagate(False)
        self.main=tk.Frame(self,bg=BG); self.main.pack(side="right",fill="both",expand=True)
        self.nav_header()
        self.nav_btn("Dashboard",self.show_dashboard,"D")
        self.nav_btn("Kasir / POS",self.show_pos,"P")
        self.sep("OPERASIONAL")
        self.nav_btn("Menu Produk",self.show_products,"M")
        self.nav_btn("Bahan & Stok",self.show_stock,"S")
        self.nav_btn("Recipe / BOM",self.show_bom,"R")
        self.nav_btn("Monitoring Stok",self.show_monitor,"O")
        self.sep("BISNIS")
        self.nav_btn("Keuangan",self.show_finance,"K")
        self.nav_btn("Laporan & Analitik",self.show_reports,"L")
        tk.Frame(self.nav,bg=NAV).pack(fill="both",expand=True)
        tk.Button(self.nav,text="Logout",command=self.show_login,bg="#4A1D2A",fg="white",relief="flat",
                  activebackground="#672638",font=("Segoe UI",10,"bold"),anchor="w",padx=18).pack(fill="x",padx=14,pady=14,ipady=10)
        self.show_dashboard()

    def nav_header(self):
        tk.Label(self.nav,text="F&B",bg=NAV,fg="#60A5FA",font=("Segoe UI",30,"bold")).pack(anchor="w",padx=20,pady=(25,0))
        tk.Label(self.nav,text="MANAGEMENT SYSTEM • V7 PRO",bg=NAV,fg="white",font=("Segoe UI",8,"bold")).pack(anchor="w",padx=21,pady=(0,18))
        tk.Frame(self.nav,bg=DARK_LINE,height=1).pack(fill="x",padx=18)
        tk.Label(self.nav,text=f"{self.user['username'].upper()} • {self.user['role'].upper()}",bg=NAV,fg="#A9B8CD",
                 font=("Segoe UI",9,"bold")).pack(anchor="w",padx=20,pady=17)

    def sep(self,t):
        tk.Label(self.nav,text=t,bg=NAV,fg="#64748B",font=("Segoe UI",8,"bold")).pack(anchor="w",padx=20,pady=(17,6))

    def nav_btn(self,t,cmd,letter):
        b=tk.Button(self.nav,text=f"  {letter}   {t}",command=cmd,bg=NAV,fg="#DDE7F5",activebackground=NAV2,activeforeground="white",
                    relief="flat",anchor="w",padx=10,font=("Segoe UI",10))
        b.pack(fill="x",padx=8,pady=2,ipady=7)

    def page_title(self,title,sub=""):
        top=tk.Frame(self.main,bg=BG); top.pack(fill="x",padx=30,pady=(24,8))
        tk.Label(top,text=title,bg=BG,fg=TEXT,font=("Segoe UI",24,"bold")).pack(anchor="w")
        if sub: tk.Label(top,text=sub,bg=BG,fg=MUTED,font=("Segoe UI",10)).pack(anchor="w",pady=(3,0))
        tk.Frame(self.main,bg=ACCENT,height=2).pack(fill="x",padx=30,pady=(5,18))

    def card(self,parent,**kw):
        return tk.Frame(parent,bg=CARD,highlightbackground=LINE,highlightthickness=1,**kw)

    def stat(self,parent,label,value,accent,icon):
        c=self.card(parent); c.pack(side="left",fill="both",expand=True,padx=6)
        tk.Label(c,text=icon,bg=CARD,fg=accent,font=("Segoe UI",20,"bold")).pack(anchor="w",padx=18,pady=(13,0))
        tk.Label(c,text=label,bg=CARD,fg=MUTED,font=("Segoe UI",8,"bold")).pack(anchor="w",padx=18,pady=(3,0))
        tk.Label(c,text=value,bg=CARD,fg=TEXT,font=("Segoe UI",17,"bold")).pack(anchor="w",padx=18,pady=(2,14))

    def food_animation(self,parent):
        box=self.card(parent); box.pack(fill="x",padx=30,pady=(0,15))
        canvas=tk.Canvas(box,height=88,bg="#0E1A2E",highlightthickness=0)
        canvas.pack(fill="x",padx=1,pady=1)
        canvas.create_text(24,44,text="LIVE KITCHEN",anchor="w",fill="#93C5FD",font=("Segoe UI",9,"bold"))
        items=[]
        symbols=["FOOD","DRINK","SNACK","ORDER","FOOD","DRINK"]
        for i,s in enumerate(symbols):
            x=190+i*150; y=random.randint(18,68)
            item=canvas.create_text(x,y,text=s,fill=random.choice(["#60A5FA","#22C55E","#F59E0B","#A78BFA"]),font=("Segoe UI",10,"bold"))
            items.append([item,x,y,random.choice([-1,1]),random.uniform(.4,1.0)])
        def animate():
            if not canvas.winfo_exists(): return
            w=max(canvas.winfo_width(),700)
            for it in items:
                it[1]+=it[3]*it[4]
                if it[1] < 120: it[1]=w-20
                if it[1] > w-10: it[1]=120
                canvas.coords(it[0],it[1],it[2])
            self.anim_ids.append(self.after(35,animate))
        animate()

    def show_dashboard(self):
        for w in self.main.winfo_children(): w.destroy()
        self.page_title("Dashboard","Ringkasan operasional dan performa bisnis hari ini.")
        c=db(); today=date.today().isoformat()
        omzet=c.execute("SELECT COALESCE(SUM(total),0) v FROM transactions WHERE date(created_at)=?",(today,)).fetchone()["v"]
        trx=c.execute("SELECT COUNT(*) v FROM transactions WHERE date(created_at)=?",(today,)).fetchone()["v"]
        exp=c.execute("SELECT COALESCE(SUM(amount),0) v FROM expenses WHERE date(created_at)=?",(today,)).fetchone()["v"]
        low=c.execute("SELECT COUNT(*) v FROM ingredients WHERE stock<=min_stock").fetchone()["v"]
        top=c.execute("""SELECT p.name,SUM(ti.qty) qty FROM transaction_items ti JOIN products p ON p.id=ti.product_id
                        JOIN transactions t ON t.id=ti.transaction_id WHERE date(t.created_at)=? GROUP BY p.id ORDER BY qty DESC LIMIT 5""",(today,)).fetchall(); c.close()
        row=tk.Frame(self.main,bg=BG); row.pack(fill="x",padx=24)
        self.stat(row,"OMZET HARI INI",rupiah(omzet),ACCENT,"RP")
        self.stat(row,"TRANSAKSI",str(trx),ACCENT2,"TRX")
        self.stat(row,"PENGELUARAN",rupiah(exp),ORANGE,"OUT")
        self.stat(row,"STOK MENIPIS",str(low),RED,"LOW")
        self.food_animation(self.main)
        body=tk.Frame(self.main,bg=BG); body.pack(fill="both",expand=True,padx=30,pady=2)
        left=self.card(body); left.pack(side="left",fill="both",expand=True,padx=(0,8))
        tk.Label(left,text="Performa Penjualan",bg=CARD,fg=TEXT,font=("Segoe UI",14,"bold")).pack(anchor="w",padx=18,pady=(14,0))
        tk.Label(left,text="Omzet 7 hari terakhir",bg=CARD,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",padx=18)
        canvas=tk.Canvas(left,bg=CARD,highlightthickness=0); canvas.pack(fill="both",expand=True,padx=12,pady=10)
        self.draw_chart(canvas)
        right=self.card(body,width=330); right.pack(side="right",fill="y",padx=(8,0)); right.pack_propagate(False)
        tk.Label(right,text="Menu Terlaris Hari Ini",bg=CARD,fg=TEXT,font=("Segoe UI",14,"bold")).pack(anchor="w",padx=18,pady=(14,8))
        if top:
            for idx,r in enumerate(top,1):
                rr=tk.Frame(right,bg=CARD); rr.pack(fill="x",padx=16,pady=7)
                tk.Label(rr,text=f"{idx:02d}",bg=SOFT,fg=ACCENT,font=("Segoe UI",9,"bold"),width=3).pack(side="left")
                tk.Label(rr,text=r["name"],bg=CARD,fg=TEXT,font=("Segoe UI",10,"bold")).pack(side="left",padx=9)
                tk.Label(rr,text=f"{r['qty']}x",bg=CARD,fg=MUTED).pack(side="right")
        else:
            tk.Label(right,text="Belum ada transaksi hari ini.",bg=CARD,fg=MUTED).pack(pady=25)
        tk.Frame(right,bg=LINE,height=1).pack(fill="x",padx=16,pady=14)
        pulse=tk.Label(right,text="●  SYSTEM ONLINE",bg=CARD,fg=GREEN,font=("Segoe UI",10,"bold")); pulse.pack(anchor="w",padx=18,pady=7)
        def pulse_anim():
            if not pulse.winfo_exists(): return
            pulse.config(fg=ACCENT if pulse.cget("fg")==GREEN else GREEN)
            self.anim_ids.append(self.after(800,pulse_anim))
        pulse_anim()

    def draw_chart(self,canvas):
        def redraw(e=None):
            if not canvas.winfo_exists(): return
            canvas.delete("all"); w=max(canvas.winfo_width(),420); h=max(canvas.winfo_height(),230)
            pad=45; bottom=h-35; top=25
            c=db(); rows=c.execute("SELECT date(created_at) d,COALESCE(SUM(total),0) total FROM transactions WHERE date(created_at)>=date('now','-6 day') GROUP BY date(created_at) ORDER BY d").fetchall(); c.close()
            vals={r["d"]:r["total"] for r in rows}; dates=[(date.today()-timedelta(days=i)).isoformat() for i in range(6,-1,-1)]
            nums=[vals.get(d,0) for d in dates]; mx=max(nums+[1])
            for j in range(4):
                y=bottom-(bottom-top)*j/3; canvas.create_line(pad,y,w-20,y,fill=LINE)
            pts=[]
            for i,v in enumerate(nums):
                x=pad+i*(w-pad-25)/6; y=bottom-(bottom-top)*(v/mx); pts.append((x,y))
                canvas.create_oval(x-4,y-4,x+4,y+4,fill=ACCENT,outline="")
                canvas.create_text(x,bottom+16,text=dates[i][5:],fill=MUTED,font=("Segoe UI",8))
            if len(pts)>1: canvas.create_line(*[p for xy in pts for p in xy],fill=ACCENT,width=3,smooth=True)
            canvas.create_text(pad,top-8,text=rupiah(mx),anchor="w",fill=MUTED,font=("Segoe UI",8))
        canvas.bind("<Configure>",redraw); self.anim_ids.append(self.after(100,redraw))

    def show_pos(self):
        self.cart=[]
        for w in self.main.winfo_children(): w.destroy()
        self.page_title("Kasir / POS","Pilih menu di kiri. Klik tombol Tambah untuk memasukkan ke keranjang.")
        top=tk.Frame(self.main,bg=BG); top.pack(fill="x",padx=30,pady=(0,12))
        search=ttk.Entry(top); search.pack(side="left",fill="x",expand=True)
        cat=ttk.Combobox(top,values=["Semua","Makanan","Minuman","Snack"],state="readonly",width=16); cat.set("Semua"); cat.pack(side="left",padx=8)
        wrap=tk.Frame(self.main,bg=BG); wrap.pack(fill="both",expand=True,padx=30)
        left=self.card(wrap); left.pack(side="left",fill="both",expand=True,padx=(0,8))
        right=self.card(wrap,width=390); right.pack(side="right",fill="y",padx=(8,0)); right.pack_propagate(False)
        tk.Label(left,text="MENU HARI INI",bg=CARD,fg=TEXT,font=("Segoe UI",13,"bold")).pack(anchor="w",padx=16,pady=(12,5))
        menu_canvas=tk.Canvas(left,bg=CARD,highlightthickness=0); menu_canvas.pack(fill="both",expand=True,padx=8,pady=5)
        menu_inner=tk.Frame(menu_canvas,bg=CARD); win=menu_canvas.create_window((0,0),window=menu_inner,anchor="nw")
        def resize_inner(e): menu_canvas.itemconfigure(win,width=max(e.width,600))
        menu_canvas.bind("<Configure>",resize_inner)
        cart_tree=self.tree(right,[("Produk",160),("Qty",55),("Subtotal",135)])
        tk.Label(right,text="KERANJANG",bg=CARD,fg=TEXT,font=("Segoe UI",14,"bold")).pack(anchor="w",padx=18,pady=(14,4))
        # Tree helper already fills the cart area.
        total_lbl=tk.Label(right,text="Rp 0",bg=CARD,fg=ACCENT,font=("Segoe UI",23,"bold")); total_lbl.pack(anchor="e",padx=18,pady=6)
        pay=tk.Frame(right,bg=CARD); pay.pack(fill="x",padx=18)
        tk.Label(pay,text="Bayar",bg=CARD,fg=MUTED).grid(row=0,column=0,sticky="w",pady=5)
        payent=ttk.Entry(pay); payent.grid(row=0,column=1,sticky="ew",padx=8,pady=5)
        tk.Label(pay,text="Metode",bg=CARD,fg=MUTED).grid(row=1,column=0,sticky="w",pady=5)
        method=ttk.Combobox(pay,values=["Cash","QRIS","Debit","Transfer"],state="readonly"); method.set("Cash"); method.grid(row=1,column=1,sticky="ew",padx=8,pady=5)
        pay.columnconfigure(1,weight=1)
        ttk.Button(right,text="PROSES PEMBAYARAN",command=lambda:self.checkout(cart_tree,total_lbl,payent,method)).pack(fill="x",padx=18,pady=(7,15))
        def load_menu():
            for w in menu_inner.winfo_children(): w.destroy()
            q=search.get().strip().lower(); selected=cat.get()
            c=db(); rows=c.execute("SELECT id,name,category,price FROM products WHERE status='Aktif' ORDER BY category,name").fetchall(); c.close()
            rows=[r for r in rows if (not q or q in r["name"].lower()) and (selected=="Semua" or r["category"]==selected)]
            for idx,r in enumerate(rows):
                rr=idx//2; cc=idx%2
                card=self.card(menu_inner); card.grid(row=rr,column=cc,sticky="nsew",padx=6,pady=6)
                badge=tk.Label(card,text=r["category"].upper(),bg=SOFT,fg=ACCENT,font=("Segoe UI",8,"bold")); badge.pack(anchor="w",padx=12,pady=(10,2))
                tk.Label(card,text=r["name"],bg=CARD,fg=TEXT,font=("Segoe UI",12,"bold")).pack(anchor="w",padx=12,pady=3)
                tk.Label(card,text=rupiah(r["price"]),bg=CARD,fg=GREEN,font=("Segoe UI",11,"bold")).pack(anchor="w",padx=12)
                ttk.Button(card,text="＋ Tambah",command=lambda row=r:self.add_to_cart(row,cart_tree,total_lbl)).pack(anchor="e",padx=10,pady=9)
            menu_inner.update_idletasks(); menu_canvas.configure(scrollregion=menu_canvas.bbox("all"))
        search.bind("<KeyRelease>",lambda e:load_menu()); cat.bind("<<ComboboxSelected>>",lambda e:load_menu()); load_menu()

    def add_to_cart(self,row,tree,total_lbl):
        found=next((x for x in self.cart if x["id"]==row["id"]),None)
        if found: found["qty"]+=1
        else: self.cart.append({"id":row["id"],"name":row["name"],"price":row["price"],"qty":1})
        self.refresh_cart(tree,total_lbl)

    def refresh_cart(self,tree,total_lbl):
        for x in tree.get_children(): tree.delete(x)
        total=0
        for i,x in enumerate(self.cart):
            sub=x["price"]*x["qty"]; total+=sub; tree.insert("","end",iid=str(i),values=(x["name"],x["qty"],rupiah(sub)))
        total_lbl.config(text=rupiah(total))

    def checkout(self,tree,total_lbl,payent,method):
        if not self.cart: return messagebox.showwarning("Keranjang","Belum ada menu yang dipilih.")
        total=sum(x["price"]*x["qty"] for x in self.cart)
        try: pay=float(payent.get())
        except Exception: return messagebox.showwarning("Pembayaran","Masukkan nominal pembayaran.")
        if pay<total: return messagebox.showwarning("Pembayaran",f"Uang kurang {rupiah(total-pay)}")
        c=db()
        for item in self.cart:
            rows=c.execute("SELECT b.qty,i.name,i.unit,i.stock FROM bom b JOIN ingredients i ON i.id=b.ingredient_id WHERE b.product_id=?",(item["id"],)).fetchall()
            if not rows:
                c.close(); return messagebox.showerror("Recipe belum ada",f"{item['name']} belum memiliki Recipe/BOM.")
            for r in rows:
                need=r["qty"]*item["qty"]
                if r["stock"]<need:
                    c.close(); return messagebox.showerror("Stok tidak cukup",f"{r['name']} tersisa {fmt_qty(r['stock'])} {r['unit']}.")
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"); no="TRX-"+datetime.now().strftime("%Y%m%d%H%M%S")
        cur=c.cursor(); cur.execute("INSERT INTO transactions(trx_no,created_at,total,payment,change_amount,payment_method) VALUES(?,?,?,?,?,?)",(no,now,total,pay,pay-total,method.get())); tid=cur.lastrowid
        for item in self.cart:
            cur.execute("INSERT INTO transaction_items(transaction_id,product_id,qty,price,subtotal) VALUES(?,?,?,?,?)",(tid,item["id"],item["qty"],item["price"],item["price"]*item["qty"]))
            for r in c.execute("SELECT b.qty,i.id FROM bom b JOIN ingredients i ON i.id=b.ingredient_id WHERE b.product_id=?",(item["id"],)):
                cur.execute("UPDATE ingredients SET stock=stock-? WHERE id=?",(r["qty"]*item["qty"],r["id"]))
        c.commit(); c.close()
        change=pay-total; self.save_receipt(no,now,self.cart,total,pay,change,method.get())
        self.cart=[]; self.refresh_cart(tree,total_lbl); payent.delete(0,"end")
        messagebox.showinfo("Transaksi berhasil",f"{no}\nTotal {rupiah(total)}\nKembalian {rupiah(change)}")

    def save_receipt(self,no,now,items,total,pay,change,method):
        path=os.path.join(RECEIPT_DIR,no+".txt")
        with open(path,"w",encoding="utf-8") as f:
            f.write("F&B MANAGEMENT SYSTEM V7 PRO\n"+"="*42+"\n"+no+"\n"+now+"\n"+"-"*42+"\n")
            for x in items: f.write(f"{x['name'][:24]:24} {x['qty']:>2}  {rupiah(x['price']*x['qty']):>14}\n")
            f.write("-"*42+"\nTOTAL   "+rupiah(total)+"\nBAYAR   "+rupiah(pay)+"\nKEMBALI "+rupiah(change)+"\nMETODE  "+method+"\n")

    def tree(self,parent,cols):
        wrap=tk.Frame(parent,bg=CARD); wrap.pack(fill="both",expand=True,padx=0,pady=0); wrap.pack_propagate(False)
        t=ttk.Treeview(wrap,columns=[x[0] for x in cols],show="headings")
        for name,width in cols:
            t.heading(name,text=name); t.column(name,width=width,anchor="w")
        sy=ttk.Scrollbar(wrap,orient="vertical",command=t.yview); t.configure(yscrollcommand=sy.set)
        t.pack(side="left",fill="both",expand=True); sy.pack(side="right",fill="y")
        return t

    def table_frame(self,parent,cols,**packkw):
        wrap=tk.Frame(parent,bg=CARD,highlightbackground=LINE,highlightthickness=1)
        wrap.pack(**packkw)
        t=ttk.Treeview(wrap,columns=[x[0] for x in cols],show="headings")
        for name,width in cols: t.heading(name,text=name); t.column(name,width=width,anchor="w")
        sy=ttk.Scrollbar(wrap,orient="vertical",command=t.yview); t.configure(yscrollcommand=sy.set)
        t.pack(side="left",fill="both",expand=True); sy.pack(side="right",fill="y")
        return t

    def show_products(self):
        for w in self.main.winfo_children(): w.destroy()
        self.page_title("Menu Produk","Tambah, edit, aktif/nonaktif, dan hapus menu.")
        form=self.card(self.main); form.pack(fill="x",padx=30,pady=(0,10))
        es=[]
        for lab in ["Nama","Kategori","Harga"]:
            tk.Label(form,text=lab,bg=CARD,fg=MUTED,font=("Segoe UI",9,"bold")).pack(side="left",padx=(12,4),pady=14)
            e=ttk.Entry(form,width=18); e.pack(side="left",pady=14,padx=(0,8)); es.append(e)
        status=ttk.Combobox(form,values=["Aktif","Nonaktif"],state="readonly",width=12); status.set("Aktif"); status.pack(side="left",padx=5)
        selected=[None]
        t=self.table_frame(self.main,[("ID",55),("Nama",230),("Kategori",140),("Harga",130),("Status",100)],fill="both",expand=True,padx=30,pady=(0,5))
        def clear_fields():
            selected[0]=None
            for e in es:e.delete(0,"end")
            status.set("Aktif")
        def load():
            for x in t.get_children():t.delete(x)
            c=db(); rows=c.execute("SELECT id,name,category,price,status FROM products ORDER BY id DESC").fetchall(); c.close()
            for r in rows:t.insert("","end",values=(r["id"],r["name"],r["category"],rupiah(r["price"]),r["status"]))
        def save():
            if not es[0].get().strip(): return messagebox.showwarning("Data","Nama menu wajib diisi.")
            price=num(es[2].get())
            c=db()
            if selected[0]: c.execute("UPDATE products SET name=?,category=?,price=?,status=? WHERE id=?",(es[0].get().strip(),es[1].get().strip() or "Umum",price,status.get(),selected[0]))
            else: c.execute("INSERT INTO products(name,category,price,status) VALUES(?,?,?,?)",(es[0].get().strip(),es[1].get().strip() or "Umum",price,status.get()))
            c.commit();c.close();clear_fields();load()
        def delete():
            if not selected[0]: return messagebox.showwarning("Pilih menu","Klik satu menu terlebih dahulu.")
            if not messagebox.askyesno("Hapus","Hapus menu ini? BOM terkait juga akan ikut terhapus."): return
            c=db(); c.execute("DELETE FROM products WHERE id=?",(selected[0],)); c.commit(); c.close(); clear_fields(); load()
        def pick(e=None):
            s=t.selection()
            if not s:return
            v=t.item(s[0],"values"); selected[0]=int(v[0]); es[0].delete(0,"end");es[0].insert(0,v[1]);es[1].delete(0,"end");es[1].insert(0,v[2]);es[2].delete(0,"end");es[2].insert(0,v[3].replace("Rp ","").replace(".",""));status.set(v[4])
        ttk.Button(form,text="Simpan / Update",command=save).pack(side="left",padx=8)
        ttk.Button(form,text="Bersihkan",command=clear_fields).pack(side="left",padx=4)
        ttk.Button(form,text="Hapus",command=delete).pack(side="left",padx=4)
        t.bind("<<TreeviewSelect>>",pick); load()
        tk.Label(self.main,text="Tip: klik baris untuk edit. Perubahan langsung masuk database.",bg=BG,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",padx=30,pady=5)

    def show_stock(self):
        for w in self.main.winfo_children(): w.destroy()
        self.page_title("Bahan & Stok","Kelola bahan, satuan, stok hari ini, minimum, dan harga satuan.")
        form=self.card(self.main); form.pack(fill="x",padx=30,pady=(0,10))
        es=[]
        for lab in ["Nama","Satuan","Stok","Minimum","Harga/Satuan"]:
            tk.Label(form,text=lab,bg=CARD,fg=MUTED,font=("Segoe UI",9,"bold")).pack(side="left",padx=(10,3),pady=13)
            e=ttk.Entry(form,width=14); e.pack(side="left",pady=13,padx=(0,7)); es.append(e)
        selected=[None]
        t=self.table_frame(self.main,[("ID",50),("Bahan",190),("Satuan",90),("Stok Hari Ini",135),("Minimum",110),("Harga/Satuan",140),("Status",110)],fill="both",expand=True,padx=30,pady=(0,5))
        def clear_fields():
            selected[0]=None
            for e in es:e.delete(0,"end")
        def load():
            for x in t.get_children():t.delete(x)
            c=db(); rows=c.execute("SELECT * FROM ingredients ORDER BY name").fetchall(); c.close()
            for r in rows:
                st="RESTOCK" if r["stock"]<=r["min_stock"] else "AMAN"
                t.insert("","end",values=(r["id"],r["name"],r["unit"],f"{fmt_qty(r['stock'])} {r['unit']}",f"{fmt_qty(r['min_stock'])} {r['unit']}",rupiah(r["cost"]),st))
        def save():
            if not es[0].get().strip() or not es[1].get().strip(): return messagebox.showwarning("Data","Nama dan satuan wajib diisi.")
            vals=(es[0].get().strip(),es[1].get().strip(),num(es[2].get()),num(es[3].get()),num(es[4].get()))
            c=db()
            if selected[0]: c.execute("UPDATE ingredients SET name=?,unit=?,stock=?,min_stock=?,cost=? WHERE id=?",(*vals,selected[0]))
            else:c.execute("INSERT INTO ingredients(name,unit,stock,min_stock,cost) VALUES(?,?,?,?,?)",vals)
            c.commit();c.close();clear_fields();load()
        def restock():
            if not selected[0]: return messagebox.showwarning("Pilih bahan","Pilih bahan dulu.")
            q=simpledialog.askfloat("Restock","Tambahkan berapa stok?",minvalue=0)
            if q is None:return
            c=db();c.execute("UPDATE ingredients SET stock=stock+? WHERE id=?",(q,selected[0]));c.commit();c.close();load()
        def delete():
            if not selected[0]: return messagebox.showwarning("Pilih bahan","Pilih bahan dulu.")
            if not messagebox.askyesno("Hapus","Hapus bahan ini? BOM yang menggunakan bahan ini juga terhapus."):return
            c=db();c.execute("DELETE FROM ingredients WHERE id=?",(selected[0],));c.commit();c.close();clear_fields();load()
        def pick(e=None):
            s=t.selection()
            if not s:return
            v=t.item(s[0],"values");selected[0]=int(v[0])
            for e in es:e.delete(0,"end")
            es[0].insert(0,v[1]);es[1].insert(0,v[2]);es[2].insert(0,v[3].split()[0]);es[3].insert(0,v[4].split()[0]);es[4].insert(0,v[5].replace("Rp ","").replace(".",""))
        ttk.Button(form,text="Simpan / Update",command=save).pack(side="left",padx=6)
        ttk.Button(form,text="Restock",command=restock).pack(side="left",padx=4)
        ttk.Button(form,text="Bersihkan",command=clear_fields).pack(side="left",padx=4)
        ttk.Button(form,text="Hapus",command=delete).pack(side="left",padx=4)
        t.bind("<<TreeviewSelect>>",pick); load()
        tk.Label(self.main,text="Contoh stok: 50 pcs Ayam • 12 kg Beras • 10 liter Minyak. Klik baris untuk edit.",bg=BG,fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",padx=30,pady=5)

    def show_bom(self):
        for w in self.main.winfo_children():w.destroy()
        self.page_title("Recipe / BOM","Atur bahan yang dipakai untuk satu porsi setiap menu. Bisa tambah, edit, dan hapus.")
        form=self.card(self.main);form.pack(fill="x",padx=30,pady=(0,10))
        c=db(); ps=c.execute("SELECT id,name FROM products ORDER BY name").fetchall(); ins=c.execute("SELECT id,name,unit FROM ingredients ORDER BY name").fetchall();c.close()
        pmap={r["name"]:r["id"] for r in ps}; imap={r["name"]:(r["id"],r["unit"]) for r in ins}
        tk.Label(form,text="Menu",bg=CARD,fg=MUTED,font=("Segoe UI",9,"bold")).pack(side="left",padx=(12,4),pady=13)
        pc=ttk.Combobox(form,values=list(pmap),width=22,state="readonly");pc.pack(side="left",pady=13,padx=5)
        tk.Label(form,text="Bahan",bg=CARD,fg=MUTED,font=("Segoe UI",9,"bold")).pack(side="left",padx=4)
        ic=ttk.Combobox(form,values=list(imap),width=22,state="readonly");ic.pack(side="left",pady=13,padx=5)
        tk.Label(form,text="Qty/Porsi",bg=CARD,fg=MUTED,font=("Segoe UI",9,"bold")).pack(side="left",padx=4)
        qe=ttk.Entry(form,width=12);qe.pack(side="left",pady=13,padx=5)
        selected=[None]
        t=self.table_frame([""],) if False else self.table_frame(self.main,[("ID",50),("Menu",220),("Bahan",200),("Qty/Porsi",110),("Satuan",100)],fill="both",expand=True,padx=30,pady=(0,5))
        def reload_maps():
            nonlocal pmap,imap
            c=db(); pmap={r["name"]:r["id"] for r in c.execute("SELECT id,name FROM products ORDER BY name")}; imap={r["name"]:(r["id"],r["unit"]) for r in c.execute("SELECT id,name,unit FROM ingredients ORDER BY name")}; c.close()
            pc["values"]=list(pmap);ic["values"]=list(imap)
        def load():
            for x in t.get_children():t.delete(x)
            c=db(); rows=c.execute("""SELECT b.id,p.name pn,i.name inn,b.qty,i.unit FROM bom b JOIN products p ON p.id=b.product_id JOIN ingredients i ON i.id=b.ingredient_id ORDER BY p.name,i.name""").fetchall();c.close()
            for r in rows:t.insert("","end",values=(r["id"],r["pn"],r["inn"],fmt_qty(r["qty"]),r["unit"]))
        def clear_fields():selected[0]=None;pc.set("");ic.set("");qe.delete(0,"end")
        def save():
            if not pc.get() or not ic.get():return messagebox.showwarning("Data","Pilih menu dan bahan.")
            q=num(qe.get())
            if q<=0:return messagebox.showwarning("Qty","Qty/Porsi harus lebih dari 0.")
            c=db()
            if selected[0]: c.execute("UPDATE bom SET product_id=?,ingredient_id=?,qty=? WHERE id=?",(pmap[pc.get()],imap[ic.get()][0],q,selected[0]))
            else:c.execute("INSERT INTO bom(product_id,ingredient_id,qty) VALUES(?,?,?)",(pmap[pc.get()],imap[ic.get()][0],q))
            c.commit();c.close();clear_fields();load()
        def delete():
            if not selected[0]:return messagebox.showwarning("Pilih resep","Pilih baris resep dulu.")
            c=db();c.execute("DELETE FROM bom WHERE id=?",(selected[0],));c.commit();c.close();clear_fields();load()
        def pick(e=None):
            s=t.selection()
            if not s:return
            v=t.item(s[0],"values");selected[0]=int(v[0]);pc.set(v[1]);ic.set(v[2]);qe.delete(0,"end");qe.insert(0,v[3])
        ttk.Button(form,text="Simpan / Update",command=save).pack(side="left",padx=7)
        ttk.Button(form,text="Bersihkan",command=clear_fields).pack(side="left",padx=4)
        ttk.Button(form,text="Hapus",command=delete).pack(side="left",padx=4)
        t.bind("<<TreeviewSelect>>",pick);load()

    def show_monitor(self):
        for w in self.main.winfo_children():w.destroy()
        self.page_title("Monitoring Stok","Pantau stok hari ini, satuan, dan bahan yang perlu segera direstock.")
        c=db(); total=c.execute("SELECT COUNT(*) n FROM ingredients").fetchone()["n"]; low=c.execute("SELECT COUNT(*) n FROM ingredients WHERE stock<=min_stock").fetchone()["n"]; safe=total-low;c.close()
        row=tk.Frame(self.main,bg=BG);row.pack(fill="x",padx=24,pady=(0,12))
        self.stat(row,"TOTAL BAHAN",str(total),ACCENT,"ALL");self.stat(row,"AMAN",str(safe),GREEN,"OK");self.stat(row,"PERLU RESTOCK",str(low),RED,"LOW")
        wrap=self.card(self.main);wrap.pack(fill="both",expand=True,padx=30,pady=(0,8))
        bar=tk.Frame(wrap,bg=CARD);bar.pack(fill="x",padx=15,pady=12)
        search=ttk.Entry(bar);search.pack(side="left",fill="x",expand=True)
        t=self.table_frame(wrap,[("ID",55),("Bahan",220),("Satuan",100),("Stok Hari Ini",170),("Minimum",140),("Status",160)],fill="both",expand=True,padx=12,pady=(0,10))
        def load():
            for x in t.get_children():t.delete(x)
            q=search.get().lower().strip(); c=db();rows=c.execute("SELECT id,name,unit,stock,min_stock FROM ingredients ORDER BY name").fetchall();c.close()
            for r in rows:
                if q and q not in r["name"].lower():continue
                status="PERLU RESTOCK" if r["stock"]<=r["min_stock"] else "AMAN"
                t.insert("","end",values=(r["id"],r["name"],r["unit"],f"{fmt_qty(r['stock'])} {r['unit']}",f"{fmt_qty(r['min_stock'])} {r['unit']}",status))
        def edit_selected():
            s=t.selection()
            if not s:return messagebox.showwarning("Pilih bahan","Pilih bahan yang ingin diedit.")
            v=t.item(s[0],"values"); iid=int(v[0])
            c=db();r=c.execute("SELECT * FROM ingredients WHERE id=?",(iid,)).fetchone();c.close()
            if not r:return
            win=tk.Toplevel(self);win.title("Edit Stok");win.geometry("430x360");win.configure(bg=CARD);win.resizable(False,False)
            tk.Label(win,text=f"Edit: {r['name']}",bg=CARD,fg=TEXT,font=("Segoe UI",18,"bold")).pack(pady=20)
            fields=[]
            for lab,val in [("Nama",r["name"]),("Satuan",r["unit"]),("Stok Hari Ini",r["stock"]),("Minimum",r["min_stock"]),("Harga/Satuan",r["cost"])]:
                rowf=tk.Frame(win,bg=CARD);rowf.pack(fill="x",padx=35,pady=4);tk.Label(rowf,text=lab,bg=CARD,fg=MUTED,width=14,anchor="w").pack(side="left");e=ttk.Entry(rowf);e.pack(side="left",fill="x",expand=True);e.insert(0,str(val));fields.append(e)
            def save_edit():
                if not fields[0].get().strip() or not fields[1].get().strip():return messagebox.showwarning("Data","Nama dan satuan wajib diisi.",parent=win)
                c=db();c.execute("UPDATE ingredients SET name=?,unit=?,stock=?,min_stock=?,cost=? WHERE id=?",(fields[0].get().strip(),fields[1].get().strip(),num(fields[2].get()),num(fields[3].get()),num(fields[4].get()),iid));c.commit();c.close();win.destroy();load()
            ttk.Button(win,text="SIMPAN PERUBAHAN",command=save_edit).pack(pady=18)
        def restock_selected():
            s=t.selection()
            if not s:return messagebox.showwarning("Pilih bahan","Pilih bahan yang ingin direstock.")
            v=t.item(s[0],"values");q=simpledialog.askfloat("Restock",f"Tambah stok {v[1]} ({v[2]})",minvalue=0)
            if q is not None:
                c=db();c.execute("UPDATE ingredients SET stock=stock+? WHERE id=?",(q,int(v[0])));c.commit();c.close();load()
        ttk.Button(bar,text="Edit Bahan",command=edit_selected).pack(side="left",padx=(8,4))
        ttk.Button(bar,text="Restock",command=restock_selected).pack(side="left",padx=4)
        search.bind("<KeyRelease>",lambda e:load());load()

    def show_finance(self):
        for w in self.main.winfo_children():w.destroy()
        self.page_title("Keuangan","Catat pengeluaran dan pantau selisih omzet dengan biaya operasional.")
        c=db();om=c.execute("SELECT COALESCE(SUM(total),0) v FROM transactions").fetchone()["v"];ex=c.execute("SELECT COALESCE(SUM(amount),0) v FROM expenses").fetchone()["v"];c.close()
        row=tk.Frame(self.main,bg=BG);row.pack(fill="x",padx=24,pady=(0,12));self.stat(row,"TOTAL OMZET",rupiah(om),ACCENT,"IN");self.stat(row,"PENGELUARAN",rupiah(ex),RED,"OUT");self.stat(row,"SELISIH",rupiah(om-ex),GREEN,"NET")
        form=self.card(self.main);form.pack(fill="x",padx=30,pady=(0,10));es=[]
        for lab in ["Keterangan","Kategori","Nominal"]:
            tk.Label(form,text=lab,bg=CARD,fg=MUTED,font=("Segoe UI",9,"bold")).pack(side="left",padx=(12,4),pady=13);e=ttk.Entry(form,width=22);e.pack(side="left",pady=13,padx=(0,8));es.append(e)
        t=self.table_frame(self.main,[("ID",50),("Tanggal",180),("Keterangan",260),("Kategori",160),("Nominal",150)],fill="both",expand=True,padx=30,pady=(0,5))
        def load():
            for x in t.get_children():t.delete(x)
            c=db();rows=c.execute("SELECT id,created_at,title,category,amount FROM expenses ORDER BY id DESC").fetchall();c.close()
            for r in rows:t.insert("","end",values=(r["id"],r["created_at"],r["title"],r["category"],rupiah(r["amount"])))
        def add():
            a=num(es[2].get());
            if not es[0].get().strip() or a<=0:return messagebox.showwarning("Data","Isi keterangan dan nominal.")
            c=db();c.execute("INSERT INTO expenses(title,amount,category,created_at) VALUES(?,?,?,?)",(es[0].get().strip(),a,es[1].get().strip() or "Operasional",datetime.now().strftime("%Y-%m-%d %H:%M:%S")));c.commit();c.close();load()
        def delete():
            s=t.selection()
            if not s:return
            if not messagebox.askyesno("Hapus","Hapus pengeluaran ini?"):return
            c=db();c.execute("DELETE FROM expenses WHERE id=?",(t.item(s[0],"values")[0],));c.commit();c.close();load()
        ttk.Button(form,text="＋ Catat Pengeluaran",command=add).pack(side="left",padx=8);ttk.Button(form,text="Hapus",command=delete).pack(side="left",padx=4);load()

    def show_reports(self):
        for w in self.main.winfo_children():w.destroy()
        self.page_title("Laporan & Analitik","Export transaksi/stok dan lihat menu paling laris.")
        row=tk.Frame(self.main,bg=BG);row.pack(fill="x",padx=30,pady=(0,10))
        ttk.Button(row,text="Export Transaksi CSV",command=self.export_transactions).pack(side="left",padx=(0,8));ttk.Button(row,text="Export Stok CSV",command=self.export_stock).pack(side="left")
        box=self.card(self.main);box.pack(fill="both",expand=True,padx=30,pady=5)
        tk.Label(box,text="Menu Terlaris",bg=CARD,fg=TEXT,font=("Segoe UI",15,"bold")).pack(anchor="w",padx=18,pady=14)
        t=self.table_frame(box,[("Rank",70),("Produk",320),("Qty Terjual",140),("Omzet",180)],fill="both",expand=True,padx=18,pady=(0,18))
        c=db();rows=c.execute("""SELECT p.name,SUM(ti.qty) qty,SUM(ti.subtotal) omzet FROM transaction_items ti JOIN products p ON p.id=ti.product_id GROUP BY p.id ORDER BY qty DESC LIMIT 20""").fetchall();c.close()
        for n,r in enumerate(rows,1):t.insert("","end",values=(n,r["name"],r["qty"],rupiah(r["omzet"])))

    def export_transactions(self):
        path=os.path.join(EXPORT_DIR,"laporan_transaksi_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".csv")
        c=db();rows=c.execute("""SELECT t.trx_no,t.created_at,p.name,ti.qty,ti.price,ti.subtotal,t.payment_method FROM transaction_items ti JOIN transactions t ON t.id=ti.transaction_id JOIN products p ON p.id=ti.product_id ORDER BY t.id DESC""").fetchall();c.close()
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f);w.writerow(["No Transaksi","Tanggal","Produk","Qty","Harga","Subtotal","Metode"]);[w.writerow(list(r)) for r in rows]
        messagebox.showinfo("Export berhasil",f"File disimpan di:\n{path}")

    def export_stock(self):
        path=os.path.join(EXPORT_DIR,"laporan_stok_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".csv")
        c=db();rows=c.execute("SELECT name,unit,stock,min_stock,cost FROM ingredients ORDER BY name").fetchall();c.close()
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f);w.writerow(["Bahan","Satuan","Stok Hari Ini","Minimum","Harga/Satuan"]);[w.writerow(list(r)) for r in rows]
        messagebox.showinfo("Export berhasil",f"File disimpan di:\n{path}")


if __name__ == "__main__":
    init_db()
    App().mainloop()
