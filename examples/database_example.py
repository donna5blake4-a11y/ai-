#!/usr/bin/env python3
"""
Database Example - مثال قاعدة البيانات
"""

import sys
import os
import json
from datetime import datetime

# إضافة المجلد الأب إلى Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_database import EnhancedDatabaseManager, Product

def main():
    """مثال قاعدة البيانات المحسنة"""
    
    print("🗄️ AI Deals Manager - Database Example")
    print("=" * 50)
    
    try:
        # إنشاء مدير قاعدة البيانات
        print("📦 Creating Database Manager...")
        db = EnhancedDatabaseManager()
        
        # عرض إحصائيات قاعدة البيانات
        print("\n📊 Database Statistics:")
        stats = db.get_database_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # إنشاء منتجات تجريبية
        print("\n📦 Creating test products...")
        test_products = [
            Product(
                asin="TEST001",
                name="ماكينة حلاقة متعددة الاستخدامات 10 في 1",
                url="https://www.amazon.eg/test1",
                img="https://example.com/img1.jpg",
                section="Electronics",
                current_price=847.92,
                strike_price=1200.0,
                discount_percent=29.34,
                last_updated=datetime.now(),
                created_at=datetime.now(),
                ai_score=0.85,
                market_comparison="تحليل السعر: 28.1% ✅ عرض جيد",
                is_verified_deal=True
            ),
            Product(
                asin="TEST002",
                name="سماعات بلوتوث لاسلكية",
                url="https://www.amazon.eg/test2",
                img="https://example.com/img2.jpg",
                section="Electronics",
                current_price=299.99,
                strike_price=450.0,
                discount_percent=33.34,
                last_updated=datetime.now(),
                created_at=datetime.now(),
                ai_score=0.92,
                market_comparison="تحليل السعر: 35.2% 🔥 عرض ممتاز",
                is_verified_deal=True
            ),
            Product(
                asin="TEST003",
                name="هاتف ذكي جديد",
                url="https://www.amazon.eg/test3",
                img="https://example.com/img3.jpg",
                section="Electronics",
                current_price=8999.99,
                strike_price=12000.0,
                discount_percent=25.0,
                last_updated=datetime.now(),
                created_at=datetime.now(),
                ai_score=0.78,
                market_comparison="تحليل السعر: 22.1% ✅ عرض جيد",
                is_verified_deal=False
            )
        ]
        
        # إضافة المنتجات إلى قاعدة البيانات
        print("\n💾 Adding products to database...")
        for product in test_products:
            success = db.add_product(product)
            if success:
                print(f"   ✅ Added: {product.name[:40]}...")
            else:
                print(f"   ❌ Failed to add: {product.name[:40]}...")
        
        # تحديث أسعار المنتجات
        print("\n💰 Updating product prices...")
        db.update_product_price("TEST001", 800.0, 1200.0)
        db.update_product_price("TEST002", 280.0, 450.0)
        print("   ✅ Prices updated")
        
        # جلب منتج واحد
        print("\n🔍 Getting single product...")
        product = db.get_product("TEST001")
        if product:
            print(f"   ✅ Found: {product.name}")
            print(f"   💰 Price: {product.current_price} EGP")
            print(f"   📉 Discount: {product.discount_percent:.1f}%")
            print(f"   🎯 AI Score: {product.ai_score}")
        else:
            print("   ❌ Product not found")
        
        # جلب العروض المخفضة
        print("\n🎯 Getting discounted deals...")
        deals = db.get_deals(min_discount=25, limit=5, verified_only=True)
        print(f"   ✅ Found {len(deals)} verified deals")
        
        for i, deal in enumerate(deals, 1):
            print(f"   {i}. {deal.name[:40]}... - {deal.discount_percent:.1f}% off")
        
        # جلب تاريخ الأسعار
        print("\n📈 Getting price history...")
        history = db.get_price_history("TEST001", days=7)
        print(f"   ✅ Found {len(history)} price records")
        
        for record in history[:3]:  # أول 3 سجلات فقط
            print(f"   📅 {record.date} {record.time}: {record.price} EGP")
        
        # حفظ تحليل AI
        print("\n🤖 Saving AI analysis...")
        analysis_data = {
            'market_average': 1150.0,
            'best_alternative_price': 1180.0,
            'best_alternative_website': 'Jumia',
            'price_difference': 332.08,
            'price_difference_percent': 28.1,
            'confidence_score': 0.85,
            'is_good_deal': True,
            'recommendations': ['عرض ممتاز', 'توفير كبير'],
            'analysis_summary': 'تحليل السعر: 28.1% ✅ عرض جيد'
        }
        
        success = db.save_ai_analysis("TEST001", analysis_data)
        if success:
            print("   ✅ AI analysis saved")
        else:
            print("   ❌ Failed to save AI analysis")
        
        # تصدير البيانات
        print("\n📤 Exporting data...")
        export_success = db.export_to_json("test_export.json")
        if export_success:
            print("   ✅ Data exported to test_export.json")
        else:
            print("   ❌ Failed to export data")
        
        # عرض الإحصائيات النهائية
        print("\n📊 Final Database Statistics:")
        final_stats = db.get_database_stats()
        for key, value in final_stats.items():
            print(f"   {key}: {value}")
        
        # إغلاق قاعدة البيانات
        db.close()
        print("\n🔒 Database connection closed")
        
        print("\n✅ Database example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)