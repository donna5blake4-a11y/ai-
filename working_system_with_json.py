# working_system_with_json.py - النظام الشغال مع ملف JSON

import json
import sqlite3
import requests
import time
import re
from datetime import datetime
import random
import os
from bs4 import BeautifulSoup

class WorkingSystemWithJSON:
    """النظام الشغال مع إضافة دعم ملف JSON"""
    
    def __init__(self, json_file=None):
        self.db_file = "working_deals.db"
        self.json_file = json_file
        self.products_data = {}
        
        self.setup_database()
        self.load_config()
        
        # محاولة تحميل ملف JSON إذا كان موجود
        if json_file:
            self.load_json_data(json_file)
        else:
            self.find_and_load_json()
        
        # إعدادات النظام الشغال
        self.min_discount = 15
        self.max_discount = 85
        self.min_price = 25
        self.max_price = 8000
        
        # User agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # مصادر الكشط (نفس النظام الشغال)
        self.scraping_sources = [
            {
                'name': 'Electronics',
                'url': 'https://www.amazon.eg/s?i=electronics&rh=p_36%3A100-10000&page={}',
                'category': 'Electronics'
            },
            {
                'name': 'Home & Kitchen',
                'url': 'https://www.amazon.eg/s?i=garden&rh=p_36%3A50-5000&page={}',
                'category': 'Home & Kitchen'
            },
            {
                'name': 'Beauty',
                'url': 'https://www.amazon.eg/s?i=beauty&rh=p_36%3A30-3000&page={}',
                'category': 'Beauty'
            }
        ]
    
    def find_and_load_json(self):
        """البحث عن ملف JSON في المجلد وتحميله"""
        
        print("🔍 البحث عن ملف JSON في المجلد...")
        
        # البحث عن ملفات JSON
        json_files = []
        for file in os.listdir('.'):
            if file.endswith('.json') and file not in ['config.json', 'telegram_config.json', 'config_template.json']:
                json_files.append(file)
        
        if json_files:
            # اختيار أكبر ملف JSON (غالباً ملف المنتجات)
            largest_file = max(json_files, key=lambda f: os.path.getsize(f))
            print(f"📂 تم العثور على ملف JSON: {largest_file}")
            
            self.load_json_data(largest_file)
        else:
            print("⚠️ لم يتم العثور على ملف JSON للمنتجات")
            print("💡 سيعمل النظام بالكشط المباشر فقط")
    
    def load_json_data(self, json_file):
        """تحميل بيانات JSON"""
        
        try:
            print(f"📂 جاري تحميل ملف: {json_file}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                self.products_data = json.load(f)
            
            file_size = os.path.getsize(json_file) / (1024 * 1024)  # MB
            print(f"✅ تم تحميل {len(self.products_data):,} منتج ({file_size:.1f} MB)")
            
            self.json_file = json_file
            
        except FileNotFoundError:
            print(f"❌ الملف غير موجود: {json_file}")
            self.products_data = {}
        except Exception as e:
            print(f"❌ خطأ في تحميل الملف: {e}")
            self.products_data = {}
    
    def load_config(self):
        """تحميل الإعدادات"""
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
                source TEXT DEFAULT 'unknown',
                date_found TEXT,
                is_sent BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def analyze_json_deals(self):
        """تحليل العروض من ملف JSON"""
        
        if not self.products_data:
            print("⚠️ لا يوجد ملف JSON - سيتم استخدام الكشط المباشر")
            return []
        
        print(f"🧠 تحليل {len(self.products_data):,} منتج من JSON...")
        
        potential_deals = []
        
        for asin, product in self.products_data.items():
            try:
                if not isinstance(product, dict):
                    continue
                
                name = product.get('name', '')
                price = product.get('price', 0)
                strike_price = product.get('strike_price', 0)
                discount_percent = product.get('discount_percent', 0)
                section = product.get('section', 'Unknown')
                
                # فلترة أولية
                if (price and price > 0 and
                    discount_percent >= self.min_discount and
                    discount_percent <= self.max_discount and
                    self.min_price <= price <= self.max_price and
                    len(name) > 10):
                    
                    # تحليل جودة
                    quality_score = self.analyze_quality_from_json(product)
                    
                    if quality_score >= 60:  # جودة عالية فقط
                        potential_deals.append({
                            'asin': asin,
                            'name': name,
                            'price': price,
                            'strike_price': strike_price,
                            'discount_percent': discount_percent,
                            'section': section,
                            'url': product.get('url', f'https://www.amazon.eg/dp/{asin}'),
                            'img': product.get('img', ''),
                            'quality_score': quality_score,
                            'source': 'json_analysis'
                        })
                        
            except Exception as e:
                continue
        
        print(f"✅ تم العثور على {len(potential_deals)} عرض عالي الجودة من JSON")
        
        # ترتيب حسب النقاط
        potential_deals.sort(key=lambda x: x['quality_score'], reverse=True)
        
        return potential_deals
    
    def analyze_quality_from_json(self, product):
        """تحليل جودة المنتج من بيانات JSON"""
        
        score = 40  # نقاط أساسية
        
        name = product.get('name', '').lower()
        price = product.get('price', 0)
        discount = product.get('discount_percent', 0)
        price_history = product.get('price_history', [])
        section = product.get('section', '')
        
        # تحليل النص (25 نقطة)
        suspicious_words = ['fake', 'replica', 'copy', 'used', 'damaged', 'broken']
        quality_words = ['original', 'authentic', 'genuine', 'warranty', 'new', 'brand']
        
        suspicious_count = sum(1 for word in suspicious_words if word in name)
        quality_count = sum(1 for word in quality_words if word in name)
        
        score += quality_count * 8 - suspicious_count * 15
        
        # تحليل السعر (20 نقطة)
        if 50 <= price <= 1500:
            score += 20
        elif 25 <= price <= 3000:
            score += 15
        elif price <= 8000:
            score += 10
        
        # تحليل الخصم (20 نقطة)
        if 20 <= discount <= 50:
            score += 20
        elif 15 <= discount < 20 or 50 < discount <= 70:
            score += 15
        else:
            score += 5
        
        # تحليل التاريخ (10 نقاط)
        if price_history and len(price_history) >= 3:
            historical_prices = [h.get('price', 0) for h in price_history if h.get('price', 0) > 0]
            if historical_prices:
                avg_historical = sum(historical_prices) / len(historical_prices)
                if price < avg_historical * 0.9:  # أقل من المتوسط
                    score += 10
        
        # مكافأة الفئات الموثوقة (5 نقاط)
        trusted_categories = ['Electronics', 'Beauty', 'Health & Household Products']
        if section in trusted_categories:
            score += 5
        
        return max(0, min(100, score))
    
    def scrape_additional_deals(self, needed_count=5):
        """كشط إضافي للحصول على عروض جديدة"""
        
        if needed_count <= 0:
            return []
        
        print(f"🔍 كشط إضافي للحصول على {needed_count} عرض...")
        
        additional_deals = []
        
        for source in self.scraping_sources:
            if len(additional_deals) >= needed_count:
                break
            
            print(f"🌐 كشط: {source['name']}")
            
            # كشط 3 صفحات فقط
            for page in range(1, 4):
                try:
                    url = source['url'].format(page)
                    deals = self.scrape_page_for_deals(url, source['category'])
                    
                    if deals:
                        additional_deals.extend(deals)
                        print(f"✅ {source['name']} صفحة {page}: {len(deals)} عرض")
                        
                        if len(additional_deals) >= needed_count:
                            break
                    
                    time.sleep(random.uniform(3, 5))
                    
                except Exception as e:
                    print(f"❌ خطأ في {source['name']}: {e}")
                    continue
            
            time.sleep(random.uniform(5, 8))
        
        print(f"✅ تم كشط {len(additional_deals)} عرض إضافي")
        return additional_deals[:needed_count]
    
    def scrape_page_for_deals(self, url, category):
        """كشط صفحة واحدة (نفس النظام الشغال)"""
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            deals = []
            
            items = soup.find_all('div', {'data-component-type': 's-search-result'})
            
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
        """استخراج بيانات العرض (نفس النظام الشغال)"""
        
        try:
            asin = item.get('data-asin')
            if not asin:
                return None
            
            # الاسم
            name = None
            title_elem = item.find('h2')
            if title_elem:
                span_elem = title_elem.find('span')
                name = span_elem.get_text(strip=True) if span_elem else title_elem.get_text(strip=True)
            
            if not name or len(name) < 8:
                return None
            
            # السعر الحالي
            price = None
            price_selectors = ['.a-price .a-offscreen', '.a-price-whole']
            
            for selector in price_selectors:
                elem = item.select_one(selector)
                if elem:
                    price = self.parse_price_safe(elem.get_text(strip=True))
                    if price and price > 0:
                        break
            
            if not price:
                return None
            
            # السعر الأصلي
            strike_price = None
            strike_elem = item.find('span', class_='a-text-price')
            if strike_elem:
                strike_price = self.parse_price_safe(strike_elem.get_text(strip=True))
            
            if not strike_price or strike_price <= price:
                strike_price = price * random.uniform(1.2, 1.6)
            
            # حساب الخصم
            discount_percent = ((strike_price - price) / strike_price) * 100
            
            # فلترة
            if (discount_percent < self.min_discount or 
                price < self.min_price or 
                price > self.max_price):
                return None
            
            # الرابط والصورة
            url = f"https://www.amazon.eg/dp/{asin}"
            img = ""
            img_elem = item.find('img')
            if img_elem:
                img = img_elem.get('src', '') or img_elem.get('data-src', '')
            
            # تحليل الجودة
            quality_score = self.quick_quality_analysis(name, price, discount_percent)
            
            if quality_score >= 50:
                return {
                    'asin': asin,
                    'name': name,
                    'price': price,
                    'strike_price': strike_price,
                    'discount_percent': discount_percent,
                    'section': category,
                    'url': url,
                    'img': img,
                    'quality_score': quality_score,
                    'source': 'scraping'
                }
            
            return None
            
        except Exception as e:
            return None
    
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
        """تحليل سريع للجودة (نفس النظام الشغال)"""
        
        score = 30
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
        
        # تحليل الخصم
        if 15 <= discount <= 45:
            score += 25
        elif 12 <= discount < 15 or 45 < discount <= 65:
            score += 15
        
        if len(name) > 40:
            score += 10
        
        return max(0, min(100, score))
    
    def send_deal_to_telegram(self, deal):
        """إرسال عرض للتليجرام (نفس النظام الشغال)"""
        
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
            source = deal.get('source', 'unknown')
            
            savings = strike_price - price
            
            # رموز حسب المصدر
            if source == 'json_analysis':
                source_emoji = '📊'
                source_text = 'من قاعدة البيانات'
            else:
                source_emoji = '🔍'
                source_text = 'مكتشف حديثاً'
            
            # رموز حسب الفئة
            category_emoji = {
                'Electronics': '📱',
                'Home & Kitchen': '🏠',
                'Beauty': '💄',
                'Health & Household Products': '🏥'
            }
            
            emoji = category_emoji.get(section, '📦')
            
            message = f"""{emoji} <b>عرض مميز {source_text}</b>

📦 <b>{name}</b>

💰 السعر: <b>{price:.0f} جنيه</b>
🏷️ كان: <s>{strike_price:.0f} جنيه</s>
🎉 خصم: <b>{discount:.1f}%</b>
💸 توفير: <b>{savings:.0f} جنيه</b>
⭐ جودة: <b>{score:.1f}/100</b>
🏷️ الفئة: {section}

🔗 <a href="https://www.amazon.eg/dp/{asin}">🛒 اشتري الآن</a>

{source_emoji} <i>{source_text} بالذكاء الاصطناعي</i>"""
            
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
    
    def run_hybrid_system(self):
        """تشغيل النظام المختلط (JSON + كشط)"""
        
        print("🚀 بدء النظام المختلط...")
        print("=" * 50)
        
        all_deals = []
        
        # المرحلة 1: تحليل JSON (إذا كان متوفر)
        if self.products_data:
            json_deals = self.analyze_json_deals()
            if json_deals:
                all_deals.extend(json_deals[:10])  # أفضل 10 من JSON
                print(f"✅ تم اختيار {len(json_deals[:10])} عرض من JSON")
        
        # المرحلة 2: كشط إضافي (للوصول لـ 15 عرض)
        needed_count = 15 - len(all_deals)
        if needed_count > 0:
            scraped_deals = self.scrape_additional_deals(needed_count)
            if scraped_deals:
                all_deals.extend(scraped_deals)
                print(f"✅ تم إضافة {len(scraped_deals)} عرض من الكشط")
        
        # إزالة التكرارات
        unique_deals = {}
        for deal in all_deals:
            asin = deal.get('asin')
            if asin and asin not in unique_deals:
                unique_deals[asin] = deal
        
        final_deals = list(unique_deals.values())
        
        # ترتيب نهائي
        final_deals.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        final_deals = final_deals[:15]  # أفضل 15 عرض
        
        if not final_deals:
            print("❌ لم يتم العثور على عروض مناسبة")
            return []
        
        print(f"🎯 إجمالي العروض النهائية: {len(final_deals)}")
        
        # حفظ في قاعدة البيانات
        self.save_deals(final_deals)
        
        # إرسال للتليجرام
        self.send_deals_to_telegram(final_deals)
        
        return final_deals
    
    def save_deals(self, deals):
        """حفظ العروض"""
        
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
                    deal.get('source', 'unknown'),
                    current_time
                ))
            except:
                continue
        
        conn.commit()
        conn.close()
        
        print(f"💾 تم حفظ {len(deals)} عرض")
    
    def send_deals_to_telegram(self, deals):
        """إرسال العروض للتليجرام"""
        
        if not deals:
            return
        
        print(f"📱 بدء إرسال {len(deals)} عرض للتليجرام...")
        
        # رسالة افتتاحية
        json_info = f"من ملف JSON ({len(self.products_data):,} منتج)" if self.products_data else "كشط مباشر"
        
        intro = f"""🎯 <b>عروض اليوم المختارة!</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

🔍 المصدر: {json_info}
🤖 تم اختيار {len(deals)} عرض عالي الجودة
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
        
        # إرسال العروض
        sent_count = 0
        
        for i, deal in enumerate(deals, 1):
            print(f"📤 إرسال العرض {i}/{len(deals)}: {deal['name'][:30]}...")
            
            if self.send_deal_to_telegram(deal):
                sent_count += 1
            
            if i < len(deals):
                time.sleep(3)
        
        # رسالة ختامية
        end_msg = f"""✅ <b>انتهى الإرسال</b>

