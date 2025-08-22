# direct_scraper_system.py - نظام كشط مباشر بدون ملف JSON

import json
import sqlite3
import requests
import time
import re
from datetime import datetime
import random
from bs4 import BeautifulSoup
from urllib.parse import quote

class DirectScraperSystem:
    """نظام كشط مباشر يعمل بدون ملف JSON"""
    
    def __init__(self):
        self.db_file = "direct_deals.db"
        self.setup_database()
        self.load_config()
        
        # إعدادات مرنة للحصول على نتائج أكثر
        self.min_discount = 12   # قللت الحد الأدنى
        self.max_discount = 90   # زودت الحد الأقصى
        self.min_price = 20      # قللت الحد الأدنى
        self.max_price = 12000   # زودت الحد الأقصى
        
        # User agents متنوعة
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # مصادر كشط متنوعة ومضمونة
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
        
        print("✅ تم تهيئة النظام بنجاح")
        print(f"📊 الإعدادات: خصم {self.min_discount}%-{self.max_discount}%, سعر {self.min_price}-{self.max_price} جنيه")
    
    def load_config(self):
        """تحميل الإعدادات"""
        try:
            with open('telegram_config.json', 'r') as f:
                config = json.load(f)
                self.bot_token = config.get('bot_token')
                self.users = config.get('users', [])
                print(f"✅ تم تحميل إعدادات التليجرام: {len(self.users)} مستخدم")
        except Exception as e:
            print(f"⚠️ خطأ في تحميل إعدادات التليجرام: {e}")
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
                is_sent BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ تم إعداد قاعدة البيانات")
    
    def scrape_amazon_direct(self):
        """كشط مباشر من أمازون"""
        
        print("🔍 بدء الكشط المباشر من أمازون...")
        
        all_deals = []
        
        for source in self.scraping_sources:
            print(f"🌐 كشط من: {source['name']}")
            
            # كشط 5 صفحات من كل مصدر
            for page in range(1, 6):
                try:
                    url = source['url'].format(page)
                    deals = self.scrape_page_for_deals(url, source['category'])
                    
                    if deals:
                        all_deals.extend(deals)
                        print(f"✅ {source['name']} صفحة {page}: {len(deals)} عرض")
                    else:
                        print(f"⚠️ {source['name']} صفحة {page}: لا توجد عروض")
                    
                    # تأخير عشوائي
                    time.sleep(random.uniform(3, 6))
                    
                except Exception as e:
                    print(f"❌ خطأ في {source['name']} صفحة {page}: {e}")
                    continue
            
            # تأخير بين المصادر
            time.sleep(random.uniform(8, 12))
        
        print(f"✅ إجمالي العروض المكتشفة: {len(all_deals)}")
        return all_deals
    
    def scrape_page_for_deals(self, url, category):
        """كشط صفحة واحدة للعثور على العروض"""
        
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
                print(f"⚠️ HTTP {response.status_code} for {url}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            deals = []
            
            # البحث عن المنتجات
            items = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            # طرق بديلة للبحث
            if not items:
                items = soup.find_all('div', class_='s-result-item')
            
            if not items:
                items = soup.find_all('div', attrs={'data-asin': True})
            
            print(f"🔍 تم العثور على {len(items)} عنصر في الصفحة")
            
            for item in items:
                deal = self.extract_deal_from_item(item, category)
                if deal:
                    deals.append(deal)
            
            return deals
            
        except Exception as e:
            print(f"⚠️ خطأ في كشط الصفحة: {e}")
            return []
    
    def extract_deal_from_item(self, item, category):
        """استخراج بيانات العرض من عنصر HTML"""
        
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
                # افتراض سعر أصلي أعلى
                original_price = current_price * random.uniform(1.15, 1.8)
            
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
        
        # طرق متعددة للبحث عن الاسم
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
        """استخراج السعر الحالي"""
        
        # طرق متعددة للبحث عن السعر
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
        """استخراج السعر الأصلي"""
        
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
        """استخراج رابط المنتج"""
        
        # البحث عن الرابط
        link_elem = item.find('a')
        if link_elem and link_elem.get('href'):
            href = link_elem.get('href')
            if href.startswith('/'):
                return f"https://www.amazon.eg{href}"
            else:
                return href
        
        # رابط افتراضي من ASIN
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
            # إزالة جميع الرموز عدا الأرقام والنقاط
            cleaned = re.sub(r'[^\d.]', '', str(price_text).replace(',', ''))
            
            # البحث عن أرقام
            numbers = re.findall(r'\d+\.?\d*', cleaned)
            
            if numbers:
                # أخذ أول رقم معقول
                for num in numbers:
                    price = float(num)
                    if 10 <= price <= 50000:  # نطاق معقول
                        return price
            
            return None
            
        except:
            return None
    
    def extract_price_from_text(self, text):
        """استخراج السعر من النص الكامل"""
        
        try:
            # أنماط البحث عن السعر
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
        """تحليل سريع لجودة المنتج"""
        
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
            score += 5  # مشبوه
        
        # مكافأة الأسماء المفصلة
        if len(name) > 40:
            score += 10
        
        return max(0, min(100, score))
    
    def send_deal_to_telegram(self, deal):
        """إرسال عرض واحد للتليجرام"""
        
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
            
            savings = strike_price - price
            
            # رموز حسب الفئة
            emoji_map = {
                'Electronics': '📱',
                'Home & Garden': '🏠',
                'Beauty': '💄',
                'Special Deals': '🔥',
                'Lightning Deals': '⚡'
            }
            
            emoji = emoji_map.get(section, '📦')
            
            # رسالة محسنة
            message = f"""{emoji} <b>عرض مكتشف حديثاً!</b>

📦 <b>{name}</b>

💰 السعر: <b>{price:.0f} جنيه</b>
🏷️ كان: <s>{strike_price:.0f} جنيه</s>
🎉 خصم: <b>{discount:.1f}%</b>
💸 توفير: <b>{savings:.0f} جنيه</b>
⭐ جودة: <b>{score:.1f}/100</b>

🔗 <a href="https://www.amazon.eg/dp/{asin}">🛒 اشتري الآن</a>

🤖 <i>مكتشف بالذكاء الاصطناعي</i>
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
                        print(f"✅ تم إرسال العرض للمستخدم {user_id}")
                        sent_to_any = True
                    else:
                        print(f"❌ فشل الإرسال للمستخدم {user_id}: {response.status_code}")
                        
                except Exception as e:
                    print(f"⚠️ خطأ في إرسال للمستخدم {user_id}: {e}")
                    continue
            
            return sent_to_any
            
        except Exception as e:
            print(f"❌ خطأ في إرسال العرض: {e}")
            return False
    
    def filter_and_send_deals(self, all_deals):
        """فلترة وإرسال العروض"""
        
        print(f"🔍 فلترة {len(all_deals)} عرض...")
        
        if not all_deals:
            print("❌ لا توجد عروض للفلترة")
            return []
        
        # إزالة التكرارات
        unique_deals = {}
        for deal in all_deals:
            asin = deal.get('asin')
            if asin and asin not in unique_deals:
                unique_deals[asin] = deal
        
        deals = list(unique_deals.values())
        print(f"✅ بعد إزالة التكرارات: {len(deals)} عرض")
        
        # فلترة جودة عالية
        high_quality_deals = []
        
        for deal in deals:
            quality_score = deal.get('quality_score', 0)
            name = deal.get('name', '').lower()
            
            # شروط صارمة
            if (quality_score >= 50 and
                len(deal.get('name', '')) >= 15 and
                not any(word in name for word in ['fake', 'replica', 'copy', 'used'])):
                
                high_quality_deals.append(deal)
        
        print(f"✅ عروض عالية الجودة: {len(high_quality_deals)}")
        
        # ترتيب حسب النقاط
        high_quality_deals.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        # انتقاء أفضل 15 عرض
        selected_deals = high_quality_deals[:15]
        
        if not selected_deals:
            print("❌ لا توجد عروض تستوفي معايير الجودة العالية")
            return []
        
        print(f"🎯 تم انتقاء {len(selected_deals)} عرض للإرسال")
        
        # حفظ في قاعدة البيانات
        self.save_deals(selected_deals)
        
        # إرسال للتليجرام
        self.send_deals_to_telegram(selected_deals)
        
        return selected_deals
    
    def save_deals(self, deals):
        """حفظ العروض في قاعدة البيانات"""
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for deal in deals:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO deals 
                    (asin, name, price, strike_price, discount_percent, section, url, img, 
                     quality_score, date_found)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    current_time
                ))
            except Exception as e:
                continue
        
        conn.commit()
        conn.close()
        
        print(f"💾 تم حفظ {len(deals)} عرض")
    
    def send_deals_to_telegram(self, deals):
        """إرسال جميع العروض للتليجرام"""
        
        if not deals:
            return
        
        print(f"📱 بدء إرسال {len(deals)} عرض للتليجرام...")
        
        # رسالة افتتاحية
        intro = f"""🎯 <b>عروض اليوم المكتشفة!</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

🔍 تم اكتشاف {len(deals)} عرض عالي الجودة
🤖 فلترة ذكية + تحليل دقيق

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
        
        # إرسال العروض
        sent_count = 0
        
        for i, deal in enumerate(deals, 1):
            print(f"📤 إرسال العرض {i}/{len(deals)}: {deal['name'][:30]}...")
            
            if self.send_deal_to_telegram(deal):
                sent_count += 1
            
            # تأخير بين العروض
            if i < len(deals):
                time.sleep(3)
        
        # رسالة ختامية
        end_msg = f"""✅ <b>انتهى الإرسال</b>

📊 تم إرسال {sent_count} عرض
⭐ متوسط الجودة: {sum(d['quality_score'] for d in deals) / len(deals):.1f}/100

🤖 نظام LAQTA الذكي"""
        
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
    
    def run_system(self):
        """تشغيل النظام الكامل"""
        
        print("🚀 بدء نظام الكشط المباشر...")
        print("=" * 50)
        
        # كشط العروض
        all_deals = self.scrape_amazon_direct()
        
        if not all_deals:
            print("❌ لم يتم العثور على عروض")
            return []
        
        # فلترة وإرسال
        final_deals = self.filter_and_send_deals(all_deals)
        
        if final_deals:
            print("\n🏆 العروض المرسلة:")
            print("-" * 40)
            
            for i, deal in enumerate(final_deals, 1):
                name = deal['name'][:40] + "..."
                price = deal['price']
                discount = deal['discount_percent']
                score = deal['quality_score']
                
                print(f"{i:2d}. {name}")
                print(f"    💰 {price:.0f} جنيه | 🎉 {discount:.1f}% | ⭐ {score:.1f}")
            
            print(f"\n✅ تم إرسال {len(final_deals)} عرض!")
        else:
            print("❌ لا توجد عروض للإرسال")
        
        return final_deals

def run_direct_system():
    """تشغيل النظام المباشر"""
    
    system = DirectScraperSystem()
    return system.run_system()

if __name__ == "__main__":
    try:
        print("🤖 نظام LAQTA المباشر - بدون ملف JSON")
        print("=" * 50)
        
        deals = run_direct_system()
        
        if deals:
            print(f"\n🎉 النظام اكتشف وأرسل {len(deals)} عرض عالي الجودة!")
        else:
            print("\n❌ لم يتم العثور على عروض مناسبة اليوم")
            
    except Exception as e:
        print(f"❌ خطأ في النظام: {e}")
        import traceback
        traceback.print_exc()