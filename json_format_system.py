# json_format_system.py - نظام يتعامل مع تنسيق JSON الفعلي

import json
import sqlite3
import requests
import time
import re
from datetime import datetime
import random
import os
from PIL import Image
from io import BytesIO

class JSONFormatSystem:
    """نظام يتعامل مع تنسيق JSON الفعلي ويحسب الخصومات تلقائياً"""
    
    def __init__(self, json_file=None):
        self.db_file = "json_format_deals.db"
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
        self.min_discount = 10    # قللت الحد الأدنى
        self.max_discount = 85
        self.min_price = 30
        self.max_price = 8000
        
        # إعدادات الصور
        self.send_with_images = True
        self.max_image_size_kb = 800
        
        print("✅ تم تهيئة النظام للتعامل مع تنسيق JSON الفعلي")
    
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
                current_price REAL,
                historical_avg REAL,
                historical_min REAL,
                historical_max REAL,
                calculated_discount REAL,
                section TEXT,
                url TEXT,
                img TEXT,
                quality_score REAL DEFAULT 0,
                price_trend TEXT,
                date_found TEXT,
                is_sent BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def calculate_discount_from_history(self, current_price, price_history):
        """حساب الخصم من تاريخ الأسعار"""
        
        if not price_history or len(price_history) < 3:
            return None, None, None
        
        try:
            # استخراج الأسعار التاريخية
            historical_prices = []
            for entry in price_history:
                if isinstance(entry, dict) and entry.get('price'):
                    historical_prices.append(float(entry['price']))
            
            if not historical_prices:
                return None, None, None
            
            # حساب الإحصائيات
            avg_price = sum(historical_prices) / len(historical_prices)
            min_price = min(historical_prices)
            max_price = max(historical_prices)
            
            # حساب الخصم بناء على المتوسط التاريخي
            if avg_price > current_price:
                discount_from_avg = ((avg_price - current_price) / avg_price) * 100
            else:
                discount_from_avg = 0
            
            # حساب الخصم بناء على أعلى سعر
            if max_price > current_price:
                discount_from_max = ((max_price - current_price) / max_price) * 100
            else:
                discount_from_max = 0
            
            # استخدام أفضل خصم
            best_discount = max(discount_from_avg, discount_from_max)
            
            return best_discount, avg_price, min_price
            
        except Exception as e:
            return None, None, None
    
    def analyze_price_trend(self, price_history, current_price):
        """تحليل اتجاه السعر"""
        
        if not price_history or len(price_history) < 5:
            return "unknown"
        
        try:
            # أخذ آخر 10 أسعار
            recent_prices = []
            for entry in price_history[-10:]:
                if isinstance(entry, dict) and entry.get('price'):
                    recent_prices.append(float(entry['price']))
            
            if len(recent_prices) < 3:
                return "unknown"
            
            # حساب الاتجاه
            if current_price < recent_prices[0] * 0.95:
                return "dropping"  # السعر ينخفض
            elif current_price > recent_prices[0] * 1.05:
                return "rising"   # السعر يرتفع
            else:
                return "stable"   # السعر مستقر
                
        except Exception as e:
            return "unknown"
    
    def analyze_json_deals_enhanced(self):
        """تحليل محسن لملف JSON"""
        
        if not self.products_data:
            print("❌ لا توجد بيانات للتحليل")
            return []
        
        print(f"🧠 تحليل محسن لـ {len(self.products_data):,} منتج...")
        
        potential_deals = []
        processed_count = 0
        
        for asin, product in self.products_data.items():
            try:
                processed_count += 1
                
                if processed_count % 10000 == 0:
                    print(f"📊 تم معالجة {processed_count:,} منتج...")
                
                if not isinstance(product, dict):
                    continue
                
                # استخراج البيانات الأساسية
                name = product.get('name', '')
                current_price = product.get('price', 0)
                section = product.get('section', '')
                img_url = product.get('img', '')
                price_history = product.get('price_history', [])
                
                # التحقق من البيانات الأساسية
                if (not name or len(name) < 15 or
                    not current_price or current_price <= 0 or
                    not img_url or
                    current_price < self.min_price or 
                    current_price > self.max_price):
                    continue
                
                # حساب الخصم من التاريخ
                calculated_discount, avg_price, min_price = self.calculate_discount_from_history(
                    current_price, price_history
                )
                
                # يجب أن يكون هناك خصم معقول
                if not calculated_discount or calculated_discount < self.min_discount:
                    continue
                
                # تحليل اتجاه السعر
                price_trend = self.analyze_price_trend(price_history, current_price)
                
                # تحليل شامل للجودة
                quality_analysis = self.comprehensive_quality_analysis_enhanced(
                    product, calculated_discount, price_trend, avg_price
                )
                
                # قبول العروض عالية الجودة فقط
                if quality_analysis['total_score'] >= 60:
                    potential_deals.append({
                        'asin': asin,
                        'name': name,
                        'current_price': current_price,
                        'historical_avg': avg_price,
                        'historical_min': min_price,
                        'calculated_discount': calculated_discount,
                        'section': section,
                        'url': product.get('url', f'https://www.amazon.eg/dp/{asin}'),
                        'img': img_url,
                        'price_history': price_history,
                        'price_trend': price_trend,
                        'quality_score': quality_analysis['total_score'],
                        'quality_details': quality_analysis['details']
                    })
                    
            except Exception as e:
                continue
        
        print(f"✅ تم تحليل {processed_count:,} منتج")
        print(f"✅ تم العثور على {len(potential_deals)} عرض عالي الجودة")
        
        # ترتيب حسب النقاط الجودة
        potential_deals.sort(key=lambda x: x['quality_score'], reverse=True)
        
        # انتقاء أفضل 20 عرض مع التنويع
        final_deals = self.select_diverse_deals_enhanced(potential_deals, 20)
        
        print(f"🎯 تم انتقاء {len(final_deals)} عرض للإرسال")
        
        return final_deals
    
    def comprehensive_quality_analysis_enhanced(self, product, calculated_discount, price_trend, avg_price):
        """تحليل شامل محسن للجودة"""
        
        name = product.get('name', '').lower()
        current_price = product.get('price', 0)
        section = product.get('section', '')
        price_history = product.get('price_history', [])
        
        details = {
            'text_score': 0,
            'discount_score': 0,
            'trend_score': 0,
            'history_score': 0,
            'category_score': 0
        }
        
        # 1. تحليل النص (25 نقطة)
        suspicious_words = ['fake', 'replica', 'copy', 'used', 'damaged', 'broken', 'refurbished']
        quality_words = ['original', 'authentic', 'genuine', 'warranty', 'new', 'brand new', 'authorized']
        brand_words = ['samsung', 'apple', 'xiaomi', 'anker', 'sony', 'lg', 'philips', 'panasonic']
        
        suspicious_count = sum(1 for word in suspicious_words if word in name)
        quality_count = sum(1 for word in quality_words if word in name)
        brand_count = sum(1 for word in brand_words if word in name)
        
        details['text_score'] = quality_count * 8 + brand_count * 5 - suspicious_count * 20
        
        # مكافأة للأسماء المفصلة
        if len(product.get('name', '')) > 60:
            details['text_score'] += 5
        
        # 2. تحليل الخصم (30 نقطة)
        if 15 <= calculated_discount <= 40:
            details['discount_score'] = 30  # خصم ممتاز
        elif 10 <= calculated_discount < 15:
            details['discount_score'] = 25  # خصم جيد
        elif 40 < calculated_discount <= 60:
            details['discount_score'] = 20  # خصم عالي
        elif calculated_discount > 60:
            details['discount_score'] = 10  # خصم مشبوه
        else:
            details['discount_score'] = 5
        
        # 3. تحليل اتجاه السعر (20 نقطة)
        if price_trend == "dropping":
            details['trend_score'] = 20  # السعر ينخفض - ممتاز
        elif price_trend == "stable":
            details['trend_score'] = 15  # السعر مستقر - جيد
        elif price_trend == "rising":
            details['trend_score'] = 5   # السعر يرتفع - ليس مثالي
        else:
            details['trend_score'] = 10  # غير معروف
        
        # 4. تحليل التاريخ (20 نقطة)
        if len(price_history) >= 10:
            details['history_score'] = 15  # تاريخ غني
            
            # مكافأة إضافية إذا كان السعر أقل من أقل سعر تاريخي
            historical_prices = [h.get('price', 0) for h in price_history if h.get('price', 0) > 0]
            if historical_prices and current_price <= min(historical_prices):
                details['history_score'] += 5  # أقل سعر تاريخي
                
        elif len(price_history) >= 5:
            details['history_score'] = 10  # تاريخ متوسط
        else:
            details['history_score'] = 5   # تاريخ محدود
        
        # 5. تحليل الفئة والسعر (5 نقاط)
        premium_categories = ['Electronics', 'Beauty', 'Health & Household Products']
        if section in premium_categories:
            details['category_score'] = 5
        
        # حساب النقاط الإجمالية
        total_score = sum(details.values())
        
        return {
            'total_score': max(0, min(100, total_score + 10)),  # إضافة 10 نقاط أساسية
            'details': details
        }
    
    def select_diverse_deals_enhanced(self, deals, target_count):
        """انتقاء متنوع محسن للعروض"""
        
        selected = []
        category_counts = {}
        price_ranges = {'low': 0, 'medium': 0, 'high': 0}
        discount_ranges = {'good': 0, 'excellent': 0, 'amazing': 0}
        
        for deal in deals:
            if len(selected) >= target_count:
                break
            
            category = deal.get('section', 'Unknown')
            price = deal.get('current_price', 0)
            discount = deal.get('calculated_discount', 0)
            
            # تحديد نطاق السعر
            if price < 200:
                price_range = 'low'
            elif price < 1000:
                price_range = 'medium'
            else:
                price_range = 'high'
            
            # تحديد نطاق الخصم
            if discount >= 30:
                discount_range = 'amazing'
            elif discount >= 20:
                discount_range = 'excellent'
            else:
                discount_range = 'good'
            
            # شروط التنويع المحسنة
            if (category_counts.get(category, 0) < 4 and      # حد أقصى 4 لكل فئة
                price_ranges[price_range] < 8 and             # حد أقصى 8 لكل نطاق سعري
                discount_ranges[discount_range] < 10):        # توزيع الخصومات
                
                selected.append(deal)
                category_counts[category] = category_counts.get(category, 0) + 1
                price_ranges[price_range] += 1
                discount_ranges[discount_range] += 1
        
        return selected
    
    def download_and_optimize_image(self, img_url):
        """تحميل وتحسين صورة المنتج"""
        
        if not img_url:
            return None
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/*,*/*;q=0.8',
                'Referer': 'https://www.amazon.eg/'
            }
            
            response = requests.get(img_url, headers=headers, timeout=12)
            
            if response.status_code == 200 and len(response.content) > 1000:
                img = Image.open(BytesIO(response.content))
                
                # تحويل إلى RGB
                if img.mode != 'RGB':
                    if img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1])
                        img = background
                    else:
                        img = img.convert('RGB')
                
                # تحسين الحجم
                if img.size[0] < 500 or img.size[1] < 500:
                    new_size = (max(600, img.size[0]), max(600, img.size[1]))
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
    
    def send_deal_with_image(self, deal):
        """إرسال عرض مع صورة"""
        
        if not self.bot_token or not self.users:
            return False
        
        try:
            name = deal.get('name', 'منتج')
            current_price = deal.get('current_price', 0)
            historical_avg = deal.get('historical_avg', 0)
            calculated_discount = deal.get('calculated_discount', 0)
            score = deal.get('quality_score', 0)
            asin = deal.get('asin', '')
            section = deal.get('section', 'غير محدد')
            img_url = deal.get('img', '')
            price_trend = deal.get('price_trend', 'unknown')
            
            savings = historical_avg - current_price if historical_avg else 0
            
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
            
            # رموز اتجاه السعر
            trend_emojis = {
                'dropping': '📉 السعر ينخفض',
                'stable': '📊 السعر مستقر',
                'rising': '📈 السعر يرتفع',
                'unknown': '❓ اتجاه غير محدد'
            }
            
            trend_text = trend_emojis.get(price_trend, '❓ اتجاه غير محدد')
            
            # تحضير النص
            caption = f"""{emoji} <b>عرض مكتشف من التحليل الذكي</b>

📦 <b>{name}</b>

💰 السعر الحالي: <b>{current_price:.0f} جنيه</b>
📊 المتوسط التاريخي: <s>{historical_avg:.0f} جنيه</s>
🎉 خصم محسوب: <b>{calculated_discount:.1f}%</b>
💸 التوفير: <b>{savings:.0f} جنيه</b>
⭐ تقييم الجودة: <b>{score:.1f}/100</b>
📈 اتجاه السعر: {trend_text}
🏷️ الفئة: <b>{section}</b>

🔗 <a href="https://www.amazon.eg/dp/{asin}">🛒 اشتري الآن من أمازون</a>

🧠 <i>تحليل ذكي من {len(self.products_data):,} منتج</i>
📊 <i>بناءً على تاريخ أسعار حقيقي</i>"""
            
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
                            
                            response = requests.post(url, data=data, files=files, timeout=30)
                            
                            if response.status_code == 200:
                                print(f"✅ تم إرسال العرض مع الصورة للمستخدم {user_id}")
                                sent_successfully = True
                                continue
                    
                    # fallback: إرسال نص فقط
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
            
            return sent_successfully
            
        except Exception as e:
            return False
    
    def send_deals_to_telegram_with_images(self, deals):
        """إرسال العروض مع الصور"""
        
        if not deals:
            return 0
        
        print(f"📱 بدء إرسال {len(deals)} عرض مع الصور...")
        
        # رسالة افتتاحية
        intro = f"""🎯 <b>عروض مختارة بعناية</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}

🧠 تحليل ذكي من {len(self.products_data):,} منتج
📊 بناءً على تاريخ أسعار حقيقي
🎯 تم اختيار {len(deals)} عرض عالي الجودة

📸 كل عرض مرفق بصورة عالية الجودة
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
        
        time.sleep(3)
        
        # إرسال العروض
        sent_count = 0
        
        for i, deal in enumerate(deals, 1):
            print(f"📤 إرسال العرض {i}/{len(deals)}: {deal['name'][:35]}...")
            
            if self.send_deal_with_image(deal):
                sent_count += 1
                self.mark_deal_as_sent(deal['asin'])
            
            if i < len(deals):
                time.sleep(4)  # تأخير بين العروض
        
        # رسالة ختامية
        summary = f"""✅ <b>انتهى الإرسال</b>

