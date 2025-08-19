#!/usr/bin/env python3
"""
Basic Usage Example - مثال الاستخدام الأساسي
"""

import sys
import os

# إضافة المجلد الأب إلى Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_deals_manager import AIDealsManager

def main():
    """مثال أساسي لاستخدام AI Deals Manager"""
    
    print("🚀 AI Deals Manager - Basic Usage Example")
    print("=" * 50)
    
    try:
        # إنشاء مدير العروض
        print("📦 Creating AI Deals Manager...")
        manager = AIDealsManager()
        
        # عرض الإحصائيات الأولية
        print("\n📊 Initial Statistics:")
        manager.print_stats()
        
        # تشغيل تحليل واحد
        print("\n🔍 Running single analysis...")
        sent_count = manager.run_single_analysis(limit=5)
        print(f"✅ Analysis completed! {sent_count} deals processed")
        
        # الحصول على أفضل العروض
        print("\n🎯 Getting top AI deals...")
        top_deals = manager.get_top_ai_deals(limit=3)
        
        if top_deals:
            print(f"\n🏆 Top {len(top_deals)} AI Verified Deals:")
            for i, deal in enumerate(top_deals, 1):
                print(f"\n{i}. {deal['name'][:60]}...")
                print(f"   💰 Price: {deal['price']:,.0f} EGP")
                print(f"   📉 Discount: {deal['discount']:.1f}%")
                print(f"   🎯 AI Score: {deal['ai_score']:.2f}")
                print(f"   🔗 URL: {deal['url']}")
        else:
            print("❌ No AI verified deals found")
        
        # عرض الإحصائيات النهائية
        print("\n📈 Final Statistics:")
        manager.print_stats()
        
        print("\n✅ Basic usage example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)