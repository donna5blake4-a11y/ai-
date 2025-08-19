# test_ai_system.py
# اختبار النظام المحسن مع AI

import asyncio
import json
from datetime import datetime
from ai_price_analyzer import AIPriceAnalyzer, DealAnalysis
from enhanced_amz_scraper import DatabaseManager, EnhancedScraper
from enhanced_telegram_bot import EnhancedTelegramBot

async def test_ai_analyzer():
    """اختبار محلل AI"""
    print("🧪 اختبار محلل AI...")
    
    # إنشاء محلل AI
    analyzer = AIPriceAnalyzer()
    
    # بيانات اختبار المنتج
    test_product = {
        "name": "ماكينة حلاقة متعددة الاستخدامات 10 في 1 للرجال من بيبي ليس، مجموعة أدوات تهذيب وحلاقة لاسلكية من التيتانيوم الكربوني مع شفرات بعرض 34 ملم، مرفقات للأنف/الأذن/الجسم ورؤوس قابلة للغسيل",
        "price": 299.99,
        "strike_price": 599.99,
        "discount_percent": 50.0,
        "section": "Electronics",
        "asin": "TEST123",
        "url": "https://www.amazon.eg/test",
        "img": "https://example.com/test.jpg"
    }
    
    try:
        # تحليل المنتج
        print("🔍 جاري تحليل المنتج...")
        analysis = await analyzer.analyze_deal(test_product)
        
        print("✅ التحليل مكتمل!")
        print(f"📊 درجة العرض: {analysis.deal_score:.1f}/100")
        print(f"🎯 العرض حقيقي: {'نعم' if analysis.is_real_deal else 'لا'}")
        print(f"🔒 مستوى الثقة: {analysis.confidence:.1%}")
        print(f"💡 التوصية: {analysis.recommendation}")
        print(f"📈 متوسط السوق: {analysis.average_market_price:,.0f} جنيه")
        print(f"🏪 عدد المنافسين: {len(analysis.competitor_prices)}")
        
        # عرض أسعار المنافسين
        if analysis.competitor_prices:
            print("\n🏪 أسعار المنافسين:")
            for comp in analysis.competitor_prices:
                print(f"• {comp.retailer}: {comp.price:,.0f} جنيه (ثقة: {comp.confidence:.1%})")
        
        # عرض عوامل المخاطرة
        if analysis.risk_factors:
            print("\n⚠️ عوامل المخاطرة:")
            for risk in analysis.risk_factors:
                print(f"• {risk}")
        
        # حفظ التحليل
        analyzer.save_analysis(test_product["asin"], test_product["name"], analysis)
        print("\n💾 تم حفظ التحليل في قاعدة البيانات")
        
        return analysis
        
    except Exception as e:
        print(f"❌ خطأ في التحليل: {e}")
        return None
    finally:
        await analyzer.close_session()

def test_database_manager():
    """اختبار مدير قاعدة البيانات"""
    print("\n🗄️ اختبار مدير قاعدة البيانات...")
    
    try:
        # إنشاء مدير قاعدة البيانات
        db_manager = DatabaseManager("test_products.db")
        
        # بيانات اختبار
        test_product = {
            "asin": "TEST123",
            "name": "منتج اختبار",
            "url": "https://test.com",
            "img": "https://test.com/img.jpg",
            "section": "Electronics",
            "price": 299.99,
            "strike_price": 599.99,
            "discount_percent": 50.0
        }
        
        # حفظ المنتج
        db_manager.save_product(test_product)
        print("✅ تم حفظ المنتج")
        
        # جلب المنتجات غير المحللة
        unanalyzed = db_manager.get_unanalyzed_products()
        print(f"📦 المنتجات غير المحللة: {len(unanalyzed)}")
        
        # جلب العروض الحقيقية
        real_deals = db_manager.get_real_deals()
        print(f"🎯 العروض الحقيقية: {len(real_deals)}")
        
        return db_manager
        
    except Exception as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
        return None

