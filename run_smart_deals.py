#!/usr/bin/env python3
# run_smart_deals.py - تشغيل نظام العروض الذكي

import asyncio
import sys
import os
from datetime import datetime

# إضافة المجلد الحالي للـ path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from integrated_smart_system import IntegratedSmartSystem, quick_test
    from smart_deal_filter import SmartDealFilter
except ImportError as e:
    print(f"❌ خطأ في الاستيراد: {e}")
    print("تأكد من وجود جميع الملفات المطلوبة")
    sys.exit(1)

def print_banner():
    """طباعة شعار النظام"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🤖 النظام الذكي لفلترة العروض - Smart Deals Filter       ║
║                                                              ║
║    يحول 1000+ عرض وهمي إلى 15 عرض موثوق يومياً             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

def print_help():
    """طباعة تعليمات الاستخدام"""
    print("""
🔧 طرق الاستخدام:

1. تشغيل النظام الكامل:
   python run_smart_deals.py

2. اختبار سريع:
   python run_smart_deals.py test

3. فلترة ملف JSON موجود:
   python run_smart_deals.py filter products.json

4. عرض الإحصائيات فقط:
   python run_smart_deals.py stats

5. عرض هذه المساعدة:
   python run_smart_deals.py help
    """)

def check_requirements():
    """فحص المتطلبات الأساسية"""
    
    required_files = [
        'config.json',
        'telegram_config.json',
        'categories.py',
        'smart_deal_filter.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ ملفات مفقودة:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    # فحص الإعدادات
    try:
        import json
        
        with open('config.json', 'r') as f:
            config = json.load(f)
            if not config.get('SCRAPER_API_KEY'):
                print("⚠️ تحذير: SCRAPER_API_KEY غير موجود في config.json")
        
        with open('telegram_config.json', 'r') as f:
            telegram_config = json.load(f)
            if not telegram_config.get('bot_token'):
                print("⚠️ تحذير: bot_token غير موجود في telegram_config.json")
    
    except Exception as e:
        print(f"⚠️ تحذير: خطأ في قراءة الإعدادات: {e}")
    
    return True

async def run_full_system():
    """تشغيل النظام الكامل"""
    
    print("🚀 بدء تشغيل النظام الذكي المتكامل...")
    print(f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        system = IntegratedSmartSystem()
        
        # عرض الإحصائيات الحالية
        stats = system.get_statistics()
        print("📊 الإحصائيات الحالية:")
        print(f"   - إجمالي العروض: {stats['total_deals']:,}")
        print(f"   - عروض اليوم: {stats['today_deals']:,}")
        print(f"   - متوسط النقاط: {stats['average_score']}")
        print(f"   - أفضل فئة: {stats['best_category']}")
        print()
        
        # تشغيل التحليل اليومي
        best_deals = await system.run_daily_analysis()
        
        if best_deals:
            print("\n🏆 تم العثور على العروض التالية:")
            print("=" * 70)
            
            for i, deal in enumerate(best_deals, 1):
                name = deal.get('name', 'منتج')[:50]
                price = deal.get('price', 0)
                discount = deal.get('discount_percent', 0)
                score = deal.get('final_score', 0)
                
                print(f"{i:2d}. {name}...")
                print(f"    💰 السعر: {price:.0f} جنيه")
                print(f"    🎉 الخصم: {discount:.1f}%")
                print(f"    ⭐ النقاط: {score:.1f}/100")
                print(f"    🔗 https://amazon.eg/dp/{deal.get('asin', '')}")
                print()
        else:
            print("❌ لم يتم العثور على عروض تستوفي المعايير اليوم")
            print("💡 جرب تقليل معايير الفلترة أو تشغيل النظام في وقت لاحق")
        
        # عرض الإحصائيات المحدثة
        updated_stats = system.get_statistics()
        print(f"\n📈 الإحصائيات المحدثة:")
        print(f"   - عروض اليوم: {updated_stats['today_deals']:,}")
        print(f"   - متوسط النقاط: {updated_stats['average_score']}")
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل النظام: {e}")
        print("💡 تأكد من اتصال الإنترنت والإعدادات")

def filter_json_file(json_file):
    """فلترة ملف JSON موجود"""
    
    if not os.path.exists(json_file):
        print(f"❌ الملف غير موجود: {json_file}")
        return
    
    try:
        import json
        
        print(f"📂 جاري تحميل الملف: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # تحويل البيانات للتنسيق المطلوب
        products = []
        
        if isinstance(data, dict):
            # إذا كان الملف بتنسيق {asin: product_data}
            for asin, product_data in data.items():
                if isinstance(product_data, dict):
                    product = {
                        'asin': asin,
                        'name': product_data.get('name', ''),
                        'price': product_data.get('price', 0),
                        'strike_price': product_data.get('strike_price', 0),
                        'discount_percent': product_data.get('discount_percent', 0),
                        'section': product_data.get('section', ''),
                        'url': product_data.get('url', ''),
                        'img': product_data.get('img', ''),
                        'price_history': product_data.get('price_history', [])
                    }
                    
                    # فلترة أولية
                    if (product['price'] > 0 and 
                        product['discount_percent'] >= 15 and
                        product['strike_price'] > product['price']):
                        products.append(product)
        
        elif isinstance(data, list):
            # إذا كان الملف عبارة عن قائمة
            products = data
        
        print(f"✅ تم تحميل {len(products)} منتج")
        
        if not products:
            print("❌ لا توجد منتجات صالحة للفلترة")
            return
        
        # تشغيل الفلترة
        smart_filter = SmartDealFilter()
        best_deals = smart_filter.filter_deals_smart(products, target_count=15)
        
        if best_deals:
            print(f"\n🎯 تم انتقاء {len(best_deals)} عرض عالي الجودة:")
            print("-" * 60)
            
            for i, deal in enumerate(best_deals, 1):
                name = deal.get('name', 'منتج')[:45]
                price = deal.get('price', 0)
                discount = deal.get('discount_percent', 0)
                score = deal.get('final_score', 0)
                
                print(f"{i:2d}. {name}...")
                print(f"    💰 {price:.0f} جنيه | 🎉 {discount:.1f}% | ⭐ {score:.1f}")
            
            # حفظ النتائج
            output_file = f"filtered_deals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(best_deals, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 تم حفظ النتائج في: {output_file}")
            
        else:
            print("❌ لم يتم العثور على عروض تستوفي المعايير")
    
    except Exception as e:
        print(f"❌ خطأ في معالجة الملف: {e}")

def show_stats():
    """عرض الإحصائيات فقط"""
    
    try:
        system = IntegratedSmartSystem()
        stats = system.get_statistics()
        
        print("📊 إحصائيات النظام:")
        print("=" * 30)
        print(f"📦 إجمالي العروض: {stats['total_deals']:,}")
        print(f"🗓️ عروض اليوم: {stats['today_deals']:,}")
        print(f"⭐ متوسط النقاط: {stats['average_score']}")
        print(f"🏆 أفضل فئة: {stats['best_category']}")
        
        # عرض عروض اليوم إن وجدت
        today_deals = system.get_today_deals()
        if today_deals:
            print(f"\n🎯 عروض اليوم ({len(today_deals)}):")
            print("-" * 40)
            
            for deal in today_deals[:10]:  # أول 10 عروض
                print(f"• {deal[2][:40]}... - {deal[9]:.1f} نقطة")
        else:
            print("\n📭 لا توجد عروض اليوم")
    
    except Exception as e:
        print(f"❌ خطأ في عرض الإحصائيات: {e}")

async def main():
    """الدالة الرئيسية"""
    
    print_banner()
    
    # فحص المعاملات
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "help":
            print_help()
            return
        
        elif command == "test":
            print("🧪 تشغيل الاختبار السريع...")
            quick_test()
            return
        
        elif command == "stats":
            show_stats()
            return
        
        elif command == "filter" and len(sys.argv) > 2:
            json_file = sys.argv[2]
            filter_json_file(json_file)
            return
        
        else:
            print(f"❌ أمر غير معروف: {command}")
            print_help()
            return
    
    # فحص المتطلبات
    if not check_requirements():
        print("\n❌ يرجى إكمال المتطلبات قبل تشغيل النظام")
        return
    
    # تشغيل النظام الكامل
    await run_full_system()
    
    print("\n✅ تم انتهاء العملية بنجاح")
    print(f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف النظام بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        sys.exit(1)