📊 تم إرسال {sent_count} عرض بنجاح
📈 معدل النجاح: {(sent_count/len(deals)*100):.1f}%
💰 إجمالي التوفير: {sum(deal.get('historical_avg', 0) - deal.get('current_price', 0) for deal in deals):.0f} جنيه

🤖 نظام LAQTA الذكي مع الصور"""
        
        for user_id in self.users:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                data = {
                    'chat_id': user_id,
                    'text': summary,
                    'parse_mode': 'HTML'
                }
                requests.post(url, data=data, timeout=10)
            except:
                pass
        
        print(f"🎉 تم إرسال {sent_count} عرض مع الصور!")
        return sent_count
    
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
                    (asin, name, current_price, historical_avg, historical_min, 
                     calculated_discount, section, url, img, quality_score, 
                     price_trend, date_found)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    deal.get('asin', ''),
                    deal.get('name', ''),
                    deal.get('current_price', 0),
                    deal.get('historical_avg', 0),
                    deal.get('historical_min', 0),
                    deal.get('calculated_discount', 0),
                    deal.get('section', ''),
                    deal.get('url', ''),
                    deal.get('img', ''),
                    deal.get('quality_score', 0),
                    deal.get('price_trend', 'unknown'),
                    current_time
                ))
                saved_count += 1
                
            except Exception as e:
                continue
        
        conn.commit()
        conn.close()
        
        print(f"💾 تم حفظ {saved_count} عرض")
        return saved_count
    
    def mark_deal_as_sent(self, asin):
        """وضع علامة على العرض كمرسل"""
        
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE deals SET is_sent = 1 WHERE asin = ?', (asin,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            pass
    
    def run_system(self):
        """تشغيل النظام الكامل"""
        
        print("🚀 بدء النظام المحسن للتعامل مع JSON...")
        print("=" * 60)
        
        if not self.products_data:
            print("❌ لا توجد بيانات للتحليل")
            return []
        
        # تحليل العروض
        best_deals = self.analyze_json_deals_enhanced()
        
        if not best_deals:
            print("❌ لم يتم العثور على عروض مناسبة")
            return []
        
        # حفظ في قاعدة البيانات
        self.save_deals_to_db(best_deals)
        
        # إرسال مع الصور
        sent_count = self.send_deals_to_telegram_with_images(best_deals)
        
        # عرض النتائج
        print("\n🏆 أفضل العروض:")
        print("=" * 60)
        
        for i, deal in enumerate(best_deals, 1):
            name = deal.get('name', 'منتج')[:50] + "..."
            price = deal.get('current_price', 0)
            discount = deal.get('calculated_discount', 0)
            score = deal.get('quality_score', 0)
            trend = deal.get('price_trend', 'unknown')
            
            print(f"{i:2d}. {name}")
            print(f"    💰 {price:.0f} جنيه | 🎉 {discount:.1f}% | ⭐ {score:.1f} | 📈 {trend}")
        
        print(f"\n✅ تم إرسال {sent_count} عرض مع الصور!")
        
        return best_deals

def run_json_format_system(json_file=None):
    """تشغيل النظام المحسن"""
    
    system = JSONFormatSystem(json_file)
    return system.run_system()

if __name__ == "__main__":
    import sys
    
    json_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        if json_file:
            print(f"📂 استخدام ملف: {json_file}")
        else:
            print("🔍 البحث التلقائي عن ملف JSON...")
        
        deals = run_json_format_system(json_file)
        
        if deals:
            print(f"\n🎉 تم إرسال {len(deals)} عرض مع الصور!")
        else:
            print("\n❌ لا توجد عروض مناسبة في البيانات")
            
    except Exception as e:
        print(f"❌ خطأ في النظام: {e}")
        import traceback
        traceback.print_exc()