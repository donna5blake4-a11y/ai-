# fixed_integrated_system.py - نظام محسن بدون أخطاء

import asyncio
import json
import sqlite3
import requests
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import quote

class FixedSmartSystem:
    """نظام محسن بدون أخطاء NoneType"""
    
    def __init__(self):
        self.db_file = "fixed_smart_deals.db"
        self.setup_database()
        self.load_config()
        
        # إعدادات محسنة
        self.min_discount = 15  # قللنا الحد الأدنى
        self.max_discount = 90  # زودنا الحد الأقصى
        self.min_price = 20     # قللنا الحد الأدنى
        self.max_price = 10000  # زودنا الحد الأقصى
        
        # فئات موثوقة
        self.trusted_categories = [
            'Electronics', 'Home & Kitchen', 'Beauty', 'Health & Household Products',
            'Tools & Home Improvement', 'Automotive', 'Fashion', 'Grocery'
        ]
        
        # كلمات مشبوهة
        self.suspicious_words = [
            'fake', 'replica', 'copy', 'imitation', 'used', 'damaged', 'broken',
            'refurbished', 'second hand', 'مستعمل', 'مقلد', 'نسخة'
        ]
        
        # مؤشرات الجودة
        self.quality_indicators = [
            'original', 'authentic', 'genuine', 'warranty', 'new', 'brand new',
            'authorized', 'official', 'أصلي', 'ضمان', 'جديد', 'معتمد'
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
    
    def scrape_amazon_safely(self):
        """كشط آمن من أمازون"""
        
        print("🔍 بدء الكشط الآمن من أمازون...")
        
        # روابط محسنة للكشط
        safe_urls = [
            # Electronics - صفحات مختلفة
            "https://www.amazon.eg/s?k=electronics&rh=p_36%3A1000-50000&page={}",
            "https://www.amazon.eg/s?k=mobile+phone&rh=p_36%3A1000-30000&page={}",
            "https://www.amazon.eg/s?k=laptop&rh=p_36%3A5000-50000&page={}",
            
            # Home & Kitchen
            "https://www.amazon.eg/s?k=kitchen&rh=p_36%3A100-5000&page={}",
            "https://www.amazon.eg/s?k=home+appliances&rh=p_36%3A500-10000&page={}",
            
            # Beauty
            "https://www.amazon.eg/s?k=beauty&rh=p_36%3A50-2000&page={}",
            "https://www.amazon.eg/s?k=skincare&rh=p_36%3A100-1000&page={}",
            
            # Health
            "https://www.amazon.eg/s?k=health&rh=p_36%3A50-2000&page={}",
            
            # Tools
            "https://www.amazon.eg/s?k=tools&rh=p_36%3A100-5000&page={}",
        ]
        
        all_products = []
        
        for url_template in safe_urls:
            print(f"🌐 كشط من: {url_template.split('k=')[1].split('&')[0]}")
            
            # كشط 5 صفحات من كل رابط
            for page in range(1, 6):
                try:
                    url = url_template.format(page)
                    products = self.scrape_single_page_safe(url)
                    
                    if products:
                        all_products.extend(products)
                        print(f"✅ صفحة {page}: {len(products)} منتج")
                    else:
                        print(f"⚠️ صفحة {page}: لا توجد منتجات")
                    
                    # تأخير بين الصفحات
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"❌ خطأ في الصفحة {page}: {e}")
                    continue
            
            # تأخير بين الفئات
            time.sleep(3)
        
        print(f"✅ تم كشط {len(all_products)} منتج إجمالي")
        return all_products
    
    def scrape_single_page_safe(self, url):
        """كشط صفحة واحدة بأمان"""
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # البحث عن المنتجات
            products = []
            items = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            for item in items:
                product = self.extract_product_safe(item)
                if product:
                    products.append(product)
            
            return products
            
        except Exception as e:
            print(f"⚠️ خطأ في كشط الصفحة: {e}")
            return []
    
    def extract_product_safe(self, item):
        """استخراج بيانات المنتج بأمان"""
        
        try:
            # ASIN
            asin = item.get('data-asin')
            if not asin or asin.strip() == "":
                return None
            
            # الاسم
            title_elem = item.find('h2')
            if title_elem:
                span_elem = title_elem.find('span')
                name = span_elem.get_text(strip=True) if span_elem else title_elem.get_text(strip=True)
            else:
                name = "Unknown Product"
            
            # السعر الحالي - تجربة عدة طرق
            price = None
            
            # طريقة 1: البحث في a-price
            price_elem = item.find('span', class_='a-price-whole')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self.parse_price_safe(price_text)
            
            # طريقة 2: البحث في a-offscreen
            if not price:
                price_elem = item.find('span', class_='a-offscreen')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = self.parse_price_safe(price_text)
            
            # طريقة 3: البحث في أي span يحتوي على "EGP"
            if not price:
                all_spans = item.find_all('span')
                for span in all_spans:
                    text = span.get_text(strip=True)
                    if 'EGP' in text or 'جنيه' in text:
                        price = self.parse_price_safe(text)
                        if price:
                            break
            
            # إذا لم نجد سعر، نتجاهل المنتج
            if not price or price <= 0:
                return None
            
            # السعر الأصلي (strike price)
            strike_price = None
            strike_elem = item.find('span', class_='a-text-price')
            if strike_elem:
                strike_text = strike_elem.get_text(strip=True)
                strike_price = self.parse_price_safe(strike_text)
            
            # حساب الخصم بأمان
            discount_percent = 0
            if strike_price and strike_price > 0 and price and price > 0:
                if strike_price > price:
                    discount_percent = ((strike_price - price) / strike_price) * 100
            
            # فلترة أولية
            if discount_percent < self.min_discount:
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
                img = img_elem.get('src', '') or img_elem.get('data-src', '')
            
            # تحديد الفئة من URL
            section = self.determine_category_from_url_and_name(url, name)
            
            return {
                'asin': asin,
                'name': name,
                'price': price,
                'strike_price': strike_price or price * 1.2,  # افتراضي إذا لم يوجد
                'discount_percent': discount_percent,
                'section': section,
                'url': url,
                'img': img,
                'price_history': []
            }
            
        except Exception as e:
            print(f"⚠️ خطأ في استخراج المنتج: {e}")
            return None
    
    def parse_price_safe(self, price_text):
        """تحليل آمن للأسعار مع معالجة جميع الحالات"""
        
        if not price_text:
            return None
        
        try:
            # إزالة جميع الرموز والكلمات
            cleaned = re.sub(r'[^\d.,]', '', str(price_text))
            
            # إزالة الفواصل
            cleaned = cleaned.replace(',', '')
            
            # البحث عن الرقم
            numbers = re.findall(r'\d+\.?\d*', cleaned)
            
            if numbers:
                return float(numbers[0])
            
            return None
            
        except Exception as e:
            return None
    
    def determine_category_from_url_and_name(self, url, name):
        """تحديد الفئة من الرابط والاسم"""
        
        name_lower = name.lower()
        url_lower = url.lower()
        
        # تحديد الفئة بناء على الكلمات المفتاحية
        if any(word in name_lower for word in ['phone', 'iphone', 'samsung', 'laptop', 'electronics']):
            return 'Electronics'
        elif any(word in name_lower for word in ['kitchen', 'home', 'furniture', 'appliance']):
            return 'Home & Kitchen'
        elif any(word in name_lower for word in ['beauty', 'skincare', 'makeup', 'cosmetic']):
            return 'Beauty'
        elif any(word in name_lower for word in ['health', 'medical', 'vitamin', 'supplement']):
            return 'Health & Household Products'
        elif any(word in name_lower for word in ['tool', 'drill', 'hammer', 'repair']):
            return 'Tools & Home Improvement'
        elif any(word in name_lower for word in ['car', 'auto', 'vehicle', 'tire']):
            return 'Automotive'
        elif any(word in name_lower for word in ['fashion', 'clothing', 'shirt', 'dress']):
            return 'Fashion'
        elif any(word in name_lower for word in ['food', 'grocery', 'snack', 'drink']):
            return 'Grocery'
        else:
            return 'Electronics'  # افتراضي
    
    def filter_deals_enhanced(self, products, target_count=15):
        """فلترة محسنة للعروض"""
        
        print(f"🔍 بدء فلترة {len(products)} منتج...")
        
        if not products:
            print("❌ لا توجد منتجات للفلترة")
            return []
        
        # مرحلة 1: فلترة أساسية محسنة
        basic_filtered = []
        
        for product in products:
            # فحص البيانات الأساسية بأمان
            price = product.get('price') or 0
            discount = product.get('discount_percent') or 0
            strike_price = product.get('strike_price') or 0
            name = product.get('name') or ""
            section = product.get('section') or ""
            
            # شروط أساسية مرنة
            if (self.min_price <= price <= self.max_price and
                discount >= self.min_discount and
                discount <= self.max_discount and
                strike_price > price and
                len(name) > 5):  # اسم معقول
                
                basic_filtered.append(product)
        
        print(f"✅ المرحلة 1: {len(basic_filtered)} منتج اجتاز الفلترة الأساسية")
        
        # مرحلة 2: تحليل نصي محسن
        text_filtered = []
        
        for product in basic_filtered:
            name = (product.get('name') or "").lower()
            
            # فحص الكلمات المشبوهة
            suspicious_count = sum(1 for word in self.suspicious_words if word in name)
            
            # فحص مؤشرات الجودة
            quality_count = sum(1 for indicator in self.quality_indicators if indicator in name)
            
            # نقاط النص
            text_score = quality_count * 10 - suspicious_count * 15
            product['text_score'] = text_score
            
            # قبول المنتجات ذات النقاط الإيجابية أو المحايدة
            if text_score >= -10:  # مرونة أكثر
                text_filtered.append(product)
        
        print(f"✅ المرحلة 2: {len(text_filtered)} منتج اجتاز التحليل النصي")
        
        # مرحلة 3: تحليل منطقية السعر
        price_filtered = []
        
        for product in text_filtered:
            price = product.get('price') or 0
            strike_price = product.get('strike_price') or 0
            discount = product.get('discount_percent') or 0
            
            # فحص منطقية الخصم
            if strike_price > 0 and price > 0:
                calculated_discount = ((strike_price - price) / strike_price) * 100
                
                # هامش خطأ أكبر للمرونة
                if abs(calculated_discount - discount) <= 5:
                    price_score = 20
                else:
                    price_score = 10  # نقاط أقل لكن لا نستبعد
                
                product['price_score'] = price_score
                price_filtered.append(product)
        
        print(f"✅ المرحلة 3: {len(price_filtered)} منتج اجتاز تحليل الأسعار")
        
        # مرحلة 4: حساب النقاط النهائية
        for product in price_filtered:
            final_score = 0
            
            # نقاط الخصم (50%)
            discount = product.get('discount_percent') or 0
            final_score += min(50, discount * 0.8)
            
            # نقاط النص (30%)
            text_score = product.get('text_score') or 0
            final_score += min(30, max(0, text_score + 10))  # إضافة 10 للمرونة
            
            # نقاط السعر (20%)
            price_score = product.get('price_score') or 10
            final_score += min(20, price_score)
            
            product['final_score'] = final_score
        
        # ترتيب وانتقاء الأفضل
        sorted_products = sorted(price_filtered, key=lambda x: x.get('final_score', 0), reverse=True)
        
        # تنويع الاختيار
        final_deals = self.diversify_selection(sorted_products, target_count)
        
        print(f"🎯 النتيجة النهائية: {len(final_deals)} عرض عالي الجودة")
        
        return final_deals
    
    def diversify_selection(self, sorted_products, target_count):
        """تنويع الاختيار عبر الفئات والأسعار"""
        
        selected = []
        category_counts = {}
        price_ranges = {}
        
        for product in sorted_products:
            if len(selected) >= target_count:
                break
            
            category = product.get('section', 'Unknown')
            price = product.get('price', 0)
            
            # تحديد نطاق السعر
            if price < 100:
                price_range = 'low'
            elif price < 1000:
                price_range = 'medium'
            else:
                price_range = 'high'
            
            # حد أقصى 4 منتجات لكل فئة
            # حد أقصى 6 منتجات لكل نطاق سعري
            if (category_counts.get(category, 0) < 4 and
                price_ranges.get(price_range, 0) < 6):
                
                selected.append(product)
                category_counts[category] = category_counts.get(category, 0) + 1
                price_ranges[price_range] = price_ranges.get(price_range, 0) + 1
        
        return selected
    
    def save_deals_to_db(self, deals):
        """حفظ العروض في قاعدة البيانات"""
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        saved_count = 0
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for deal in deals:
            try:
                # تحديد مستوى الجودة
                score = deal.get('final_score', 0)
                if score >= 70:
                    quality_level = 'excellent'
                elif score >= 50:
                    quality_level = 'good'
                elif score >= 30:
                    quality_level = 'fair'
                else:
                    quality_level = 'poor'
                
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
        
        # تنسيق الرسالة
        message = f"🎯 <b>أفضل {len(deals)} عرض اليوم</b>\n"
        message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        for i, deal in enumerate(deals[:10], 1):  # أول 10 عروض
            name = (deal.get('name', 'منتج') or 'منتج')[:50] + "..."
            price = deal.get('price') or 0
            strike_price = deal.get('strike_price') or 0
            discount = deal.get('discount_percent') or 0
            score = deal.get('final_score') or 0
            
            savings = strike_price - price
            
            message += f"<b>{i}. {name}</b>\n"
            message += f"💰 السعر: {price:.0f} جنيه\n"
            message += f"🏷️ السعر الأصلي: {strike_price:.0f} جنيه\n"
            message += f"🎉 الخصم: {discount:.1f}% (توفير {savings:.0f} جنيه)\n"
            message += f"⭐ نقاط الجودة: {score:.1f}/100\n"
            
            if deal.get('asin'):
                message += f"🔗 <a href='https://www.amazon.eg/dp/{deal['asin']}'>رابط المنتج</a>\n"
            
            message += "\n"
        
        message += "🤖 <i>تم اختيار هذه العروض بواسطة النظام الذكي المحسن</i>"
        
        # إرسال للمستخدمين
        sent_count = 0
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
                    sent_count += 1
                    print(f"✅ تم إرسال العروض للمستخدم {user_id}")
                else:
                    print(f"❌ فشل إرسال العروض للمستخدم {user_id}")
                    
            except Exception as e:
                print(f"⚠️ خطأ في إرسال التليجرام: {e}")
        
        print(f"📱 تم إرسال العروض لـ {sent_count} مستخدم")
    
    def run_complete_analysis(self):
        """تشغيل التحليل الكامل المحسن"""
        
        print("🚀 بدء النظام الذكي المحسن...")
        print("=" * 60)
        
        # مرحلة 1: كشط آمن
        all_products = self.scrape_amazon_safely()
        
        if not all_products:
            print("❌ لم يتم العثور على منتجات")
            return
        
        # مرحلة 2: فلترة ذكية
        best_deals = self.filter_deals_enhanced(all_products, target_count=15)
        
        if not best_deals:
            print("❌ لم يتم العثور على عروض تستوفي المعايير")
            return
        
        # مرحلة 3: حفظ النتائج
        saved_count = self.save_deals_to_db(best_deals)
        
        # مرحلة 4: إرسال للتليجرام
        self.send_deals_to_telegram(best_deals)
        
        # عرض النتائج
        print("\n🏆 أفضل العروض:")
        print("=" * 60)
        
        for i, deal in enumerate(best_deals, 1):
            name = (deal.get('name') or 'منتج')[:50] + "..."
            price = deal.get('price') or 0
            discount = deal.get('discount_percent') or 0
            score = deal.get('final_score') or 0
            
            print(f"{i:2d}. {name}")
            print(f"    💰 {price:.0f} جنيه | 🎉 {discount:.1f}% | ⭐ {score:.1f}")
        
        print(f"\n✅ تم حفظ وإرسال {len(best_deals)} عرض عالي الجودة!")
        return best_deals

# دالة تشغيل مبسطة
def run_fixed_system():
    """تشغيل النظام المحسن"""
    
    system = FixedSmartSystem()
    return system.run_complete_analysis()

if __name__ == "__main__":
    try:
        run_fixed_system()
    except Exception as e:
        print(f"❌ خطأ في النظام: {e}")
        import traceback
        traceback.print_exc()