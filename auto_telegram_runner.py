# auto_telegram_runner.py - دمج النظام الحالي مع الإرسال التلقائي

import asyncio
import json
import sqlite3
import requests
import time
from datetime import datetime
import threading
from PIL import Image
from io import BytesIO

# استيراد النظام الحالي
try:
    from fixed_integrated_system import FixedSmartSystem
    from enhanced_telegram_system import EnhancedTelegramSystem
except ImportError:
    FixedSmartSystem = None
    EnhancedTelegramSystem = None

class AutoTelegramRunner:
    """نظام مدمج: كشط + تحليل JSON + إرسال تلقائي بالصور"""
    
    def __init__(self, json_file="products.json"):
        self.json_file = json_file
        self.scraping_system = FixedSmartSystem() if FixedSmartSystem else None
        self.json_system = EnhancedTelegramSystem(json_file) if EnhancedTelegramSystem else None
        self.load_config()
        
        # إعدادات النظام المدمج
        self.use_scraping = True      # استخدام الكشط المباشر
        self.use_json_analysis = True # استخدام تحليل JSON
        self.auto_send = True         # إرسال تلقائي
        self.send_with_images = True  # إرسال مع الصور
        
    def load_config(self):
        """تحميل الإعدادات"""
        try:
            with open('telegram_config.json', 'r') as f:
                config = json.load(f)
                self.bot_token = config.get('bot_token')
                self.users = config.get('users', [])
        except:
            self.bot_token = None
            self.users = []
    
    def send_deal_with_image_enhanced(self, deal):
        """إرسال عرض مع صورة محسن"""
        
        if not self.bot_token or not self.users:
            return False
        
        try:
            name = deal.get('name', 'منتج')
            price = deal.get('price', 0)
            strike_price = deal.get('strike_price', 0)
            discount = deal.get('discount_percent', 0)
            score = deal.get('final_score', deal.get('total_score', 0))
            asin = deal.get('asin', '')
            img_url = deal.get('img', '')
            section = deal.get('section', 'غير محدد')
            
            savings = strike_price - price
            
            # تحضير النص المحسن
            caption = f"""🎯 <b>عرض مميز معتمد بالذكاء الاصطناعي</b>

📦 <b>{name[:85]}</b>

💰 السعر الحالي: <b>{price:.0f} جنيه</b>
🏷️ السعر الأصلي: <s>{strike_price:.0f} جنيه</s>
🎉 نسبة الخصم: <b>{discount:.1f}%</b>
💸 مقدار التوفير: <b>{savings:.0f} جنيه</b>
⭐ تقييم الجودة: <b>{score:.1f}/100</b>
🏷️ الفئة: <b>{section}</b>

🔗 <a href="https://www.amazon.eg/dp/{asin}">🛒 اشتري الآن من أمازون</a>

🤖 <i>تم اختيار هذا العرض بعناية من آلاف المنتجات</i>
⚡ <i>عرض محدود - قد ينتهي قريباً</i>"""
            
            sent_successfully = False
            
            # محاولة إرسال مع الصورة لكل مستخدم
            for user_id in self.users:
                try:
                    # تحميل ومعالجة الصورة
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
                    
                except Exception as e:
                    print(f"⚠️ خطأ في إرسال للمستخدم {user_id}: {e}")
                    continue
            
            return sent_successfully
            
        except Exception as e:
            print(f"❌ خطأ في إرسال العرض: {e}")
            return False
    
    def download_and_optimize_image(self, img_url, max_size_kb=900):
        """تحميل وتحسين الصورة"""
        
        if not img_url:
            return None
        
        try:
            # تحميل الصورة
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            response = requests.get(img_url, headers=headers, timeout=15)
            
            if response.status_code == 200 and len(response.content) > 0:
                # فتح الصورة
                img = Image.open(BytesIO(response.content))
                
                # تحويل إلى RGB إذا لزم الأمر
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # تحسين الحجم
                original_size = img.size
                if original_size[0] > 1200 or original_size[1] > 1200:
                    img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                
                # ضغط تدريجي
                output = BytesIO()
                quality = 90
                
                for attempt in range(5):
                    output.seek(0)
                    output.truncate()
                    
                    img.save(output, format='JPEG', quality=quality, optimize=True)
                    
                    size_kb = len(output.getvalue()) / 1024
                    
                    if size_kb <= max_size_kb:
                        print(f"✅ تم تحسين الصورة: {size_kb:.1f} KB (جودة {quality}%)")
                        return output.getvalue()
                    
                    quality -= 15
                    if quality < 30:
                        break
                
                # إذا فشل التحسين، أرجع الصورة كما هي
                if len(response.content) <= max_size_kb * 1024:
                    return response.content
            
            return None
            
        except Exception as e:
            print(f"⚠️ خطأ في معالجة الصورة: {e}")
            return None
    
    def run_hybrid_system(self):
        """تشغيل النظام المختلط"""
        
        print("🚀 بدء النظام المختلط المحسن...")
        print("=" * 60)
        
        all_deals = []
        
        # الطريقة 1: تحليل JSON (سريع ودقيق)
        if self.use_json_analysis and self.json_system:
            print("📊 المرحلة 1: تحليل ملف JSON...")
            json_deals = self.json_system.analyze_and_find_deals()
            
            if json_deals:
                all_deals.extend(json_deals[:10])  # أفضل 10 من JSON
                print(f"✅ تم اختيار {len(json_deals[:10])} عرض من تحليل JSON")
        
        # الطريقة 2: كشط مباشر (للعروض الجديدة)
        if self.use_scraping and self.scraping_system and len(all_deals) < 15:
            print("🔍 المرحلة 2: كشط مباشر للعروض الجديدة...")
            
            try:
                scraped_deals = self.scraping_system.run_complete_analysis()
                
                if scraped_deals:
                    # إضافة العروض الجديدة فقط
                    existing_asins = {deal.get('asin') for deal in all_deals}
                    new_deals = [deal for deal in scraped_deals 
                                if deal.get('asin') not in existing_asins]
                    
                    needed_count = 15 - len(all_deals)
                    all_deals.extend(new_deals[:needed_count])
                    
                    print(f"✅ تم إضافة {len(new_deals[:needed_count])} عرض جديد من الكشط")
                    
            except Exception as e:
                print(f"⚠️ خطأ في الكشط المباشر: {e}")
        
        # ترتيب نهائي حسب النقاط
        all_deals.sort(key=lambda x: x.get('final_score', x.get('total_score', 0)), reverse=True)
        
        # أخذ أفضل 15 عرض
        final_deals = all_deals[:15]
        
        if not final_deals:
            print("❌ لم يتم العثور على عروض للإرسال")
            return []
        
        print(f"🎯 إجمالي العروض المختارة: {len(final_deals)}")
        
        # إرسال تلقائي مع الصور
        if self.auto_send:
            self.send_deals_auto_with_images(final_deals)
        
        return final_deals
    
    def send_deals_auto_with_images(self, deals):
        """إرسال العروض تلقائياً مع الصور"""
        
        if not self.bot_token or not self.users:
            print("⚠️ إعدادات التليجرام غير مكتملة")
            return
        
        print(f"📱 بدء الإرسال التلقائي لـ {len(deals)} عرض مع الصور...")
        
        # رسالة افتتاحية
        intro_msg = f"""🎯 <b>العروض المميزة اليوم</b>
📅 {datetime.now().strftime('%A, %Y-%m-%d %H:%M')}

🤖 <b>تم اختيار {len(deals)} عرض عالي الجودة</b>
🧠 تحليل ذكي متطور + فحص دقيق
📸 مع الصور والتفاصيل الكاملة

⏳ جاري الإرسال..."""
        
        # إرسال الرسالة الافتتاحية
        for user_id in self.users:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                data = {
                    'chat_id': user_id,
                    'text': intro_msg,
                    'parse_mode': 'HTML'
                }
                requests.post(url, data=data, timeout=10)
            except:
                pass
        
        # تأخير قبل بدء الإرسال
        time.sleep(2)
        
        # إرسال كل عرض بصورته
        sent_count = 0
        
        for i, deal in enumerate(deals, 1):
            print(f"📤 إرسال العرض {i}/{len(deals)}: {deal.get('name', 'منتج')[:35]}...")
            
            success = self.send_deal_with_image_enhanced(deal)
            if success:
                sent_count += 1
            
            # تأخير بين العروض
            if i < len(deals):
                delay = 4 if i <= 5 else 3  # تأخير أطول للعروض الأولى
                time.sleep(delay)
        
        # رسالة ختامية محسنة
        end_msg = f"""🎉 <b>تم الانتهاء من إرسال العروض</b>

📊 <b>ملخص اليوم:</b>
• العروض المرسلة: {sent_count} عرض
• متوسط الجودة: {sum(d.get('final_score', d.get('total_score', 0)) for d in deals) / len(deals):.1f}/100
• إجمالي التوفير المحتمل: {sum((d.get('strike_price', 0) - d.get('price', 0)) for d in deals):.0f} جنيه

🎯 <b>جميع العروض:</b>
• ✅ معتمدة بالذكاء الاصطناعي
• 🔍 مفحوصة ومتأكد من جودتها
• 📸 مرفقة بالصور والتفاصيل

🔔 <b>تنبيه:</b> العروض محدودة وقد تنتهي سريعاً!

🤖 <i>نظام LAQTA الذكي - خدمة مجانية</i>"""
        
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
        
        print(f"🎉 تم إرسال {sent_count} عرض بنجاح مع الصور!")
        return sent_count
    
    def send_deal_with_image_enhanced(self, deal):
        """إرسال عرض واحد مع صورة محسنة"""
        
        try:
            name = deal.get('name', 'منتج')
            price = deal.get('price', 0)
            strike_price = deal.get('strike_price', 0)
            discount = deal.get('discount_percent', 0)
            score = deal.get('final_score', deal.get('total_score', 0))
            asin = deal.get('asin', '')
            img_url = deal.get('img', '')
            section = deal.get('section', 'غير محدد')
            
            savings = strike_price - price
            
            # رموز تعبيرية حسب الفئة
            category_emoji = {
                'Electronics': '📱',
                'Home & Kitchen': '🏠',
                'Beauty': '💄',
                'Health & Household Products': '🏥',
                'Tools & Home Improvement': '🔧',
                'Automotive': '🚗',
                'Fashion': '👕',
                'Grocery': '🛒'
            }
            
            emoji = category_emoji.get(section, '📦')
            
            # تحضير النص المحسن
            caption = f"""{emoji} <b>عرض مميز معتمد</b>

📦 <b>{name[:90]}</b>

💰 <b>{price:.0f} جنيه</b> (كان <s>{strike_price:.0f}</s>)
🎉 خصم <b>{discount:.1f}%</b> - توفير <b>{savings:.0f} جنيه</b>
⭐ جودة <b>{score:.1f}/100</b>

🔗 <a href="https://www.amazon.eg/dp/{asin}">🛒 اشتري الآن</a>

🤖 معتمد بالذكاء الاصطناعي"""
            
            sent_to_any = False
            
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
                                sent_to_any = True
                                continue
                    
                    # إرسال نص فقط كـ fallback
                    url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                    data = {
                        'chat_id': user_id,
                        'text': caption,
                        'parse_mode': 'HTML'
                    }
                    
                    response = requests.post(url, data=data, timeout=15)
                    
                    if response.status_code == 200:
                        sent_to_any = True
                        
                except Exception as e:
                    continue
            
            return sent_to_any
            
        except Exception as e:
            print(f"⚠️ خطأ في إرسال العرض: {e}")
            return False
    
    def download_and_optimize_image(self, img_url, max_size_kb=800):
        """تحميل وتحسين الصورة للتليجرام"""
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/*,*/*;q=0.8'
            }
            
            response = requests.get(img_url, headers=headers, timeout=12)
            
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                
                # تحويل للـ RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # تصغير إذا كان كبير
                if img.size[0] > 1000 or img.size[1] > 1000:
                    img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
                
                # ضغط
                output = BytesIO()
                quality = 85
                
                while quality >= 30:
                    output.seek(0)
                    output.truncate()
                    img.save(output, format='JPEG', quality=quality, optimize=True)
                    
                    if len(output.getvalue()) <= max_size_kb * 1024:
                        return output.getvalue()
                    
                    quality -= 10
                
                return output.getvalue()  # أرجع حتى لو كان كبير
            
            return None
            
        except Exception as e:
            return None
    
    def run_complete_system(self):
        """تشغيل النظام الكامل"""
        
        print("🤖 بدء النظام الكامل المحسن...")
        print("=" * 60)
        
        # استخدام النظام المعتمد على JSON (أسرع وأدق)
        if self.json_system:
            deals = self.json_system.analyze_and_find_deals()
            
            if deals:
                print(f"✅ تم العثور على {len(deals)} عرض عالي الجودة")
                
                # إرسال تلقائي مع الصور
                if self.auto_send:
                    sent_count = 0
                    
                    for i, deal in enumerate(deals, 1):
                        print(f"📤 إرسال العرض {i}/{len(deals)}...")
                        
                        if self.send_deal_with_image_enhanced(deal):
                            sent_count += 1
                        
                        # تأخير بين العروض
                        if i < len(deals):
                            time.sleep(3)
                    
                    print(f"🎉 تم إرسال {sent_count} عرض بنجاح!")
                
                # عرض النتائج
                print("\n🏆 العروض المرسلة:")
                print("-" * 50)
                
                for i, deal in enumerate(deals, 1):
                    name = deal.get('name', 'منتج')[:45] + "..."
                    price = deal.get('price', 0)
                    discount = deal.get('discount_percent', 0)
                    score = deal.get('total_score', 0)
                    
                    print(f"{i:2d}. {name}")
                    print(f"    💰 {price:.0f} جنيه | 🎉 {discount:.1f}% | ⭐ {score:.1f}")
                
                return deals
            else:
                print("❌ لم يتم العثور على عروض مناسبة")
                return []
        else:
            print("❌ النظام غير متاح")
            return []

def run_auto_telegram_system(json_file="products.json"):
    """تشغيل النظام التلقائي"""
    
    runner = AutoTelegramRunner(json_file)
    return runner.run_complete_system()

if __name__ == "__main__":
    import sys
    
    json_file = sys.argv[1] if len(sys.argv) > 1 else "products.json"
    
    try:
        print(f"📂 استخدام ملف: {json_file}")
        deals = run_auto_telegram_system(json_file)
        
        if deals:
            print(f"\n✅ تم إرسال {len(deals)} عرض بنجاح!")
        else:
            print("\n❌ لا توجد عروض للإرسال اليوم")
            
    except Exception as e:
        print(f"❌ خطأ في النظام: {e}")
        import traceback
        traceback.print_exc()