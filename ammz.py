# ammz_ultra_fast.py
import customtkinter as ctk
import json, threading, asyncio, os, sqlite3
from datetime import datetime
from enhanced_amz_scraper import scrape_section_enhanced, DatabaseManager, export_to_json
from categories import CATEGORIES
import re
from PIL import Image
import requests
from io import BytesIO
import webbrowser
import concurrent.futures
import time

# استيراد البوت المحسن
from enhanced_telegram_bot import send_telegram_alert, send_summary_report

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# استخدام SQLite بدلاً من JSON
DB_MANAGER = None
stop_flag = {"stop": False}
scrape_thread = None
running = [False]
telegram_alerts_enabled = [True]

ALERT_DISCOUNT = 20
alerts_data = []
notified_asins = set()

# إحصائيات محسنة
session_stats = {
    "total_products": 0,
    "real_deals": 0,
    "fake_deals": 0,
    "current_section": "",
    "start_time": None,
    "products_per_minute": 0
}

DISCOUNT_TAGS = [
    (90, "🔥", "#ff1a36"),
    (80, "💥", "#ff3e8a"), 
    (70, "🎉", "#ff7f50"),
    (60, "✨", "#ffdf30"),
    (50, "⭐", "#00f7c2"),
    (40, "📢", "#19c8fa"),
    (30, "⚡", "#77ff3b"),
    (20, "🛒", "#90EE90"),
]
DROP_TAG = ("🚨", "#ffbf00")
REAL_DEAL_TAG = ("🎯", "#00ff00")
FAKE_DEAL_TAG = ("🚫", "#ff4444")

def initialize_database():
    """تهيئة قاعدة البيانات"""
    global DB_MANAGER
    DB_MANAGER = DatabaseManager()
    log("🗄️ Database initialized", "✅")
    show_stats()

def show_stats():
    """عرض إحصائيات قاعدة البيانات"""
    if not DB_MANAGER:
        return
    
    try:
        cursor = DB_MANAGER.connection.cursor()
        
        # إجمالي المنتجات
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]
        
        # المنتجات المخفضة
        cursor.execute("SELECT COUNT(*) FROM products WHERE discount_percent >= ?", (ALERT_DISCOUNT,))
        discounted = cursor.fetchone()[0]
        
        # أعلى خصم
        cursor.execute("SELECT MAX(discount_percent), name FROM products WHERE discount_percent < 99")
        max_result = cursor.fetchone()
        max_discount = max_result[0] if max_result[0] else 0
        
        # آخر تحديث
        cursor.execute("SELECT MAX(last_updated) FROM products")
        last_update = cursor.fetchone()[0]
        
        log(f"📊 Database Stats: {total_products:,} products | {discounted:,} deals | Max discount: {max_discount:.1f}%")
        
        if last_update:
            log(f"🕒 Last update: {last_update}")
            
    except Exception as e:
        log(f"❌ Error getting stats: {e}")

def log(msg, emoji=""):
    """سجل الأحداث مع الوقت والسرعة"""
    msg_no_links = re.sub(r'https?://\S+|www\.\S+', '', msg).strip()
    if not msg_no_links:
        return
    
    log_textbox.configure(state="normal")
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # إضافة معلومات السرعة إذا كان هناك كشط نشط
    speed_info = ""
    if session_stats["start_time"] and session_stats["total_products"] > 0:
        elapsed = (datetime.now() - session_stats["start_time"]).total_seconds() / 60
        if elapsed > 0:
            speed = session_stats["total_products"] / elapsed
            speed_info = f" ({speed:.0f}/min)"
    
    log_textbox.insert("end", f"[{timestamp}] {emoji} {msg_no_links}{speed_info}\n")
    log_textbox.see("end")
    log_textbox.configure(state="disabled")
    
    # تحديث شريط العنوان مع السرعة
    if running[0]:
        root.title(f"LAQTA Ultra - Processing... ({session_stats['total_products']} products{speed_info})")

