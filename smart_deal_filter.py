# smart_deal_filter.py - نظام فلترة العروض الذكي
import json
import sqlite3
import requests
import time
import random
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from playwright.async_api import async_playwright
import re
from urllib.parse import quote

class SmartDealFilter:
    """نظام فلترة العروض الذكي - مجاني ودقيق"""
    
    def __init__(self):
        # تحميل الإعدادات
        self.load_config()
        
        # إعدادات الفلترة
        self.min_discount = 20  # حد أدنى للخصم
        self.max_discount = 80  # حد أقصى للخصم (أعلى من كده مشبوه)
        self.min_price = 30     # حد أدنى للسعر
        self.max_price = 5000   # حد أقصى للسعر
        
        # فئات موثوقة
        self.trusted_categories = [
            'Electronics', 'Home & Kitchen', 'Beauty', 'Health & Household Products',
            'Tools & Home Improvement', 'Automotive', 'Fashion', 'Grocery'
        ]
        
        # كلمات مشبوهة في أسماء المنتجات
        self.suspicious_words = [
            'fake', 'replica', 'copy', 'imitation', 'نسخة', 'مقلد', 'تقليد',
            'مستعمل', 'used', 'damaged', 'broken', 'عطلان'
        ]
        
        # مؤشرات الجودة
        self.quality_indicators = [
            'original', 'authentic', 'genuine', 'warranty', 'أصلي', 'ضمان',
            'new', 'brand new', 'جديد', 'معتمد', 'authorized'
        ]
        
    def load_config(self):
        """تحميل الإعدادات من الملفات"""
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
    
    def filter_deals_smart(self, products_list, target_count=15):
        """الفلترة الذكية للعروض"""
        
        print(f"🔍 بدء فلترة {len(products_list)} منتج للحصول على أفضل {target_count} عرض...")
        
        # المرحلة 1: الفلترة الأساسية
        basic_filtered = self.basic_filter(products_list)
        print(f"✅ المرحلة 1: تم فلترة {len(basic_filtered)} منتج من الفلترة الأساسية")
        
        # المرحلة 2: التحليل النصي
        text_filtered = self.text_analysis_filter(basic_filtered)
        print(f"✅ المرحلة 2: تم فلترة {len(text_filtered)} منتج من التحليل النصي")
        
        # المرحلة 3: تحليل الأسعار التاريخية (إن وجدت)
        price_filtered = self.price_analysis_filter(text_filtered)
        print(f"✅ المرحلة 3: تم فلترة {len(price_filtered)} منتج من تحليل الأسعار")
        
        # المرحلة 4: التحقق من توفر المنتج
        available_filtered = self.availability_filter(price_filtered[:50])  # أفضل 50 فقط
        print(f"✅ المرحلة 4: تم التحقق من {len(available_filtered)} منتج متوفر")
        
        # المرحلة 5: الترتيب النهائي وانتقاء الأفضل
        final_deals = self.final_ranking(available_filtered, target_count)
        print(f"🎯 النتيجة النهائية: {len(final_deals)} عرض عالي الجودة")
        
        return final_deals
    
    def basic_filter(self, products):
        """الفلترة الأساسية"""
        filtered = []
        
        for product in products:
            # فلتر السعر
            price = product.get('price', 0)
            if not (self.min_price <= price <= self.max_price):
                continue
            
            # فلتر الخصم
            discount = product.get('discount_percent', 0)
            if not (self.min_discount <= discount <= self.max_discount):
                continue
            
            # فلتر الفئة
            category = product.get('section', '')
            if category not in self.trusted_categories:
                continue
            
            # فلتر السعر الأصلي
            strike_price = product.get('strike_price', 0)
            if strike_price <= 0 or strike_price <= price:
                continue
            
            filtered.append(product)
        
        return filtered
    
    def text_analysis_filter(self, products):
        """فلترة بناء على تحليل النص"""
        filtered = []
        
        for product in products:
            name = product.get('name', '').lower()
            
            # فحص الكلمات المشبوهة
            suspicious_count = sum(1 for word in self.suspicious_words if word in name)
            if suspicious_count > 0:
                continue
            
            # فحص مؤشرات الجودة
            quality_count = sum(1 for indicator in self.quality_indicators if indicator in name)
            
            # حساب نقاط النص
            text_score = quality_count * 10 - suspicious_count * 20
            
            # إضافة النقاط للمنتج
            product['text_score'] = text_score
            
            if text_score >= 0:  # نقاط إيجابية أو محايدة
                filtered.append(product)
        
        return filtered
    
    def price_analysis_filter(self, products):
        """فلترة بناء على تحليل الأسعار"""
        filtered = []
        
        for product in products:
            price_history = product.get('price_history', [])
            
            # حساب نقاط تحليل السعر
            price_score = 0
            
            if len(price_history) >= 3:
                # تحليل تاريخ الأسعار
                prices = [h.get('price', 0) for h in price_history if h.get('price', 0) > 0]
                
                if prices:
                    avg_price = sum(prices) / len(prices)
                    current_price = product.get('price', 0)
                    
                    # العرض جيد إذا كان أقل من المتوسط بـ 15%+
                    if current_price < avg_price * 0.85:
                        price_score += 30
                    elif current_price < avg_price:
                        price_score += 15
                    
                    # فحص استقرار الأسعار
                    price_variance = (max(prices) - min(prices)) / avg_price
                    if price_variance < 0.3:  # تباين أقل من 30%
                        price_score += 10
            
            # فحص منطقية السعر مقارنة بالخصم
            discount = product.get('discount_percent', 0)
            price = product.get('price', 0)
            strike_price = product.get('strike_price', 0)
            
            # التحقق من صحة حساب الخصم
            calculated_discount = ((strike_price - price) / strike_price) * 100
            if abs(calculated_discount - discount) <= 2:  # هامش خطأ 2%
                price_score += 20
            
            product['price_score'] = price_score
            
            if price_score >= 15:  # حد أدنى لنقاط السعر
                filtered.append(product)
        
        return filtered
    
    def availability_filter(self, products):
        """فحص توفر المنتجات"""
        available_products = []
        
        print("🔍 فحص توفر المنتجات...")
        
        for i, product in enumerate(products):
            asin = product.get('asin', '')
            if not asin:
                continue
            
            # فحص التوفر باستخدام ScraperAPI
            is_available = self.check_product_availability(asin)
            
            if is_available:
                product['availability_checked'] = True
                available_products.append(product)
                print(f"✅ متوفر: {product.get('name', 'منتج')[:50]}...")
            else:
                print(f"❌ غير متوفر: {product.get('name', 'منتج')[:50]}...")
            
            # تأخير لتجنب الحظر
            if i % 5 == 0:
                time.sleep(random.uniform(2, 5))
        
        return available_products
    
    def check_product_availability(self, asin):
        """فحص توفر منتج واحد"""
        if not self.scraper_api_key:
            return True  # افتراض التوفر إذا لم يكن هناك API key
        
        try:
            url = f"https://api.scraperapi.com/?api_key={self.scraper_api_key}&url=https://www.amazon.eg/dp/{asin}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # البحث عن مؤشرات عدم التوفر
                unavailable_indicators = [
                    'currently unavailable', 'غير متوفر', 'out of stock',
                    'temporarily out of stock', 'نفد المخزون'
                ]
                
                for indicator in unavailable_indicators:
                    if indicator in content:
                        return False
                
                # البحث عن مؤشرات التوفر
                available_indicators = [
                    'add to cart', 'أضف إلى السلة', 'buy now', 'اشتري الآن',
                    'in stock', 'متوفر', 'available'
                ]
                
                for indicator in available_indicators:
                    if indicator in content:
                        return True
            
            return True  # افتراض التوفر في حالة عدم وضوح الحالة
            
        except Exception as e:
            print(f"⚠️ خطأ في فحص التوفر: {e}")
            return True  # افتراض التوفر في حالة الخطأ
    
    def final_ranking(self, products, target_count):
        """الترتيب النهائي وانتقاء الأفضل"""
        
        # حساب النقاط النهائية لكل منتج
        for product in products:
            final_score = 0
            
            # نقاط الخصم (40%)
            discount = product.get('discount_percent', 0)
            final_score += min(40, discount * 0.6)
            
            # نقاط تحليل النص (30%)
            text_score = product.get('text_score', 0)
            final_score += min(30, max(0, text_score))
            
            # نقاط تحليل السعر (30%)
            price_score = product.get('price_score', 0)
            final_score += min(30, price_score)
            
            product['final_score'] = final_score
        
        # ترتيب حسب النقاط النهائية
        sorted_products = sorted(products, key=lambda x: x['final_score'], reverse=True)
        
        # انتقاء الأفضل مع التنويع
        final_deals = self.diversify_selection(sorted_products, target_count)
        
        return final_deals
    
    def diversify_selection(self, sorted_products, target_count):
        """تنويع الاختيار عبر الفئات"""
        selected = []
        category_counts = {}
        
        for product in sorted_products:
            category = product.get('section', '')
            
            # حد أقصى 3 منتجات لكل فئة
            if category_counts.get(category, 0) < 3:
                selected.append(product)
                category_counts[category] = category_counts.get(category, 0) + 1
                
                if len(selected) >= target_count:
                    break
        
        return selected
    
    def send_deals_to_telegram(self, deals):
        """إرسال العروض لبوت التليجرام"""
        if not self.bot_token or not self.users:
            print("⚠️ إعدادات التليجرام غير مكتملة")
            return
        
        message = self.format_deals_message(deals)
        
        for user_id in self.users:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                data = {
                    'chat_id': user_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, data=data)
                
                if response.status_code == 200:
                    print(f"✅ تم إرسال العروض للمستخدم {user_id}")
                else:
                    print(f"❌ فشل إرسال العروض للمستخدم {user_id}")
                    
            except Exception as e:
                print(f"⚠️ خطأ في إرسال التليجرام: {e}")
    
    def format_deals_message(self, deals):
        """تنسيق رسالة العروض"""
        message = f"🎯 <b>أفضل {len(deals)} عرض اليوم</b>\n"
        message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        for i, deal in enumerate(deals, 1):
            name = deal.get('name', 'منتج')[:50] + "..."
            price = deal.get('price', 0)
            strike_price = deal.get('strike_price', 0)
            discount = deal.get('discount_percent', 0)
            score = deal.get('final_score', 0)
            
            savings = strike_price - price
            
            message += f"<b>{i}. {name}</b>\n"
            message += f"💰 السعر: {price:.0f} جنيه\n"
            message += f"🏷️ السعر الأصلي: {strike_price:.0f} جنيه\n"
            message += f"🎉 الخصم: {discount:.1f}% (توفير {savings:.0f} جنيه)\n"
            message += f"⭐ نقاط الجودة: {score:.1f}/100\n"
            
            if deal.get('asin'):
                message += f"🔗 <a href='https://www.amazon.eg/dp/{deal['asin']}'>رابط المنتج</a>\n"
            
            message += "\n"
        
        message += "🤖 <i>تم اختيار هذه العروض بواسطة النظام الذكي</i>"
        
        return message

