# image_telegram_system.py - نظام محسن يرسل الصور مع الإشعارات

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

class ImageTelegramSystem:
    """نظام محسن يرسل صورة المنتج مع كل إشعار"""
    
    def __init__(self, json_file=None):
        self.db_file = "image_deals.db"
        self.json_file = json_file
        self.products_data = {}
        
        self.setup_database()
        self.load_config()
        
        # تحميل ملف JSON
        if json_file:
            self.load_json_data(json_file)
        else:
            self.find_and_load_json()
        
        # إعدادات النظام
        self.min_discount = 15
        self.max_discount = 85
        self.min_price = 25
        self.max_price = 8000
        
        # إعدادات الصور
        self.send_with_images = True
        self.max_image_size_kb = 800
        self.image_quality = 85
        
        print("✅ تم تهيئة نظام الإرسال بالصور")
    
    def find_and_load_json(self):
        """البحث عن ملف JSON وتحميله"""
        
        print("🔍 البحث عن ملف JSON...")
        
        json_files = []
        for file in os.listdir('.'):
            if (file.endswith('.json') and 
                file not in ['config.json', 'telegram_config.json', 'config_template.json']):
                json_files.append(file)
        
        if json_files:
            largest_file = max(json_files, key=lambda f: os.path.getsize(f))
            print(f"📂 تم العثور على: {largest_file}")
            self.load_json_data(largest_file)
        else:
            print("⚠️ لم يتم العثور على ملف JSON")
    
    def load_json_data(self, json_file):
        """تحميل بيانات JSON"""
        
        try:
            print(f"📂 جاري تحميل: {json_file}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                self.products_data = json.load(f)
            
            file_size = os.path.getsize(json_file) / (1024 * 1024)
            print(f"✅ تم تحميل {len(self.products_data):,} منتج ({file_size:.1f} MB)")
            
        except Exception as e:
            print(f"❌ خطأ في تحميل الملف: {e}")
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
                image_sent BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def analyze_json_for_deals(self):
        """تحليل ملف JSON للعثور على أفضل العروض"""
        
        if not self.products_data:
            print("❌ لا توجد بيانات JSON للتحليل")
            return []
        
        print(f"🧠 تحليل {len(self.products_data):,} منتج...")
        
        high_quality_deals = []
        
        for asin, product in self.products_data.items():
            try:
                if not isinstance(product, dict):
                    continue
                
                # استخراج البيانات
                name = product.get('name', '')
                price = product.get('price', 0)
                strike_price = product.get('strike_price', 0)
                discount_percent = product.get('discount_percent', 0)
                section = product.get('section', '')
                img_url = product.get('img', '')
                price_history = product.get('price_history', [])
                
                # فلترة أولية صارمة
                if (price and price > 0 and
                    strike_price and strike_price > price and
                    discount_percent >= self.min_discount and
                    discount_percent <= self.max_discount and
                    self.min_price <= price <= self.max_price and
                    len(name) > 15 and
                    img_url):  # يجب أن تكون هناك صورة
                    
                    # تحليل شامل للجودة
                    quality_analysis = self.comprehensive_quality_analysis(product)
                    
                    if quality_analysis['total_score'] >= 65:  # معايير صارمة
                        high_quality_deals.append({
                            'asin': asin,
                            'name': name,
                            'price': price,
                            'strike_price': strike_price,
                            'discount_percent': discount_percent,
                            'section': section,
                            'url': product.get('url', f'https://www.amazon.eg/dp/{asin}'),
                            'img': img_url,
                            'price_history': price_history,
                            'quality_score': quality_analysis['total_score'],
                            'quality_details': quality_analysis['details']
                        })
                        
            except Exception as e:
                continue
        
        print(f"✅ تم العثور على {len(high_quality_deals)} عرض عالي الجودة")
        
        # ترتيب حسب النقاط الجودة
        high_quality_deals.sort(key=lambda x: x['quality_score'], reverse=True)
        
        # تنويع الاختيار
        final_deals = self.select_diverse_deals(high_quality_deals, 15)
        
        print(f"🎯 تم انتقاء {len(final_deals)} عرض للإرسال")
        
        return final_deals
    
    def comprehensive_quality_analysis(self, product):
        """تحليل شامل لجودة المنتج"""
        
        name = product.get('name', '').lower()
        price = product.get('price', 0)
        discount = product.get('discount_percent', 0)
        price_history = product.get('price_history', [])
        section = product.get('section', '')
        
        details = {
            'text_score': 0,
            'price_score': 0,
            'discount_score': 0,
            'history_score': 0,
            'category_score': 0
        }
        
        # 1. تحليل النص (30 نقطة)
        suspicious_words = ['fake', 'replica', 'copy', 'used', 'damaged', 'broken', 'refurbished']
        quality_words = ['original', 'authentic', 'genuine', 'warranty', 'new', 'brand new', 'authorized']
        
        suspicious_count = sum(1 for word in suspicious_words if word in name)
        quality_count = sum(1 for word in quality_words if word in name)
        
        details['text_score'] = quality_count * 10 - suspicious_count * 15
        
        # مكافأة للأسماء المفصلة
        if len(product.get('name', '')) > 50:
            details['text_score'] += 5
        
        # 2. تحليل السعر (25 نقطة)
        if 50 <= price <= 1000:
            details['price_score'] = 25
        elif 30 <= price <= 2500:
            details['price_score'] = 20
        elif 25 <= price <= 5000:
            details['price_score'] = 15
        else:
            details['price_score'] = 10
        
        # 3. تحليل الخصم (25 نقطة)
        if 20 <= discount <= 45:
            details['discount_score'] = 25
        elif 15 <= discount < 20:
            details['discount_score'] = 20
        elif 45 < discount <= 60:
            details['discount_score'] = 15
        elif 60 < discount <= 75:
            details['discount_score'] = 10
        else:
            details['discount_score'] = 5
        
        # 4. تحليل التاريخ (15 نقطة)
        if price_history and len(price_history) >= 3:
            historical_prices = [h.get('price', 0) for h in price_history if h.get('price', 0) > 0]
            
            if historical_prices:
                avg_historical = sum(historical_prices) / len(historical_prices)
                min_historical = min(historical_prices)
                
                if price <= min_historical:
                    details['history_score'] = 15  # أقل سعر تاريخي
                elif price < avg_historical * 0.85:
                    details['history_score'] = 12  # أقل من المتوسط بكثير
                elif price < avg_historical:
                    details['history_score'] = 8   # أقل من المتوسط
                else:
                    details['history_score'] = 3
        else:
            details['history_score'] = 5  # نقاط محايدة لعدم وجود تاريخ
        
        # 5. تحليل الفئة (5 نقاط)
        premium_categories = ['Electronics', 'Beauty', 'Health & Household Products', 'Home & Kitchen']
        if section in premium_categories:
            details['category_score'] = 5
        
        # حساب النقاط الإجمالية
        total_score = sum(details.values())
        
        return {
            'total_score': max(0, min(100, total_score + 15)),  # إضافة 15 نقطة أساسية
            'details': details
        }
    
    def select_diverse_deals(self, deals, target_count):
        """انتقاء متنوع للعروض"""
        
        selected = []
        category_counts = {}
        price_ranges = {'low': 0, 'medium': 0, 'high': 0}
        
        for deal in deals:
            if len(selected) >= target_count:
                break
            
            category = deal.get('section', 'Unknown')
            price = deal.get('price', 0)
            
            # تحديد نطاق السعر
            if price < 150:
                price_range = 'low'
            elif price < 1000:
                price_range = 'medium'
            else:
                price_range = 'high'
            
            # شروط التنويع
            if (category_counts.get(category, 0) < 3 and
                price_ranges[price_range] < 6):
                
                selected.append(deal)
                category_counts[category] = category_counts.get(category, 0) + 1
                price_ranges[price_range] += 1
        
        return selected
    
    def download_and_optimize_image(self, img_url):
        """تحميل وتحسين صورة المنتج"""
        
        if not img_url:
            return None
        
        try:
            # تحميل الصورة
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Referer': 'https://www.amazon.eg/'
            }
            
            response = requests.get(img_url, headers=headers, timeout=15)
            
            if response.status_code == 200 and len(response.content) > 1000:  # حد أدنى لحجم الصورة
                # فتح الصورة
                img = Image.open(BytesIO(response.content))
                
                # تحويل إلى RGB إذا لزم الأمر
                if img.mode in ('RGBA', 'P', 'LA'):
                    # إنشاء خلفية بيضاء للشفافية
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # تحسين الحجم - تكبير الصور الصغيرة
                width, height = img.size
                if width < 400 or height < 400:
                    # تكبير الصور الصغيرة
                    new_size = (max(600, width), max(600, height))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                elif width > 1200 or height > 1200:
                    # تصغير الصور الكبيرة
                    img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                
                # ضغط تدريجي للحصول على الحجم المناسب
                output = BytesIO()
                quality = self.image_quality
                
                for attempt in range(5):
                    output.seek(0)
                    output.truncate()
                    
                    img.save(output, format='JPEG', quality=quality, optimize=True)
                    
                    size_kb = len(output.getvalue()) / 1024
                    
                    if size_kb <= self.max_image_size_kb:
                        print(f"✅ تم تحسين الصورة: {size_kb:.1f} KB (جودة {quality}%)")
                        return output.getvalue()
                    
                    quality -= 10
                    if quality < 40:
                        break
                
                # إرجاع الصورة حتى لو كانت كبيرة قليلاً
                return output.getvalue()
            
            return None
            
        except Exception as e:
            print(f"⚠️ خطأ في معالجة الصورة: {e}")
            return None
    
    def send_deal_with_image_to_telegram(self, deal):
        """إرسال عرض مع صورة للتليجرام"""
        
        if not self.bot_token or not self.users:
            print("⚠️ إعدادات التليجرام غير مكتملة")
            return False
        
        try:
            # بيانات العرض
            name = deal.get('name', 'منتج')
            price = deal.get('price', 0)
            strike_price = deal.get('strike_price', 0)
            discount = deal.get('discount_percent', 0)
            score = deal.get('quality_score', 0)
            asin = deal.get('asin', '')
            section = deal.get('section', 'غير محدد')
            img_url = deal.get('img', '')
            
            savings = strike_price - price
            
            # رموز تعبيرية حسب الفئة
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
            
            # تحضير النص المحسن
            caption = f"""{emoji} <b>عرض مميز معتمد بالذكاء الاصطناعي</b>

📦 <b>{name}</b>

💰 السعر الحالي: <b>{price:.0f} جنيه</b>
🏷️ السعر الأصلي: <s>{strike_price:.0f} جنيه</s>
🎉 نسبة الخصم: <b>{discount:.1f}%</b>
💸 مقدار التوفير: <b>{savings:.0f} جنيه</b>
⭐ تقييم الجودة: <b>{score:.1f}/100</b>
🏷️ الفئة: <b>{section}</b>

🔗 <a href="https://www.amazon.eg/dp/{asin}">🛒 اشتري الآن من أمازون</a>

🤖 <i>تم اختيار هذا العرض من {len(self.products_data):,} منتج</i>
⚡ <i>عرض محدود - قد ينتهي قريباً!</i>"""
            
            sent_successfully = False
            
            # إرسال لكل مستخدم
            for user_id in self.users:
                try:
                    # محاولة إرسال مع الصورة
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
                            
                            response = requests.post(url, data=data, files=files, timeout=30)
                            
                            if response.status_code == 200:
                                print(f"✅ تم إرسال العرض مع الصورة للمستخدم {user_id}")
                                sent_successfully = True
                                continue
                            else:
                                print(f"⚠️ فشل إرسال الصورة للمستخدم {user_id}: {response.status_code}")
                    
                    # fallback: إرسال نص فقط
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
                        print(f"❌ فشل إرسال النص للمستخدم {user_id}: {response.status_code}")
                        
                except Exception as e:
                    print(f"⚠️ خطأ في إرسال للمستخدم {user_id}: {e}")
                    continue
            
            return sent_successfully
            
        except Exception as e:
            print(f"❌ خطأ في إرسال العرض: {e}")
            return False
    
    def send_deals_batch_to_telegram(self, deals):
        """إرسال مجموعة العروض للتليجرام"""
        
        if not deals:
            print("❌ لا توجد عروض للإرسال")
            return
        
        print(f"📱 بدء إرسال {len(deals)} عرض مع الصور...")
        
        # رسالة افتتاحية
        intro_message = f"""🎯 <b>أفضل العروض اليوم</b>
📅 {datetime.now().strftime('%A, %Y-%m-%d %H:%M')}

🧠 تحليل ذكي من {len(self.products_data):,} منتج
🎯 تم اختيار {len(deals)} عرض عالي الجودة
⭐ متوسط الجودة: {sum(d['quality_score'] for d in deals) / len(deals):.1f}/100
💰 إجمالي التوفير المحتمل: {sum((d['strike_price'] - d['price']) for d in deals):.0f} جنيه

📸 <b>كل عرض مرفق بصورة المنتج</b>
⏳ جاري الإرسال..."""
        
        # إرسال الرسالة الافتتاحية
        for user_id in self.users:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                data = {
                    'chat_id': user_id,
                    'text': intro_message,
                    'parse_mode': 'HTML'
                }
                requests.post(url, data=data, timeout=10)
            except Exception as e:
                print(f"⚠️ خطأ في إرسال الرسالة الافتتاحية: {e}")
        
        # تأخير قبل بدء إرسال العروض
        time.sleep(3)
        
        # إرسال كل عرض منفصل مع صورته
        sent_count = 0
        failed_count = 0
        
        for i, deal in enumerate(deals, 1):
            print(f"📤 إرسال العرض {i}/{len(deals)}: {deal['name'][:35]}...")
            
            success = self.send_deal_with_image_to_telegram(deal)
            
            if success:
                sent_count += 1
                # تحديث قاعدة البيانات
                self.mark_deal_as_sent(deal['asin'], with_image=True)
            else:
                failed_count += 1
                print(f"❌ فشل إرسال العرض {i}")
            
            # تأخير بين العروض لتجنب flood protection
            if i < len(deals):
                delay = 4 if i <= 5 else 3  # تأخير أطول للعروض الأولى
                time.sleep(delay)
        
        # رسالة ختامية
        summary_message = f"""✅ <b>تم الانتهاء من الإرسال</b>

📊 <b>ملخص الإرسال:</b>
• العروض المرسلة بنجاح: <b>{sent_count}</b>
• العروض الفاشلة: <b>{failed_count}</b>
• معدل النجاح: <b>{(sent_count/len(deals)*100):.1f}%</b>

💡 <b>نصائح:</b>
• العروض محدودة وقد تنتهي سريعاً
• تأكد من الأسعار قبل الشراء
• احفظ العروض المهمة لديك

🤖 <i>نظام LAQTA الذكي - مع الصور</i>
🔔 <i>ستصلك تنبيهات جديدة عند اكتشاف عروض أخرى</i>"""
        
        for user_id in self.users:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                data = {
                    'chat_id': user_id,
                    'text': summary_message,
                    'parse_mode': 'HTML'
                }
                requests.post(url, data=data, timeout=10)
            except Exception as e:
                print(f"⚠️ خطأ في إرسال الرسالة الختامية: {e}")
        
        print(f"🎉 تم إرسال {sent_count} عرض بنجاح!")
        print(f"📊 معدل النجاح: {(sent_count/len(deals)*100):.1f}%")
        
        return sent_count
    
    def mark_deal_as_sent(self, asin, with_image=False):
        """وضع علامة على العرض كمرسل"""
        
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            sent_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                UPDATE deals 
                SET is_sent = 1, image_sent = ?, sent_at = ?
                WHERE asin = ?
            ''', (1 if with_image else 0, sent_time, asin))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"⚠️ خطأ في تحديث قاعدة البيانات: {e}")
    
    def save_deals_to_db(self, deals):
        """حفظ العروض في قاعدة البيانات"""
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        saved_count = 0
        
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
                saved_count += 1
                
            except Exception as e:
                print(f"⚠️ خطأ في حفظ العرض: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"💾 تم حفظ {saved_count} عرض في قاعدة البيانات")
        return saved_count
    
    def run_system_with_images(self):
        """تشغيل النظام الكامل مع الصور"""
        
        print("🚀 بدء نظام الإرسال مع الصور...")
        print("=" * 60)
        
        if not self.products_data:
            print("❌ لا توجد بيانات للتحليل")
            print("💡 تأكد من وجود ملف JSON في المجلد")
            return []
        
        # تحليل وانتقاء العروض
        best_deals = self.analyze_json_for_deals()
        
        if not best_deals:
            print("❌ لم يتم العثور على عروض تستوفي المعايير")
            return []
        
        # حفظ في قاعدة البيانات
        self.save_deals_to_db(best_deals)
        
        # إرسال مع الصور
        sent_count = self.send_deals_batch_to_telegram(best_deals)
        
        # عرض النتائج
        print("\n🏆 العروض المرسلة مع الصور:")
        print("=" * 60)
        
        for i, deal in enumerate(best_deals, 1):
            name = deal.get('name', 'منتج')[:50] + "..."
            price = deal.get('price', 0)
            discount = deal.get('discount_percent', 0)
            score = deal.get('quality_score', 0)
            
            print(f"{i:2d}. {name}")
            print(f"    💰 {price:.0f} جنيه | 🎉 {discount:.1f}% | ⭐ {score:.1f}")
        
        print(f"\n🎉 تم إرسال {sent_count} عرض مع الصور بنجاح!")
        print(f"📊 من أصل {len(self.products_data):,} منتج في قاعدة البيانات")
        
        return best_deals
    
    def get_today_statistics(self):
        """إحصائيات اليوم"""
        
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            # عروض اليوم
            cursor.execute('SELECT COUNT(*) FROM deals WHERE date_found LIKE ?', (f'{today}%',))
            today_deals = cursor.fetchone()[0]
            
            # العروض المرسلة
            cursor.execute('SELECT COUNT(*) FROM deals WHERE is_sent = 1 AND date_found LIKE ?', (f'{today}%',))
            sent_deals = cursor.fetchone()[0]
            
            # العروض المرسلة مع صور
            cursor.execute('SELECT COUNT(*) FROM deals WHERE image_sent = 1 AND date_found LIKE ?', (f'{today}%',))
            image_deals = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"\n📊 إحصائيات اليوم:")
            print(f"   - عروض مكتشفة: {today_deals}")
            print(f"   - عروض مرسلة: {sent_deals}")
            print(f"   - عروض مع صور: {image_deals}")
            
            return {
                'today_deals': today_deals,
                'sent_deals': sent_deals,
                'image_deals': image_deals
            }
            
        except Exception as e:
            print(f"⚠️ خطأ في الإحصائيات: {e}")
            return {}

def run_image_system(json_file=None):
    """تشغيل نظام الإرسال مع الصور"""
    
    system = ImageTelegramSystem(json_file)
    deals = system.run_system_with_images()
    
    # عرض الإحصائيات
    system.get_today_statistics()
    
    return deals

if __name__ == "__main__":
    import sys
    
    # يمكن تمرير اسم ملف JSON أو البحث التلقائي
    json_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        if json_file:
            print(f"📂 استخدام ملف محدد: {json_file}")
        else:
            print("🔍 البحث التلقائي عن ملف JSON...")
        
        deals = run_image_system(json_file)
        
        if deals:
            print(f"\n🎉 تم إرسال {len(deals)} عرض مع الصور بنجاح!")
        else:
            print("\n❌ لا توجد عروض للإرسال")
            
    except Exception as e:
        print(f"❌ خطأ في النظام: {e}")
        import traceback
        traceback.print_exc()