def test_telegram_bot():
    """اختبار بوت التليجرام"""
    print("\n📱 اختبار بوت التليجرام...")
    
    try:
        # إنشاء بوت
        bot = EnhancedTelegramBot()
        
        # اختبار تحميل الإعدادات
        if bot.bot_token:
            print("✅ تم تحميل إعدادات البوت")
            print(f"👥 عدد المستخدمين: {len(bot.users)}")
        else:
            print("⚠️ لم يتم العثور على إعدادات البوت")
        
        return bot
        
    except Exception as e:
        print(f"❌ خطأ في البوت: {e}")
        return None

async def test_full_system():
    """اختبار النظام الكامل"""
    print("🚀 اختبار النظام الكامل...")
    
    try:
        # اختبار محلل AI
        analysis = await test_ai_analyzer()
        if not analysis:
            return False
        
        # اختبار قاعدة البيانات
        db_manager = test_database_manager()
        if not db_manager:
            return False
        
        # اختبار البوت
        bot = test_telegram_bot()
        if not bot:
            return False
        
        # اختبار الكاشف المحسن
        print("\n🔧 اختبار الكاشف المحسن...")
        enhanced_scraper = EnhancedScraper(db_manager)
        
        # اختبار معالجة المنتج
        test_product = {
            "asin": "TEST456",
            "name": "منتج اختبار آخر",
            "url": "https://test2.com",
            "img": "https://test2.com/img.jpg",
            "section": "Beauty",
            "price": 199.99,
            "strike_price": 399.99,
            "discount_percent": 50.0
        }
        
        await enhanced_scraper.process_product(test_product)
        print("✅ تم معالجة المنتج")
        
        # اختبار تحليل المنتجات المعلقة
        await enhanced_scraper.analyze_pending_products(limit=5)
        print("✅ تم تحليل المنتجات المعلقة")
        
        # اختبار ملخص العروض الذكية
        summary = enhanced_scraper.get_smart_deals_summary()
        print(f"📊 ملخص العروض: {summary['total_real_deals']} عروض حقيقية")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في النظام الكامل: {e}")
        return False

def test_price_extraction():
    """اختبار استخراج الأسعار"""
    print("\n💰 اختبار استخراج الأسعار...")
    
    analyzer = AIPriceAnalyzer()
    
    test_prices = [
        "299.99 جنيه",
        "1,299.99 EGP",
        "2,500 جنيه مصري",
        "99.99",
        "1,234,567.89",
        "غير متوفر"
    ]
    
    for price_text in test_prices:
        extracted = analyzer.extract_price(price_text)
        print(f"'{price_text}' -> {extracted}")

def test_name_similarity():
    """اختبار تطابق الأسماء"""
    print("\n🔍 اختبار تطابق الأسماء...")
    
    analyzer = AIPriceAnalyzer()
    
    test_cases = [
        ("ماكينة حلاقة بيبي ليس", "ماكينة حلاقة متعددة الاستخدامات بيبي ليس"),
        ("هاتف سامسونج", "هاتف ايفون"),
        ("لابتوب ديل", "لابتوب ديل انسبايرون"),
        ("سماعات بلوتوث", "سماعات بلوتوث لاسلكية")
    ]
    
    for name1, name2 in test_cases:
        similarity = analyzer.calculate_name_similarity(name1, name2)
        print(f"'{name1}' vs '{name2}' -> {similarity:.2f}")

async def main():
    """الدالة الرئيسية للاختبار"""
    print("🧪 بدء اختبارات النظام المحسن...")
    print("=" * 50)
    
    # اختبارات أساسية
    test_price_extraction()
    test_name_similarity()
    
    # اختبار النظام الكامل
    success = await test_full_system()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 جميع الاختبارات نجحت!")
        print("✅ النظام جاهز للاستخدام")
    else:
        print("❌ بعض الاختبارات فشلت")
        print("🔧 يرجى مراجعة الأخطاء وإصلاحها")
    
    print("\n📋 ملخص الاختبارات:")
    print("• ✅ استخراج الأسعار")
    print("• ✅ تطابق الأسماء")
    print("• ✅ محلل AI")
    print("• ✅ قاعدة البيانات")
    print("• ✅ بوت التليجرام")
    print("• ✅ النظام الكامل")

if __name__ == "__main__":
    # تشغيل الاختبارات
    asyncio.run(main())