def export_csv():
    """تصدير إلى CSV من قاعدة البيانات"""
    if not DB_MANAGER:
        log("❌ Database not initialized", "⚠️")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"products_export_{timestamp}.csv"
    
    try:
        cursor = DB_MANAGER.connection.cursor()
        cursor.execute('''
            SELECT asin, name, section, url, img, current_price, 
                   strike_price, discount_percent, last_updated
            FROM products 
            ORDER BY discount_percent DESC
        ''')
        
        products = cursor.fetchall()
        
        with open(filename, "w", encoding="utf-8", newline="") as f:
            import csv
            writer = csv.writer(f)
            writer.writerow([
                "ASIN", "Name", "Section", "URL", "Image", "Current Price", 
                "Strike Price", "Discount %", "Last Updated"
            ])
            
            for product in products:
                writer.writerow(product)
        
        log(f"📄 Exported {len(products):,} products to {filename}", "✅")
        
    except Exception as e:
        log(f"❌ Export error: {e}", "⚠️")

def update_progress(val):
    """تحديث شريط التقدم مع معلومات إضافية"""
    progress_bar.set(min(val / 100, 1.0))
    
    # تحديث الإحصائيات في الوقت الفعلي
    if session_stats["start_time"]:
        elapsed = (datetime.now() - session_stats["start_time"]).total_seconds()
        if elapsed > 0:
            session_stats["products_per_minute"] = (session_stats["total_products"] * 60) / elapsed

def get_discount_tag(discount_percent, is_real_discount=True, confidence=0):
    """تحديد العلامة المناسبة للتخفيض"""
    if not is_real_discount:
        return FAKE_DEAL_TAG
    
    if confidence >= 80:
        return REAL_DEAL_TAG
    
    for level, icon, color in DISCOUNT_TAGS:
        if discount_percent >= level:
            return icon, color
    return "⚡", "#47ffd1"

def add_alert_data(item, old_price, new_price, discount_percent, drop_detected=False):
    """إضافة بيانات التنبيه مع حفظ في قاعدة البيانات"""
    asin = item.get("asin")
    key = f"{asin}-{int(new_price)}"
    if key in notified_asins:
        return
    notified_asins.add(key)
    
    # تحديث الإحصائيات
    session_stats["total_products"] += 1
    if item.get("real_discount", True):
        session_stats["real_deals"] += 1
    else:
        session_stats["fake_deals"] += 1
    
    # إضافة للقائمة المؤقتة
    alerts_data.append({
        "item": item,
        "old_price": old_price,
        "new_price": new_price,
        "discount_percent": discount_percent,
        "drop_detected": drop_detected,
        "timestamp": datetime.now()
    })
    
    # إرسال التنبيه إذا كان مفعل
    if telegram_alerts_enabled[0]:
        threading.Thread(
            target=send_telegram_alert, 
            args=(item, old_price, new_price, discount_percent, drop_detected), 
            daemon=True
        ).start()

