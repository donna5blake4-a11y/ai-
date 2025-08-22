# enhanced_telegram_system.py - نظام محسن مع إرسال تلقائي بالصور

import json
import sqlite3
import requests
import time
import re
from datetime import datetime
import random
from PIL import Image
from io import BytesIO
import base64

class EnhancedTelegramSystem:
    """نظام محسن مع إرسال تلقائي بالصور للتليجرام"""
    
    def __init__(self, json_file_path="products.json"):
        self.json_file = json_file_path
        self.db_file = "enhanced_telegram_deals.db"
        self.products_data = {}
        
        self.setup_database()
        self.load_config()
        self.load_products_data()
        
        # إعدادات محسنة
        self.min_discount = 15
        self.max_discount = 85
        self.min_price = 30
        self.max_price = 8000
        self.target_deals_count = 15  # عدد العروض المطلوبة
        
        # إعدادات الإرسال
        self.send_with_images = True
        self.auto_send_enabled = True
        self.max_image_size = 5 * 1024 * 1024  # 5MB
        
        # فئات موثوقة
        self.trusted_categories = [
            'Electronics', 'Home & Kitchen', 'Beauty', 'Health & Household Products',
            'Tools & Home Improvement', 'Automotive', 'Fashion', 'Grocery'
        ]
        
        # كلمات مشبوهة
        self.suspicious_words = [
            'fake', 'replica', 'copy', 'imitation', 'used', 'damaged', 'broken',
            'refurbished', 'second hand', 'مستعمل', 'مقلد', 'نسخة', 'تقليد'
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
                is_sent BOOLEAN DEFAULT 0,
                sent_at TEXT,
                image_downloaded BOOLEAN DEFAULT 0
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
    
    def analyze_and_find_deals(self):
        """تحليل البيانات والعثور على أفضل العروض"""
        
        print("🧠 بدء التحليل الذكي للبيانات...")
        
        if not self.products_data:
            print("❌ لا توجد بيانات للتحليل")
            return []
        
        potential_deals = []
        
        for asin, product in self.products_data.items():
            try:
                if not isinstance(product, dict):
                    continue
                
                name = product.get('name', '')
                price = product.get('price', 0)
                strike_price = product.get('strike_price', 0)
                discount_percent = product.get('discount_percent', 0)
                section = product.get('section', '')
                price_history = product.get('price_history', [])
                img_url = product.get('img', '')
                
                # فلترة أولية صارمة
                if (price and price > 0 and
                    discount_percent >= self.min_discount and
                    discount_percent <= self.max_discount and
                    self.min_price <= price <= self.max_price and
                    section in self.trusted_categories and
                    len(name) > 10):
                    
                    # تحليل شامل
                    analysis_score = self.comprehensive_analysis(
                        name, price, strike_price, discount_percent, 
                        price_history, section
                    )
                    
                    if analysis_score['total_score'] >= 50:  # حد أدنى صارم
                        potential_deals.append({
                            'asin': asin,
                            'name': name,
                            'price': price,
                            'strike_price': strike_price,
                            'discount_percent': discount_percent,
                            'section': section,
                            'url': product.get('url', ''),
                            'img': img_url,
                            'price_history': price_history,
                            'total_score': analysis_score['total_score'],
                            'analysis_details': analysis_score
                        })
                        
            except Exception as e:
                continue
        
        print(f"✅ تم العثور على {len(potential_deals)} عرض محتمل عالي الجودة")
        
        # ترتيب حسب النقاط
        potential_deals.sort(key=lambda x: x['total_score'], reverse=True)
        
        # انتقاء الأفضل مع التنويع
        final_deals = self.select_diverse_deals(potential_deals, self.target_deals_count)
        
        print(f"🎯 تم انتقاء {len(final_deals)} عرض نهائي للإرسال")
        
        return final_deals
    
    def comprehensive_analysis(self, name, price, strike_price, discount_percent, price_history, section):
        """تحليل شامل للمنتج"""
        
        total_score = 0
        details = {
            'text_analysis': 0,
            'price_analysis': 0,
            'discount_analysis': 0,
            'history_analysis': 0,
            'category_bonus': 0
        }
        
        # 1. تحليل النص (25 نقطة)
        name_lower = name.lower()
        
        # كلمات مشبوهة
        suspicious_count = sum(1 for word in self.suspicious_words if word in name_lower)
        if suspicious_count > 0:
            details['text_analysis'] -= suspicious_count * 10
        
        # مؤشرات الجودة
        quality_count = sum(1 for word in self.quality_indicators if word in name_lower)
        details['text_analysis'] += quality_count * 8
        
        # طول الاسم (تفصيل أكثر = جودة أعلى)
        if len(name) > 60:
            details['text_analysis'] += 5
        
        # 2. تحليل السعر (25 نقطة)
        if 50 <= price <= 1000:
            details['price_analysis'] += 15  # نطاق سعري ممتاز
        elif 30 <= price <= 3000:
            details['price_analysis'] += 10  # نطاق سعري جيد
        elif price <= 10000:
            details['price_analysis'] += 5   # نطاق سعري مقبول
        
        # 3. تحليل الخصم (30 نقطة)
        if strike_price and price:
            calculated_discount = ((strike_price - price) / strike_price) * 100
            
            # دقة حساب الخصم
            if abs(calculated_discount - discount_percent) <= 1:
                details['discount_analysis'] += 15
            elif abs(calculated_discount - discount_percent) <= 3:
                details['discount_analysis'] += 10
            
            # معقولية الخصم
            if 20 <= discount_percent <= 50:
                details['discount_analysis'] += 15
            elif 15 <= discount_percent < 20 or 50 < discount_percent <= 70:
                details['discount_analysis'] += 10
        
        # 4. تحليل التاريخ (15 نقطة)
        if price_history and len(price_history) >= 3:
            historical_prices = [h.get('price', 0) for h in price_history if h.get('price', 0) > 0]
            
            if historical_prices:
                avg_historical = sum(historical_prices) / len(historical_prices)
                
                if price < avg_historical * 0.8:
                    details['history_analysis'] += 15  # أقل بكثير من المتوسط
                elif price < avg_historical * 0.9:
                    details['history_analysis'] += 10  # أقل من المتوسط
                elif price < avg_historical:
                    details['history_analysis'] += 5   # أقل قليلاً
        
        # 5. مكافأة الفئة (5 نقاط)
        premium_categories = ['Electronics', 'Beauty', 'Health & Household Products']
        if section in premium_categories:
            details['category_bonus'] += 5
        
        # حساب النقاط الإجمالية
        total_score = sum(details.values())
        
        return {
            'total_score': max(0, min(100, total_score + 20)),  # إضافة 20 نقطة أساسية
            'details': details
        }
    
    def select_diverse_deals(self, deals, target_count):
        """انتقاء متنوع للعروض"""
        
        selected = []
        category_counts = {}
        price_ranges = {'low': 0, 'medium': 0, 'high': 0}
        
        # أولاً: أفضل عرض من كل فئة
        categories_covered = set()
        for deal in deals:
            category = deal.get('section', 'Unknown')
            if category not in categories_covered and len(selected) < target_count:
                selected.append(deal)
                categories_covered.add(category)
                category_counts[category] = 1
                
                # تحديد نطاق السعر
                price = deal.get('price', 0)
                if price < 200:
                    price_ranges['low'] += 1
                elif price < 1500:
                    price_ranges['medium'] += 1
                else:
                    price_ranges['high'] += 1
        
        # ثانياً: ملء باقي الأماكن مع التنويع
        for deal in deals:
            if len(selected) >= target_count:
                break
                
            if deal in selected:
                continue
            
            category = deal.get('section', 'Unknown')
            price = deal.get('price', 0)
            
            # تحديد نطاق السعر
            if price < 200:
                price_range = 'low'
            elif price < 1500:
                price_range = 'medium'
            else:
                price_range = 'high'
            
            # شروط التنويع
            if (category_counts.get(category, 0) < 3 and  # حد أقصى 3 لكل فئة
                price_ranges[price_range] < 6):             # حد أقصى 6 لكل نطاق سعري
                
                selected.append(deal)
                category_counts[category] = category_counts.get(category, 0) + 1
                price_ranges[price_range] += 1
        
        return selected
    
    def download_and_process_image(self, img_url, max_size_kb=800):
        """تحميل ومعالجة الصورة"""
        
        if not img_url:
            return None
        
        try:
            # تحميل الصورة
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(img_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # فتح الصورة
                img = Image.open(BytesIO(response.content))
                
                # تحسين الصورة
                # تحويل إلى RGB إذا كانت RGBA
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # تصغير الحجم إذا كان كبير
                if img.size[0] > 800 or img.size[1] > 800:
                    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                
                # ضغط الصورة
                output = BytesIO()
                quality = 85
                
                while quality > 20:
                    output.seek(0)
                    output.truncate()
                    img.save(output, format='JPEG', quality=quality, optimize=True)
                    
                    if len(output.getvalue()) <= max_size_kb * 1024:
                        break
                    
                    quality -= 10
                
                return output.getvalue()
            
            return None
            
        except Exception as e:
            print(f"⚠️ خطأ في تحميل الصورة: {e}")
            return None
    
    def send_deal_with_image(self, deal, user_id):
        """إرسال عرض واحد مع الصورة"""
        
        try:
            name = deal.get('name', 'منتج')
            price = deal.get('price', 0)
            strike_price = deal.get('strike_price', 0)
            discount = deal.get('discount_percent', 0)
            score = deal.get('total_score', 0)
            asin = deal.get('asin', '')
            img_url = deal.get('img', '')
            
            savings = strike_price - price
            
            # تحضير النص
            caption = f"""🎯 <b>عرض معتمد بالذكاء الاصطناعي</b>

📦 <b>{name[:80]}...</b>

💰 السعر: <b>{price:.0f} جنيه</b>
🏷️ السعر الأصلي: <s>{strike_price:.0f} جنيه</s>
🎉 الخصم: <b>{discount:.1f}%</b>
💸 التوفير: <b>{savings:.0f} جنيه</b>
⭐ نقاط الجودة: <b>{score:.1f}/100</b>
🏷️ الفئة: {deal.get('section', 'غير محدد')}

🔗 <a href="https://www.amazon.eg/dp/{asin}">رابط المنتج</a>

🤖 <i>تم اختيار هذا العرض من {len(self.products_data):,} منتج</i>"""
            
            # محاولة الإرسال مع الصورة
            if self.send_with_images and img_url:
                image_data = self.download_and_process_image(img_url)
                
                if image_data:
                    # إرسال مع الصورة
                    url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
                    
                    files = {'photo': ('image.jpg', image_data, 'image/jpeg')}
                    data = {
                        'chat_id': user_id,
                        'caption': caption,
                        'parse_mode': 'HTML'
                    }
                    
                    response = requests.post(url, data=data, files=files, timeout=30)
                    
                    if response.status_code == 200:
                        print(f"✅ تم إرسال العرض مع الصورة للمستخدم {user_id}")
                        return True
                    else:
                        print(f"⚠️ فشل إرسال الصورة، محاولة إرسال نص فقط...")
            
            # إرسال نص فقط (fallback)
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
                return True
            else:
                print(f"❌ فشل إرسال العرض للمستخدم {user_id}")
                return False
                
        except Exception as e:
            print(f"⚠️ خطأ في إرسال العرض: {e}")
            return False
    
    def send_deals_to_telegram_auto(self, deals):
        """إرسال العروض تلقائياً للتليجرام مع الصور"""
        
        if not self.bot_token or not self.users or not deals:
            print("⚠️ إعدادات التليجرام غير مكتملة أو لا توجد عروض")
            return
        
        if not self.auto_send_enabled:
            print("⚠️ الإرسال التلقائي معطل")
            return
        
        print(f"📱 بدء الإرسال التلقائي لـ {len(deals)} عرض...")
        
        # إرسال رسالة تمهيدية
        intro_message = f"""🎯 <b>العروض اليومية المختارة</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
🤖 تحليل ذكي من {len(self.products_data):,} منتج

🏆 سيتم إرسال {len(deals)} عرض عالي الجودة...
⏱️ يرجى الانتظار..."""
        
        for user_id in self.users:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                data = {
                    'chat_id': user_id,
                    'text': intro_message,
                    'parse_mode': 'HTML'
                }
                requests.post(url, data=data, timeout=10)
            except:
                pass
        
        # إرسال كل عرض منفصل مع صورته
        sent_count = 0
        
        for i, deal in enumerate(deals, 1):
            print(f"📤 إرسال العرض {i}/{len(deals)}: {deal['name'][:40]}...")
            
            for user_id in self.users:
                success = self.send_deal_with_image(deal, user_id)
                if success:
                    sent_count += 1
            
            # تأخير بين العروض لتجنب flood protection
            if i < len(deals):
                time.sleep(3)
        
        # رسالة ختامية
        summary_message = f"""✅ <b>تم الانتهاء من الإرسال</b>

📊 الملخص:
• تم إرسال: {len(deals)} عرض
• إجمالي الرسائل: {sent_count}
• متوسط النقاط: {sum(d['total_score'] for d in deals) / len(deals):.1f}

🎯 جميع العروض معتمدة بالذكاء الاصطناعي
🔔 ستصلك تنبيهات أخرى عند اكتشاف عروض جديدة

🤖 <i>نظام LAQTA الذكي</i>"""
        
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
        
        print(f"🎉 تم إرسال {len(deals)} عرض بنجاح!")
        
        # تحديث قاعدة البيانات
        self.mark_deals_as_sent(deals)
    
    def mark_deals_as_sent(self, deals):
        """وضع علامة على العروض المرسلة"""
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        sent_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for deal in deals:
            asin = deal.get('asin', '')
            if asin:
                cursor.execute('''
                    UPDATE deals 
                    SET is_sent = 1, sent_at = ? 
                    WHERE asin = ?
                ''', (sent_time, asin))
        
        conn.commit()
        conn.close()
        
        print(f"✅ تم وضع علامة على {len(deals)} عرض كمرسل")
    
    def save_deals_to_db(self, deals):
        """حفظ العروض في قاعدة البيانات"""
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        saved_count = 0
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for deal in deals:
            try:
                score = deal.get('total_score', 0)
                
                # تحديد مستوى الجودة
                if score >= 80:
                    quality_level = 'excellent'
                elif score >= 65:
                    quality_level = 'very_good'
                elif score >= 50:
                    quality_level = 'good'
                else:
                    quality_level = 'fair'
                
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
    
    def run_auto_system(self):
        """تشغيل النظام التلقائي الكامل"""
        
        print("🤖 بدء النظام التلقائي المحسن...")
        print("=" * 60)
        
        if not self.products_data:
            print("❌ لا توجد بيانات للتحليل")
            return []
        
        # مرحلة 1: تحليل وانتقاء العروض
        best_deals = self.analyze_and_find_deals()
        
        if not best_deals:
            print("❌ لم يتم العثور على عروض تستوفي المعايير العالية")
            return []
        
        # مرحلة 2: حفظ في قاعدة البيانات
        saved_count = self.save_deals_to_db(best_deals)
        
        # مرحلة 3: إرسال تلقائي للتليجرام مع الصور
        if self.auto_send_enabled:
            self.send_deals_to_telegram_auto(best_deals)
        
        # عرض النتائج
        print("\n🏆 العروض المختارة والمرسلة:")
        print("=" * 70)
        
        for i, deal in enumerate(best_deals, 1):
            name = deal.get('name', 'منتج')[:55] + "..."
            price = deal.get('price', 0)
            discount = deal.get('discount_percent', 0)
            score = deal.get('total_score', 0)
            
            print(f"{i:2d}. {name}")
            print(f"    💰 {price:.0f} جنيه | 🎉 {discount:.1f}% | ⭐ {score:.1f}")
        
        print(f"\n🎉 تم اختيار وإرسال {len(best_deals)} عرض عالي الجودة!")
        print(f"📊 من أصل {len(self.products_data):,} منتج في قاعدة البيانات")
        print(f"📱 تم الإرسال التلقائي للتليجرام مع الصور")
        
        return best_deals
    
    def get_today_stats(self):
        """إحصائيات اليوم"""
        
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            # عروض اليوم
            cursor.execute('SELECT COUNT(*) FROM deals WHERE date_added LIKE ?', (f'{today}%',))
            today_deals = cursor.fetchone()[0]
            
            # العروض المرسلة
            cursor.execute('SELECT COUNT(*) FROM deals WHERE is_sent = 1 AND date_added LIKE ?', (f'{today}%',))
            sent_deals = cursor.fetchone()[0]
            
            # متوسط النقاط
            cursor.execute('SELECT AVG(smart_score) FROM deals WHERE date_added LIKE ?', (f'{today}%',))
            avg_score = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'today_deals': today_deals,
                'sent_deals': sent_deals,
                'avg_score': round(avg_score, 1)
            }
            
        except Exception as e:
            print(f"⚠️ خطأ في الإحصائيات: {e}")
            return {'today_deals': 0, 'sent_deals': 0, 'avg_score': 0}

# دالة تشغيل مبسطة
def run_enhanced_telegram_system(json_file="products.json"):
    """تشغيل النظام المحسن مع التليجرام"""
    
    system = EnhancedTelegramSystem(json_file)
    return system.run_auto_system()

# دالة للتشغيل المجدول (يمكن استخدامها مع cron أو task scheduler)
def run_scheduled():
    """تشغيل مجدول للنظام"""
    
    print(f"⏰ تشغيل مجدول في {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # فحص إذا كان تم الإرسال اليوم
    system = EnhancedTelegramSystem()
    stats = system.get_today_stats()
    
    if stats['sent_deals'] > 0:
        print(f"✅ تم إرسال {stats['sent_deals']} عرض اليوم بالفعل")
        return
    
    # تشغيل النظام
    deals = system.run_auto_system()
    
    if deals:
        print(f"🎉 تم إرسال {len(deals)} عرض جديد!")
    else:
        print("❌ لا توجد عروض جديدة اليوم")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "scheduled":
            run_scheduled()
        else:
            json_file = sys.argv[1]
            run_enhanced_telegram_system(json_file)
    else:
        run_enhanced_telegram_system()