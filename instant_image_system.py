# instant_image_system.py - نظام إرسال فوري بالصور

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
import threading

class InstantImageSystem:
    """نظام إرسال فوري بالصور عند اكتشاف العروض"""
    
    def __init__(self):
        self.db_file = "instant_deals.db"
        self.products_data = {}
        
        self.setup_database()
        self.load_config()
        self.try_load_json()
        
        # إعدادات النظام (نفس النظام الشغال)
        self.min_discount = 12
        self.max_discount = 90
        self.min_price = 20
        self.max_price = 12000
        
        # إعدادات الإرسال الفوري
        self.instant_send = True
        self.send_with_images = True
        self.max_image_size_kb = 800
        
        # User agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # مصادر الكشط (نفس النظام الشغال)
        self.scraping_sources = [
            {
                'name': 'Amazon Egypt Electronics',
                'url': 'https://www.amazon.eg/s?i=electronics&rh=p_36%3A100-10000&s=price-desc-rank&page={}',
                'category': 'Electronics'
            },
            {
                'name': 'Amazon Egypt Home',
                'url': 'https://www.amazon.eg/s?i=garden&rh=p_36%3A50-5000&s=price-desc-rank&page={}',
                'category': 'Home & Garden'
            },
            {
                'name': 'Amazon Egypt Beauty',
                'url': 'https://www.amazon.eg/s?i=beauty&rh=p_36%3A30-3000&s=price-desc-rank&page={}',
                'category': 'Beauty'
            },
            {
                'name': 'Today Deals',
                'url': 'https://www.amazon.eg/gp/goldbox?ref_=nav_cs_gb&page={}',
                'category': 'Special Deals'
            }
        ]
        
        print("✅ تم تهيئة نظام الإرسال الفوري بالصور")
    
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
                
                # ضغط الصورة
                output = BytesIO()
                quality = 85
                
                for attempt in range(4):
                    output.seek(0)
                    output.truncate()
                    img.save(output, format='JPEG', quality=quality, optimize=True)
                    
                    size_kb = len(output.getvalue()) / 1024
                    if size_kb <= self.max_image_size_kb:
                        print(f"✅ تم تحسين الصورة: {size_kb:.1f} KB")
                        return output.getvalue()
                    
                    quality -= 15
                
                return output.getvalue()
            
            return None
            
        except Exception as e:
            print(f"⚠️ خطأ في معالجة الصورة: {e}")
            return None
    
    def send_deal_instantly_with_image(self, deal):
        """إرسال العرض فوراً مع الصورة"""
        
        if not self.bot_token or not self.users:
            print("⚠️ إعدادات التليجرام غير مكتملة")
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
                'Home & Garden': '🏠',
                'Beauty': '💄',
                'Special Deals': '🔥',
                'Lightning Deals': '⚡'
            }
            
            emoji = category_emojis.get(section, '📦')
            
            # تحضير النص
            caption = f"""{emoji} <b>🚨 عرض مكتشف حديثاً!</b>

📦 <b>{name}</b>

💰 السعر: <b>{price:.0f} جنيه</b>
🏷️ كان: <s>{strike_price:.0f} جنيه</s>
🎉 خصم: <b>{discount:.1f}%</b>
💸 توفير: <b>{savings:.0f} جنيه</b>
⭐ جودة: <b>{score:.1f}/100</b>
🏷️ الفئة: {section}

🔗 <a href="https://www.amazon.eg/dp/{asin}">🛒 اشتري الآن من أمازون</a>

⚡ <b>عرض جديد - احجز بسرعة!</b>
🤖 <i>تم اكتشافه للتو بالذكاء الاصطناعي</i>"""
            
            sent_successfully = False
            
            # إرسال لكل مستخدم
            for user_id in self.users:
                try:
                    # محاولة إرسال مع الصورة أولاً
                    if self.send_with_images and img_url:
                        image_data = self.download_and_optimize_image(img_url)
                        
                        if image_data:
                            # إرسال مع الصورة
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
                            else:
                                print(f"⚠️ فشل إرسال الصورة: {response.status_code}")
                    
                    # إرسال نص فقط كـ fallback
                    url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                    data = {
                        'chat_id': user_id,
                        'text': caption,
                        'parse_mode': 'HTML',
                        'disable_web_page_preview': False
                    }
                    
                    response = requests.post(url, data=data, timeout=15)
                    
                    if response.status_code == 200:
                        print(f"✅ تم إرسال العرض (نص) للمستخدم {user_id}")
                        sent_successfully = True
                    else:
                        print(f"❌ فشل إرسال النص: {response.status_code}")
                        
                except Exception as e:
                    print(f"⚠️ خطأ في إرسال للمستخدم {user_id}: {e}")
                    continue
            
            # تحديث قاعدة البيانات
            if sent_successfully:
                self.mark_deal_as_sent(deal, with_image=(img_url and self.send_with_images))
            
            return sent_successfully
            
        except Exception as e:
            print(f"❌ خطأ في إرسال العرض: {e}")
            return False
    
    def enhance_deal_with_json(self, deal):
        """تحسين بيانات العرض من JSON"""
        
        if not self.products_data:
            return deal
        
        asin = deal.get('asin', '')
        if not asin:
            return deal
        
        json_product = self.products_data.get(asin)
        if not json_product:
            return deal
        
        try:
            # تحسين البيانات من JSON
            if json_product.get('name') and len(json_product['name']) > len(deal.get('name', '')):
                deal['name'] = json_product['name']
                print(f"🧠 تحسين الاسم من JSON: {deal['name'][:30]}...")
            
            if json_product.get('img') and not deal.get('img'):
                deal['img'] = json_product['img']
                print(f"📸 إضافة صورة من JSON")
            
            if json_product.get('url'):
                deal['url'] = json_product['url']
            
            # تحليل تاريخ الأسعار للمكافأة
            price_history = json_product.get('price_history', [])
            if price_history and len(price_history) >= 5:
                historical_prices = [h.get('price', 0) for h in price_history if h.get('price', 0) > 0]
                
                if historical_prices:
                    avg_historical = sum(historical_prices) / len(historical_prices)
                    current_price = deal.get('price', 0)
                    
                    if current_price < avg_historical * 0.9:
                        deal['quality_score'] = deal.get('quality_score', 0) + 15
                        print(f"🎯 مكافأة JSON: +15 نقطة (أقل من المتوسط التاريخي)")
            
            deal['json_enhanced'] = True
            
        except Exception as e:
            print(f"⚠️ خطأ في تحسين JSON: {e}")
        
        return deal
    
    def scrape_and_send_instantly(self):
        """كشط وإرسال فوري للعروض"""
        
        print("🚀 بدء الكشط مع الإرسال الفوري...")
        
        total_sent = 0
        
        for source in self.scraping_sources:
            print(f"🌐 كشط من: {source['name']}")
            
            # كشط 5 صفحات من كل مصدر
            for page in range(1, 6):
                try:
                    url = source['url'].format(page)
                    deals = self.scrape_page_and_send_instantly(url, source['category'])
                    
                    if deals:
                        total_sent += deals
                        print(f"✅ {source['name']} صفحة {page}: {deals} عرض تم إرساله")
                    else:
                        print(f"⚠️ {source['name']} صفحة {page}: لا توجد عروض")
                    
                    # تأخير بين الصفحات
                    time.sleep(random.uniform(4, 7))
                    
                except Exception as e:
                    print(f"❌ خطأ في {source['name']} صفحة {page}: {e}")
                    continue
            
            # تأخير بين المصادر
            time.sleep(random.uniform(10, 15))
        
        print(f"🎉 إجمالي العروض المرسلة فورياً: {total_sent}")
        return total_sent
    
    def scrape_page_and_send_instantly(self, url, category):
        """كشط صفحة وإرسال العروض فوراً"""
        
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
                return 0
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # البحث عن المنتجات
            items = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            if not items:
                items = soup.find_all('div', attrs={'data-asin': True})
            
            sent_count = 0
            
            for item in items:
                deal = self.extract_and_validate_deal(item, category)
                
                if deal:
                    # تحسين بـ JSON إذا كان متوفر
                    enhanced_deal = self.enhance_deal_with_json(deal)
                    
                    # إرسال فوراً
                    if self.send_deal_instantly_with_image(enhanced_deal):
                        sent_count += 1
                        print(f"📤 تم إرسال: {enhanced_deal['name'][:35]}...")
                        
                        # تأخير قصير بين العروض
                        time.sleep(2)
            
            return sent_count
            
        except Exception as e:
            print(f"⚠️ خطأ في كشط الصفحة: {e}")
            return 0
    
    def extract_and_validate_deal(self, item, category):
        """استخراج وتحقق من صحة العرض"""
        
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
                original_price = current_price * random.uniform(1.2, 1.7)
            
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
            
            # تحليل جودة سريع
            quality_score = self.quick_quality_analysis(name, current_price, discount_percent)
            
            # قبول العروض الجيدة فقط
            if quality_score >= 55:  # قللت الحد قليلاً للحصول على عروض أكثر
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
    
    def is_already_sent(self, asin):
        """فحص إذا كان العرض تم إرساله مسبقاً"""
        
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # فحص إذا كان تم إرساله اليوم
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
        
        score = 35  # نقاط أساسية أعلى
        name_lower = name.lower()
        
        # تحليل النص
        suspicious_words = ['fake', 'replica', 'copy', 'used', 'damaged']
        quality_words = ['original', 'authentic', 'new', 'warranty', 'brand']
        brand_words = ['samsung', 'apple', 'xiaomi', 'anker', 'sony', 'lg']
        
        suspicious_count = sum(1 for word in suspicious_words if word in name_lower)
        quality_count = sum(1 for word in quality_words if word in name_lower)
        brand_count = sum(1 for word in brand_words if word in name_lower)
        
        score += quality_count * 12 + brand_count * 8 - suspicious_count * 25
        
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
        elif 45 < discount <= 65:
            score += 15
        
        # مكافأة الأسماء المفصلة
        if len(name) > 50:
            score += 10
        
        return max(0, min(100, score))
    
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
            print(f"⚠️ خطأ في حفظ العرض: {e}")
    
    def send_session_summary(self, total_sent):
        """إرسال ملخص الجلسة"""
        
        if not self.bot_token or not self.users or total_sent == 0:
            return
        
        try:
            # جلب إحصائيات اليوم
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*), AVG(quality_score), AVG(discount_percent)
                FROM deals 
                WHERE date_found LIKE ? AND is_sent = 1
            ''', (f'{today}%',))
            
            stats = cursor.fetchone()
            conn.close()
            
            summary_message = f"""📊 <b>ملخص جلسة الكشط</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

🎯 <b>النتائج:</b>
• عروض مرسلة هذه الجلسة: <b>{total_sent}</b>
• إجمالي عروض اليوم: <b>{stats[0] if stats[0] else 0}</b>
• متوسط الجودة: <b>{stats[1]:.1f}/100</b> إذا كان stats[1] else 0
• متوسط الخصم: <b>{stats[2]:.1f}%</b> إذا كان stats[2] else 0

📸 جميع العروض مرسلة مع الصور
🤖 نظام LAQTA الفوري"""
            
            # إرسال الملخص
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
            
            print(f"📊 تم إرسال ملخص الجلسة")
            
        except Exception as e:
            print(f"⚠️ خطأ في إرسال الملخص: {e}")
    
    def run_instant_system(self):
        """تشغيل النظام الفوري"""
        
        print("🚀 بدء نظام الإرسال الفوري مع الصور...")
        print("=" * 60)
        
        # إرسال رسالة بداية الجلسة
        self.send_session_start_message()
        
        # بدء الكشط والإرسال الفوري
        total_sent = self.scrape_and_send_instantly()
        
        # إرسال ملخص الجلسة
        self.send_session_summary(total_sent)
        
        print(f"✅ انتهت الجلسة - تم إرسال {total_sent} عرض مع الصور!")
        
        return total_sent
    
    def send_session_start_message(self):
        """إرسال رسالة بداية الجلسة"""
        
        if not self.bot_token or not self.users:
            return
        
        try:
            start_message = f"""🚀 <b>بدء جلسة كشط جديدة</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

🔍 سيتم كشط العروض وإرسالها فوراً
📸 كل عرض سيُرسل مع صورة المنتج
🎯 معايير الجودة: خصم {self.min_discount}%+ ونقاط 55+

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
            print(f"⚠️ خطأ في إرسال رسالة البداية: {e}")
    
    def get_today_stats(self):
        """إحصائيات اليوم"""
        
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute('SELECT COUNT(*) FROM deals WHERE date_found LIKE ?', (f'{today}%',))
            today_deals = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM deals WHERE is_sent = 1 AND date_found LIKE ?', (f'{today}%',))
            sent_deals = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM deals WHERE sent_with_image = 1 AND date_found LIKE ?', (f'{today}%',))
            image_deals = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'today_deals': today_deals,
                'sent_deals': sent_deals,
                'image_deals': image_deals
            }
            
        except Exception as e:
            return {'today_deals': 0, 'sent_deals': 0, 'image_deals': 0}

def run_instant_system():
    """تشغيل النظام الفوري"""
    
    system = InstantImageSystem()
    return system.run_instant_system()

if __name__ == "__main__":
    try:
        print("🤖 نظام LAQTA الفوري مع الصور")
        print("=" * 50)
        
        total_sent = run_instant_system()
        
        if total_sent > 0:
            print(f"\n🎉 تم إرسال {total_sent} عرض فورياً مع الصور!")
        else:
            print("\n❌ لم يتم العثور على عروض مناسبة")
            
    except Exception as e:
        print(f"❌ خطأ في النظام: {e}")
        import traceback
        traceback.print_exc()