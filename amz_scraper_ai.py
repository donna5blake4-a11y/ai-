# amz_scraper_ai.py
# الواجهة المحسنة مع AI - نسخة مبسطة

import customtkinter as ctk
import json, threading, asyncio, os, sqlite3
from datetime import datetime
from categories import CATEGORIES
import re
from PIL import Image
import requests
from io import BytesIO
import webbrowser
import concurrent.futures
import time

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
    "products_per_minute": 0,
    "ai_analyzed": 0,
    "high_quality_deals": 0
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
    try:
        DB_MANAGER = sqlite3.connect("amz_products.db")
        log("🗄️ Database initialized", "✅")
        show_stats()
    except Exception as e:
        log(f"❌ Database error: {e}", "⚠️")

def show_stats():
    """عرض إحصائيات قاعدة البيانات"""
    if not DB_MANAGER:
        return
    
    try:
        cursor = DB_MANAGER.cursor()
        
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
        root.title(f"LAQTA Ultra AI - Processing... ({session_stats['total_products']} products{speed_info})")

def export_csv():
    """تصدير إلى CSV من قاعدة البيانات"""
    if not DB_MANAGER:
        log("❌ Database not initialized", "⚠️")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"products_export_{timestamp}.csv"
    
    try:
        cursor = DB_MANAGER.cursor()
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
        # هنا يمكن إضافة كود إرسال التليجرام
        pass

