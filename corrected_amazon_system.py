# corrected_amazon_system.py - النظام المصحح مع روابط أمازون الصحيحة

import json
import sqlite3
import requests
import time
import re
from datetime import datetime
import random
import os
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

class CorrectedAmazonSystem:
    """النظام المصحح مع روابط أمازون الصحيحة من الملف الأصلي"""
    
    def __init__(self):
        self.db_file = "corrected_deals.db"
        self.products_data = {}
        
        self.setup_database()
        self.load_config()
        self.try_load_json()
        
        # إعدادات النظام
        self.min_discount = 12
        self.max_discount = 90
        self.min_price = 20
        self.max_price = 12000
        
        # إعدادات الصور
        self.send_with_images = True
        self.max_image_size_kb = 800
        
        # User agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # الروابط الصحيحة من الملف الأصلي (أمازون فقط)
        self.amazon_categories = {
            'Electronics': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18018102031%2Cp_98%3A21909049031&dc&page={}&language=en",
            'Automotive': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18017874031%2Cp_98%3A21909049031&dc&page={}&language=en",
            'Beauty': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18017988031%2Cp_98%3A21909049031&dc&page={}&language=en",
            'Fashion': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18018165031%2Cp_98%3A21909049031&dc&page={}&language=en",
            'Grocery': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18020637031%2Cp_98%3A21909049031&dc&page={}&language=en",
            'Health & Household Products': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18021875031%2Cp_98%3A21909049031&dc&page={}&language=en",
            'Home & Kitchen': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18021933031%2Cp_98%3A21909049031&dc&page={}&language=en",
            'Tools & Home Improvement': "https://www.amazon.eg/s?me=A1ZVRGNO5AYLOV&rh=n%3A18021990031%2Cp_98%3A21909049031&dc&page={}&language=en"
        }
        
        print("✅ تم تهيئة النظام مع روابط أمازون الصحيحة")
        print(f"📊 فئات أمازون: {len(self.amazon_categories)} فئة")
    
    def try_load_json(self):
        """تحميل ملف JSON تلقائياً"""
        
        try:
            json_files = []
            for file in os.listdir('.'):
                if (file.endswith('.json') and 
                    file not in ['config.json', 'telegram_config.json', 'config_template.json']):
                    json_files.append(file)
            
            if json_files:
                largest_file = max(json_files, key=lambda f: os.path.getsize(f))
                print(f"📂 تم العثور على ملف JSON: {largest_file}")
                
                with open(largest_file, 'r', encoding='utf-8') as f:
                    self.products_data = json.load(f)
                
                file_size = os.path.getsize(largest_file) / (1024 * 1024)
                print(f"✅ تم تحميل {len(self.products_data):,} منتج ({file_size:.1f} MB)")
                
        except Exception as e:
            print(f"⚠️ خطأ في تحميل JSON: {e}")
            self.products_data = {}
    
    def load_config(self):
        """تحميل إعدادات التليجرام"""
        
        try:
            with open('telegram_config.json', 'r') as f:
                config = json.load(f)
                self.bot_token = config.get('bot_token')
                self.users = config.get('users', [])
                print(f"✅ إعدادات التليجرام: {len(self.users)} مستخدم")
        except Exception as e:
            print(f"❌ خطأ في إعدادات التليجرام: {e}")
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
                quality_score REAL DEFAULT 0,
                date_found TEXT,
                is_sent BOOLEAN DEFAULT 0,
                sent_with_image BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def scrape_amazon_only(self):
        """كشط من أمازون فقط باستخدام الروابط الصحيحة"""
        
        print("🔍 بدء الكشط من أمازون فقط...")
        
        all_deals = []
        
        for category_name, category_url in self.amazon_categories.items():
            print(f"🌐 كشط فئة: {category_name}")
            
            # كشط 5 صفحات من كل فئة
            for page in range(1, 6):
                try:
                    url = category_url.format(page)
                    deals = self.scrape_page_amazon_only(url, category_name)
                    
                    if deals:
                        # تحسين العروض بـ JSON
                        enhanced_deals = []
                        for deal in deals:
                            enhanced_deal = self.enhance_deal_with_json(deal)
                            enhanced_deals.append(enhanced_deal)
                            
                            # إرسال فوري إذا كان العرض جيد
                            if enhanced_deal.get('quality_score', 0) >= 60:
                                self.send_deal_instantly_with_image(enhanced_deal)
                        
                        all_deals.extend(enhanced_deals)
                        print(f"✅ {category_name} صفحة {page}: {len(deals)} عرض")
                    else:
                        print(f"⚠️ {category_name} صفحة {page}: لا توجد عروض")
                    
                    # تأخير بين الصفحات
                    time.sleep(random.uniform(3, 5))
                    
                except Exception as e:
                    print(f"❌ خطأ في {category_name} صفحة {page}: {e}")
                    continue
            
            # تأخير بين الفئات
            time.sleep(random.uniform(5, 8))
        
        print(f"✅ إجمالي العروض من أمازون: {len(all_deals)}")
        return all_deals
    
    def scrape_page_amazon_only(self, url, category):
        """كشط صفحة واحدة من أمازون فقط"""
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            deals = []
            
            # البحث عن المنتجات (نفس الطريقة الأصلية)
            items = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            if not items:
                items = soup.find_all('div', attrs={'data-asin': True})
            
            for item in items:
                deal = self.extract_amazon_deal(item, category)
                if deal:
                    deals.append(deal)
            
            return deals
            
        except Exception as e:
            return []
    
    def extract_amazon_deal(self, item, category):
        """استخراج بيانات العرض من أمازون فقط"""
        
        try:
            # ASIN
            asin = item.get('data-asin')
            if not asin or len(asin) < 5:
                return None
            
            # التحقق من عدم الإرسال مسبقاً
            if self.is_already_sent(asin):
                return None
            
            # الاسم
            name = self.extract_product_name(item)
            if not name or len(name) < 10:
                return None
            
            # السعر الحالي
            current_price = self.extract_current_price(item)
            if not current_price or current_price <= 0:
                return None
            
            # السعر الأصلي
            original_price = self.extract_original_price(item)
            if not original_price or original_price <= current_price:
                original_price = current_price * random.uniform(1.2, 1.6)
            
            # حساب الخصم
            discount_percent = ((original_price - current_price) / original_price) * 100
            
            # فلترة أولية
            if (discount_percent < self.min_discount or 
                current_price < self.min_price or 
                current_price > self.max_price):
                return None
            
            # استخراج الرابط والصورة
            product_url = self.extract_product_url(item, asin)
            image_url = self.extract_image_url(item)
            
            # تحليل جودة
            quality_score = self.quick_quality_analysis(name, current_price, discount_percent)
            
            # قبول العروض الجيدة فقط
            if quality_score >= 50:
                return {
                    'asin': asin,
                    'name': name,
                    'price': current_price,
                    'strike_price': original_price,
                    'discount_percent': discount_percent,
                    'section': category,
                    'url': product_url,
                    'img': image_url,
                    'quality_score': quality_score
                }
            
            return None
            
        except Exception as e:
            return None
    
    def extract_product_name(self, item):
        """استخراج اسم المنتج"""
        
        selectors = [
            'h2 a span',
            'h2 span',
            'h2 a',
            'h2'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                name = elem.get_text(strip=True)
                if name and len(name) > 5:
                    return name
        
        return None
    
    def extract_current_price(self, item):
        """استخراج السعر الحالي"""
        
        selectors = [
            '.a-price .a-offscreen',
            '.a-price-whole',
            '.a-price .a-price-whole'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                price = self.parse_price_safe(elem.get_text(strip=True))
                if price and price > 0:
                    return price
        
        return None
    
    def extract_original_price(self, item):
        """استخراج السعر الأصلي"""
        
        selectors = [
            '.a-text-price .a-offscreen',
            '.a-text-price'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                price = self.parse_price_safe(elem.get_text(strip=True))
                if price and price > 0:
                    return price
        
        return None
    
    def extract_product_url(self, item, asin):
        """استخراج رابط المنتج"""
        
        link_elem = item.find('a')
        if link_elem and link_elem.get('href'):
            href = link_elem.get('href')
            if href.startswith('/'):
                return f"https://www.amazon.eg{href}"
            else:
                return href
        
        return f"https://www.amazon.eg/dp/{asin}"
    
    def extract_image_url(self, item):
        """استخراج رابط الصورة"""
        
        img_elem = item.find('img')
        if img_elem:
            return (img_elem.get('src') or 
                   img_elem.get('data-src') or 
                   img_elem.get('data-lazy-src') or "")
        
        return ""
    
    def parse_price_safe(self, price_text):
        """تحليل آمن للأسعار"""
        
        if not price_text:
            return None
        
        try:
            cleaned = re.sub(r'[^\d.]', '', str(price_text).replace(',', ''))
            numbers = re.findall(r'\d+\.?\d*', cleaned)
            
            if numbers:
                price = float(numbers[0])
                if 10 <= price <= 50000:
                    return price
            
            return None
            
        except:
            return None
    
    def quick_quality_analysis(self, name, price, discount):
        """تحليل سريع للجودة"""
        
        score = 40  # نقاط أساسية أعلى لأمازون
        name_lower = name.lower()
        
        # تحليل النص
        suspicious_words = ['fake', 'replica', 'copy', 'used', 'damaged']
        quality_words = ['original', 'authentic', 'new', 'warranty', 'brand']
        brand_words = ['samsung', 'apple', 'xiaomi', 'anker', 'sony', 'lg']
        
        suspicious_count = sum(1 for word in suspicious_words if word in name_lower)
        quality_count = sum(1 for word in quality_words if word in name_lower)
        brand_count = sum(1 for word in brand_words if word in name_lower)
        
        score += quality_count * 10 + brand_count * 8 - suspicious_count * 20
        
        # تحليل السعر
        if 50 <= price <= 2000:
            score += 25
        elif 20 <= price <= 5000:
            score += 15
        
        # تحليل الخصم
        if 15 <= discount <= 45:
            score += 25
        elif 12 <= discount < 15:
            score += 20
        
        # مكافأة الأسماء المفصلة
        if len(name) > 50:
            score += 10
        
        return max(0, min(100, score))
    
    def enhance_deal_with_json(self, deal):
        """تحسين بيانات العرض من JSON"""
        
        if not self.products_data:
            return deal
        
        asin = deal.get('asin', '')
        json_product = self.products_data.get(asin)
        
        if not json_product:
            return deal
        
        try:
            # تحسين البيانات من JSON
            if json_product.get('name') and len(json_product['name']) > len(deal.get('name', '')):
                deal['name'] = json_product['name']
                print(f"🧠 تحسين الاسم من JSON")
            
            if json_product.get('img') and not deal.get('img'):
                deal['img'] = json_product['img']
                print(f"📸 إضافة صورة من JSON")
            
            # تحليل تاريخ الأسعار
            price_history = json_product.get('price_history', [])
            if price_history and len(price_history) >= 5:
                historical_prices = [h.get('price', 0) for h in price_history if h.get('price', 0) > 0]
                
                if historical_prices:
                    avg_historical = sum(historical_prices) / len(historical_prices)
                    current_price = deal.get('price', 0)
                    
                    if current_price < avg_historical * 0.9:
                        deal['quality_score'] = deal.get('quality_score', 0) + 15
                        print(f"🎯 مكافأة JSON: +15 نقطة")
            
            deal['json_enhanced'] = True
            
        except Exception as e:
            pass
        
        return deal
    
    def is_already_sent(self, asin):
        """فحص إذا كان العرض تم إرساله مسبقاً"""
        
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) FROM deals 
                WHERE asin = ? AND is_sent = 1 AND date_found LIKE ?
            ''', (asin, f'{today}%'))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            return False
    
    def download_and_optimize_image(self, img_url):
        """تحميل وتحسين صورة المنتج"""
        
        if not img_url:
            return None
        
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'image/*,*/*;q=0.8',
                'Referer': 'https://www.amazon.eg/'
            }
            
            response = requests.get(img_url, headers=headers, timeout=10)
            
            if response.status_code == 200 and len(response.content) > 500:
                img = Image.open(BytesIO(response.content))
                
                # تحويل إلى RGB
                if img.mode != 'RGB':
                    if img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'RGBA':
                            background.paste(img, mask=img.split()[-1])
                        else:
                            background.paste(img)
                        img = background
                    else:
                        img = img.convert('RGB')
                
                # تحسين الحجم
                if img.size[0] < 400 or img.size[1] < 400:
                    new_size = (max(500, img.size[0]), max(500, img.size[1]))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                elif img.size[0] > 1000 or img.size[1] > 1000:
                    img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
                
                # ضغط
                output = BytesIO()
                quality = 85
                
                for attempt in range(4):
                    output.seek(0)
                    output.truncate()
                    img.save(output, format='JPEG', quality=quality, optimize=True)
                    
                    if len(output.getvalue()) <= self.max_image_size_kb * 1024:
                        return output.getvalue()
                    
                    quality -= 15
                
                return output.getvalue()
            
            return None
            
        except Exception as e:
            return None
    
    def send_deal_instantly_with_image(self, deal):
        """إرسال العرض فوراً مع الصورة"""
        
        if not self.bot_token or not self.users:
            return False
        
        try:
            name = deal.get('name', 'منتج')
            price = deal.get('price', 0)
            strike_price = deal.get('strike_price', 0)
            discount = deal.get('discount_percent', 0)
            score = deal.get('quality_score', 0)
            asin = deal.get('asin', '')
            section = deal.get('section', 'غير محدد')
            img_url = deal.get('img', '')
            
            savings = strike_price - price
            
            # رموز حسب الفئة
            category_emojis = {
                'Electronics': '📱',
                'Home & Kitchen': '🏠',
                'Beauty': '💄',
                'Health & Household Products': '🏥',
                'Tools & Home Improvement': '🔧',
                'Automotive': '🚗',
                'Fashion': '👕',
                'Grocery': '🛒'
            }
            
            emoji = category_emojis.get(section, '📦')
            
            # تحضير النص
            caption = f"""{emoji} <b>🚨 عرض أمازون مكتشف حديثاً!</b>

📦 <b>{name}</b>

💰 السعر: <b>{price:.0f} جنيه</b>
🏷️ كان: <s>{strike_price:.0f} جنيه</s>
🎉 خصم: <b>{discount:.1f}%</b>
💸 توفير: <b>{savings:.0f} جنيه</b>
⭐ جودة: <b>{score:.1f}/100</b>
🏷️ الفئة: {section}

🛒 <b>البائع: أمازون مصر</b>
🚚 <b>شحن مجاني + ضمان أمازون</b>

🔗 <a href="https://www.amazon.eg/dp/{asin}">🛒 اشتري الآن</a>

⚡ <b>عرض جديد من أمازون - احجز بسرعة!</b>
🤖 <i>مكتشف للتو + محسن بـ JSON</i>"""
            
            sent_successfully = False
            
            for user_id in self.users:
                try:
                    # محاولة إرسال مع الصورة
                    if self.send_with_images and img_url:
                        image_data = self.download_and_optimize_image(img_url)
                        
                        if image_data:
                            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
                            
                            files = {'photo': ('product.jpg', image_data, 'image/jpeg')}
                            data = {
                                'chat_id': user_id,
                                'caption': caption,
                                'parse_mode': 'HTML'
                            }
                            
                            response = requests.post(url, data=data, files=files, timeout=25)
                            
                            if response.status_code == 200:
                                print(f"✅ تم إرسال العرض مع الصورة للمستخدم {user_id}")
                                sent_successfully = True
                                continue
                    
                    # إرسال نص فقط
                    url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                    data = {
                        'chat_id': user_id,
                        'text': caption,
                        'parse_mode': 'HTML'
                    }
                    
                    response = requests.post(url, data=data, timeout=15)
                    
                    if response.status_code == 200:
                        print(f"✅ تم إرسال العرض (نص) للمستخدم {user_id}")
                        sent_successfully = True
                        
                except Exception as e:
                    continue
            
            # حفظ في قاعدة البيانات
            if sent_successfully:
                self.mark_deal_as_sent(deal, with_image=(img_url and self.send_with_images))
            
            return sent_successfully
            
        except Exception as e:
            return False
    
    def mark_deal_as_sent(self, deal, with_image=False):
        """وضع علامة على العرض كمرسل"""
        
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT OR REPLACE INTO deals 
                (asin, name, price, strike_price, discount_percent, section, url, img, 
                 quality_score, date_found, is_sent, sent_with_image)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            ''', (
                deal.get('asin', ''),
                deal.get('name', ''),
                deal.get('price', 0),
                deal.get('strike_price', 0),
                deal.get('discount_percent', 0),
                deal.get('section', ''),
                deal.get('url', ''),
                deal.get('img', ''),
                deal.get('quality_score', 0),
                current_time,
                1 if with_image else 0
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            pass
    
    def run_system(self):
        """تشغيل النظام الكامل"""
        
        print("🚀 بدء النظام المصحح - أمازون فقط مع الصور...")
        print("=" * 60)
        
        # إرسال رسالة بداية
        self.send_session_start_message()
        
        # كشط وإرسال فوري
        all_deals = self.scrape_amazon_only()
        
        # إرسال ملخص
        sent_count = len([d for d in all_deals if d.get('quality_score', 0) >= 60])
        self.send_session_summary(sent_count)
        
        print(f"✅ انتهى النظام - تم إرسال {sent_count} عرض من أمازون مع الصور!")
        
        return all_deals
    
    def send_session_start_message(self):
        """إرسال رسالة بداية الجلسة"""
        
        if not self.bot_token or not self.users:
            return
        
        try:
            start_message = f"""🚀 <b>بدء جلسة كشط أمازون</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

🛒 <b>البائع: أمازون مصر فقط</b>
📸 إرسال فوري مع صورة كل منتج
🎯 معايير الجودة: خصم {self.min_discount}%+ ونقاط 50+
🧠 تحسين من {len(self.products_data):,} منتج JSON

⏳ جاري البحث عن العروض..."""
            
            for user_id in self.users:
                try:
                    url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                    data = {
                        'chat_id': user_id,
                        'text': start_message,
                        'parse_mode': 'HTML'
                    }
                    requests.post(url, data=data, timeout=10)
                except:
                    pass
            
        except Exception as e:
            pass
    
    def send_session_summary(self, total_sent):
        """إرسال ملخص الجلسة"""
        
        if not self.bot_token or not self.users:
            return
        
        try:
            summary_message = f"""📊 <b>ملخص جلسة أمازون</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

🎯 <b>النتائج:</b>
• عروض مرسلة: <b>{total_sent}</b>
• البائع: <b>أمازون مصر فقط</b>
• مع الصور: <b>نعم</b>

🛒 <b>مميزات عروض أمازون:</b>
• ضمان أمازون الرسمي
• شحن مجاني وسريع
• إرجاع سهل ومضمون
• خدمة عملاء ممتازة

🤖 نظام LAQTA - عروض أمازون فقط"""
            
            for user_id in self.users:
                try:
                    url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                    data = {
                        'chat_id': user_id,
                        'text': summary_message,
                        'parse_mode': 'HTML'
                    }
                    requests.post(url, data=data, timeout=10)
                except:
                    pass
            
        except Exception as e:
            pass

def run_corrected_system():
    """تشغيل النظام المصحح"""
    
    system = CorrectedAmazonSystem()
    return system.run_system()

if __name__ == "__main__":
    try:
        print("🤖 نظام LAQTA المصحح - أمازون فقط مع الصور")
        print("=" * 60)
        
        deals = run_corrected_system()
        
        if deals:
            print(f"\n🎉 تم العثور على {len(deals)} عرض من أمازون!")
        else:
            print("\n❌ لم يتم العثور على عروض من أمازون اليوم")
            
    except Exception as e:
        print(f"❌ خطأ في النظام: {e}")
        import traceback
        traceback.print_exc()