# enhanced_amz_scraper.py
import sqlite3
import requests
import json
import time
import random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# إعداد الـ logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    """مدير قاعدة البيانات المحسن مع دعم SQLite"""
    
    def __init__(self, db_file="amz_products.db"):
        self.db_file = db_file
        self.connection = None
        self.lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        """إنشاء قاعدة البيانات والجداول"""
        try:
            self.connection = sqlite3.connect(self.db_file, check_same_thread=False)
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=50000")
            
            # جدول المنتجات الرئيسي
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
                    ai_verified BOOLEAN DEFAULT FALSE,
                    ai_score REAL DEFAULT 0,
                    ai_analysis TEXT,
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
                    source TEXT DEFAULT 'amazon',
                    FOREIGN KEY (asin) REFERENCES products (asin)
                )
            ''')
            
            # جدول مقارنة الأسعار من المواقع المختلفة
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS price_comparison (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT,
                    asin TEXT,
                    site_name TEXT,
                    price REAL,
                    url TEXT,
                    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asin) REFERENCES products (asin)
                )
            ''')
            
            # جدول تحليل AI
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS ai_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asin TEXT,
                    analysis_type TEXT,
                    result TEXT,
                    confidence_score REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asin) REFERENCES products (asin)
                )
            ''')
            
            # إنشاء الفهارس
            self.connection.execute('CREATE INDEX IF NOT EXISTS idx_products_price ON products (current_price)')
            self.connection.execute('CREATE INDEX IF NOT EXISTS idx_products_discount ON products (discount_percent)')
            self.connection.execute('CREATE INDEX IF NOT EXISTS idx_products_ai_score ON products (ai_score)')
            self.connection.execute('CREATE INDEX IF NOT EXISTS idx_price_history_asin ON price_history (asin)')
            self.connection.execute('CREATE INDEX IF NOT EXISTS idx_price_comparison_asin ON price_comparison (asin)')
            
            self.connection.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def insert_product(self, product_data):
        """إدراج أو تحديث منتج"""
        try:
            with self.lock:
                cursor = self.connection.cursor()
                
                # التحقق من وجود المنتج
                cursor.execute('SELECT asin FROM products WHERE asin = ?', (product_data['asin'],))
                exists = cursor.fetchone()
                
                if exists:
                    # تحديث المنتج الموجود
                    cursor.execute('''
                        UPDATE products SET 
                        name = ?, url = ?, img = ?, section = ?, 
                        current_price = ?, strike_price = ?, discount_percent = ?,
                        last_updated = CURRENT_TIMESTAMP
                        WHERE asin = ?
                    ''', (
                        product_data.get('name'),
                        product_data.get('url'),
                        product_data.get('img'),
                        product_data.get('section'),
                        product_data.get('price'),
                        product_data.get('strike_price'),
                        product_data.get('discount_percent'),
                        product_data['asin']
                    ))
                else:
                    # إدراج منتج جديد
                    cursor.execute('''
                        INSERT INTO products 
                        (asin, name, url, img, section, current_price, strike_price, discount_percent)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        product_data['asin'],
                        product_data.get('name'),
                        product_data.get('url'),
                        product_data.get('img'),
                        product_data.get('section'),
                        product_data.get('price'),
                        product_data.get('strike_price'),
                        product_data.get('discount_percent')
                    ))
                
                # إضافة تاريخ السعر
                if product_data.get('price'):
                    cursor.execute('''
                        INSERT INTO price_history (asin, price, date, time)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        product_data['asin'],
                        product_data['price'],
                        datetime.now().strftime('%Y-%m-%d'),
                        datetime.now().strftime('%H:%M')
                    ))
                
                self.connection.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error inserting product: {e}")
            return False
    
    def get_products_for_ai_analysis(self, limit=50):
        """الحصول على منتجات تحتاج تحليل AI"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM products 
                WHERE ai_verified = FALSE OR ai_verified IS NULL
                AND discount_percent > 15
                ORDER BY discount_percent DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in cursor.description]
            products = []
            for row in cursor.fetchall():
                products.append(dict(zip(columns, row)))
            
            return products
            
        except Exception as e:
            logger.error(f"Error getting products for AI analysis: {e}")
            return []
    
    def update_ai_analysis(self, asin, ai_score, analysis, verified=True):
        """تحديث تحليل AI للمنتج"""
        try:
            with self.lock:
                cursor = self.connection.cursor()
                cursor.execute('''
                    UPDATE products SET 
                    ai_verified = ?, ai_score = ?, ai_analysis = ?
                    WHERE asin = ?
                ''', (verified, ai_score, analysis, asin))
                
                # حفظ تحليل AI في جدول منفصل
                cursor.execute('''
                    INSERT INTO ai_analysis (asin, analysis_type, result, confidence_score)
                    VALUES (?, ?, ?, ?)
                ''', (asin, 'deal_verification', analysis, ai_score))
                
                self.connection.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating AI analysis: {e}")
            return False

def scrape_section_enhanced(section_name, section_url, start_page=1, end_page=5, db=None, stop_flag=None):
    """نسخة محسنة من scraper مع دعم قاعدة البيانات"""
    
    if not db:
        db = DatabaseManager()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection': 'keep-alive',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    total_products = 0
    
    for page in range(start_page, end_page + 1):
        if stop_flag and stop_flag.get('stop', False):
            break
            
        try:
            url = section_url.format(page)
            logger.info(f"Scraping {section_name} - Page {page}")
            
            response = session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            for product in products:
                if stop_flag and stop_flag.get('stop', False):
                    break
                
                try:
                    # استخراج ASIN
                    asin_element = product.get('data-asin')
                    if not asin_element:
                        continue
                    
                    # استخراج اسم المنتج
                    name_element = product.find('h2', class_='a-size-mini')
                    if not name_element:
                        name_element = product.find('span', class_='a-size-base-plus')
                    name = name_element.get_text(strip=True) if name_element else "Unknown Product"
                    
                    # استخراج الرابط
                    link_element = product.find('h2', class_='a-size-mini')
                    if link_element:
                        link_element = link_element.find('a')
                    if not link_element:
                        link_element = product.find('a', class_='a-link-normal')
                    
                    url = urljoin('https://www.amazon.eg', link_element['href']) if link_element else ""
                    
                    # استخراج الصورة
                    img_element = product.find('img', class_='s-image')
                    img_url = img_element['src'] if img_element else ""
                    
                    # استخراج السعر
                    current_price = 0
                    strike_price = None
                    discount_percent = 0
                    
                    # السعر الحالي
                    price_element = product.find('span', class_='a-price-whole')
                    if price_element:
                        price_text = price_element.get_text(strip=True).replace(',', '')
                        try:
                            current_price = float(price_text)
                        except ValueError:
                            current_price = 0
                    
                    # السعر المشطوب
                    strike_element = product.find('span', class_='a-price a-text-price')
                    if strike_element:
                        strike_text = strike_element.get_text(strip=True).replace('EGP', '').replace(',', '').strip()
                        try:
                            strike_price = float(re.findall(r'[\d.]+', strike_text)[0])
                        except (ValueError, IndexError):
                            strike_price = None
                    
                    # حساب نسبة الخصم
                    if current_price > 0 and strike_price and strike_price > current_price:
                        discount_percent = ((strike_price - current_price) / strike_price) * 100
                    
                    # إنشاء بيانات المنتج
                    product_data = {
                        'asin': asin_element,
                        'name': name,
                        'url': url,
                        'img': img_url,
                        'section': section_name,
                        'price': current_price,
                        'strike_price': strike_price,
                        'discount_percent': discount_percent
                    }
                    
                    # حفظ في قاعدة البيانات
                    if db.insert_product(product_data):
                        total_products += 1
                        logger.info(f"Product saved: {name[:50]}... - {discount_percent:.1f}% off")
                    
                except Exception as e:
                    logger.error(f"Error processing product: {e}")
                    continue
            
            # تأخير بين الطلبات
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            logger.error(f"Error scraping page {page}: {e}")
            continue
    
    logger.info(f"Scraping completed. Total products: {total_products}")
    return total_products

def export_to_json(db_file="amz_products.db", output_file="exported_products.json"):
    """تصدير البيانات من SQLite إلى JSON"""
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products ORDER BY ai_score DESC, discount_percent DESC')
        columns = [description[0] for description in cursor.description]
        
        products = {}
        for row in cursor.fetchall():
            product = dict(zip(columns, row))
            asin = product['asin']
            
            # الحصول على تاريخ الأسعار
            cursor.execute('''
                SELECT price, date, time FROM price_history 
                WHERE asin = ? ORDER BY date DESC, time DESC
            ''', (asin,))
            
            price_history = []
            for price_row in cursor.fetchall():
                price_history.append({
                    'price': price_row[0],
                    'date': price_row[1],
                    'time': price_row[2]
                })
            
            product['price_history'] = price_history
            products[asin] = product
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        
        conn.close()
        logger.info(f"Data exported to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        return False

if __name__ == "__main__":
    # اختبار النظام
    db = DatabaseManager()
    print("Database manager initialized successfully!")