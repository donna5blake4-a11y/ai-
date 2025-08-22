# setup.py - إعداد النظام والتثبيت التلقائي
import os
import sys
import subprocess
import json
import sqlite3
from pathlib import Path

def print_header():
    """طباعة رأس الإعداد"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🚀 AI-Enhanced Amazon Deal Analyzer Setup                ║
║                                                              ║
║    مرحباً بك في معالج الإعداد السريع                         ║
║    سنقوم بإعداد النظام خطوة بخطوة                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

def check_python_version():
    """فحص إصدار Python"""
    print("🔍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_requirements():
    """تثبيت المتطلبات"""
    print("\\n📦 Installing requirements...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def setup_database():
    """إعداد قاعدة البيانات"""
    print("\\n🗄️ Setting up database...")
    
    try:
        from enhanced_amz_scraper import DatabaseManager
        
        db_manager = DatabaseManager()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def setup_api_keys():
    """إعداد مفاتيح API"""
    print("\\n🔑 Setting up API keys...")
    
    config = {}
    
    # Gemini API Key
    print("\\n🤖 Gemini AI Configuration:")
    print("1. Visit: https://makersuite.google.com/app/apikey")
    print("2. Create a new API key")
    print("3. Copy the key")
    
    gemini_key = input("\\nEnter your Gemini API key (or press Enter to skip): ").strip()
    if gemini_key:
        config['gemini_api_key'] = gemini_key
        print("✅ Gemini API key saved")
    else:
        print("⏭️ Gemini API key skipped (you can add it later in the GUI)")
    
    # Telegram Bot
    print("\\n📱 Telegram Bot Configuration:")
    print("1. Message @BotFather on Telegram")
    print("2. Create a new bot with /newbot")
    print("3. Copy the bot token")
    
    bot_token = input("\\nEnter your Telegram bot token (or press Enter to skip): ").strip()
    if bot_token:
        user_ids = input("Enter user IDs (comma separated): ").strip()
        
        telegram_config = {
            "bot_token": bot_token,
            "users": [uid.strip() for uid in user_ids.split(',') if uid.strip()]
        }
        
        with open('telegram_config.json', 'w') as f:
            json.dump(telegram_config, f, indent=2)
        
        print("✅ Telegram bot configured")
    else:
        print("⏭️ Telegram bot skipped")
    
    # حفظ إعدادات عامة
    if config:
        with open('api_config.json', 'w') as f:
            json.dump(config, f, indent=2)
    
    return True

def setup_directories():
    """إنشاء المجلدات المطلوبة"""
    print("\\n📁 Creating directories...")
    
    directories = [
        'data',
        'logs',
        'backups',
        'exports'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ {directory}/")
    
    return True

def create_sample_data():
    """إنشاء بيانات تجريبية"""
    print("\\n📊 Creating sample data...")
    
    try:
        # إنشاء قاعدة بيانات تجريبية صغيرة
        conn = sqlite3.connect('amz_products.db')
        cursor = conn.cursor()
        
        # إدراج بعض البيانات التجريبية
        sample_products = [
            ('B0C7CQT9ZS', 'Anker Soundcore Earbuds', 'https://amazon.eg/dp/B0C7CQT9ZS', 
             'https://m.media-amazon.com/images/I/51Sc5zOZGzL._AC_UL320_.jpg', 
             'Electronics', 847.92, 899.0, 5.7),
            ('B0SAMPLE01', 'ماكينة حلاقة متعددة الاستخدامات', 'https://amazon.eg/dp/B0SAMPLE01',
             'https://example.com/image.jpg', 'Beauty', 450.0, 600.0, 25.0),
            ('B0SAMPLE02', 'سماعات بلوتوث لاسلكية', 'https://amazon.eg/dp/B0SAMPLE02',
             'https://example.com/image2.jpg', 'Electronics', 299.0, 450.0, 33.6)
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO products 
            (asin, name, url, img, section, current_price, strike_price, discount_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_products)
        
        conn.commit()
        conn.close()
        
        print("✅ Sample data created")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        return False

def run_initial_test():
    """تشغيل اختبار أولي"""
    print("\\n🧪 Running initial tests...")
    
    try:
        # اختبار قاعدة البيانات
        conn = sqlite3.connect('amz_products.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM products')
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"✅ Database test passed ({count} products)")
        
        # اختبار الاستيرادات
        try:
            from ai_price_analyzer import AIAnalyzer
            print("✅ AI analyzer import test passed")
        except ImportError as e:
            print(f"⚠️ AI analyzer import warning: {e}")
        
        try:
            from enhanced_telegram_bot import EnhancedTelegramBot
            print("✅ Telegram bot import test passed")
        except ImportError as e:
            print(f"⚠️ Telegram bot import warning: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Initial tests failed: {e}")
        return False

def show_next_steps():
    """عرض الخطوات التالية"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🎉 إعداد النظام مكتمل بنجاح!                             ║
║                                                              ║
║    الخطوات التالية:                                          ║
║                                                              ║
║    1️⃣  تشغيل الواجهة الرسومية:                              ║
║       python main.py                                         ║
║                                                              ║
║    2️⃣  تحليل AI من سطر الأوامر:                             ║
║       python main.py analyze --api-key YOUR_KEY             ║
║                                                              ║
║    3️⃣  البحث عن أسعار منتج:                                ║
║       python main.py search --product "اسم المنتج"          ║
║                                                              ║
║    4️⃣  تشغيل بوت التليجرام:                                 ║
║       python main.py telegram                               ║
║                                                              ║
║    5️⃣  تحويل بيانات JSON:                                   ║
║       python main.py migrate --json-file products.json     ║
║                                                              ║
║    📖 للمزيد من التفاصيل، راجع README.md                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

def main():
    """الدالة الرئيسية للإعداد"""
    print_header()
    
    steps = [
        ("Python Version", check_python_version),
        ("Install Requirements", install_requirements),
        ("Setup Database", setup_database),
        ("Create Directories", setup_directories),
        ("API Keys Configuration", setup_api_keys),
        ("Sample Data", create_sample_data),
        ("Initial Tests", run_initial_test)
    ]
    
    print("🚀 Starting setup process...\\n")
    
    for step_name, step_function in steps:
        print(f"📋 Step: {step_name}")
        
        if not step_function():
            print(f"\\n❌ Setup failed at step: {step_name}")
            print("Please check the error messages above and try again.")
            return False
        
        print()
    
    show_next_steps()
    
    print("\\n✨ Setup completed successfully!")
    print("You can now start using the AI-Enhanced Amazon Deal Analyzer.")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n\\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n\\n❌ Unexpected error during setup: {e}")
        sys.exit(1)