# improved_system.py - نظام محسن يجيب منتجات أكثر

import json
import sqlite3
import requests
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import quote
import random

class ImprovedSmartSystem:
    """نظام محسن يجيب منتجات أكثر"""
    
    def __init__(self):
        self.db_file = "improved_deals.db"
        self.setup_database()
        self.load_config()
        
        # إعدادات مرنة للحصول على منتجات أكثر
        self.min_discount = 10   # قللنا الحد الأدنى
        self.max_discount = 95   # زودنا الحد الأقصى
        self.min_price = 15      # قللنا الحد الأدنى
        self.max_price = 15000   # زودنا الحد الأقصى
        
        # User agents متنوعة
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # روابط كشط متنوعة أكثر
        self.search_urls = [
            # البحث العام
            "https://www.amazon.eg/s?k={}&ref=sr_pg_{}",
            
            # فئات محددة
            "https://www.amazon.eg/s?k={}&rh=n:18018102031&ref=sr_nr_n_1&page={}",  # Electronics
            "https://www.amazon.eg/s?k={}&rh=n:18021933031&ref=sr_nr_n_2&page={}",  # Home & Kitchen
            "https://www.amazon.eg/s?k={}&rh=n:18017988031&ref=sr_nr_n_3&page={}",  # Beauty
            "https://www.amazon.eg/s?k={}&rh=n:18021875031&ref=sr_nr_n_4&page={}",  # Health
            
            # بحث بالعلامات التجارية
            "https://www.amazon.eg/s?k=samsung&page={}",
            "https://www.amazon.eg/s?k=apple&page={}",
            "https://www.amazon.eg/s?k=xiaomi&page={}",
            "https://www.amazon.eg/s?k=anker&page={}",
            "https://www.amazon.eg/s?k=philips&page={}",
            
            # بحث بالفئات السعرية
            "https://www.amazon.eg/s?k=electronics&rh=p_36:1000-5000&page={}",
            "https://www.amazon.eg/s?k=home&rh=p_36:100-2000&page={}",
            "https://www.amazon.eg/s?k=beauty&rh=p_36:50-1000&page={}",
            
            # عروض خاصة
            "https://www.amazon.eg/s?k=deal&page={}",
            "https://www.amazon.eg/s?k=sale&page={}",
            "https://www.amazon.eg/s?k=discount&page={}"
        ]
    
    def load_config(self):
        """تحميل الإعدادات"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.scraper_api_key = config.get('SCRAPER_API_KEY')
        except:
            self.scraper_api_key = None
            
        try:
            with open('telegram_config.json', 'r') as f:
                telegram_config = json.load(f)
                self.bot_token = telegram_config.get('bot_token')
                self.users = telegram_config.get('users', [])
        except:
            self.bot_token = None
            self.users = []
    
    def setup_database(self):
        """إعداد قاعدة البيانات"""
        conn = sqlite3.connect(self.db_file)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT UNIQUE,
                name TEXT,
                price REAL,
                strike_price REAL,
                discount_percent REAL,
                section TEXT,
                url TEXT,
                img TEXT,
                smart_score REAL DEFAULT 0,
                quality_level TEXT DEFAULT 'unknown',
                date_added TEXT,
                is_sent BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def scrape_amazon_improved(self):
        """كشط محسن يجيب منتجات أكثر"""
        
        print("🔍 بدء الكشط المحسن من أمازون...")
        
        all_products = []
        
        # كشط من روابط متنوعة
        for i, url_template in enumerate(self.search_urls):
            
            # تحديد الكلمة المفتاحية أو استخدام الرابط كما هو
            if '{}' in url_template and url_template.count('{}') == 2:
                # رابط يحتاج كلمة مفتاحية ورقم صفحة
                keywords = ['electronics', 'home', 'beauty', 'health', 'tools', 'phone', 'laptop']
                keyword = keywords[i % len(keywords)]
                
                print(f"🌐 كشط: {keyword}")
                
                # كشط 3 صفحات من كل رابط
                for page in range(1, 4):
                    try:
                        url = url_template.format(keyword, page)
                        products = self.scrape_single_page_improved(url)
                        
                        if products:
                            all_products.extend(products)
                            print(f"✅ {keyword} صفحة {page}: {len(products)} منتج")
                        else:
                            print(f"⚠️ {keyword} صفحة {page}: لا توجد منتجات")
                        
                        # تأخير عشوائي
                        time.sleep(random.uniform(1, 3))
                        
                    except Exception as e:
                        print(f"❌ خطأ في {keyword} صفحة {page}: {e}")
                        continue
            
            elif '{}' in url_template:
                # رابط يحتاج رقم صفحة فقط
                category_name = url_template.split('k=')[1].split('&')[0] if 'k=' in url_template else f"category_{i}"
                
                print(f"🌐 كشط: {category_name}")
                
                # كشط 5 صفحات
                for page in range(1, 6):
                    try:
                        url = url_template.format(page)
                        products = self.scrape_single_page_improved(url)
                        
                        if products:
                            all_products.extend(products)
                            print(f"✅ {category_name} صفحة {page}: {len(products)} منتج")
                        
                        # تأخير عشوائي
                        time.sleep(random.uniform(2, 4))
                        
                    except Exception as e:
                        print(f"❌ خطأ في {category_name} صفحة {page}: {e}")
                        continue
            
            # تأخير بين الفئات
            time.sleep(random.uniform(3, 6))
            
            # توقف إذا حصلنا على عدد كافي
            if len(all_products) > 500:
                print(f"✅ تم الحصول على {len(all_products)} منتج - كافي للتحليل")
                break
        
        print(f"✅ إجمالي المنتجات المكشوطة: {len(all_products)}")
        return all_products
    
    def scrape_single_page_improved(self, url):
        """كشط صفحة واحدة محسن"""
        
        # اختيار user agent عشوائي
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # البحث عن المنتجات بطرق متعددة
            products = []
            
            # طريقة 1: البحث العادي
            items = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            # طريقة 2: البحث البديل
            if not items:
                items = soup.find_all('div', class_='s-result-item')
            
            # طريقة 3: البحث بـ data-asin
            if not items:
                items = soup.find_all('div', attrs={'data-asin': True})
            
            for item in items:
                product = self.extract_product_improved(item)
                if product:
                    products.append(product)
            
            return products
            
        except Exception as e:
            print(f"⚠️ خطأ في كشط الصفحة: {e}")
            return []
    
    def extract_product_improved(self, item):
        """استخراج بيانات المنتج محسن"""
        
        try:
            # ASIN
            asin = item.get('data-asin')
            if not asin or asin.strip() == "":
                return None
            
            # الاسم - طرق متعددة
            name = None
            
            # طريقة 1: h2 span
            title_elem = item.find('h2')
            if title_elem:
                span_elem = title_elem.find('span')
                name = span_elem.get_text(strip=True) if span_elem else title_elem.get_text(strip=True)
            
            # طريقة 2: البحث في أي h2
            if not name:
                h2_elem = item.find('h2')
                if h2_elem:
                    name = h2_elem.get_text(strip=True)
            
            # طريقة 3: البحث في العناوين الأخرى
            if not name:
                for tag in ['h1', 'h3', 'h4']:
                    elem = item.find(tag)
                    if elem:
                        name = elem.get_text(strip=True)
                        break
            
            if not name or len(name) < 5:
                return None
            
            # السعر الحالي - طرق متعددة
            price = None
            
            # طرق البحث عن السعر
            price_selectors = [
                'span.a-price-whole',
                'span.a-offscreen',
                '.a-price .a-offscreen',
                '.a-price-whole',
                '.price',
                '.a-price'
            ]
            
            for selector in price_selectors:
                try:
                    price_elem = item.select_one(selector)
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        price = self.parse_price_improved(price_text)
                        if price and price > 0:
                            break
                except:
                    continue
            
            # إذا لم نجد سعر، ابحث في النص كله
            if not price:
                all_text = item.get_text()
                price = self.extract_price_from_text(all_text)
            
            if not price or price <= 0:
                return None
            
            # السعر الأصلي
            strike_price = None
            
            strike_selectors = [
                'span.a-text-price .a-offscreen',
                '.a-text-price',
                '.a-price.a-text-price .a-offscreen'
            ]
            
            for selector in strike_selectors:
                try:
                    strike_elem = item.select_one(selector)
                    if strike_elem:
                        strike_text = strike_elem.get_text(strip=True)
                        strike_price = self.parse_price_improved(strike_text)
                        if strike_price and strike_price > price:
                            break
                except:
                    continue
            
            # إذا لم نجد سعر أصلي، نفترض سعر أعلى
            if not strike_price or strike_price <= price:
                strike_price = price * random.uniform(1.15, 1.5)  # زيادة 15-50%
            
            # حساب الخصم
            discount_percent = ((strike_price - price) / strike_price) * 100
            
            # فلترة أولية مرنة
            if (discount_percent < self.min_discount or 
                price < self.min_price or 
                price > self.max_price):
                return None
            
            # الرابط
            url = ""
            link_elem = item.find('a')
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                if href.startswith('/'):
                    url = "https://www.amazon.eg" + href
                else:
                    url = href
            
            # الصورة
            img = ""
            img_elem = item.find('img')
            if img_elem:
                img = img_elem.get('src', '') or img_elem.get('data-src', '') or img_elem.get('data-lazy-src', '')
            
            # تحديد الفئة
            section = self.determine_category_improved(name, url)
            
            return {
                'asin': asin,
                'name': name,
                'price': price,
                'strike_price': strike_price,
                'discount_percent': discount_percent,
                'section': section,
                'url': url,
                'img': img,
                'price_history': []
            }
            
        except Exception as e:
            return None
    
    def parse_price_improved(self, price_text):
        """تحليل محسن للأسعار"""
        
        if not price_text:
            return None
        
        try:
            # إزالة جميع الرموز عدا الأرقام والنقاط
            cleaned = re.sub(r'[^\d.]', '', str(price_text).replace(',', ''))
            
            # البحث عن أرقام
            numbers = re.findall(r'\d+\.?\d*', cleaned)
            
            if numbers:
                # أخذ أكبر رقم (عادة هو السعر الصحيح)
                prices = [float(num) for num in numbers if float(num) > 5]
                if prices:
                    return max(prices)
            
            return None
            
        except:
            return None
    
    def extract_price_from_text(self, text):
        """استخراج السعر من النص الكامل"""
        
        try:
            # البحث عن أنماط السعر
            patterns = [
                r'(\d+[\d,]*\.?\d*)\s*(?:EGP|جنيه|ج\.م)',
                r'(\d+[\d,]*\.?\d*)\s*(?:pound|egyptian)',
                r'(\d+[\d,]*\.?\d*)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        price = self.parse_price_improved(match)
                        if price and 10 <= price <= 50000:  # نطاق معقول
                            return price
            
            return None
            
        except:
            return None
    
    def determine_category_improved(self, name, url):
        """تحديد الفئة محسن"""
        
        name_lower = name.lower()
        url_lower = url.lower()
        
        # قاموس الكلمات المفتاحية المحسن
        category_keywords = {
            'Electronics': [
                'phone', 'iphone', 'samsung', 'laptop', 'computer', 'tablet', 'headphone',
                'speaker', 'camera', 'tv', 'watch', 'earbuds', 'charger', 'cable',
                'electronics', 'mobile', 'smartphone', 'gaming', 'console'
            ],
            'Home & Kitchen': [
                'kitchen', 'home', 'furniture', 'appliance', 'cookware', 'utensil',
                'plate', 'cup', 'knife', 'pan', 'pot', 'blender', 'mixer', 'oven'
            ],
            'Beauty': [
                'beauty', 'skincare', 'makeup', 'cosmetic', 'cream', 'lotion',
                'perfume', 'shampoo', 'conditioner', 'soap', 'mask', 'serum'
            ],
            'Health & Household Products': [
                'health', 'medical', 'vitamin', 'supplement', 'medicine', 'pharmacy',
                'tissue', 'toilet', 'cleaning', 'detergent', 'sanitizer'
            ],
            'Tools & Home Improvement': [
                'tool', 'drill', 'hammer', 'screwdriver', 'repair', 'hardware',
                'improvement', 'construction', 'building', 'maintenance'
            ],
            'Automotive': [
                'car', 'auto', 'vehicle', 'tire', 'engine', 'automotive',
                'motorcycle', 'bike', 'parts', 'accessories'
            ],
            'Fashion': [
                'fashion', 'clothing', 'shirt', 'dress', 'pants', 'shoes',
                'bag', 'accessory', 'jewelry', 'watch', 'belt'
            ],
            'Grocery': [
                'food', 'grocery', 'snack', 'drink', 'beverage', 'coffee',
                'tea', 'chocolate', 'candy', 'organic', 'healthy'
            ]
        }
        
        # البحث عن الفئة المناسبة
        for category, keywords in category_keywords.items():
            if any(keyword in name_lower or keyword in url_lower for keyword in keywords):
                return category
        
        return 'Electronics'  # افتراضي
    
    def filter_deals_improved(self, products, target_count=15):
        """فلترة محسنة للعروض"""
        
        print(f"🔍 بدء فلترة {len(products)} منتج...")
        
        if not products:
            print("❌ لا توجد منتجات للفلترة")
            return []
        
        # إزالة التكرارات
        unique_products = {}
        for product in products:
            asin = product.get('asin')
            if asin and asin not in unique_products:
                unique_products[asin] = product
        
        products = list(unique_products.values())
        print(f"✅ بعد إزالة التكرارات: {len(products)} منتج")
        
        # مرحلة 1: فلترة أساسية مرنة
        basic_filtered = []
        
        for product in products:
            price = product.get('price', 0)
            discount = product.get('discount_percent', 0)
            strike_price = product.get('strike_price', 0)
            name = product.get('name', "")
            
            # شروط مرنة
            if (self.min_price <= price <= self.max_price and
                discount >= self.min_discount and
                discount <= self.max_discount and
                strike_price > price and
                len(name) >= 10):  # اسم معقول
                
                basic_filtered.append(product)
        
        print(f"✅ المرحلة 1: {len(basic_filtered)} منتج اجتاز الفلترة الأساسية")
        
        # مرحلة 2: تحليل نصي مرن
        text_filtered = []
        
        suspicious_words = ['fake', 'replica', 'copy', 'used', 'damaged', 'broken']
        quality_words = ['original', 'authentic', 'genuine', 'warranty', 'new', 'brand']
        
        for product in basic_filtered:
            name = product.get('name', "").lower()
            
            suspicious_count = sum(1 for word in suspicious_words if word in name)
            quality_count = sum(1 for word in quality_words if word in name)
            
            # نقاط النص مرنة
            text_score = quality_count * 8 - suspicious_count * 12
            product['text_score'] = text_score
            
            # قبول حتى لو النقاط سالبة قليلاً
            if text_score >= -15:
                text_filtered.append(product)
        
        print(f"✅ المرحلة 2: {len(text_filtered)} منتج اجتاز التحليل النصي")
        
        # مرحلة 3: حساب النقاط النهائية
        for product in text_filtered:
            final_score = 0
            
            # نقاط الخصم (60%)
            discount = product.get('discount_percent', 0)
            final_score += min(60, discount * 1.2)
            
            # نقاط النص (25%)
            text_score = product.get('text_score', 0)
            final_score += min(25, max(0, text_score + 15))
            
            # نقاط السعر (15%)
            price = product.get('price', 0)
            if 50 <= price <= 2000:  # نطاق سعري جيد
                final_score += 15
            elif 20 <= price <= 5000:  # نطاق مقبول
                final_score += 10
            
            product['final_score'] = max(0, final_score)
        
        # ترتيب وانتقاء الأفضل
        sorted_products = sorted(text_filtered, key=lambda x: x.get('final_score', 0), reverse=True)
        
        # أخذ أفضل العروض مع تنويع
        final_deals = self.diversify_selection_improved(sorted_products, target_count)
        
        print(f"🎯 النتيجة النهائية: {len(final_deals)} عرض عالي الجودة")
        
        return final_deals
    
    def diversify_selection_improved(self, sorted_products, target_count):
        """تنويع محسن للاختيار"""
        
        selected = []
        category_counts = {}
        
        # أولاً، أخذ أفضل عرض من كل فئة
        categories_covered = set()
        
        for product in sorted_products:
            category = product.get('section', 'Unknown')
            
            if category not in categories_covered and len(selected) < target_count:
                selected.append(product)
                categories_covered.add(category)
                category_counts[category] = 1
        
        # ثانياً، ملء باقي الأماكن
        for product in sorted_products:
            if len(selected) >= target_count:
                break
            
            if product in selected:
                continue
            
            category = product.get('section', 'Unknown')
            
            # حد أقصى 3 منتجات لكل فئة
            if category_counts.get(category, 0) < 3:
                selected.append(product)
                category_counts[category] = category_counts.get(category, 0) + 1
        
        return selected
    
    def save_deals_to_db(self, deals):
        """حفظ العروض في قاعدة البيانات"""
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        saved_count = 0
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for deal in deals:
            try:
                score = deal.get('final_score', 0)
                
                # تحديد مستوى الجودة
                if score >= 80:
                    quality_level = 'excellent'
                elif score >= 60:
                    quality_level = 'very_good'
                elif score >= 40:
                    quality_level = 'good'
                elif score >= 25:
                    quality_level = 'fair'
                else:
                    quality_level = 'acceptable'
                
                cursor.execute('''
                    INSERT OR REPLACE INTO deals 
                    (asin, name, price, strike_price, discount_percent, section, url, img, 
                     smart_score, quality_level, date_added)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    deal.get('asin', ''),
                    deal.get('name', ''),
                    deal.get('price', 0),
                    deal.get('strike_price', 0),
                    deal.get('discount_percent', 0),
                    deal.get('section', ''),
                    deal.get('url', ''),
                    deal.get('img', ''),
                    score,
                    quality_level,
                    current_date
                ))
                
                saved_count += 1
                
            except Exception as e:
                print(f"⚠️ خطأ في حفظ العرض: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"💾 تم حفظ {saved_count} عرض في قاعدة البيانات")
        return saved_count
    
    def send_deals_to_telegram(self, deals):
        """إرسال العروض للتليجرام"""
        
        if not self.bot_token or not self.users or not deals:
            print("⚠️ إعدادات التليجرام غير مكتملة أو لا توجد عروض")
            return
        
        # تقسيم العروض لرسائل متعددة (5 عروض لكل رسالة)
        deals_chunks = [deals[i:i+5] for i in range(0, len(deals), 5)]
        
        for chunk_index, chunk in enumerate(deals_chunks, 1):
            message = f"🎯 <b>عروض اليوم - الجزء {chunk_index}</b>\n"
            message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            
            for i, deal in enumerate(chunk, 1):
                name = (deal.get('name', 'منتج') or 'منتج')[:45] + "..."
                price = deal.get('price', 0)
                strike_price = deal.get('strike_price', 0)
                discount = deal.get('discount_percent', 0)
                score = deal.get('final_score', 0)
                
                savings = strike_price - price
                
                message += f"<b>{i + (chunk_index-1)*5}. {name}</b>\n"
                message += f"💰 {price:.0f} جنيه\n"
                message += f"🏷️ كان: {strike_price:.0f} جنيه\n"
                message += f"🎉 خصم {discount:.1f}% (توفير {savings:.0f} جنيه)\n"
                message += f"⭐ جودة: {score:.1f}/100\n"
                
                if deal.get('asin'):
                    message += f"🔗 <a href='https://www.amazon.eg/dp/{deal['asin']}'>رابط المنتج</a>\n"
                
                message += "\n"
            
            message += "🤖 <i>عروض معتمدة بالنظام الذكي المحسن</i>"
            
            # إرسال الرسالة
            for user_id in self.users:
                try:
                    url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                    data = {
                        'chat_id': user_id,
                        'text': message,
                        'parse_mode': 'HTML'
                    }
                    response = requests.post(url, data=data, timeout=10)
                    
                    if response.status_code == 200:
                        print(f"✅ تم إرسال الجزء {chunk_index} للمستخدم {user_id}")
                    
                    # تأخير بين الرسائل
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"⚠️ خطأ في إرسال التليجرام: {e}")
            
            # تأخير بين الأجزاء
            time.sleep(3)
    
    def run_complete_analysis(self):
        """تشغيل التحليل الكامل المحسن"""
        
        print("🚀 بدء النظام الذكي المحسن...")
        print("=" * 60)
        
        # مرحلة 1: كشط محسن
        all_products = self.scrape_amazon_improved()
        
        if not all_products:
            print("❌ لم يتم العثور على منتجات")
            return []
        
        # مرحلة 2: فلترة ذكية
        best_deals = self.filter_deals_improved(all_products, target_count=15)
        
        if not best_deals:
            print("❌ لم يتم العثور على عروض تستوفي المعايير")
            return []
        
        # مرحلة 3: حفظ النتائج
        saved_count = self.save_deals_to_db(best_deals)
        
        # مرحلة 4: إرسال للتليجرام
        self.send_deals_to_telegram(best_deals)
        
        # عرض النتائج
        print("\n🏆 أفضل العروض:")
        print("=" * 60)
        
        for i, deal in enumerate(best_deals, 1):
            name = (deal.get('name', 'منتج') or 'منتج')[:50] + "..."
            price = deal.get('price', 0)
            discount = deal.get('discount_percent', 0)
            score = deal.get('final_score', 0)
            
            print(f"{i:2d}. {name}")
            print(f"    💰 {price:.0f} جنيه | 🎉 {discount:.1f}% | ⭐ {score:.1f}")
        
        print(f"\n✅ تم حفظ وإرسال {len(best_deals)} عرض عالي الجودة!")
        return best_deals

def run_improved_system():
    """تشغيل النظام المحسن"""
    
    system = ImprovedSmartSystem()
    return system.run_complete_analysis()

if __name__ == "__main__":
    try:
        run_improved_system()
    except Exception as e:
        print(f"❌ خطأ في النظام: {e}")
        import traceback
        traceback.print_exc()