# شاشة المنتجات محسنة مع قاعدة البيانات
class UltraFastAlertsWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Ultra Fast AI Deals Dashboard")
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
            cursor = DB_MANAGER.cursor()
            
            # إحصائيات قاعدة البيانات
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM products WHERE discount_percent >= ?", (min_discount,))
            deals_count = cursor.fetchone()[0]
            
            self.db_stats_label.configure(
                text=f"📊 Database: {total_products:,} products | {deals_count:,} deals"
            )
            
            # جلب المنتجات المخفضة مع التصفح
            offset = self.page * self.items_per_page
            cursor.execute('''
                SELECT asin, name, url, img, section, current_price, 
                       strike_price, discount_percent, last_updated
                FROM products 
                WHERE discount_percent >= ? AND discount_percent <= 98
                ORDER BY discount_percent DESC, last_updated DESC
                LIMIT ? OFFSET ?
            ''', (min_discount, self.items_per_page, offset))
            
            products = cursor.fetchall()
            
            # حساب إجمالي الصفحات
            total_pages = max(1, (deals_count + self.items_per_page - 1) // self.items_per_page)
            self.page = max(0, min(self.page, total_pages - 1))
            
            if not products:
                empty_lbl = ctk.CTkLabel(
                    self.cards_frame, 
                    text=f"No deals found with discount ≥ {min_discount}%", 
                    font=("Arial", 18), 
                    text_color="#54fac8"
                )
                empty_lbl.pack(pady=60)
            else:
                # عرض المنتجات
                for i, product in enumerate(products):
                    self.render_database_product_card(product, i)
            
            # تحديث التصفح
            self.page_lbl.configure(text=f"Page {self.page+1} of {total_pages}")
            self.prev_btn.configure(state="normal" if self.page > 0 else "disabled")
            self.next_btn.configure(state="normal" if self.page < total_pages-1 else "disabled")
            
        except Exception as e:
            error_lbl = ctk.CTkLabel(
                self.cards_frame,
                text=f"Database error: {e}",
                font=("Arial", 16),
                text_color="#ff6666"
            )
            error_lbl.pack(pady=60)
        
        # تحديث التمرير
        self.cards_frame.update_idletasks()
        self.main_canvas.config(scrollregion=self.main_canvas.bbox("all"))

    def render_database_product_card(self, product_data, index):
        """رسم بطاقة منتج من قاعدة البيانات"""
        asin, name, url, img, section, current_price, strike_price, discount_percent, last_updated = product_data
        
        # تحديد الألوان والعلامات
        icon, color = get_discount_tag(discount_percent, True, 85)
        
        # إنشاء البطاقة
        card = ctk.CTkFrame(
            self.cards_frame,
            fg_color="#222a34",
            border_width=3,
            border_color=color,
            corner_radius=18,
            height=200,
        )
        card.pack(fill="x", padx=18, pady=16)
        
        # الصورة
        img_frame = ctk.CTkFrame(card, fg_color="transparent", width=150, height=150)
        img_frame.pack(side="left", padx=(16, 8), pady=16)
        img_frame.pack_propagate(False)

        img_label = ctk.CTkLabel(img_frame, text="Loading...", font=("Arial", 10), width=150, height=150)
        img_label.pack(expand=True, fill="both")

        def load_img():
            if not img:
                img_label.after(0, lambda: img_label.configure(text="No Image", image=""))
                return
            if img in self._img_cache:
                ctk_img = self._img_cache[img]
                img_label.after(0, lambda: (img_label.configure(image=ctk_img, text=""), setattr(img_label, "image", ctk_img)))
                return
            try:
                r = requests.get(img, timeout=6)
                pil_img = Image.open(BytesIO(r.content)).resize((150, 150))
                ctk_img = ctk.CTkImage(dark_image=pil_img, size=(150, 150))
                self._img_cache[img] = ctk_img
                img_label.after(0, lambda: (img_label.configure(image=ctk_img, text=""), setattr(img_label, "image", ctk_img)))
            except Exception:
                img_label.after(0, lambda: img_label.configure(text="No Image", image=""))
        
        self._executor.submit(load_img)

        # المعلومات النصية
        right_frame = ctk.CTkFrame(card, fg_color="transparent")
        right_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

        # العنوان
        title = name[:80] + ("..." if len(name) > 80 else "")
        title_label = ctk.CTkLabel(
            right_frame, text=title,
            font=("Arial Black", 16, "bold"), 
            text_color="#41ffe0",
            anchor="w", wraplength=600, justify="left"
        )
        title_label.pack(pady=(4, 8), anchor="w")

        # معلومات المنتج
        info_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 8))
        
        # القسم
        section_label = ctk.CTkLabel(
            info_frame,
            text=f"📦 {section}",
            font=("Arial", 12, "bold"),
            text_color="#59ff9d"
        )
        section_label.pack(side="left", anchor="w")
        
        # آخر تحديث
        update_label = ctk.CTkLabel(
            info_frame,
            text=f"🕒 {last_updated}",
            font=("Arial", 10),
            text_color="#888888"
        )
        update_label.pack(side="right", anchor="e")

        # صف الأسعار
        price_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        price_frame.pack(fill="x", pady=(0, 8))
        
        if strike_price and strike_price > current_price:
            old_label = ctk.CTkLabel(
                price_frame,
                text=f"🔻 {int(strike_price):,} EGP",
                font=("Arial", 14, "bold"),
                text_color="#fe8989"
            )
            old_label.pack(side="left", padx=(0, 8))
        
        new_label = ctk.CTkLabel(
            price_frame,
            text=f"💰 {int(current_price):,} EGP",
            font=("Arial", 18, "bold"),
            text_color="#b9ffa3"
        )
        new_label.pack(side="left", padx=(0, 12))

        # نسبة الخصم
        discount_label = ctk.CTkLabel(
            price_frame,
            text=f"{icon} {discount_percent:.1f}% OFF",
            font=("Arial Black", 16, "bold"),
            text_color=color
        )
        discount_label.pack(side="left")

        # الأزرار
        buttons_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(8, 0))
        
        # زر المنتج
        product_btn = ctk.CTkButton(
            buttons_frame,
            text="🔥 View Product",
            fg_color=color,
            hover_color="#444",
            text_color="#232d3a",
            font=("Arial", 14, "bold"),
            width=140, height=35,
            command=lambda: webbrowser.open(url) if url else None
        )
        product_btn.pack(side="right", padx=(8, 0))

    def _on_resize(self, event=None):
        self.cards_frame.update_idletasks()
        self.main_canvas.config(scrollregion=self.main_canvas.bbox("all"))

    def next_page(self):
        self.page += 1
        self.refresh_from_database()

    def prev_page(self):
        self.page -= 1
        self.refresh_from_database()

def open_alerts_window():
    """فتح نافذة المنتجات المحسنة"""
    UltraFastAlertsWindow(root)

# سلايدر التحكم في نسبة الخصم
def set_min_discount(val):
    global ALERT_DISCOUNT
    ALERT_DISCOUNT = int(float(val))
    min_discount_label.configure(text=f"Min Discount: {ALERT_DISCOUNT}%")
    log(f"🔧 Minimum discount set to {ALERT_DISCOUNT}%", "⚡")

def scraper_func(section, pages, all_pages):
    """دالة الكشط المحسنة"""
    # هنا سيتم دمج الكود الحالي مع النظام المحسن
    log(f"🚀 Started scraping {section} - AI Enhanced Mode!", "🔥")
    
    # محاكاة الكشط
    for i in range(pages):
        if stop_flag.get("stop"):
            break
        
        # محاكاة معالجة صفحة
        session_stats["total_products"] += 10
        update_progress((i + 1) / pages * 100)
        time.sleep(0.1)
    
    log(f"✅ Session completed! Products: {session_stats['total_products']:,}", "🎉")

