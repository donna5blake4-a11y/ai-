#!/usr/bin/env python3
"""
Telegram Bot Example - مثال بوت تليجرام
"""

import sys
import os
import time

# إضافة المجلد الأب إلى Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_telegram_bot import EnhancedTelegramBot
from enhanced_database import EnhancedDatabaseManager, Product

def main():
    """مثال بوت تليجرام محسن"""
    
    print("🤖 AI Deals Manager - Telegram Bot Example")
    print("=" * 50)
    
    try:
        # إنشاء بوت تليجرام
        print("📱 Creating Telegram Bot...")
        bot = EnhancedTelegramBot()
        
        # عرض إعدادات البوت
        print("\n⚙️ Bot Settings:")
        stats = bot.get_bot_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # إنشاء منتج تجريبي
        print("\n📦 Creating test product...")
        test_product = Product(
            asin="TEST123",
            name="منتج تجريبي للاختبار - ماكينة حلاقة متعددة الاستخدامات",
            url="https://www.amazon.eg/test-product",
            img="https://example.com/image.jpg",
            section="Electronics",
            current_price=847.92,
            strike_price=1200.0,
            discount_percent=29.34,
            last_updated=time.time(),
            created_at=time.time()
        )
        
        # بيانات تحليل AI تجريبية
        test_analysis = {
            'market_average': 1150.0,
            'best_alternative_price': 1180.0,
            'best_alternative_website': 'Jumia',
            'price_difference': 332.08,
            'price_difference_percent': 28.1,
            'confidence_score': 0.85,
            'is_good_deal': True,
            'recommendations': [
                '✅ عرض ممتاز - سعر جيد مقارنة بالسوق',
                '🔥 توفير كبير - أرخص من السوق بـ 20%+',
                '🎯 تحليل موثوق - بيانات دقيقة'
            ],
            'analysis_summary': 'تحليل السعر: 28.1% ✅ عرض جيد | الثقة: 0.9'
        }
        
        # إرسال تنبيه تجريبي
        print("\n📤 Sending test alert...")
        success = bot.send_ai_enhanced_alert(test_product, test_analysis)
        
        if success:
            print("✅ Test alert sent successfully!")
        else:
            print("❌ Failed to send test alert")
        
        # إرسال ملخص يومي تجريبي
        print("\n📊 Sending daily summary...")
        summary_success = bot.send_daily_summary()
        
        if summary_success:
            print("✅ Daily summary sent successfully!")
        else:
            print("❌ Failed to send daily summary")
        
        # عرض إحصائيات البوت النهائية
        print("\n📈 Final Bot Statistics:")
        final_stats = bot.get_bot_stats()
        for key, value in final_stats.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Telegram bot example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)