# convert_simple.py
# ملف بسيط لتحويل JSON إلى SQLite

import json
import sqlite3
import os

def convert_json_to_sqlite():
    """تحويل ملف JSON إلى SQLite"""
    
    # اسم الملفات
    json_file = "amz_products.json"
    db_file = "amz_products.db"
    
    print("🚀 بدء تحويل JSON إلى SQLite...")
    
    # التحقق من وجود ملف JSON
    if not os.path.exists(json_file):
        print(f"❌ الملف {json_file} غير موجود!")
        print("   تأكد من وجود الملف في نفس المجلد")
        return False
    
    try:
        # قراءة ملف JSON
        print("📖 جاري قراءة ملف JSON...")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ تم تحميل {len(data):,} منتج من JSON")
        
        # إنشاء قاعدة البيانات
        print("🗄️ جاري إنشاء قاعدة البيانات...")
        conn = sqlite3.connect(db_file)
        
        # إنشاء جدول المنتجات
        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                asin TEXT PRIMARY KEY,
                name TEXT,
                url TEXT,
                img TEXT,
                section TEXT,
                current_price REAL,
                strike_price REAL,
                discount_percent REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # إنشاء جدول تاريخ الأسعار
        conn.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT,
                price REAL,
                date TEXT,
                time TEXT,
                FOREIGN KEY (asin) REFERENCES products (asin)
            )
        ''')
        
        # معالجة المنتجات
        print("🔄 جاري معالجة المنتجات...")
        processed = 0
        
        for asin, product in data.items():
            try:
                # إدخال المنتج
                conn.execute('''
                    INSERT OR REPLACE INTO products 
                    (asin, name, url, img, section, current_price, strike_price, discount_percent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    asin,
                    product.get('name', ''),
                    product.get('url', ''),
                    product.get('img', ''),
                    product.get('section', ''),
                    product.get('price'),
                    product.get('strike_price'),
                    product.get('discount_percent', 0)
                ))
                
                # إدخال تاريخ الأسعار
                price_history = product.get('price_history', [])
                for entry in price_history:
                    conn.execute('''
                        INSERT INTO price_history (asin, price, date, time)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        asin,
                        entry.get('price'),
                        entry.get('date'),
                        entry.get('time', '00:00')
                    ))
                
                processed += 1
                
                # عرض التقدم كل 1000 منتج
                if processed % 1000 == 0:
                    print(f"✅ تم معالجة {processed:,} منتج...")
                    
            except Exception as e:
                print(f"⚠️ خطأ في معالجة {asin}: {e}")
                continue
        
        # حفظ التغييرات
        conn.commit()
        conn.close()
        
        print(f"🎉 تم الانتهاء! {processed:,} منتج تم معالجتها")
        
        # عرض الإحصائيات
        show_stats(db_file)
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في التحويل: {e}")
        return False

def show_stats(db_file):
    """عرض إحصائيات قاعدة البيانات"""
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # إجمالي المنتجات
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]
        
        # المنتجات المخفضة
        cursor.execute("SELECT COUNT(*) FROM products WHERE discount_percent > 0")
        discounted = cursor.fetchone()[0]
        
        # إجمالي تاريخ الأسعار
        cursor.execute("SELECT COUNT(*) FROM price_history")
        total_history = cursor.fetchone()[0]
        
        # حجم الملف
        file_size = os.path.getsize(db_file) / (1024*1024)
        
        print("\n📊 إحصائيات قاعدة البيانات:")
        print(f"   📦 إجمالي المنتجات: {total_products:,}")
        print(f"   🎉 المنتجات المخفضة: {discounted:,}")
        print(f"   💾 سجلات تاريخ الأسعار: {total_history:,}")
        print(f"   💽 حجم قاعدة البيانات: {file_size:.1f} MB")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ خطأ في عرض الإحصائيات: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("🔄 محول JSON إلى SQLite")
    print("=" * 50)
    
    success = convert_json_to_sqlite()
    
    if success:
        print("\n✅ تم التحويل بنجاح!")
        print("🎯 يمكنك الآن تشغيل النظام المحسن")
        print("\n📋 الخطوات التالية:")
        print("   1. شغل: python amz_scraper_enhanced.py")
        print("   2. اضغط على '🤖 AI Dashboard'")
        print("   3. استمتع بالعروض الحقيقية فقط!")
    else:
        print("\n❌ فشل في التحويل")
        print("🔧 يرجى مراجعة الأخطاء أعلاه")
    
    input("\nاضغط Enter للخروج...")