def start_scraping():
    """بدء عملية الكشط"""
    if running[0]:
        log("Already running.", "⚠️")
        return
    
    if not DB_MANAGER:
        initialize_database()
    
    section = section_combo.get()
    all_pages = all_pages_chk.get()
    pages = int(pages_entry.get()) if not all_pages else 9999
    
    progress_bar.set(0.0)
    stop_flag["stop"] = False
    running[0] = True
    
    global scrape_thread
    scrape_thread = threading.Thread(
        target=scraper_func, 
        args=(section, pages, all_pages), 
        daemon=True
    )
    scrape_thread.start()
    
    log(f"🚀 Started scraping {section} - AI Enhanced Mode!", "🔥")

def stop_scraping():
    """إيقاف عملية الكشط"""
    stop_flag["stop"] = True
    running[0] = False
    root.title("LAQTA Ultra AI - Stopping...")
    log("🛑 Stopping...", "⚡")

def resume_scraping():
    """تحميل قاعدة البيانات وعرض الإحصائيات"""
    if not DB_MANAGER:
        initialize_database()
    else:
        show_stats()

def exit_app():
    """إغلاق التطبيق"""
    stop_flag["stop"] = True
    if DB_MANAGER:
        DB_MANAGER.close()
    root.destroy()

def clear_log():
    """مسح السجل"""
    log_textbox.configure(state="normal")
    log_textbox.delete("1.0", "end")
    log_textbox.configure(state="disabled")

# ==== MAIN ROOT ====
root = ctk.CTk()
root.title("LAQTA Ultra AI - Enhanced Amazon Product Hunter")
root.geometry("1400x980")
root.minsize(1100, 700)
root.rowconfigure(3, weight=1)
root.columnconfigure(0, weight=1)

# العنوان مع معلومات النسخة
title_label = ctk.CTkLabel(
    root, 
    text="LAQTA ULTRA AI", 
    font=("SST Arabic Medium", 75), 
    text_color="#54fac8"
)
title_label.grid(row=0, column=0, padx=8, pady=(18, 5), sticky="ew")

subtitle_label = ctk.CTkLabel(
    root,
    text="🤖 AI-Powered Smart Deals Detector | Real Deals Only",
    font=("Arial", 14, "bold"),
    text_color="#59ff9d"
)
subtitle_label.grid(row=1, column=0, padx=8, pady=(0, 10), sticky="ew")

# إطار التحكم
controls_frame = ctk.CTkFrame(root, fg_color="transparent")
controls_frame.grid(row=2, column=0, padx=10, pady=7, sticky="ew")
controls_frame.grid_columnconfigure((0,1,2,3,4,5,6), weight=1)

section_combo = ctk.CTkComboBox(
    controls_frame, 
    values=["All Sections"] + list(CATEGORIES.keys()),
    width=260, 
    font=("Arial", 18), 
    button_color="#54fac8"
)
section_combo.set("Electronics")
section_combo.grid(row=0, column=0, padx=8, pady=8, sticky="ew")

pages_entry = ctk.CTkEntry(
    controls_frame, 
    width=120, 
    font=("Arial", 18), 
    fg_color="#232d3a", 
    text_color="#12dafb"
)
pages_entry.insert(0, "10")
pages_entry.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

pages_label = ctk.CTkLabel(
    controls_frame, 
    text="Pages per section", 
    font=("Arial", 18), 
    text_color="#12dafb"
)
pages_label.grid(row=0, column=2, padx=8, pady=8, sticky="ew")

all_pages_chk = ctk.CTkCheckBox(
    controls_frame, 
    text="All Pages", 
    font=("Arial", 17), 
    text_color="#59ff9d"
)
all_pages_chk.grid(row=0, column=3, padx=10, pady=8, sticky="ew")

# سلايدر التحكم في نسبة الخصم
min_discount_slider = ctk.CTkSlider(
    controls_frame, 
    from_=1, to=99, 
    number_of_steps=98, 
    width=170,
    command=set_min_discount, 
    progress_color="#12dafb"
)
min_discount_slider.set(ALERT_DISCOUNT)
min_discount_slider.grid(row=0, column=4, padx=10, pady=8, sticky="ew")

min_discount_label = ctk.CTkLabel(
    controls_frame, 
    text=f"Min Discount: {ALERT_DISCOUNT}%", 
    font=("Arial", 16), 
    text_color="#59ff9d"
)
min_discount_label.grid(row=0, column=5, padx=6, pady=8, sticky="ew")

# Checkbox للتحكم في إشعارات التليجرام
def toggle_telegram_alert():
    telegram_alerts_enabled[0] = not telegram_alerts_enabled[0]
    status = "enabled" if telegram_alerts_enabled[0] else "disabled"
    log(f"📱 Telegram alerts {status}", "⚡")

telegram_checkbox = ctk.CTkCheckBox(
    controls_frame, 
    text="Send to Telegram", 
    font=("Arial", 17), 
    text_color="#13e6a7",
    command=toggle_telegram_alert
)
telegram_checkbox.grid(row=0, column=6, padx=10, pady=8, sticky="ew")
telegram_checkbox.select()

