# enhanced_ammz_gui.py - الواجهة المحسنة مع النظام الذكي
import customtkinter as ctk
import json, threading, asyncio, os, sqlite3
from datetime import datetime
import re
from PIL import Image
import requests
from io import BytesIO
import webbrowser
import concurrent.futures
import time

# استيراد النظام الذكي
try:
    from smart_deal_filter import SmartDealFilter
except ImportError:
    SmartDealFilter = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# متغيرات النظام
DB_MANAGER = None
stop_flag = {"stop": False}
scrape_thread = None
running = [False]
telegram_alerts_enabled = [True]
smart_filter_enabled = [True]  # جديد

ALERT_DISCOUNT = 20
alerts_data = []
notified_asins = set()

# إحصائيات محسنة
session_stats = {
    "total_products": 0,
    "real_deals": 0,
    "fake_deals": 0,
    "smart_filtered": 0,  # جديد
    "current_section": "",
    "start_time": None,
    "products_per_minute": 0
}

# علامات التخفيض
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
SMART_APPROVED_TAG = ("🤖", "#00ff88")  # جديد

# نظام قاعدة البيانات المحسن
class EnhancedDatabaseManager:
    def __init__(self, db_file="enhanced_deals.db"):
        self.db_file = db_file
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.setup_tables()
        
    def setup_tables(self):
        """إعداد جداول قاعدة البيانات"""
        
        # جدول المنتجات الأساسي
        self.connection.execute('''
            CREATE TABLE IF NOT EXISTS products (
                asin TEXT PRIMARY KEY,
                name TEXT,
                url TEXT,
                img TEXT,
                section TEXT,
                current_price REAL,
                strike_price REAL,
                discount_percent REAL,
                smart_score REAL DEFAULT 0,
                is_smart_approved BOOLEAN DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول تاريخ الأسعار
        self.connection.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT,
                price REAL,
                date TEXT,
                time TEXT,
                FOREIGN KEY (asin) REFERENCES products (asin)
            )
        ''')
        
        # جدول العروض المعتمدة
        self.connection.execute('''
            CREATE TABLE IF NOT EXISTS approved_deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT,
                approval_date TEXT,
                smart_score REAL,
                reasons TEXT,
                is_sent BOOLEAN DEFAULT 0,
                FOREIGN KEY (asin) REFERENCES products (asin)
            )
        ''')
        
        # إنشاء الفهارس
        self.connection.execute('CREATE INDEX IF NOT EXISTS idx_asin ON products(asin)')
        self.connection.execute('CREATE INDEX IF NOT EXISTS idx_smart_score ON products(smart_score)')
        self.connection.execute('CREATE INDEX IF NOT EXISTS idx_smart_approved ON products(is_smart_approved)')
        
        self.connection.commit()

def initialize_enhanced_database():
    """تهيئة قاعدة البيانات المحسنة"""
    global DB_MANAGER
    DB_MANAGER = EnhancedDatabaseManager()
    log("🗄️ Enhanced Database initialized", "✅")
    show_enhanced_stats()

def show_enhanced_stats():
    """عرض إحصائيات محسنة"""
    if not DB_MANAGER:
        return
    
    try:
        cursor = DB_MANAGER.connection.cursor()
        
        # إجمالي المنتجات
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]
        
        # المنتجات المعتمدة بالذكاء الاصطناعي
        cursor.execute("SELECT COUNT(*) FROM products WHERE is_smart_approved = 1")
        smart_approved = cursor.fetchone()[0]
        
        # متوسط النقاط الذكية
        cursor.execute("SELECT AVG(smart_score) FROM products WHERE smart_score > 0")
        avg_score = cursor.fetchone()[0] or 0
        
        # أعلى نقاط
        cursor.execute("SELECT MAX(smart_score), name FROM products WHERE smart_score > 0")
        max_result = cursor.fetchone()
        max_score = max_result[0] if max_result[0] else 0
        
        log(f"📊 Enhanced Stats: {total_products:,} products | {smart_approved:,} AI approved | Avg score: {avg_score:.1f}")
        
        if max_score > 0:
            log(f"🏆 Best deal: {max_score:.1f} points")
            
    except Exception as e:
        log(f"❌ Error getting enhanced stats: {e}")