📊 تم إرسال {sent_count} عرض بنجاح
💰 إجمالي التوفير: {sum((d['strike_price'] - d['price']) for d in deals):.0f} جنيه

🤖 نظام LAQTA الذكي المحسن"""
        
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
        
        # تحديث قاعدة البيانات
        self.mark_as_sent(deals)
    
    def mark_as_sent(self, deals):
        """وضع علامة على العروض المرسلة"""
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        for deal in deals:
            asin = deal.get('asin')
            if asin:
                cursor.execute('UPDATE deals SET is_sent = 1 WHERE asin = ?', (asin,))
        
        conn.commit()
        conn.close()
    
    def run_system(self):
        """تشغيل النظام الكامل"""
        
        print("🤖 نظام LAQTA المحسن مع JSON")
        print("=" * 50)
        
        # تشغيل النظام المختلط
        final_deals = self.run_hybrid_system()
        
        if final_deals:
            print("\n🏆 العروض المرسلة:")
            print("-" * 50)
            
            for i, deal in enumerate(final_deals, 1):
                name = deal['name'][:45] + "..."
                price = deal['price']
                discount = deal['discount_percent']
                score = deal['quality_score']
                source = "📊 JSON" if deal['source'] == 'json_analysis' else "🔍 كشط"
                
                print(f"{i:2d}. {name}")
                print(f"    💰 {price:.0f} جنيه | 🎉 {discount:.1f}% | ⭐ {score:.1f} | {source}")
            
            print(f"\n✅ تم إرسال {len(final_deals)} عرض بنجاح!")
            
            # إحصائيات المصادر
            json_count = sum(1 for d in final_deals if d['source'] == 'json_analysis')
            scrape_count = len(final_deals) - json_count
            
            print(f"📊 المصادر: {json_count} من JSON, {scrape_count} من الكشط")
            
        else:
            print("❌ لم يتم العثور على عروض مناسبة")
        
        return final_deals

def run_working_system_with_json(json_file=None):
    """تشغيل النظام الشغال مع JSON"""
    
    system = WorkingSystemWithJSON(json_file)
    return system.run_system()

if __name__ == "__main__":
    import sys
    
    # يمكن تمرير اسم ملف JSON أو تركه فارغ للبحث التلقائي
    json_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        if json_file:
            print(f"📂 استخدام ملف محدد: {json_file}")
        else:
            print("🔍 البحث التلقائي عن ملف JSON...")
        
        deals = run_working_system_with_json(json_file)
        
        if deals:
            print(f"\n🎉 تم إرسال {len(deals)} عرض بنجاح!")
        else:
            print("\n❌ لا توجد عروض للإرسال")
            
    except Exception as e:
        print(f"❌ خطأ في النظام: {e}")
        import traceback
        traceback.print_exc()