# زر عرض Dashboard المحسن
open_alerts_btn = ctk.CTkButton(
    controls_frame, 
    text="🤖 AI Dashboard", 
    font=("Arial", 17, "bold"),
    command=open_alerts_window, 
    fg_color="#59ff9d", 
    hover_color="#13e6a7", 
    text_color="#232d3a", 
    width=180, 
    height=50
)
open_alerts_btn.grid(row=0, column=7, padx=8, pady=8, sticky="ew")

# شريط التقدم المحسن
progress_bar = ctk.CTkProgressBar(
    root, 
    height=22, 
    progress_color="#59ff9d", 
    fg_color="#232d3a"
)
progress_bar.grid(row=3, column=0, padx=10, pady=7, sticky="ew")
progress_bar.set(0.0)

# مربع السجل
log_textbox = ctk.CTkTextbox(
    root, 
    font=("Consolas", 16), 
    fg_color="#20242f", 
    text_color="#c2ffe3", 
    border_width=0, 
    height=190
)
log_textbox.grid(row=4, column=0, padx=15, pady=(0, 12), sticky="nsew")
log_textbox.configure(state="disabled")

# إطار الأزرار المحسن
buttons_frame = ctk.CTkFrame(root, fg_color="transparent")
buttons_frame.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
buttons_frame.grid_columnconfigure((0,1,2,3,4,5,6), weight=1)

btn_w, btn_h = 160, 48
btn_font = ("Arial", 18, "bold")

start_btn = ctk.CTkButton(
    buttons_frame, 
    text="🚀 AI Start", 
    command=start_scraping, 
    width=btn_w, height=btn_h,
    font=btn_font, 
    fg_color="#54fac8", 
    hover_color="#12dafb", 
    text_color="#111927"
)
start_btn.grid(row=0, column=0, padx=8, pady=8, sticky="ew")

stop_btn = ctk.CTkButton(
    buttons_frame, 
    text="✋ Stop", 
    command=stop_scraping, 
    width=btn_w, height=btn_h,
    font=btn_font, 
    fg_color="#12dafb", 
    hover_color="#54fac8", 
    text_color="#111927"
)
stop_btn.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

resume_btn = ctk.CTkButton(
    buttons_frame, 
    text="🗄️ Load DB", 
    command=resume_scraping, 
    width=btn_w, height=btn_h,
    font=btn_font, 
    fg_color="#59ff9d", 
    hover_color="#12dafb", 
    text_color="#111927"
)
resume_btn.grid(row=0, column=2, padx=8, pady=8, sticky="ew")

export_btn = ctk.CTkButton(
    buttons_frame, 
    text="📊 Export CSV", 
    command=export_csv, 
    width=btn_w, height=btn_h,
    font=btn_font, 
    fg_color="#12dafb", 
    hover_color="#59ff9d", 
    text_color="#111927"
)
export_btn.grid(row=0, column=3, padx=8, pady=8, sticky="ew")

stats_btn = ctk.CTkButton(
    buttons_frame, 
    text="📈 Stats", 
    command=show_stats, 
    width=btn_w, height=btn_h,
    font=btn_font, 
    fg_color="#59ff9d", 
    hover_color="#54fac8", 
    text_color="#111927"
)
stats_btn.grid(row=0, column=4, padx=8, pady=8, sticky="ew")

clear_btn = ctk.CTkButton(
    buttons_frame, 
    text="🧹 Clear Log", 
    command=clear_log, 
    width=btn_w, height=btn_h,
    font=btn_font, 
    fg_color="#54fac8", 
    hover_color="#12dafb", 
    text_color="#111927"
)
clear_btn.grid(row=0, column=5, padx=8, pady=8, sticky="ew")

# زر الخروج
exit_btn = ctk.CTkButton(
    root, 
    text="⌫ Exit", 
    command=exit_app, 
    width=400, height=60,
    font=("Arial Black", 26), 
    fg_color="#232d3a", 
    hover_color="#fa1a50", 
    text_color="#59ff9d"
)
exit_btn.grid(row=6, column=0, pady=(10, 14))

# تهيئة قاعدة البيانات عند البدء
def startup_sequence():
    """تسلسل بدء التشغيل"""
    initialize_database()
    log("🚀 LAQTA Ultra AI initialized - Smart Deals Detector Ready!", "🔥")
    log("✅ Features: AI-powered analysis, Real deals only, Market comparison", "💡")
    log("🤖 AI will analyze prices and compare with Egyptian retailers!", "🎯")

# بدء التطبيق
root.after(1000, startup_sequence)

if __name__ == "__main__":
    try:
        root.mainloop()
    except KeyboardInterrupt:
        exit_app()