def log(msg, emoji=""):
    """سجل الأحداث المحسن"""
    msg_no_links = re.sub(r'https?://\S+|www\.\S+', '', msg).strip()
    if not msg_no_links:
        return
    
    log_textbox.configure(state="normal")
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # معلومات السرعة
    speed_info = ""
    if session_stats["start_time"] and session_stats["total_products"] > 0:
        elapsed = (datetime.now() - session_stats["start_time"]).total_seconds() / 60
        if elapsed > 0:
            speed = session_stats["total_products"] / elapsed
            speed_info = f" ({speed:.0f}/min)"
    
    # معلومات النظام الذكي
    smart_info = ""
    if session_stats["smart_filtered"] > 0:
        smart_info = f" | Smart: {session_stats['smart_filtered']}"
    
    log_textbox.insert("end", f"[{timestamp}] {emoji} {msg_no_links}{speed_info}{smart_info}\n")
    log_textbox.see("end")
    log_textbox.configure(state="disabled")
    
    # تحديث شريط العنوان
    if running[0]:
        root.title(f"Enhanced LAQTA - Processing... ({session_stats['total_products']} products{speed_info}{smart_info})")

def enhanced_add_alert_data(item, old_price, new_price, discount_percent, drop_detected=False):
    """إضافة بيانات التنبيه مع النظام الذكي"""
    asin = item.get("asin")
    key = f"{asin}-{int(new_price)}"
    if key in notified_asins:
        return
    notified_asins.add(key)
    
    # تطبيق النظام الذكي إذا كان مفعل
    is_smart_approved = False
    smart_score = 0
    
    if smart_filter_enabled[0] and SmartDealFilter:
        try:
            smart_filter = SmartDealFilter()
            
            # تحويل البيانات للتنسيق المطلوب
            product_for_analysis = {
                'asin': asin,
                'name': item.get('name', ''),
                'price': new_price,
                'strike_price': old_price,
                'discount_percent': discount_percent,
                'section': item.get('section', ''),
                'url': item.get('url', ''),
                'img': item.get('img', ''),
                'price_history': item.get('price_history', [])
            }
            
            # تحليل بالنظام الذكي
            filtered_deals = smart_filter.filter_deals_smart([product_for_analysis], target_count=1)
            
            if filtered_deals:
                is_smart_approved = True
                smart_score = filtered_deals[0].get('final_score', 0)
                session_stats["smart_filtered"] += 1
                
                log(f"🤖 Smart approved: {item.get('name', '')[:50]}... (Score: {smart_score:.1f})", "✅")
            else:
                log(f"🚫 Smart rejected: {item.get('name', '')[:50]}...", "❌")
                
        except Exception as e:
            log(f"⚠️ Smart filter error: {e}")
    
    # تحديث الإحصائيات
    session_stats["total_products"] += 1
    if is_smart_approved:
        session_stats["real_deals"] += 1
    else:
        session_stats["fake_deals"] += 1
    
    # حفظ في قاعدة البيانات مع النقاط الذكية
    if DB_MANAGER:
        try:
            cursor = DB_MANAGER.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO products 
                (asin, name, url, img, section, current_price, strike_price, 
                 discount_percent, smart_score, is_smart_approved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                asin, item.get('name', ''), item.get('url', ''), item.get('img', ''),
                item.get('section', ''), new_price, old_price, discount_percent,
                smart_score, is_smart_approved
            ))
            
            # إضافة للعروض المعتمدة إذا كان معتمد
            if is_smart_approved:
                cursor.execute('''
                    INSERT INTO approved_deals (asin, approval_date, smart_score, reasons)
                    VALUES (?, ?, ?, ?)
                ''', (asin, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), smart_score, 
                      f"Smart filter approved with score {smart_score:.1f}"))
            
            DB_MANAGER.connection.commit()
            
        except Exception as e:
            log(f"❌ Database error: {e}")
    
    # إضافة للقائمة المؤقتة (فقط العروض المعتمدة)
    if is_smart_approved:
        alerts_data.append({
            "item": item,
            "old_price": old_price,
            "new_price": new_price,
            "discount_percent": discount_percent,
            "drop_detected": drop_detected,
            "smart_score": smart_score,
            "timestamp": datetime.now()
        })
        
        # إرسال التنبيه للتليجرام (فقط العروض المعتمدة)
        if telegram_alerts_enabled[0]:
            enhanced_message = f"🤖 AI Approved Deal (Score: {smart_score:.1f})\n"
            threading.Thread(
                target=send_enhanced_telegram_alert, 
                args=(item, old_price, new_price, discount_percent, drop_detected, smart_score), 
                daemon=True
            ).start()