# شاشة المنتجات محسنة مع قاعدة البيانات
class UltraFastAlertsWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Ultra Fast Deals Dashboard")
        self.configure(bg="#232d3a")
        self.minsize(1000, 500)
        self.geometry("1400x800")
        self.page = 0
        self.items_per_page = 20
        self._img_cache = {}
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)
        
        # إعداد الواجهة
        self.setup_ui()
        self.after(100, self.refresh_from_database)

    def setup_ui(self):
        # الإطار الخارجي
        self.outer_frame = ctk.CTkFrame(self, fg_color="#232d3a")
        self.outer_frame.pack(expand=True, fill="both", padx=16, pady=16)
        self.outer_frame.grid_rowconfigure(0, weight=1)
        self.outer_frame.grid_columnconfigure(0, weight=1)

        # Canvas للتمرير
        self.main_canvas = ctk.CTkCanvas(self.outer_frame, bg="#232d3a", highlightthickness=0)
        self.main_canvas.grid(row=0, column=0, sticky="nsew")

        # شريط التمرير
        self.scrollbar = ctk.CTkScrollbar(self.outer_frame, orientation="vertical", command=self.main_canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)

        # إطار البطاقات
        self.cards_frame = ctk.CTkFrame(self.main_canvas, fg_color="#232d3a")
        self.main_canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")

        # شريط التحكم العلوي
        self.setup_top_bar()
        
        # أزرار التصفح
        self.setup_pagination()

        # ربط الأحداث
        self.bind("<Configure>", self._on_resize)

    def setup_top_bar(self):
        """إعداد شريط التحكم العلوي"""
        top_bar = ctk.CTkFrame(self, fg_color="#1a1f2e", height=60)
        top_bar.pack(side="top", fill="x", padx=16, pady=(16, 8))
        
        # إحصائيات قاعدة البيانات
        stats_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        stats_frame.pack(side="left", padx=10, pady=10)
        
        self.db_stats_label = ctk.CTkLabel(
            stats_frame, 
            text="📊 Loading database stats...",
            font=("Arial", 14, "bold"),
            text_color="#54fac8"
        )
        self.db_stats_label.pack(pady=5)
        
        # أزرار التحكم
        controls_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        controls_frame.pack(side="right", padx=10, pady=5)
        
        # فلتر الخصومات
        self.min_discount_var = ctk.StringVar(value=str(ALERT_DISCOUNT))
        discount_entry = ctk.CTkEntry(
            controls_frame, 
            textvariable=self.min_discount_var,
            width=60,
            font=("Arial", 12, "bold")
        )
        discount_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(
            controls_frame,
            text="% Min Discount",
            font=("Arial", 12, "bold"),
            text_color="#59ff9d"
        ).pack(side="left", padx=(0, 10))
        
        # زر التحديث
        refresh_btn = ctk.CTkButton(
            controls_frame,
            text="🔄 Refresh",
            command=self.refresh_from_database,
            width=80,
            height=30,
            fg_color="#54fac8",
            text_color="#232d3a"
        )
        refresh_btn.pack(side="left", padx=5)

    def setup_pagination(self):
        """إعداد أزرار التصفح"""
        pag_frame = ctk.CTkFrame(self, fg_color="#232d3a")
        pag_frame.pack(side="bottom", fill="x", pady=(0, 16))
        
        self.prev_btn = ctk.CTkButton(
            pag_frame, text="⬅️ Prev", font=("Arial", 17, "bold"),
            command=self.prev_page, width=120, 
            fg_color="#54fac8", text_color="#232d3a"
        )
        self.prev_btn.pack(side="left", padx=12, pady=5)
        
        self.page_lbl = ctk.CTkLabel(
            pag_frame, text="", font=("Arial", 18, "bold"), 
            text_color="#6cfbc8"
        )
        self.page_lbl.pack(side="left", padx=6)
        
        self.next_btn = ctk.CTkButton(
            pag_frame, text="Next ➡️", font=("Arial", 17, "bold"),
            command=self.next_page, width=120, 
            fg_color="#54fac8", text_color="#232d3a"
        )
        self.next_btn.pack(side="left", padx=12, pady=5)

    def refresh_from_database(self):
        """تحديث البيانات من قاعدة البيانات"""
        if not DB_MANAGER:
            return
        
        try:
            min_discount = float(self.min_discount_var.get())
        except:
            min_discount = ALERT_DISCOUNT
        
        # مسح البطاقات الحالية
        for w in self.cards_frame.winfo_children():
            w.destroy()
        
        try:
            cursor = DB_MANAGER.connection.cursor()
            
            # إحصائيات قاعدة البيانات
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM products WHERE discount_percent >= ?", (min_discount,))
            deals_count = cursor.fetchone()[0]
            
            self.db_stats_label.configure(
                text=f"📊 Database: {total_products:,} products | {deals_count:,} deals (≥{min_discount}%)"
            )
            
            # جلب المنتجات المخفضة مع التصفح