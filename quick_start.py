#!/usr/bin/env python3
# quick_start.py
# سكريبت سريع لبدء تنفيذ النظام المحسن

import os
import sys
import subprocess
import json
from pathlib import Path

def print_banner():
    """طباعة شعار النظام"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║  🚀 LAQTA Ultra - كاشف العروض الذكي                        ║
    ║                                                              ║
    ║  نظام متقدم لضمان العروض الحقيقية فقط                       ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """فحص إصدار Python"""
    if sys.version_info < (3, 7):
        print("❌ يتطلب النظام Python 3.7 أو أحدث")
        print(f"   الإصدار الحالي: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} - متوافق")
    return True

def install_requirements():
    """تثبيت المكتبات المطلوبة"""
    print("\n📦 تثبيت المكتبات المطلوبة...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ تم تثبيت المكتبات بنجاح")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تثبيت المكتبات: {e}")
        return False

def check_json_file():
    """فحص وجود ملف JSON"""
    json_files = ["amz_products.json", "amz_products.json.gz"]
    
    for file in json_files:
        if os.path.exists(file):
            size_mb = os.path.getsize(file) / (1024 * 1024)
            print(f"✅ تم العثور على {file} ({size_mb:.1f} MB)")
            return file
    
    print("⚠️ لم يتم العثور على ملف JSON للمنتجات")
    print("   يرجى التأكد من وجود amz_products.json")
    return None

def setup_database():
    """إعداد قاعدة البيانات"""
    print("\n🗄️ إعداد قاعدة البيانات...")
    
    try:
        from enhanced_amz_scraper import DatabaseManager
        db_manager = DatabaseManager()
        print("✅ تم إعداد قاعدة البيانات بنجاح")
        return True
    except Exception as e:
        print(f"❌ خطأ في إعداد قاعدة البيانات: {e}")
        return False

def test_ai_system():
    """اختبار النظام الذكي"""
    print("\n🧪 اختبار النظام الذكي...")
    
    try:
        result = subprocess.run([sys.executable, "test_ai_system.py"], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ اختبار النظام نجح")
            return True
        else:
            print("⚠️ اختبار النظام فشل")
            print("   الأخطاء:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️ انتهت مهلة الاختبار")
        return False
    except Exception as e:
        print(f"❌ خطأ في الاختبار: {e}")
        return False

def process_historical_data(json_file, limit=10000):
    """معالجة البيانات التاريخية"""
    print(f"\n📊 معالجة البيانات التاريخية (أول {limit:,} منتج)...")
    
    try:
        from historical_data_analyzer import process_large_json_file
        process_large_json_file(json_file, limit=limit)
        print("✅ تمت معالجة البيانات التاريخية")
        return True
    except Exception as e:
        print(f"❌ خطأ في معالجة البيانات: {e}")
        return False

def show_next_steps():
    """عرض الخطوات التالية"""
    print("\n" + "="*60)
    print("🎯 الخطوات التالية:")
    print("="*60)
    
    steps = [
        "1. 🔧 تحديث selectors المواقع في egyptian_retailers.py",
        "2. 🤖 ضبط معايير AI في ai_price_analyzer.py",
        "3. 📱 اختبار بوت التليجرام",
        "4. 🔄 دمج النظام المحسن مع الكود الحالي",
        "5. 📊 معالجة كاملة للبيانات التاريخية",
        "6. 🚀 تشغيل النظام النهائي"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    print("\n📋 للمزيد من التفاصيل:")
    print("   • راجع IMPLEMENTATION_PLAN.md")
    print("   • اقرأ README.md")
    print("   • شغل python test_ai_system.py للاختبار")

def main():
    """الدالة الرئيسية"""
    print_banner()
    
    # فحص المتطلبات الأساسية
    if not check_python_version():
        return False
    
    # تثبيت المكتبات
    if not install_requirements():
        return False
    
    # فحص ملف JSON
    json_file = check_json_file()
    if not json_file:
        return False
    
    # إعداد قاعدة البيانات
    if not setup_database():
        return False
    
    # اختبار النظام
    if not test_ai_system():
        print("⚠️ فشل اختبار النظام - يرجى مراجعة الأخطاء")
    
    # معالجة البيانات التاريخية (اختياري)
    print("\n❓ هل تريد معالجة البيانات التاريخية؟ (y/n): ", end="")
    choice = input().lower().strip()
    
    if choice in ['y', 'yes', 'نعم']:
        limit = 10000  # معالجة أول 10,000 منتج للاختبار
        process_historical_data(json_file, limit)
    
    # عرض الخطوات التالية
    show_next_steps()
    
    print("\n🎉 تم إعداد النظام بنجاح!")
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ النظام جاهز للاستخدام!")
        else:
            print("\n❌ فشل في إعداد النظام")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️ تم إيقاف العملية")
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        sys.exit(1)