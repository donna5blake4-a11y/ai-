# json_based_system.py - نظام يعتمد على ملف JSON بدلاً من الكشط

import json
import sqlite3
import requests
import time
import re
from datetime import datetime, timedelta
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

class JSONBasedSmartSystem:
    """نظام ذكي يعتمد على ملف JSON + تحديث أسعار انتقائي"""
    
    def __init__(self, json_file_path="products.json"):
        self.json_file = json_file_path
        self.db_file = "json_smart_deals.db"
        self.products_data = {}
        
        self.setup_database()
        self.load_config()
        self.load_products_data()
        
        # إعدادات الفلترة
        self.min_discount = 15
        self.max_discount = 85
        self.min_price = 25
        self.max_price = 8000
        
        # كلمات مشبوهة
        self.suspicious_words = [
            'fake', 'replica', 'copy', 'imitation', 'used', 'damaged', 'broken',
            'refurbished', 'second hand', 'مستعمل', 'مقلد', 'نسخة', 'تقليد'
        ]
        
        # مؤشرات الجودة
        self.quality_indicators = [
            'original', 'authentic', 'genuine', 'warranty', 'new', 'brand new',
            'authorized', 'official', 'أصلي', 'ضمان', 'جديد', 'معتمد', 'رسمي'
        ]
        
        # فئات موثوقة
        self.trusted_categories = [
            'Electronics', 'Home & Kitchen', 'Beauty', 'Health & Household Products',
            'Tools & Home Improvement', 'Automotive', 'Fashion', 'Grocery'
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
                historical_score REAL DEFAULT 0,
                current_price_checked BOOLEAN DEFAULT 0,
                last_price_check TEXT,
                quality_level TEXT DEFAULT 'unknown',
                date_added TEXT,
                is_sent BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def load_products_data(self):
        """تحميل بيانات المنتجات من JSON"""
        
        print(f"📂 جاري تحميل ملف JSON: {self.json_file}")
        
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.products_data = json.load(f)
            
            print(f"✅ تم تحميل {len(self.products_data):,} منتج من الملف")
            
        except FileNotFoundError:
            print(f"❌ الملف غير موجود: {self.json_file}")
            print("💡 ضع ملف JSON في نفس المجلد وأعد التشغيل")
            self.products_data = {}
        except Exception as e:
            print(f"❌ خطأ في تحميل الملف: {e}")
            self.products_data = {}
    
    def analyze_historical_data(self):
        """تحليل البيانات التاريخية للعثور على أفضل العروض"""
        
        print("🧠 بدء تحليل البيانات التاريخية...")
        
        if not self.products_data:
            print("❌ لا توجد بيانات للتحليل")
            return []
        
        potential_deals = []
        
        for asin, product in self.products_data.items():
            try:
                # التحقق من البيانات الأساسية
                if not isinstance(product, dict):
                    continue
                
                name = product.get('name', '')
                price = product.get('price', 0)
                strike_price = product.get('strike_price', 0)
                discount_percent = product.get('discount_percent', 0)
                section = product.get('section', '')
                price_history = product.get('price_history', [])
                
                # فلترة أولية
                if (price and price > 0 and
                    discount_percent >= self.min_discount and
                    discount_percent <= self.max_discount and
                    self.min_price <= price <= self.max_price and
                    section in self.trusted_categories):
                    
                    # تحليل تاريخ الأسعار
                    historical_analysis = self.analyze_price_history(price_history, price)
                    
                    # تحليل نصي
                    text_analysis = self.analyze_product_text(name)
                    
                    # تحليل الخصم
                    discount_analysis = self.analyze_discount_validity(price, strike_price, discount_percent)
                    
                    # حساب النقاط الإجمالية
                    total_score = (
                        historical_analysis['score'] * 0.4 +
                        text_analysis['score'] * 0.3 +
                        discount_analysis['score'] * 0.3
                    )
                    
                    if total_score >= 40:  # حد أدنى للقبول
                        potential_deals.append({
                            'asin': asin,
                            'name': name,
                            'price': price,
                            'strike_price': strike_price,
                            'discount_percent': discount_percent,
                            'section': section,
                            'url': product.get('url', ''),
                            'img': product.get('img', ''),
                            'price_history': price_history,
                            'historical_score': historical_analysis['score'],
                            'text_score': text_analysis['score'],
                            'discount_score': discount_analysis['score'],
                            'total_score': total_score,
                            'analysis_reasons': (
                                historical_analysis['reasons'] +
                                text_analysis['reasons'] +
                                discount_analysis['reasons']
                            )
                        })
                        
            except Exception as e:
                continue
        
        print(f"✅ تم العثور على {len(potential_deals)} عرض محتمل من التحليل التاريخي")
        
        # ترتيب حسب النقاط
        potential_deals.sort(key=lambda x: x['total_score'], reverse=True)
        
        return potential_deals
    
    def analyze_price_history(self, price_history, current_price):
        """تحليل تاريخ الأسعار"""
        
        if not price_history or len(price_history) < 3:
            return {
                'score': 20,  # نقاط متوسطة لعدم وجود تاريخ كافي
                'reasons': ['تاريخ أسعار محدود']
            }
        
        try:
            # استخراج الأسعار التاريخية
            historical_prices = []
            for entry in price_history:
                if isinstance(entry, dict) and entry.get('price'):
                    historical_prices.append(float(entry['price']))
            
            if not historical_prices:
                return {'score': 20, 'reasons': ['لا توجد أسعار تاريخية صحيحة']}
            
            # حساب الإحصائيات
            avg_price = sum(historical_prices) / len(historical_prices)
            min_price = min(historical_prices)
            max_price = max(historical_prices)
            
            score = 0
            reasons = []
            
            # مقارنة السعر الحالي مع التاريخ
            if current_price <= min_price:
                score += 40
                reasons.append(f'أقل سعر تاريخي ({current_price:.0f} ≤ {min_price:.0f})')
            elif current_price < avg_price * 0.85:
                score += 30
                savings = avg_price - current_price
                reasons.append(f'أقل من المتوسط بـ {savings:.0f} جنيه')
            elif current_price < avg_price:
                score += 20
                reasons.append('أقل من المتوسط التاريخي')
            
            # فحص استقرار الأسعار
            price_variance = (max_price - min_price) / avg_price
            if price_variance < 0.3:
                score += 10
                reasons.append('أسعار مستقرة تاريخياً')
            
            return {
                'score': min(50, score),
                'reasons': reasons,
                'avg_price': avg_price,
                'min_price': min_price,
                'max_price': max_price
            }
            
        except Exception as e:
            return {'score': 15, 'reasons': [f'خطأ في تحليل التاريخ: {e}']}
    
    def analyze_product_text(self, name):
        """تحليل نص المنتج"""
        
        if not name:
            return {'score': 0, 'reasons': ['اسم المنتج فارغ']}
        
        name_lower = name.lower()
        score = 0
        reasons = []
        
        # فحص الكلمات المشبوهة
        suspicious_found = [word for word in self.suspicious_words if word in name_lower]
        if suspicious_found:
            score -= len(suspicious_found) * 15
            reasons.append(f'كلمات مشبوهة: {", ".join(suspicious_found)}')
        
        # فحص مؤشرات الجودة
        quality_found = [word for word in self.quality_indicators if word in name_lower]
        if quality_found:
            score += len(quality_found) * 10
            reasons.append(f'مؤشرات جودة: {", ".join(quality_found)}')
        
        # فحص طول الاسم (أسماء طويلة عادة أفضل)
        if len(name) > 50:
            score += 5
            reasons.append('اسم مفصل')
        
        # فحص وجود أرقام (مواصفات تقنية)
        if re.search(r'\d+', name):
            score += 5
            reasons.append('يحتوي على مواصفات رقمية')
        
        return {
            'score': max(0, min(30, score + 15)),  # إضافة 15 نقطة أساسية
            'reasons': reasons or ['تحليل نصي عادي']
        }
    
    def analyze_discount_validity(self, price, strike_price, discount_percent):
        """تحليل صحة الخصم"""
        
        if not all([price, strike_price, discount_percent]):
            return {'score': 10, 'reasons': ['بيانات خصم ناقصة']}
        
        score = 0
        reasons = []
        
        # فحص منطقية الخصم
        calculated_discount = ((strike_price - price) / strike_price) * 100
        
        if abs(calculated_discount - discount_percent) <= 2:
            score += 20
            reasons.append('حساب خصم صحيح')
        elif abs(calculated_discount - discount_percent) <= 5:
            score += 15
            reasons.append('حساب خصم مقبول')
        else:
            score += 5
            reasons.append('حساب خصم غير دقيق')
        
        # فحص معقولية نسبة الخصم
        if 15 <= discount_percent <= 50:
            score += 15
            reasons.append(f'خصم معقول ({discount_percent:.1f}%)')
        elif 50 < discount_percent <= 70:
            score += 10
            reasons.append(f'خصم عالي ({discount_percent:.1f}%)')
        else:
            score += 5
            reasons.append(f'خصم مشكوك فيه ({discount_percent:.1f}%)')
        
        return {
            'score': min(25, score),
            'reasons': reasons
        }
    
    def check_current_price_sample(self, deals_sample):
        """فحص الأسعار الحالية لعينة من العروض الأفضل"""
        
        if not self.scraper_api_key or not deals_sample:
            print("⚠️ لا يمكن فحص الأسعار الحالية - ScraperAPI غير متوفر")
            return deals_sample
        
        print(f"💰 فحص الأسعار الحالية لأفضل {len(deals_sample)} عرض...")
        
        updated_deals = []
        
        # فحص أفضل 20 عرض فقط لتوفير التكلفة
        sample_to_check = deals_sample[:20]
        
        for i, deal in enumerate(sample_to_check):
            try:
                asin = deal.get('asin')
                if not asin:
                    updated_deals.append(deal)
                    continue
                
                print(f"🔍 فحص {i+1}/{len(sample_to_check)}: {deal['name'][:40]}...")
                
                # فحص السعر الحالي
                current_data = self.get_current_price(asin)
                
                if current_data:
                    # تحديث البيانات
                    deal['current_price'] = current_data['price']
                    deal['current_available'] = current_data['available']
                    deal['price_updated'] = True
                    
                    # إعادة حساب الخصم مع السعر الحالي
                    if current_data['price'] and deal.get('strike_price'):
                        new_discount = ((deal['strike_price'] - current_data['price']) / deal['strike_price']) * 100
                        deal['current_discount'] = max(0, new_discount)
                        
                        # قبول العرض إذا كان السعر الحالي لا يزال جيداً
                        if new_discount >= 10 and current_data['available']:
                            deal['final_score'] = deal['total_score'] + 10  # مكافأة للتوفر
                            updated_deals.append(deal)
                            print(f"✅ متوفر بخصم {new_discount:.1f}%")
                        else:
                            print(f"❌ السعر تغير أو غير متوفر")
                    else:
                        # إذا لم نستطع التحقق، نبقي العرض
                        deal['final_score'] = deal['total_score']
                        updated_deals.append(deal)
                        print(f"⚠️ لم يمكن التحقق من السعر")
                else:
                    # إذا فشل فحص السعر، نبقي العرض كما هو
                    deal['final_score'] = deal['total_score']
                    updated_deals.append(deal)
                    print(f"⚠️ فشل فحص السعر - الاحتفاظ بالعرض")
                
                # تأخير لتجنب الحظر
                if i % 5 == 0:
                    time.sleep(3)
                else:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"⚠️ خطأ في فحص {deal.get('name', 'منتج')}: {e}")
                # الاحتفاظ بالعرض حتى مع الخطأ
                deal['final_score'] = deal['total_score']
                updated_deals.append(deal)
                continue
        
        # إضافة باقي العروض بدون فحص (لتوفير التكلفة)
        for deal in deals_sample[20:]:
            deal['final_score'] = deal['total_score']
            updated_deals.append(deal)
        
        print(f"✅ تم فحص الأسعار وتحديث {len(updated_deals)} عرض")
        
        # إعادة ترتيب بناء على النقاط المحدثة
        updated_deals.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        return updated_deals
    
    def get_current_price(self, asin):
        """الحصول على السعر الحالي لمنتج واحد"""
        
        if not self.scraper_api_key:
            return None
        
        try:
            url = f"https://api.scraperapi.com/?api_key={self.scraper_api_key}&url=https://www.amazon.eg/dp/{asin}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # فحص التوفر
                unavailable_indicators = [
                    'currently unavailable', 'غير متوفر', 'out of stock',
                    'temporarily out of stock', 'نفد المخزون'
                ]
                
                is_available = True
                for indicator in unavailable_indicators:
                    if indicator in content:
                        is_available = False
                        break
                
                # استخراج السعر
                price = self.extract_price_from_html(response.text)
                
                return {
                    'price': price,
                    'available': is_available,
                    'checked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
            return None
            
        except Exception as e:
            print(f"⚠️ خطأ في فحص السعر: {e}")
            return None
    
    def extract_price_from_html(self, html):
        """استخراج السعر من HTML"""
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # البحث عن السعر بطرق متعددة
            price_selectors = [
                '.a-price .a-offscreen',
                '.a-price-whole',
                '#price_inside_buybox',
                '.a-price .a-price-whole'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = self.parse_price_safe(price_text)
                    if price and price > 0:
                        return price
            
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
                return float(numbers[0])
            
            return None
            
        except:
            return None
    
    def select_best_deals(self, potential_deals, target_count=15):
        """انتقاء أفضل العروض مع التنويع"""
        
        print(f"🎯 انتقاء أفضل {target_count} عرض من {len(potential_deals)} عرض محتمل...")
        
        if not potential_deals:
            return []
        
        # تنويع الاختيار
        selected_deals = []
        category_counts = {}
        
        for deal in potential_deals:
            if len(selected_deals) >= target_count:
                break
            
            category = deal.get('section', 'Unknown')
            
            # حد أقصى 3 عروض لكل فئة
            if category_counts.get(category, 0) < 3:
                selected_deals.append(deal)
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # إذا لم نصل للعدد المطلوب، أضف المزيد
        for deal in potential_deals:
            if len(selected_deals) >= target_count:
                break
            
            if deal not in selected_deals:
                selected_deals.append(deal)
        
        print(f"✅ تم انتقاء {len(selected_deals)} عرض مع التنويع")
        
        return selected_deals[:target_count]
    
    def save_deals_to_db(self, deals):
        """حفظ العروض في قاعدة البيانات"""
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        saved_count = 0
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for deal in deals:
            try:
                score = deal.get('final_score', deal.get('total_score', 0))
                
                # تحديد مستوى الجودة
                if score >= 80:
                    quality_level = 'excellent'
                elif score >= 65:
                    quality_level = 'very_good'
                elif score >= 50:
                    quality_level = 'good'
                elif score >= 35:
                    quality_level = 'fair'
                else:
                    quality_level = 'acceptable'
                
                cursor.execute('''
                    INSERT OR REPLACE INTO deals 
                    (asin, name, price, strike_price, discount_percent, section, url, img, 
                     smart_score, historical_score, quality_level, date_added)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    deal.get('historical_score', 0),
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
        
        # رسالة واحدة مع أفضل 10 عروض
        message = f"🎯 <b>أفضل {min(len(deals), 10)} عرض اليوم</b>\n"
        message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        message += f"🧠 <b>تحليل ذكي من {len(self.products_data):,} منتج</b>\n\n"
        
        for i, deal in enumerate(deals[:10], 1):
            name = deal.get('name', 'منتج')[:45] + "..."
            price = deal.get('price', 0)
            strike_price = deal.get('strike_price', 0)
            discount = deal.get('discount_percent', 0)
            score = deal.get('final_score', deal.get('total_score', 0))
            
            savings = strike_price - price
            
            message += f"<b>{i}. {name}</b>\n"
            message += f"💰 {price:.0f} جنيه"
            
            # إضافة معلومات السعر المحدث إن وجدت
            if deal.get('current_price') and deal.get('price_updated'):
                current_price = deal['current_price']
                if current_price != price:
                    message += f" (الآن: {current_price:.0f} جنيه)"
            
            message += f"\n🏷️ كان: {strike_price:.0f} جنيه\n"
            message += f"🎉 خصم {discount:.1f}% (توفير {savings:.0f} جنيه)\n"
            message += f"⭐ جودة: {score:.1f}/100\n"
            
            if deal.get('asin'):
                message += f"🔗 <a href='https://www.amazon.eg/dp/{deal['asin']}'>رابط المنتج</a>\n"
            
            message += "\n"
        
        message += "🤖 <i>تحليل ذكي من قاعدة بيانات ضخمة + فحص أسعار حالية</i>"
        
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
        """تشغيل التحليل الكامل"""
        
        print("🚀 بدء النظام الذكي المعتمد على JSON...")
        print("=" * 60)
        
        if not self.products_data:
            print("❌ لا توجد بيانات للتحليل")
            print("💡 تأكد من وجود ملف JSON في نفس المجلد")
            return []
        
        # مرحلة 1: تحليل البيانات التاريخية
        potential_deals = self.analyze_historical_data()
        
        if not potential_deals:
            print("❌ لم يتم العثور على عروض محتملة")
            return []
        
        # مرحلة 2: انتقاء الأفضل
        selected_deals = self.select_best_deals(potential_deals, target_count=25)  # نختار 25 أولاً
        
        # مرحلة 3: فحص الأسعار الحالية لأفضل العروض
        updated_deals = self.check_current_price_sample(selected_deals)
        
        # مرحلة 4: الاختيار النهائي
        final_deals = updated_deals[:15]  # أفضل 15 عرض نهائي
        
        # مرحلة 5: حفظ النتائج
        saved_count = self.save_deals_to_db(final_deals)
        
        # مرحلة 6: إرسال للتليجرام
        self.send_deals_to_telegram(final_deals)
        
        # عرض النتائج
        print("\n🏆 أفضل العروض المختارة:")
        print("=" * 70)
        
        for i, deal in enumerate(final_deals, 1):
            name = deal.get('name', 'منتج')[:50] + "..."
            price = deal.get('price', 0)
            discount = deal.get('discount_percent', 0)
            score = deal.get('final_score', 0)
            
            print(f"{i:2d}. {name}")
            print(f"    💰 {price:.0f} جنيه | 🎉 {discount:.1f}% | ⭐ {score:.1f}")
            
            # عرض أسباب الاختيار
            reasons = deal.get('analysis_reasons', [])
            if reasons:
                print(f"    📝 الأسباب: {', '.join(reasons[:2])}")
        
        print(f"\n✅ تم اختيار وإرسال {len(final_deals)} عرض عالي الجودة!")
        print(f"📊 من أصل {len(self.products_data):,} منتج في قاعدة البيانات")
        
        return final_deals

def run_json_system(json_file="products.json"):
    """تشغيل النظام المعتمد على JSON"""
    
    system = JSONBasedSmartSystem(json_file)
    return system.run_complete_analysis()

if __name__ == "__main__":
    import sys
    
    # يمكن تمرير اسم ملف JSON كمعامل
    json_file = sys.argv[1] if len(sys.argv) > 1 else "products.json"
    
    try:
        print(f"📂 استخدام ملف: {json_file}")
        run_json_system(json_file)
    except Exception as e:
        print(f"❌ خطأ في النظام: {e}")
        import traceback
        traceback.print_exc()