# دالة تشغيل النظام
def run_smart_filter():
    """تشغيل نظام الفلترة الذكي"""
    
    # إنشاء النظام
    filter_system = SmartDealFilter()
    
    # هنا تحط المنتجات اللي جايه من الكشط
    # مثال:
    sample_products = [
        {
            'asin': 'B08N5WRWNW',
            'name': 'Apple iPhone 14 Pro Max 256GB Deep Purple',
            'price': 25000,
            'strike_price': 30000,
            'discount_percent': 16.7,
            'section': 'Electronics',
            'price_history': [
                {'date': '2024-01-01', 'price': 28000},
                {'date': '2024-01-15', 'price': 26000},
                {'date': '2024-01-30', 'price': 25000}
            ]
        }
        # إضافة المزيد من المنتجات هنا...
    ]
    
    # تشغيل الفلترة
    best_deals = filter_system.filter_deals_smart(sample_products, target_count=15)
    
    # إرسال للتليجرام
    if best_deals:
        filter_system.send_deals_to_telegram(best_deals)
        
        # طباعة النتائج
        print("\n🏆 أفضل العروض:")
        for i, deal in enumerate(best_deals, 1):
            print(f"{i}. {deal['name'][:50]}... - {deal['final_score']:.1f} نقطة")
    else:
        print("❌ لم يتم العثور على عروض تستوفي المعايير")

if __name__ == "__main__":
    run_smart_filter()