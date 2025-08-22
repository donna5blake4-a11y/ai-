# integrated_smart_system.py - دمج النظام الذكي مع الكشط
import asyncio
import json
import sqlite3
from datetime import datetime
from smart_deal_filter import SmartDealFilter
from amz_scraper import scrape_section  # من amz_scraper (1).py
from categories import CATEGORIES  # من categories (1).py

class IntegratedSmartSystem:
    """النظام المتكامل - كشط + فلترة ذكية + تليجرام"""
    
    def __init__(self):
        self.smart_filter = SmartDealFilter()
        self.db_file = "smart_deals.db"
        self.setup_database()
        
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
                final_score REAL,
                date_added TEXT,
                is_sent BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    async def run_daily_analysis(self):
        """تشغيل التحليل اليومي"""
        
        print("🚀 بدء التحليل اليومي للعروض الذكية...")
        
        # مرحلة 1: كشط المنتجات من أمازون
        all_products = await self.scrape_amazon_products()
        print(f"✅ تم كشط {len(all_products)} منتج من أمازون")
        
        if not all_products:
            print("❌ لم يتم العثور على منتجات للتحليل")
            return
        
        # مرحلة 2: الفلترة الذكية
        best_deals = self.smart_filter.filter_deals_smart(all_products, target_count=15)
        
        if not best_deals:
            print("❌ لم يتم العثور على عروض تستوفي المعايير")
            return
        
        # مرحلة 3: حفظ في قاعدة البيانات
        saved_deals = self.save_deals_to_db(best_deals)
        
        # مرحلة 4: إرسال للتليجرام
        if saved_deals:
            self.smart_filter.send_deals_to_telegram(saved_deals)
            self.mark_deals_as_sent(saved_deals)
            
        print(f"🎯 تم إرسال {len(saved_deals)} عرض عالي الجودة")
        
        return saved_deals
    
    async def scrape_amazon_products(self):
        """كشط المنتجات من أمازون باستخدام النظام الموجود"""
        
        all_products = []
        
        # استخدام الفئات من categories (1).py
        for category_name, category_url in CATEGORIES.items():
            print(f"🔍 كشط فئة: {category_name}")
            
            try:
                # كشط صفحات قليلة من كل فئة لتوفير الوقت
                category_products = {}
                
                await scrape_section(
                    section=category_name,
                    section_url=category_url,
                    start_page=1,
                    end_page=3,  # 3 صفحات فقط لكل فئة
                    db=category_products,
                    log_fn=self.log_message,
                    discount_alert_cb=None,  # لا نريد تنبيهات أثناء الكشط
                    discount_threshold=20,  # حد أدنى 20% خصم
                    concurrency=5
                )
                
                # تحويل النتائج لقائمة
                for asin, product_data in category_products.items():
                    if product_data.get('price') and product_data.get('discount_percent', 0) >= 20:
                        all_products.append({
                            'asin': asin,
                            'name': product_data.get('name', ''),
                            'price': product_data.get('price'),
                            'strike_price': product_data.get('strike_price'),
                            'discount_percent': product_data.get('discount_percent', 0),
                            'section': product_data.get('section', category_name),
                            'url': product_data.get('url', ''),
                            'img': product_data.get('img', ''),
                            'price_history': product_data.get('price_history', [])
                        })
                
                print(f"✅ {category_name}: {len(category_products)} منتج")
                
                # تأخير بين الفئات
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"⚠️ خطأ في كشط {category_name}: {e}")
                continue
        
        return all_products
    
    def save_deals_to_db(self, deals):
        """حفظ العروض في قاعدة البيانات"""
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        saved_deals = []
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for deal in deals:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO deals 
                    (asin, name, price, strike_price, discount_percent, section, url, img, final_score, date_added)
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
                    deal.get('final_score', 0),
                    current_date
                ))
                
                saved_deals.append(deal)
                
            except Exception as e:
                print(f"⚠️ خطأ في حفظ العرض: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"💾 تم حفظ {len(saved_deals)} عرض في قاعدة البيانات")
        return saved_deals
    
    def mark_deals_as_sent(self, deals):
        """وضع علامة على العروض المرسلة"""
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        for deal in deals:
            asin = deal.get('asin', '')
            if asin:
                cursor.execute('UPDATE deals SET is_sent = 1 WHERE asin = ?', (asin,))
        
        conn.commit()
        conn.close()
    
    def get_today_deals(self):
        """الحصول على عروض اليوم"""
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT * FROM deals 
            WHERE date_added LIKE ? 
            ORDER BY final_score DESC
        ''', (f'{today}%',))
        
        deals = cursor.fetchall()
        conn.close()
        
        return deals
    
    def get_statistics(self):
        """إحصائيات النظام"""
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # إجمالي العروض
        cursor.execute('SELECT COUNT(*) FROM deals')
        total_deals = cursor.fetchone()[0]
        
        # عروض اليوم
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM deals WHERE date_added LIKE ?', (f'{today}%',))
        today_deals = cursor.fetchone()[0]
        
        # متوسط النقاط
        cursor.execute('SELECT AVG(final_score) FROM deals WHERE final_score > 0')
        avg_score = cursor.fetchone()[0] or 0
        
        # أفضل فئة
        cursor.execute('''
            SELECT section, COUNT(*) as count 
            FROM deals 
            GROUP BY section 
            ORDER BY count DESC 
            LIMIT 1
        ''')
        best_category = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_deals': total_deals,
            'today_deals': today_deals,
            'average_score': round(avg_score, 1),
            'best_category': best_category[0] if best_category else 'غير محدد'
        }
    
    def log_message(self, message):
        """تسجيل الرسائل"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")

# دالة تشغيل النظام المتكامل
async def run_integrated_system():
    """تشغيل النظام المتكامل"""
    
    system = IntegratedSmartSystem()
    
    print("🤖 النظام الذكي المتكامل")
    print("=" * 50)
    
    # عرض الإحصائيات الحالية
    stats = system.get_statistics()
    print(f"📊 الإحصائيات:")
    print(f"   - إجمالي العروض: {stats['total_deals']:,}")
    print(f"   - عروض اليوم: {stats['today_deals']:,}")
    print(f"   - متوسط النقاط: {stats['average_score']}")
    print(f"   - أفضل فئة: {stats['best_category']}")
    print()
    
    # تشغيل التحليل اليومي
    best_deals = await system.run_daily_analysis()
    
    if best_deals:
        print("\n🏆 أفضل العروض اليوم:")
        print("-" * 80)
        
        for i, deal in enumerate(best_deals[:10], 1):
            name = deal.get('name', 'منتج')[:60]
            price = deal.get('price', 0)
            discount = deal.get('discount_percent', 0)
            score = deal.get('final_score', 0)
            
            print(f"{i:2d}. {name}...")
            print(f"    💰 {price:.0f} جنيه | 🎉 {discount:.1f}% | ⭐ {score:.1f} نقطة")
            print()
    
    # عرض الإحصائيات المحدثة
    updated_stats = system.get_statistics()
    print(f"📈 الإحصائيات المحدثة:")
    print(f"   - عروض اليوم: {updated_stats['today_deals']:,}")

# دالة تشغيل سريع للاختبار
def quick_test():
    """اختبار سريع للنظام"""
    
    # بيانات تجريبية
    test_products = [
        {
            'asin': 'B08N5WRWNW',
            'name': 'Apple iPhone 14 Pro Max 256GB Deep Purple Original',
            'price': 25000,
            'strike_price': 30000,
            'discount_percent': 16.7,
            'section': 'Electronics',
            'url': 'https://amazon.eg/dp/B08N5WRWNW',
            'img': 'https://example.com/image.jpg',
            'price_history': [
                {'date': '2024-01-01', 'price': 28000},
                {'date': '2024-01-15', 'price': 26000},
                {'date': '2024-01-30', 'price': 25000}
            ]
        },
        {
            'asin': 'B09JFGHIJK',
            'name': 'Samsung Galaxy S23 Ultra 512GB Phantom Black',
            'price': 22000,
            'strike_price': 28000,
            'discount_percent': 21.4,
            'section': 'Electronics',
            'url': 'https://amazon.eg/dp/B09JFGHIJK',
            'img': 'https://example.com/image2.jpg',
            'price_history': [
                {'date': '2024-01-01', 'price': 26000},
                {'date': '2024-01-15', 'price': 24000},
                {'date': '2024-01-30', 'price': 22000}
            ]
        }
    ]
    
    # تشغيل الفلترة
    smart_filter = SmartDealFilter()
    best_deals = smart_filter.filter_deals_smart(test_products, target_count=15)
    
    print("🧪 نتائج الاختبار:")
    for deal in best_deals:
        print(f"✅ {deal['name'][:50]}... - نقاط: {deal['final_score']:.1f}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        quick_test()
    else:
        asyncio.run(run_integrated_system())