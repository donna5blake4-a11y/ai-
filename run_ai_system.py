#!/usr/bin/env python3
"""
Quick Start Script - تشغيل سريع لنظام AI
"""

import sys
import os
from ai_deals_manager import AIDealsManager

def check_requirements():
    """التحقق من المتطلبات"""
    print("🔍 Checking requirements...")
    
    required_files = [
        "telegram_config.json",
        "ai_config.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        print("\n📝 Please create the missing configuration files:")
        
        if "telegram_config.json" in missing_files:
            print("""
Create telegram_config.json:
{
  "bot_token": "YOUR_BOT_TOKEN",
  "users": ["YOUR_USER_ID"]
}
            """)
        
        return False
    
    print("✅ All requirements met!")
    return True

def main():
    """الدالة الرئيسية"""
    print("🚀 AI Deals Manager - Quick Start")
    print("=" * 50)
    
    # التحقق من المتطلبات
    if not check_requirements():
        sys.exit(1)
    
    try:
        # إنشاء مدير العروض
        print("🔄 Initializing AI Deals Manager...")
        manager = AIDealsManager()
        
        # عرض الإحصائيات الأولية
        manager.print_stats()
        
        # التحقق من وجود بيانات JSON للنقل
        if os.path.exists("amz_products.json"):
            print("📦 Found amz_products.json - migrating data...")
            if manager.migrate_json_data():
                print("✅ Data migration completed!")
            else:
                print("⚠️ Data migration failed")
        
        # عرض القائمة
        while True:
            print("\n🎮 Choose an option:")
            print("1. 🔍 Run single analysis (10 deals)")
            print("2. 🔄 Start continuous analysis")
            print("3. 📊 Show top AI deals")
            print("4. 📈 Show statistics")
            print("5. ⚙️ Update settings")
            print("6. 🧪 Run system test")
            print("0. 🚪 Exit")
            
            choice = input("\nEnter your choice (0-6): ").strip()
            
            if choice == "1":
                print("🔍 Running single analysis...")
                sent_count = manager.run_single_analysis(limit=10)
                print(f"✅ Analysis completed! {sent_count} deals processed")
                
            elif choice == "2":
                print("🔄 Starting continuous analysis...")
                print("Press Ctrl+C to stop")
                try:
                    manager.run_continuous_analysis()
                except KeyboardInterrupt:
                    print("\n🛑 Continuous analysis stopped")
                    
            elif choice == "3":
                print("📊 Getting top AI deals...")
                top_deals = manager.get_top_ai_deals(limit=10)
                if top_deals:
                    print(f"\n🎯 Top {len(top_deals)} AI Verified Deals:")
                    for i, deal in enumerate(top_deals, 1):
                        print(f"{i}. {deal['name'][:60]}...")
                        print(f"   💰 {deal['price']:,.0f} EGP (-{deal['discount']:.1f}%)")
                        print(f"   🎯 AI Score: {deal['ai_score']:.2f}")
                        print()
                else:
                    print("❌ No AI verified deals found")
                    
            elif choice == "4":
                manager.print_stats()
                
            elif choice == "5":
                print("⚙️ Update settings:")
                print("1. Change daily limit")
                print("2. Change minimum discount")
                print("3. Change AI confidence threshold")
                print("4. Toggle verified only mode")
                
                setting_choice = input("Enter setting choice (1-4): ").strip()
                
                if setting_choice == "1":
                    new_limit = input("Enter new daily limit: ").strip()
                    try:
                        manager.update_settings(daily_limit=int(new_limit))
                        print("✅ Daily limit updated!")
                    except ValueError:
                        print("❌ Invalid number")
                        
                elif setting_choice == "2":
                    new_discount = input("Enter new minimum discount (%): ").strip()
                    try:
                        manager.update_settings(min_discount=float(new_discount))
                        print("✅ Minimum discount updated!")
                    except ValueError:
                        print("❌ Invalid number")
                        
                elif setting_choice == "3":
                    new_confidence = input("Enter new AI confidence (0.0-1.0): ").strip()
                    try:
                        manager.update_settings(min_ai_confidence=float(new_confidence))
                        print("✅ AI confidence threshold updated!")
                    except ValueError:
                        print("❌ Invalid number")
                        
                elif setting_choice == "4":
                    current = manager.verified_only
                    manager.update_settings(verified_only=not current)
                    print(f"✅ Verified only mode: {'ON' if not current else 'OFF'}")
                    
            elif choice == "6":
                print("🧪 Running system test...")
                os.system("python test_ai_system.py")
                
            elif choice == "0":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please try again.")
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping AI Deals Manager...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'manager' in locals():
            manager.stop()

if __name__ == "__main__":
    main()