def send_enhanced_telegram_alert(item, old_price, new_price, discount_percent, drop_detected, smart_score):
    """إرسال تنبيه محسن للتليجرام"""
    try:
        # تحميل إعدادات التليجرام
        with open('telegram_config.json', 'r') as f:
            config = json.load(f)
        
        bot_token = config.get('bot_token')
        users = config.get('users', [])
        
        if not bot_token or not users:
            return
        
        # تنسيق الرسالة المحسنة
        name = item.get('name', 'منتج')[:60]
        savings = old_price - new_price
        
        message = f"""🤖 <b>عرض معتمد بالذكاء الاصطناعي</b>
        
📦 <b>{name}</b>
💰 السعر: <b>{new_price:.0f} جنيه</b>
🏷️ السعر الأصلي: <s>{old_price:.0f} جنيه</s>
🎉 الخصم: <b>{discount_percent:.1f}%</b>
💸 التوفير: <b>{savings:.0f} جنيه</b>
⭐ نقاط الجودة: <b>{smart_score:.1f}/100</b>

🔗 <a href="{item.get('url', '')}">رابط المنتج</a>

🤖 <i>تم اعتماد هذا العرض بواسطة النظام الذكي</i>"""
        
        # إرسال للمستخدمين
        for user_id in users:
            try:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                data = {
                    'chat_id': user_id,
                    'text': message,
                    'parse_mode': 'HTML',
                    'disable_web_page_preview': False
                }
                requests.post(url, data=data, timeout=10)
            except Exception as e:
                print(f"خطأ إرسال تليجرام: {e}")
                
    except Exception as e:
        print(f"خطأ في التنبيه المحسن: {e}")

# فئات محسنة مع المزيد من الصفحات
ENHANCED_CATEGORIES = {
    'Electronics': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18018102031%2Cp_98%3A21909049031&dc&page={}&language=en",
    'Home & Kitchen': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18021933031%2Cp_98%3A21909049031&dc&page={}&language=en",
    'Beauty': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18017988031%2Cp_98%3A21909049031&dc&page={}&language=en",
    'Health & Household Products': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18021875031%2Cp_98%3A21909049031&dc&page={}&language=en",
    'Tools & Home Improvement': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18021990031%2Cp_98%3A21909049031&dc&page={}&language=en",
    'Automotive': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18017874031%2Cp_98%3A21909049031&dc&page={}&language=en",
    'Fashion': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18018165031%2Cp_98%3A21909049031&dc&page={}&language=en",
    'Grocery': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18020637031%2Cp_98%3A21909049031&dc&page={}&language=en"
}

