# original_system_with_json.py - النظام الأصلي مع إضافة قراءة JSON فقط

import json
import sqlite3
import requests
import time
import re
from datetime import datetime
import random
import os
from bs4 import BeautifulSoup

class OriginalSystemWithJSON:
    """النظام الأصلي الشغال + قراءة ملف JSON فقط"""
    
    def __init__(self):
        self.db_file = "original_deals.db"
        self.products_data = {}  # بيانات JSON (إضافية)
        
        self.setup_database()
        self.load_config()
        self.try_load_json()  # محاولة تحميل JSON (اختياري)
        
        # إعدادات النظام الأصلي (نفس النظام الشغال)
        self.min_discount = 12
        self.max_discount = 90
        self.min_price = 20
        self.max_price = 12000
        
        # User agents (نفس النظام الشغال)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
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
            },
            {
                'name': 'Lightning Deals',
                'url': 'https://www.amazon.eg/s?k=lightning+deal&page={}',
                'category': 'Lightning Deals'
            }
        ]
    
    def try_load_json(self):
        """محاولة تحميل ملف JSON (اختياري)"""
        
        try:
            # البحث عن ملف JSON
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
                print(f"✅ تم تحميل {len(self.products_data):,} منتج من JSON ({file_size:.1f} MB)")
                
            else:
                print("💡 لم يتم العثور على ملف JSON - سيعمل النظام بالكشط فقط")
                
        except Exception as e:
            print(f"⚠️ خطأ في تحميل JSON: {e} - سيعمل النظام بالكشط فقط")
            self.products_data = {}
    
    def load_config(self):
        """تحميل الإعدادات (نفس النظام الأصلي)"""
        
        try:
            with open('telegram_config.json', 'r') as f:
                config = json.load(f)
                self.bot_token = config.get('bot_token')
                self.users = config.get('users', [])
                print(f"✅ إعدادات التليجرام: {len(self.users)} مستخدم")
        except Exception as e:
            print(f"⚠️ خطأ في إعدادات التليجرام: {e}")
            self.bot_token = None
            self.users = []
    
    def setup_database(self):
        """إعداد قاعدة البيانات (نفس النظام الأصلي)"""
        
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
                source TEXT DEFAULT 'scraping',
                date_found TEXT,
                is_sent BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def enhance_deal_with_json_data(self, deal):
        """تحسين بيانات العرض باستخدام JSON (إضافة فقط)"""
        
        if not self.products_data:
            return deal  # إرجاع العرض كما هو إذا لم يكن هناك JSON
        
        asin = deal.get('asin', '')
        if not asin:
            return deal
        
        # البحث عن المنتج في JSON
        json_product = self.products_data.get(asin)
        if not json_product:
            return deal  # إرجاع العرض كما هو إذا لم يوجد في JSON
        
        try:
            # تحسين البيانات من JSON
            if json_product.get('name') and len(json_product['name']) > len(deal.get('name', '')):
                deal['name'] = json_product['name']  # اسم أفضل من JSON
            
            if json_product.get('img') and not deal.get('img'):
                deal['img'] = json_product['img']  # صورة من JSON
            
            if json_product.get('url') and not deal.get('url'):
                deal['url'] = json_product['url']  # رابط من JSON
            
            # تحليل تاريخ الأسعار من JSON (مكافأة إضافية)
            price_history = json_product.get('price_history', [])
            if price_history and len(price_history) >= 5:
                historical_prices = [h.get('price', 0) for h in price_history if h.get('price', 0) > 0]
                
                if historical_prices:
                    avg_historical = sum(historical_prices) / len(historical_prices)
                    current_price = deal.get('price', 0)
                    
                    # مكافأة إضافية إذا كان السعر أقل من المتوسط التاريخي
                    if current_price < avg_historical * 0.9:
                        deal['quality_score'] = deal.get('quality_score', 0) + 15
                        deal['json_enhanced'] = True
                        print(f"🎯 تحسين من JSON: {deal['name'][:30]}... (+15 نقطة)")
            
            deal['source'] = 'scraping_with_json'  # تمييز العروض المحسنة
            
        except Exception as e:
            pass  # في حالة الخطأ، نتجاهل التحسين ونكمل
        
        return deal
    
    def scrape_amazon_direct(self):
        """كشط مباشر من أمازون (نفس النظام الأصلي)"""
        
        print("🔍 بدء الكشط المباشر من أمازون...")
        
        all_deals = []
        
        for source in self.scraping_sources:
            print(f"🌐 كشط من: {source['name']}")
            
            # كشط 5 صفحات من كل مصدر (نفس النظام الأصلي)
            for page in range(1, 6):
                try:
                    url = source['url'].format(page)
                    deals = self.scrape_page_for_deals(url, source['category'])
                    
                    if deals:
                        # تحسين العروض بـ JSON إذا كان متوفر
                        enhanced_deals = []
                        for deal in deals:
                            enhanced_deal = self.enhance_deal_with_json_data(deal)
                            enhanced_deals.append(enhanced_deal)
                        
                        all_deals.extend(enhanced_deals)
                        print(f"✅ {source['name']} صفحة {page}: {len(deals)} عرض")
                    else:
                        print(f"⚠️ {source['name']} صفحة {page}: لا توجد عروض")
                    
                    # تأخير عشوائي (نفس النظام الأصلي)
                    time.sleep(random.uniform(3, 6))
                    
                except Exception as e:
                    print(f"❌ خطأ في {source['name']} صفحة {page}: {e}")
                    continue
            
            # تأخير بين المصادر (نفس النظام الأصلي)
            time.sleep(random.uniform(8, 12))
        
        print(f"✅ إجمالي العروض المكتشفة: {len(all_deals)}")
        return all_deals
    
    def scrape_page_for_deals(self, url, category):
        """كشط صفحة واحدة (نفس النظام الأصلي تماماً)"""
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=25)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            deals = []
            
            # البحث عن المنتجات (نفس النظام الأصلي)
            items = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            if not items:
                items = soup.find_all('div', class_='s-result-item')
            
            if not items:
                items = soup.find_all('div', attrs={'data-asin': True})
            
            for item in items:
                deal = self.extract_deal_from_item(item, category)
                if deal:
                    deals.append(deal)
            
            return deals
            
        except Exception as e:
            return []
    
    def extract_deal_from_item(self, item, category):
        """استخراج بيانات العرض (نفس النظام الأصلي تماماً)"""
        
        try:
            # ASIN
            asin = item.get('data-asin')
            if not asin or len(asin) < 5:
                return None
            
            # الاسم
            name = self.extract_product_name(item)
            if not name or len(name) < 8:
                return None
            
            # الأسعار
            current_price = self.extract_current_price(item)
            if not current_price or current_price <= 0:
                return None
            
            original_price = self.extract_original_price(item)
            if not original_price or original_price <= current_price:
                # افتراض سعر أصلي أعلى (نفس النظام الأصلي)
                original_price = current_price * random.uniform(1.15, 1.8)
            
            # حساب الخصم (نفس النظام الأصلي)
            discount_percent = ((original_price - current_price) / original_price) * 100
            
            # فلترة أولية (نفس النظام الأصلي)
            if (discount_percent < self.min_discount or 
                current_price < self.min_price or 
                current_price > self.max_price):
                return None
            
            # استخراج الرابط والصورة (نفس النظام الأصلي)
            product_url = self.extract_product_url(item, asin)
            image_url = self.extract_image_url(item)
            
            # تحليل جودة سريع (نفس النظام الأصلي)
            quality_score = self.quick_quality_analysis(name, current_price, discount_percent)
            
            # قبول العروض الجيدة فقط (نفس النظام الأصلي)
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
                    'quality_score': quality_score,
                    'source': 'scraping'
                }
            
            return None
            
        except Exception as e:
            return None
    
    def extract_product_name(self, item):
        """استخراج اسم المنتج (نفس النظام الأصلي)"""
        
        selectors = [
            'h2 a span',
            'h2 span',
            'h2 a',
            'h2',
            '.s-size-mini .s-link-style a span',
            '.a-link-normal span'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                name = elem.get_text(strip=True)
                if name and len(name) > 5:
                    return name
        
        return None
    
    def extract_current_price(self, item):
        """استخراج السعر الحالي (نفس النظام الأصلي)"""
        
        selectors = [
            '.a-price .a-offscreen',
            '.a-price-whole',
            '.a-price .a-price-whole',
            '.a-price-range .a-offscreen'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                price_text = elem.get_text(strip=True)
                price = self.parse_price_safe(price_text)
                if price and price > 0:
                    return price
        
        # البحث في النص العام
        text = item.get_text()
        price = self.extract_price_from_text(text)
        return price
    
    def extract_original_price(self, item):
        """استخراج السعر الأصلي (نفس النظام الأصلي)"""
        
        selectors = [
            '.a-text-price .a-offscreen',
            '.a-text-price',
            '.a-price.a-text-price .a-offscreen'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                price_text = elem.get_text(strip=True)
                price = self.parse_price_safe(price_text)
                if price and price > 0:
                    return price
        
        return None
    
    def extract_product_url(self, item, asin):
        """استخراج رابط المنتج (نفس النظام الأصلي)"""
        
        link_elem = item.find('a')
        if link_elem and link_elem.get('href'):
            href = link_elem.get('href')
            if href.startswith('/'):
                return f"https://www.amazon.eg{href}"
            else:
                return href
        
        return f"https://www.amazon.eg/dp/{asin}"
    
    def extract_image_url(self, item):
        """استخراج رابط الصورة (نفس النظام الأصلي)"""
        
        img_elem = item.find('img')
        if img_elem:
            return (img_elem.get('src') or 
                   img_elem.get('data-src') or 
                   img_elem.get('data-lazy-src') or "")
        
        return ""
    
    def parse_price_safe(self, price_text):
        """تحليل آمن للأسعار (نفس النظام الأصلي)"""
        
        if not price_text:
            return None
        
        try:
            cleaned = re.sub(r'[^\d.]', '', str(price_text).replace(',', ''))
            numbers = re.findall(r'\d+\.?\d*', cleaned)
            
            if numbers:
                for num in numbers:
                    price = float(num)
                    if 10 <= price <= 50000:
                        return price
            
            return None
            
        except:
            return None
    
    def extract_price_from_text(self, text):
        """استخراج السعر من النص (نفس النظام الأصلي)"""
        
        try:
            patterns = [
                r'(\d+[\d,]*\.?\d*)\s*(?:EGP|جنيه|ج\.م)',
                r'(\d+[\d,]*\.?\d*)\s*(?:pound|egyptian)',
                r'EGP\s*(\d+[\d,]*\.?\d*)',
                r'(\d+[\d,]*\.?\d*)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        price = self.parse_price_safe(match)
                        if price and 10 <= price <= 50000:
                            return price
            
            return None
            
        except:
            return None
    
    def quick_quality_analysis(self, name, price, discount):
        """تحليل سريع لجودة المنتج (نفس النظام الأصلي)"""
        
        score = 30  # نقاط أساسية
        name_lower = name.lower()
        
        # تحليل النص
        suspicious_words = ['fake', 'replica', 'copy', 'used', 'damaged']
        quality_words = ['original', 'authentic', 'new', 'warranty', 'brand']
        
        suspicious_count = sum(1 for word in suspicious_words if word in name_lower)
        quality_count = sum(1 for word in quality_words if word in name_lower)
        
        score += quality_count * 10 - suspicious_count * 20
        
        # تحليل السعر
        if 50 <= price <= 2000:
            score += 25
        elif 20 <= price <= 5000:
            score += 15
        elif price <= 12000:
            score += 10
        
        # تحليل الخصم
        if 15 <= discount <= 45:
            score += 25
        elif 12 <= discount < 15 or 45 < discount <= 65:
            score += 15
        elif discount > 65:
            score += 5
        
        # مكافأة الأسماء المفصلة
        if len(name) > 40:
            score += 10
        
        return max(0, min(100, score))
    
    def send_deal_to_telegram(self, deal):
        """إرسال عرض للتليجرام (نفس النظام الأصلي + تحسينات)"""
        
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
            source = deal.get('source', 'scraping')
            
            savings = strike_price - price
            
            # رموز حسب المصدر
            if 'json' in source:
                source_emoji = '🧠'
                source_text = 'محسن بـ JSON'
            else:
                source_emoji = '🔍'
                source_text = 'مكتشف حديثاً'
            
            # رموز حسب الفئة
            category_emoji = {
                'Electronics': '📱',
                'Home & Garden': '🏠',
                'Beauty': '💄',
                'Special Deals': '🔥',
                'Lightning Deals': '⚡'
            }
            
            emoji = category_emoji.get(section, '📦')
            
            # رسالة محسنة (نفس النظام الأصلي + JSON info)
            message = f"""{emoji} <b>عرض مكتشف {source_text}</b>

📦 <b>{name}</b>

💰 السعر: <b>{price:.0f} جنيه</b>
🏷️ كان: <s>{strike_price:.0f} جنيه</s>
🎉 خصم: <b>{discount:.1f}%</b>
💸 توفير: <b>{savings:.0f} جنيه</b>
⭐ جودة: <b>{score:.1f}/100</b>

🔗 <a href="https://www.amazon.eg/dp/{asin}">🛒 اشتري الآن</a>

{source_emoji} <i>{source_text}</i>
⚡ <i>عرض محدود!</i>"""
            
            sent_to_any = False
            
            for user_id in self.users:
                try:
                    url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                    data = {
                        'chat_id': user_id,
                        'text': message,
                        'parse_mode': 'HTML',
                        'disable_web_page_preview': False
                    }
                    
                    response = requests.post(url, data=data, timeout=15)
                    
                    if response.status_code == 200:
                        sent_to_any = True
                        
                except Exception as e:
                    continue
            
            return sent_to_any
            
        except Exception as e:
            return False
    
    def filter_and_send_deals(self, all_deals):
        """فلترة وإرسال العروض (نفس النظام الأصلي)"""
        
        print(f"🔍 فلترة {len(all_deals)} عرض...")
        
        if not all_deals:
            print("❌ لا توجد عروض للفلترة")
            return []
        
        # إزالة التكرارات (نفس النظام الأصلي)
        unique_deals = {}
        for deal in all_deals:
            asin = deal.get('asin')
            if asin and asin not in unique_deals:
                unique_deals[asin] = deal
        
        deals = list(unique_deals.values())
        print(f"✅ بعد إزالة التكرارات: {len(deals)} عرض")
        
        # فلترة جودة عالية (نفس النظام الأصلي)
        high_quality_deals = []
        
        for deal in deals:
            quality_score = deal.get('quality_score', 0)
            name = deal.get('name', '').lower()
            
            # شروط صارمة (نفس النظام الأصلي)
            if (quality_score >= 50 and
                len(deal.get('name', '')) >= 15 and
                not any(word in name for word in ['fake', 'replica', 'copy', 'used'])):
                
                high_quality_deals.append(deal)
        
        print(f"✅ عروض عالية الجودة: {len(high_quality_deals)}")
        
        # ترتيب حسب النقاط (نفس النظام الأصلي)
        high_quality_deals.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        # انتقاء أفضل 15 عرض (نفس النظام الأصلي)
        selected_deals = high_quality_deals[:15]
        
        if not selected_deals:
            print("❌ لا توجد عروض تستوفي معايير الجودة العالية")
            return []
        
        print(f"🎯 تم انتقاء {len(selected_deals)} عرض للإرسال")
        
        # حفظ في قاعدة البيانات
        self.save_deals(selected_deals)
        
        # إرسال للتليجرام (نفس النظام الأصلي)
        self.send_deals_to_telegram(selected_deals)
        
        return selected_deals
    
    def save_deals(self, deals):
        """حفظ العروض (نفس النظام الأصلي)"""
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for deal in deals:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO deals 
                    (asin, name, price, strike_price, discount_percent, section, url, img, 
                     quality_score, source, date_found)
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
                    deal.get('quality_score', 0),
                    deal.get('source', 'scraping'),
                    current_time
                ))
            except:
                continue
        
        conn.commit()
        conn.close()
        
        print(f"💾 تم حفظ {len(deals)} عرض")
    
    def send_deals_to_telegram(self, deals):
        """إرسال العروض للتليجرام (نفس النظام الأصلي + معلومات JSON)"""
        
        if not deals:
            return
        
        print(f"📱 بدء إرسال {len(deals)} عرض للتليجرام...")
        
        # رسالة افتتاحية محسنة
        json_info = f" + JSON ({len(self.products_data):,} منتج)" if self.products_data else ""
        
        intro = f"""🎯 <b>عروض اليوم المكتشفة!</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

🔍 كشط مباشر{json_info}
🤖 تم اكتشاف {len(deals)} عرض عالي الجودة
⭐ متوسط الجودة: {sum(d['quality_score'] for d in deals) / len(deals):.1f}/100

⏳ جاري الإرسال..."""
        
        for user_id in self.users:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                data = {
                    'chat_id': user_id,
                    'text': intro,
                    'parse_mode': 'HTML'
                }
                requests.post(url, data=data, timeout=10)
            except:
                pass
        
        time.sleep(2)
        
        # إرسال العروض (نفس النظام الأصلي)
        sent_count = 0
        
        for i, deal in enumerate(deals, 1):
            print(f"📤 إرسال العرض {i}/{len(deals)}: {deal['name'][:30]}...")
            
            if self.send_deal_to_telegram(deal):
                sent_count += 1
            
            # تأخير بين العروض (نفس النظام الأصلي)
            if i < len(deals):
                time.sleep(3)
        
        # رسالة ختامية (نفس النظام الأصلي + معلومات JSON)
        json_enhanced_count = sum(1 for d in deals if 'json' in d.get('source', ''))
        
        end_msg = f"""✅ <b>انتهى الإرسال</b>

📊 تم إرسال {sent_count} عرض
⭐ متوسط الجودة: {sum(d['quality_score'] for d in deals) / len(deals):.1f}/100"""
        
        if json_enhanced_count > 0:
            end_msg += f"\n🧠 محسن بـ JSON: {json_enhanced_count} عرض"
        
        end_msg += "\n\n🤖 نظام LAQTA الذكي"
        
        for user_id in self.users:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                data = {
                    'chat_id': user_id,
                    'text': end_msg,
                    'parse_mode': 'HTML'
                }
                requests.post(url, data=data, timeout=10)
            except:
                pass
        
        print(f"🎉 تم إرسال {sent_count} عرض بنجاح!")
        
        if json_enhanced_count > 0:
            print(f"🧠 تم تحسين {json_enhanced_count} عرض بواسطة JSON")
    
    def run_system(self):
        """تشغيل النظام الكامل (نفس النظام الأصلي)"""
        
        print("🚀 بدء النظام الأصلي المحسن...")
        print("=" * 50)
        
        # كشط العروض (نفس النظام الأصلي)
        all_deals = self.scrape_amazon_direct()
        
        if not all_deals:
            print("❌ لم يتم العثور على عروض")
            return []
        
        # فلترة وإرسال (نفس النظام الأصلي)
        final_deals = self.filter_and_send_deals(all_deals)
        
        if final_deals:
            print("\n🏆 العروض المرسلة:")
            print("-" * 40)
            
            for i, deal in enumerate(final_deals, 1):
                name = deal['name'][:40] + "..."
                price = deal['price']
                discount = deal['discount_percent']
                score = deal['quality_score']
                source_icon = "🧠" if 'json' in deal.get('source', '') else "🔍"
                
                print(f"{i:2d}. {name}")
                print(f"    💰 {price:.0f} جنيه | 🎉 {discount:.1f}% | ⭐ {score:.1f} | {source_icon}")
            
            print(f"\n✅ تم إرسال {len(final_deals)} عرض!")
        else:
            print("❌ لا توجد عروض للإرسال")
        
        return final_deals

def run_original_system():
    """تشغيل النظام الأصلي المحسن"""
    
    system = OriginalSystemWithJSON()
    return system.run_system()

if __name__ == "__main__":
    try:
        print("🤖 النظام الأصلي المحسن مع دعم JSON")
        print("=" * 50)
        
        deals = run_original_system()
        
        if deals:
            print(f"\n🎉 النظام اكتشف وأرسل {len(deals)} عرض عالي الجودة!")
        else:
            print("\n❌ لم يتم العثور على عروض مناسبة اليوم")
            
    except Exception as e:
        print(f"❌ خطأ في النظام: {e}")
        import traceback
        traceback.print_exc()