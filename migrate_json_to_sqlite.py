# migrate_json_to_sqlite.py
import json
import sqlite3
from datetime import datetime
import os
import gzip
from pathlib import Path
import logging
from tqdm import tqdm

# إعداد الـ logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JSONToSQLiteMigrator:
    """أداة تحويل JSON إلى SQLite مع تحسينات الأداء"""
    
    def __init__(self, json_file: str, db_file: str = "amz_products.db"):
        self.json_file = json_file
        self.db_file = db_file
        self.conn = None
    
    def init_database(self):
        """إنشاء قاعدة البيانات والجداول"""
        try:
            self.conn = sqlite3.connect(self.db_file)
            
            # تحسين الأداء
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA cache_size=100000")
            self.conn.execute("PRAGMA temp_store=MEMORY")
            
            # جدول المنتجات الرئيسي
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    asin TEXT PRIMARY KEY,
                    name TEXT,
                    url TEXT,
                    img TEXT,
                    section TEXT,
                    current_price REAL,
                    strike_price REAL,
                    discount_percent REAL,
                    ai_verified BOOLEAN DEFAULT FALSE,
                    ai_score REAL DEFAULT 0,
                    ai_analysis TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول تاريخ الأسعار
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asin TEXT,
                    price REAL,
                    date TEXT,
                    time TEXT,
                    source TEXT DEFAULT 'amazon',
                    FOREIGN KEY (asin) REFERENCES products (asin)
                )
            ''')
            
            # جدول مقارنة الأسعار
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS price_comparison (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT,
                    asin TEXT,
                    site_name TEXT,
                    price REAL,
                    url TEXT,
                    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asin) REFERENCES products (asin)
                )
            ''')
            
            # جدول تحليل AI
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS ai_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asin TEXT,
                    analysis_type TEXT,
                    result TEXT,
                    confidence_score REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asin) REFERENCES products (asin)
                )
            ''')
            
            logger.info("Database schema created successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def create_indexes(self):
        """إنشاء الفهارس لتحسين الأداء"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_price ON products (current_price)",
            "CREATE INDEX IF NOT EXISTS idx_products_discount ON products (discount_percent)",
            "CREATE INDEX IF NOT EXISTS idx_products_section ON products (section)",
            "CREATE INDEX IF NOT EXISTS idx_products_ai_score ON products (ai_score)",
            "CREATE INDEX IF NOT EXISTS idx_products_ai_verified ON products (ai_verified)",
            "CREATE INDEX IF NOT EXISTS idx_price_history_asin ON price_history (asin)",
            "CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history (date, time)",
            "CREATE INDEX IF NOT EXISTS idx_price_comparison_asin ON price_comparison (asin)",
            "CREATE INDEX IF NOT EXISTS idx_price_comparison_site ON price_comparison (site_name)",
            "CREATE INDEX IF NOT EXISTS idx_ai_analysis_asin ON ai_analysis (asin)",
        ]
        
        for index_sql in indexes:
            try:
                self.conn.execute(index_sql)
                logger.info(f"Index created: {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                logger.error(f"Error creating index: {e}")
        
        self.conn.commit()
    
    def load_json_data(self) -> dict:
        """تحميل بيانات JSON"""
        try:
            logger.info(f"Loading JSON data from {self.json_file}")
            
            # التحقق من وجود الملف
            if not os.path.exists(self.json_file):
                raise FileNotFoundError(f"JSON file not found: {self.json_file}")
            
            # تحميل البيانات
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {len(data)} products from JSON")
            return data
            
        except Exception as e:
            logger.error(f"Error loading JSON data: {e}")
            raise
    
    def migrate_products(self, products_data: dict, batch_size: int = 1000):
        """تحويل المنتجات إلى قاعدة البيانات"""
        try:
            total_products = len(products_data)
            logger.info(f"Starting migration of {total_products} products")
            
            # إعداد البيانات للإدراج
            products_batch = []
            price_history_batch = []
            
            progress_bar = tqdm(total=total_products, desc="Migrating products")
            
            for asin, product in products_data.items():
                try:
                    # بيانات المنتج الأساسية
                    product_data = (
                        asin,
                        product.get('name', ''),
                        product.get('url', ''),
                        product.get('img', ''),
                        product.get('section', ''),
                        product.get('price', 0),
                        product.get('strike_price'),
                        product.get('discount_percent', 0),
                        False,  # ai_verified
                        0,      # ai_score
                        None,   # ai_analysis
                        datetime.now().isoformat(),  # last_updated
                        datetime.now().isoformat()   # created_at
                    )
                    products_batch.append(product_data)
                    
                    # تاريخ الأسعار
                    price_history = product.get('price_history', [])
                    for price_entry in price_history:
                        if isinstance(price_entry, dict) and 'price' in price_entry:
                            history_data = (
                                asin,
                                price_entry.get('price', 0),
                                price_entry.get('date', ''),
                                price_entry.get('time', ''),
                                'amazon'
                            )
                            price_history_batch.append(history_data)
                    
                    # إدراج دفعي
                    if len(products_batch) >= batch_size:
                        self._insert_batch(products_batch, price_history_batch)
                        products_batch.clear()
                        price_history_batch.clear()
                    
                    progress_bar.update(1)
                    
                except Exception as e:
                    logger.error(f"Error processing product {asin}: {e}")
                    continue
            
            # إدراج الدفعة الأخيرة
            if products_batch:
                self._insert_batch(products_batch, price_history_batch)
            
            progress_bar.close()
            logger.info("Migration completed successfully")
            
        except Exception as e:
            logger.error(f"Migration error: {e}")
            raise
    
    def _insert_batch(self, products_batch: list, price_history_batch: list):
        """إدراج دفعة من البيانات"""
        try:
            # إدراج المنتجات
            self.conn.executemany('''
                INSERT OR REPLACE INTO products 
                (asin, name, url, img, section, current_price, strike_price, 
                 discount_percent, ai_verified, ai_score, ai_analysis, 
                 last_updated, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', products_batch)
            
            # إدراج تاريخ الأسعار
            if price_history_batch:
                self.conn.executemany('''
                    INSERT OR IGNORE INTO price_history 
                    (asin, price, date, time, source)
                    VALUES (?, ?, ?, ?, ?)
                ''', price_history_batch)
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Batch insert error: {e}")
            self.conn.rollback()
            raise
    
    def get_migration_stats(self) -> dict:
        """إحصائيات ما بعد التحويل"""
        try:
            cursor = self.conn.cursor()
            
            # عدد المنتجات
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]
            
            # عدد المنتجات مع خصم
            cursor.execute("SELECT COUNT(*) FROM products WHERE discount_percent > 0")
            products_with_discount = cursor.fetchone()[0]
            
            # متوسط نسبة الخصم
            cursor.execute("SELECT AVG(discount_percent) FROM products WHERE discount_percent > 0")
            avg_discount = cursor.fetchone()[0] or 0
            
            # عدد سجلات تاريخ الأسعار
            cursor.execute("SELECT COUNT(*) FROM price_history")
            price_history_count = cursor.fetchone()[0]
            
            # أعلى خصم
            cursor.execute("SELECT MAX(discount_percent), name FROM products WHERE discount_percent > 0")
            max_discount_result = cursor.fetchone()
            max_discount = max_discount_result[0] if max_discount_result[0] else 0
            max_discount_product = max_discount_result[1] if max_discount_result[1] else "Unknown"
            
            # الأقسام
            cursor.execute("SELECT section, COUNT(*) FROM products GROUP BY section ORDER BY COUNT(*) DESC")
            sections = cursor.fetchall()
            
            stats = {
                'total_products': total_products,
                'products_with_discount': products_with_discount,
                'average_discount': round(avg_discount, 2),
                'price_history_records': price_history_count,
                'max_discount': round(max_discount, 2),
                'max_discount_product': max_discount_product,
                'sections': sections[:10]  # أول 10 أقسام
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def optimize_database(self):
        """تحسين قاعدة البيانات بعد التحويل"""
        try:
            logger.info("Optimizing database...")
            
            # تحليل الجداول لتحسين الاستعلامات
            self.conn.execute("ANALYZE")
            
            # ضغط قاعدة البيانات
            self.conn.execute("VACUUM")
            
            logger.info("Database optimization completed")
            
        except Exception as e:
            logger.error(f"Database optimization error: {e}")
    
    def migrate(self, batch_size: int = 1000, optimize: bool = True) -> dict:
        """تنفيذ التحويل الكامل"""
        try:
            logger.info("Starting JSON to SQLite migration")
            
            # إنشاء قاعدة البيانات
            self.init_database()
            
            # تحميل البيانات
            products_data = self.load_json_data()
            
            # تحويل المنتجات
            self.migrate_products(products_data, batch_size)
            
            # إنشاء الفهارس
            self.create_indexes()
            
            # تحسين قاعدة البيانات
            if optimize:
                self.optimize_database()
            
            # الحصول على الإحصائيات
            stats = self.get_migration_stats()
            
            logger.info("Migration completed successfully!")
            logger.info(f"Statistics: {stats}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()

def main():
    """الدالة الرئيسية"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate JSON data to SQLite')
    parser.add_argument('--json-file', default='products.json', help='Input JSON file')
    parser.add_argument('--db-file', default='amz_products.db', help='Output SQLite database')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for insertion')
    parser.add_argument('--no-optimize', action='store_true', help='Skip database optimization')
    
    args = parser.parse_args()
    
    # إنشاء المهاجر
    migrator = JSONToSQLiteMigrator(args.json_file, args.db_file)
    
    try:
        # تنفيذ التحويل
        stats = migrator.migrate(
            batch_size=args.batch_size,
            optimize=not args.no_optimize
        )
        
        print("\n" + "="*50)
        print("🎉 Migration Completed Successfully!")
        print("="*50)
        print(f"📊 Total Products: {stats.get('total_products', 0):,}")
        print(f"💰 Products with Discount: {stats.get('products_with_discount', 0):,}")
        print(f"📈 Average Discount: {stats.get('average_discount', 0)}%")
        print(f"🏆 Max Discount: {stats.get('max_discount', 0)}%")
        print(f"📜 Price History Records: {stats.get('price_history_records', 0):,}")
        
        print(f"\n📂 Top Sections:")
        for section, count in stats.get('sections', [])[:5]:
            print(f"   • {section}: {count:,} products")
        
        print(f"\n💾 Database saved to: {args.db_file}")
        print("="*50)
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())