def safe_scrape_section_enhanced(section, start_page=1, end_page=10):
    """كشط محسن وآمن"""
    
    if section not in ENHANCED_CATEGORIES:
        log(f"❌ Unknown section: {section}")
        return {}
    
    section_url = ENHANCED_CATEGORIES[section]
    products = {}
    
    log(f"🔍 Starting enhanced scraping: {section} (pages {start_page}-{end_page})")
    
    for page in range(start_page, end_page + 1):
        if stop_flag.get("stop"):
            break
            
        try:
            url = section_url.format(page)
            log(f"📄 Scraping page {page}: {section}")
            
            # هنا نستخدم requests بدلاً من playwright لتجنب المشاكل
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                # استخراج المنتجات من HTML
                page_products = extract_products_from_html(response.text, section)
                
                for asin, product_data in page_products.items():
                    if asin not in products:
                        products[asin] = product_data
                        
                        # تطبيق النظام الذكي فوراً
                        if smart_filter_enabled[0]:
                            apply_smart_filter_to_product(asin, product_data)
                
                log(f"✅ Page {page}: {len(page_products)} products found")
                
            else:
                log(f"⚠️ Page {page}: HTTP {response.status_code}")
            
            # تأخير بين الصفحات
            time.sleep(2)
            
        except Exception as e:
            log(f"❌ Error scraping page {page}: {e}")
            continue
    
    log(f"🎯 Section {section} completed: {len(products)} total products")
    return products

def extract_products_from_html(html_content, section):
    """استخراج المنتجات من HTML"""
    products = {}
    
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # البحث عن المنتجات
        items = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        for item in items:
            try:
                # ASIN
                asin = item.get('data-asin')
                if not asin:
                    continue
                
                # الاسم
                title_elem = item.find('h2')
                name = title_elem.get_text(strip=True) if title_elem else "Unknown"
                
                # السعر الحالي
                price_elem = item.find('span', class_='a-price-whole')
                if not price_elem:
                    price_elem = item.find('span', class_='a-offscreen')
                
                price = None
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = parse_price_safe(price_text)
                
                if not price or price <= 0:
                    continue
                
                # السعر الأصلي
                strike_elem = item.find('span', class_='a-text-price')
                strike_price = None
                if strike_elem:
                    strike_text = strike_elem.get_text(strip=True)
                    strike_price = parse_price_safe(strike_text)
                
                # حساب الخصم
                discount_percent = 0
                if strike_price and strike_price > price:
                    discount_percent = ((strike_price - price) / strike_price) * 100
                
                # فلترة أولية
                if discount_percent >= ALERT_DISCOUNT:
                    
                    # الرابط
                    link_elem = item.find('a')
                    url = ""
                    if link_elem and link_elem.get('href'):
                        url = "https://www.amazon.eg" + link_elem.get('href')
                    
                    # الصورة
                    img_elem = item.find('img')
                    img = img_elem.get('src') if img_elem else ""
                    
                    products[asin] = {
                        'name': name,
                        'url': url,
                        'img': img,
                        'section': section,
                        'price': price,
                        'strike_price': strike_price,
                        'discount_percent': discount_percent,
                        'price_history': []
                    }
                    
            except Exception as e:
                continue
                
    except ImportError:
        log("⚠️ BeautifulSoup not available, using basic parsing")
        # تحليل أساسي بدون BeautifulSoup
        pass
    except Exception as e:
        log(f"❌ HTML parsing error: {e}")
    
    return products

def parse_price_safe(price_text):
    """تحليل آمن للأسعار"""
    try:
        # إزالة الرموز والفواصل
        cleaned = re.sub(r'[^\d.]', '', price_text.replace(',', ''))
        return float(cleaned) if cleaned else None
    except:
        return None

def apply_smart_filter_to_product(asin, product_data):
    """تطبيق النظام الذكي على منتج واحد"""
    
    if not SmartDealFilter:
        return False
    
    try:
        smart_filter = SmartDealFilter()
        
        # تحويل للتنسيق المطلوب
        product_for_analysis = {
            'asin': asin,
            'name': product_data.get('name', ''),
            'price': product_data.get('price', 0),
            'strike_price': product_data.get('strike_price', 0),
            'discount_percent': product_data.get('discount_percent', 0),
            'section': product_data.get('section', ''),
            'url': product_data.get('url', ''),
            'img': product_data.get('img', ''),
            'price_history': product_data.get('price_history', [])
        }
        
        # تحليل
        filtered_deals = smart_filter.filter_deals_smart([product_for_analysis], target_count=1)
        
        if filtered_deals:
            score = filtered_deals[0].get('final_score', 0)
            
            # حفظ في قاعدة البيانات
            if DB_MANAGER:
                cursor = DB_MANAGER.connection.cursor()
                cursor.execute('''
                    UPDATE products 
                    SET smart_score = ?, is_smart_approved = 1 
                    WHERE asin = ?
                ''', (score, asin))
                DB_MANAGER.connection.commit()
            
            return True
        
    except Exception as e:
        log(f"⚠️ Smart filter error for {asin}: {e}")
    
    return False

