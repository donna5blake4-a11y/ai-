# fix_database.py - إصلاح قاعدة البيانات

import sqlite3
import os

def fix_smart_deals_database():
    """إصلاح قاعدة بيانات العروض الذكية"""
    
    db_file = "smart_deals.db"
    
    try:
        print("🔧 إصلاح قاعدة البيانات...")
        
        # إنشاء نسخة احتياطية إذا كانت موجودة
        if os.path.exists(db_file):
            backup_file = f"{db_file}.backup"
            if os.path.exists(backup_file):
                os.remove(backup_file)
            os.rename(db_file, backup_file)
            print(f"📂 تم إنشاء نسخة احتياطية: {backup_file}")
        
        # إنشاء قاعدة بيانات جديدة
        conn = sqlite3.connect(db_file)
        
        # حذف الجدول القديم إذا كان موجود
        conn.execute('DROP TABLE IF EXISTS deals')
        
        # إنشاء الجدول الجديد مع جميع الأعمدة المطلوبة
        conn.execute('''
            CREATE TABLE deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT UNIQUE,
                name TEXT,
                price REAL,
                strike_price REAL,
                discount_percent REAL,
                section TEXT,
                url TEXT,
                img TEXT,
                quality_score REAL DEFAULT 0,
                comparison_prices TEXT,
                is_verified_deal BOOLEAN DEFAULT 0,
                date_found TEXT,
                is_sent BOOLEAN DEFAULT 0,
                sent_with_image BOOLEAN DEFAULT 0
            )
        ''')
        
        # إنشاء فهارس للأداء
        conn.execute('CREATE INDEX IF NOT EXISTS idx_asin ON deals(asin)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_date ON deals(date_found)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_sent ON deals(is_sent)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_quality ON deals(quality_score)')
        
        conn.commit()
        conn.close()
        
        print("✅ تم إصلاح قاعدة البيانات بنجاح!")
        print("📊 الأعمدة المتاحة:")
        print("   - id, asin, name, price, strike_price")
        print("   - discount_percent, section, url, img")
        print("   - quality_score, comparison_prices")
        print("   - is_verified_deal, date_found")
        print("   - is_sent, sent_with_image")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إصلاح قاعدة البيانات: {e}")
        return False

def fix_all_databases():
    """إصلاح جميع قواعد البيانات"""
    
    databases = [
        "smart_deals.db",
        "ai_enhanced_deals.db", 
        "corrected_deals.db"
    ]
    
    for db_file in databases:
        try:
            if os.path.exists(db_file):
                print(f"🔧 إصلاح {db_file}...")
                
                # إنشاء نسخة احتياطية
                backup_file = f"{db_file}.backup"
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                os.rename(db_file, backup_file)
                
            # إنشاء قاعدة بيانات جديدة
            conn = sqlite3.connect(db_file)
            
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
                    quality_score REAL DEFAULT 0,
                    ai_score REAL DEFAULT 0,
                    comparison_prices TEXT,
                    is_verified_deal BOOLEAN DEFAULT 0,
                    date_found TEXT,
                    is_sent BOOLEAN DEFAULT 0,
                    sent_with_image BOOLEAN DEFAULT 0
                )
            ''')
            
            # إنشاء فهارس
            conn.execute('CREATE INDEX IF NOT EXISTS idx_asin ON deals(asin)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_date ON deals(date_found)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_sent ON deals(is_sent)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_quality ON deals(quality_score)')
            
            conn.commit()
            conn.close()
            
            print(f"✅ تم إصلاح {db_file}")
            
        except Exception as e:
            print(f"❌ خطأ في إصلاح {db_file}: {e}")

if __name__ == "__main__":
    print("🔧 إصلاح قواعد البيانات...")
    print("=" * 50)
    
    fix_all_databases()
    
    print("\n✅ تم إصلاح جميع قواعد البيانات!")
    print("🚀 يمكنك الآن تشغيل النظام بأمان:")
    print("   python smart_gui.py")
    print("   python smart_amazon_system.py")