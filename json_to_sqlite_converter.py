# json_to_sqlite_converter.py
# تحويل ملف JSON إلى قاعدة بيانات SQLite

import json
import sqlite3
import gzip
import os
from datetime import datetime
from pathlib import Path

def convert_json_to_sqlite(json_file_path: str, db_path: str = "amz_products.db", 
                          batch_size: int = 1000, limit: int = None):
    """تحويل ملف JSON إلى قاعدة بيانات SQLite"""
    
    print(f"🔄 بدء تحويل {json_file_path} إلى {db_path}")
    
    # التحقق من وجود ملف JSON
    if not os.path.exists(json_file_path):
        print(f"❌ الملف {json_file_path} غير موجود!")
        return False
    
    # إنشاء قاعدة البيانات
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=50000")
    
    # إنشاء الجداول
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
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ai_analyzed BOOLEAN DEFAULT FALSE,
            deal_score REAL DEFAULT 0,
            is_real_deal BOOLEAN DEFAULT FALSE,
            confidence REAL DEFAULT 0,
            recommendation TEXT DEFAULT ''
        )
    ''')
    
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
    
    # إنشاء الفهارس
    conn.execute('CREATE INDEX IF NOT EXISTS idx_asin ON products(asin)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_section ON products(section)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_discount ON products(discount_percent)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_price_history_asin ON price_history(asin)')
    
    try:
        # قراءة ملف JSON
        print("📖 جاري قراءة ملف JSON...")
        
        if json_file_path.endswith('.gz'):
            with gzip.open(json_file_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
        else:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        print(f"✅ تم تحميل {len(data):,} منتج من JSON")
        
        # تجهيز البيانات للنقل
        products_batch = []
        history_batch = []
        processed_count = 0
        
        # تحديد عدد المنتجات للمعالجة
        total_products = len(data)
        if limit:
            total_products = min(total_products, limit)
        
        print(f"🔄 جاري معالجة {total_products:,} منتج...")
        
        for i, (asin, product) in enumerate(data.items()):
            if limit and i >= limit:
                break
                
            try:
                # بيانات المنتج الأساسية
                products_batch.append((
                    asin,
                    product.get('name', '?'),
                    product.get('url', ''),
                    product.get('img', ''),
                    product.get('section', 'Unknown'),
                    product.get('price'),
                    product.get('strike_price'),
                    product.get('discount_percent', 0)
                ))
                
                # تاريخ الأسعار
                price_history = product.get('price_history', [])
                for entry in price_history:
                    history_batch.append((
                        asin,
                        entry.get('price'),
                        entry.get('date'),
                        entry.get('time', '00:00')
                    ))
                
                # حفظ دفعي
                if len(products_batch) >= batch_size:
                    conn.executemany('''
                        INSERT OR REPLACE INTO products 
                        (asin, name, url, img, section, current_price, strike_price, discount_percent)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', products_batch)
                    
                    if history_batch:
                        conn.executemany('''
                            INSERT INTO price_history (asin, price, date, time)
                            VALUES (?, ?, ?, ?)
                        ''', history_batch)
                    
                    conn.commit()
                    processed_count += len(products_batch)
                    print(f"✅ تم معالجة {processed_count:,} منتج...")
                    
                    products_batch = []
                    history_batch = []
                    
            except Exception as e:
                print(f"⚠️ خطأ في معالجة {asin}: {e}")
                continue
        
        # حفظ البيانات المتبقية
        if products_batch:
            conn.executemany('''
                INSERT OR REPLACE INTO products 
                (asin, name, url, img, section, current_price, strike_price, discount_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', products_batch)
            
            if history_batch:
                conn.executemany('''
                    INSERT INTO price_history (asin, price, date, time)
                    VALUES (?, ?, ?, ?)
                ''', history_batch)
            
            conn.commit()
            processed_count += len(products_batch)
        
        print(f"🎉 تم الانتهاء من التحويل! {processed_count:,} منتج تم معالجتها")
        
        # إحصائيات نهائية
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        products_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM price_history")
        history_count = cursor.fetchone()[0]
        
        print(f"📊 إحصائيات قاعدة البيانات:")
        print(f"   - المنتجات: {products_count:,}")
        print(f"   - سجلات تاريخ الأسعار: {history_count:,}")
        
        # حجم الملفات
        old_size = os.path.getsize(json_file_path) / (1024*1024)
        new_size = os.path.getsize(db_path) / (1024*1024)
        
        print(f"💾 حجم الملفات:")
        print(f"   - JSON: {old_size:.1f} MB")
        print(f"   - SQLite: {new_size:.1f} MB")
        print(f"   - توفير المساحة: {old_size - new_size:.1f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في التحويل: {e}")
        return False
    finally:
        conn.close()

def show_database_stats(db_path: str = "amz_products.db"):
    """عرض إحصائيات قاعدة البيانات"""
    
    if not os.path.exists(db_path):
        print(f"❌ قاعدة البيانات {db_path} غير موجودة!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"📊 إحصائيات قاعدة البيانات {db_path}:")
    print("=" * 50)
    
    # إجمالي المنتجات
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]
    print(f"📦 إجمالي المنتجات: {total_products:,}")
    
    # المنتجات المخفضة
    cursor.execute("SELECT COUNT(*) FROM products WHERE discount_percent > 0")
    discounted = cursor.fetchone()[0]
    print(f"🎉 المنتجات المخفضة: {discounted:,}")
    
    # أعلى خصم
    cursor.execute("SELECT MAX(discount_percent) FROM products")
    max_discount = cursor.fetchone()[0]
    print(f"🔥 أعلى خصم: {max_discount:.1f}%")
    
    # المنتجات حسب القسم
    cursor.execute('''
        SELECT section, COUNT(*) 
        FROM products 
        GROUP BY section 
        ORDER BY COUNT(*) DESC
    ''')
    sections = cursor.fetchall()
    print(f"\n📂 المنتجات حسب القسم:")
    for section, count in sections[:10]:  # أعلى 10 أقسام
        print(f"   - {section}: {count:,}")
    
    # إجمالي تاريخ الأسعار
    cursor.execute("SELECT COUNT(*) FROM price_history")
    total_history = cursor.fetchone()[0]
    print(f"\n💾 سجلات تاريخ الأسعار: {total_history:,}")
    
    # حجم الملف
    file_size = os.path.getsize(db_path) / (1024*1024)
    print(f"💽 حجم قاعدة البيانات: {file_size:.1f} MB")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("استخدام:")
        print("  python json_to_sqlite_converter.py convert [json_file] [db_file] [limit]")
        print("  python json_to_sqlite_converter.py stats [db_file]")
        print("\nأمثلة:")
        print("  python json_to_sqlite_converter.py convert amz_products.json")
        print("  python json_to_sqlite_converter.py convert amz_products.json amz_products.db 50000")
        print("  python json_to_sqlite_converter.py stats amz_products.db")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "convert":
        json_file = sys.argv[2] if len(sys.argv) > 2 else "amz_products.json"
        db_file = sys.argv[3] if len(sys.argv) > 3 else "amz_products.db"
        limit = int(sys.argv[4]) if len(sys.argv) > 4 else None
        
        convert_json_to_sqlite(json_file, db_file, limit=limit)
        
    elif command == "stats":
        db_file = sys.argv[2] if len(sys.argv) > 2 else "amz_products.db"
        show_database_stats(db_file)
        
    else:
        print(f"❌ أمر غير معروف: {command}")