# الواجهة الرئيسية المحسنة
class EnhancedAmmzGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.setup_enhanced_gui()
        
    def setup_enhanced_gui(self):
        """إعداد الواجهة المحسنة"""
        
        self.root.title("Enhanced LAQTA - Smart Deals System")
        self.root.geometry("1200x800")
        
        # الإطار الرئيسي
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # شريط التحكم العلوي
        self.setup_enhanced_controls(main_frame)
        
        # منطقة السجل
        self.setup_enhanced_log(main_frame)
        
        # شريط الحالة السفلي
        self.setup_enhanced_status(main_frame)
        
        # تهيئة قاعدة البيانات
        initialize_enhanced_database()
    
    def setup_enhanced_controls(self, parent):
        """إعداد أزرار التحكم المحسنة"""
        
        controls_frame = ctk.CTkFrame(parent)
        controls_frame.pack(fill="x", padx=5, pady=5)
        
        # زر البدء المحسن
        self.start_btn = ctk.CTkButton(
            controls_frame,
            text="🚀 Start Smart Scraping",
            command=self.start_enhanced_scraping,
            font=("Arial", 14, "bold"),
            height=40,
            fg_color="#00ff88"
        )
        self.start_btn.pack(side="left", padx=5)
        
        # زر الإيقاف
        self.stop_btn = ctk.CTkButton(
            controls_frame,
            text="⏹️ Stop",
            command=self.stop_scraping,
            font=("Arial", 14, "bold"),
            height=40,
            fg_color="#ff4444"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        # تفعيل/إلغاء النظام الذكي
        self.smart_filter_var = ctk.BooleanVar(value=True)
        self.smart_filter_checkbox = ctk.CTkCheckBox(
            controls_frame,
            text="🤖 Smart Filter",
            variable=self.smart_filter_var,
            command=self.toggle_smart_filter,
            font=("Arial", 12, "bold")
        )
        self.smart_filter_checkbox.pack(side="left", padx=10)
        
        # عرض العروض المعتمدة
        self.show_deals_btn = ctk.CTkButton(
            controls_frame,
            text="📋 Show Approved Deals",
            command=self.show_approved_deals,
            font=("Arial", 12, "bold"),
            height=40
        )
        self.show_deals_btn.pack(side="left", padx=5)
        
        # إحصائيات مباشرة
        self.stats_label = ctk.CTkLabel(
            controls_frame,
            text="📊 Ready to start...",
            font=("Arial", 12, "bold")
        )
        self.stats_label.pack(side="right", padx=10)
    
    def setup_enhanced_log(self, parent):
        """إعداد منطقة السجل المحسنة"""
        
        log_frame = ctk.CTkFrame(parent)
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        global log_textbox
        log_textbox = ctk.CTkTextbox(
            log_frame,
            font=("Consolas", 11),
            wrap="word"
        )
        log_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        # رسالة ترحيب محسنة
        welcome_msg = """🤖 Enhanced LAQTA - Smart Deals System
        
✨ المميزات الجديدة:
• 🧠 فلترة ذكية للعروض الحقيقية
• 🎯 نظام نقاط متطور (1-100)
• 🤖 اعتماد تلقائي للعروض الموثوقة
• 📊 إحصائيات مفصلة ومباشرة
• 🚀 أداء محسن وسرعة عالية

🎯 الهدف: تحويل 1000+ عرض وهمي إلى 15 عرض موثوق يومياً

اضغط 'Start Smart Scraping' للبدء!"""
        
        log_textbox.insert("end", welcome_msg)
        log_textbox.configure(state="disabled")
    
    def setup_enhanced_status(self, parent):
        """إعداد شريط الحالة المحسن"""
        
        status_frame = ctk.CTkFrame(parent)
        status_frame.pack(fill="x", padx=5, pady=5)
        
        # شريط التقدم
        global progress_bar
        progress_bar = ctk.CTkProgressBar(status_frame)
        progress_bar.pack(side="left", fill="x", expand=True, padx=5)
        progress_bar.set(0)
        
        # معلومات الحالة
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready",
            font=("Arial", 11, "bold")
        )
        self.status_label.pack(side="right", padx=10)
    
    def start_enhanced_scraping(self):
        """بدء الكشط المحسن"""
        
        if running[0]:
            log("⚠️ Scraping already running!", "🔄")
            return
        
        running[0] = True
        stop_flag["stop"] = False
        session_stats["start_time"] = datetime.now()
        session_stats["total_products"] = 0
        session_stats["smart_filtered"] = 0
        
        log("🚀 Starting enhanced smart scraping...", "✅")
        
        # تشغيل في thread منفصل
        scrape_thread = threading.Thread(
            target=self.run_enhanced_scraping,
            daemon=True
        )
        scrape_thread.start()
    
    def run_enhanced_scraping(self):
        """تشغيل الكشط المحسن"""
        
        try:
            for section_name in ENHANCED_CATEGORIES.keys():
                if stop_flag.get("stop"):
                    break
                
                session_stats["current_section"] = section_name
                log(f"🔍 Processing section: {section_name}")
                
                # كشط أكثر صفحات للحصول على منتجات أكثر
                section_products = safe_scrape_section_enhanced(section_name, 1, 15)
                
                log(f"✅ {section_name}: {len(section_products)} products processed")
                
                # تحديث شريط التقدم
                progress = (list(ENHANCED_CATEGORIES.keys()).index(section_name) + 1) / len(ENHANCED_CATEGORIES) * 100
                self.root.after(0, lambda p=progress: progress_bar.set(p/100))
                
                time.sleep(3)  # تأخير بين الأقسام
            
            # انتهاء الكشط
            self.finalize_enhanced_scraping()
            
        except Exception as e:
            log(f"❌ Enhanced scraping error: {e}")
        finally:
            running[0] = False
            stop_flag["stop"] = False
    
    def finalize_enhanced_scraping(self):
        """إنهاء الكشط وعرض النتائج"""
        
        log("🎯 Finalizing enhanced scraping...")
        
        # جلب العروض المعتمدة من قاعدة البيانات
        if DB_MANAGER:
            try:
                cursor = DB_MANAGER.connection.cursor()
                cursor.execute('''
                    SELECT * FROM products 
                    WHERE is_smart_approved = 1 
                    ORDER BY smart_score DESC 
                    LIMIT 15
                ''')
                
                approved_deals = cursor.fetchall()
                
                if approved_deals:
                    log(f"🏆 Found {len(approved_deals)} approved deals!")
                    
                    # إرسال للتليجرام
                    self.send_daily_report(approved_deals)
                    
                    # عرض النتائج
                    self.show_final_results(approved_deals)
                else:
                    log("❌ No deals met the smart criteria today")
                    
            except Exception as e:
                log(f"❌ Error finalizing: {e}")
        
        # إعادة تعيين
        progress_bar.set(0)
        self.root.title("Enhanced LAQTA - Smart Deals System")
        log("✅ Enhanced scraping completed!")
    
    def send_daily_report(self, approved_deals):
        """إرسال التقرير اليومي المحسن"""
        
        if not approved_deals:
            return
        
        try:
            with open('telegram_config.json', 'r') as f:
                config = json.load(f)
            
            bot_token = config.get('bot_token')
            users = config.get('users', [])
            
            if not bot_token or not users:
                return
            
            # تنسيق التقرير
            report = f"🎯 <b>التقرير اليومي - {datetime.now().strftime('%Y-%m-%d')}</b>\n"
            report += f"🤖 <b>عروض معتمدة بالذكاء الاصطناعي: {len(approved_deals)}</b>\n\n"
            
            for i, deal in enumerate(approved_deals[:10], 1):  # أول 10 عروض
                name = deal[1][:50] + "..." if len(deal[1]) > 50 else deal[1]
                price = deal[5]
                discount = deal[7]
                score = deal[8]
                
                report += f"<b>{i}. {name}</b>\n"
                report += f"💰 {price:.0f} جنيه | 🎉 {discount:.1f}% | ⭐ {score:.1f}\n\n"
            
            report += "🤖 <i>تم اختيار هذه العروض بواسطة النظام الذكي</i>"
            
            # إرسال للمستخدمين
            for user_id in users:
                try:
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    data = {
                        'chat_id': user_id,
                        'text': report,
                        'parse_mode': 'HTML'
                    }
                    requests.post(url, data=data, timeout=10)
                    log(f"📱 Daily report sent to user {user_id}")
                except Exception as e:
                    log(f"❌ Failed to send report: {e}")
                    
        except Exception as e:
            log(f"❌ Report generation error: {e}")
    
    def show_final_results(self, approved_deals):
        """عرض النتائج النهائية"""
        
        results_text = f"\n🏆 نتائج اليوم ({len(approved_deals)} عرض معتمد):\n"
        results_text += "=" * 60 + "\n"
        
        for i, deal in enumerate(approved_deals, 1):
            name = deal[1][:45] + "..." if len(deal[1]) > 45 else deal[1]
            results_text += f"{i:2d}. {name}\n"
            results_text += f"    💰 {deal[5]:.0f} جنيه | 🎉 {deal[7]:.1f}% | ⭐ {deal[8]:.1f}\n"
        
        log_textbox.configure(state="normal")
        log_textbox.insert("end", results_text)
        log_textbox.see("end")
        log_textbox.configure(state="disabled")
    
    def toggle_smart_filter(self):
        """تفعيل/إلغاء النظام الذكي"""
        smart_filter_enabled[0] = self.smart_filter_var.get()
        status = "enabled" if smart_filter_enabled[0] else "disabled"
        log(f"🤖 Smart filter {status}")
    
    def stop_scraping(self):
        """إيقاف الكشط"""
        stop_flag["stop"] = True
        running[0] = False
        log("⏹️ Stopping scraping...", "🛑")
    
    def show_approved_deals(self):
        """عرض العروض المعتمدة"""
        
        if not DB_MANAGER:
            log("❌ Database not initialized")
            return
        
        try:
            cursor = DB_MANAGER.connection.cursor()
            cursor.execute('''
                SELECT name, current_price, discount_percent, smart_score, url
                FROM products 
                WHERE is_smart_approved = 1 
                ORDER BY smart_score DESC 
                LIMIT 20
            ''')
            
            deals = cursor.fetchall()
            
            if deals:
                deals_text = f"\n📋 العروض المعتمدة ({len(deals)}):\n"
                deals_text += "-" * 50 + "\n"
                
                for i, deal in enumerate(deals, 1):
                    name = deal[0][:40] + "..." if len(deal[0]) > 40 else deal[0]
                    deals_text += f"{i:2d}. {name}\n"
                    deals_text += f"    💰 {deal[1]:.0f} جنيه | 🎉 {deal[2]:.1f}% | ⭐ {deal[3]:.1f}\n"
                
                log_textbox.configure(state="normal")
                log_textbox.insert("end", deals_text)
                log_textbox.see("end")
                log_textbox.configure(state="disabled")
            else:
                log("📭 No approved deals found")
                
        except Exception as e:
            log(f"❌ Error showing deals: {e}")
    
    def run(self):
        """تشغيل الواجهة"""
        self.root.mainloop()

# متغيرات عامة للواجهة
root = None
log_textbox = None
progress_bar = None

def create_enhanced_gui():
    """إنشاء الواجهة المحسنة"""
    
    global root, log_textbox, progress_bar
    
    app = EnhancedAmmzGUI()
    root = app.root
    
    return app

if __name__ == "__main__":
    # تشغيل الواجهة المحسنة
    app = create_enhanced_gui()
    app.run()