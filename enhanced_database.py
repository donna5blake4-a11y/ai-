import sqlite3
import json
import gzip
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass, asdict
import threading

logger = logging.getLogger(__name__)

@dataclass
class Product:
    """نموذج المنتج"""
    asin: str
    name: str
    url: str
    img: str
    section: str
    current_price: float
    strike_price: Optional[float]
    discount_percent: float
    last_updated: datetime
    created_at: datetime
    ai_score: Optional[float] = None
    market_comparison: Optional[str] = None
    is_verified_deal: bool = False

@dataclass
class PriceHistory:
    """نموذج تاريخ الأسعار"""
    id: Optional[int]
    asin: str
    price: float
    date: str
    time: str
    created_at: datetime

class EnhancedDatabaseManager:
    """مدير قاعدة البيانات المحسن"""
    
    def __init__(self, db_path: str = "amz_products.db"):
        self.db_path = db_path
        self.connection = None
        self.lock = threading.Lock()
        self.initialize_database()
    
    def initialize_database(self):
        """تهيئة قاعدة البيانات"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            
            # تحسين الأداء
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=50000")
            self.connection.execute("PRAGMA temp_store=MEMORY")
            self.connection.execute("PRAGMA mmap_size=268435456")  # 256MB
            
            self._create_tables()
            self._create_indexes()
            
            logger.info(f"✅ Database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def _create_tables(self):
        """إنشاء الجداول"""
        with self.lock:
            # جدول المنتجات الرئيسي
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    asin TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT,
                    img TEXT,
                    section TEXT,
                    current_price REAL,
                    strike_price REAL,
                    discount_percent REAL DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ai_score REAL,
                    market_comparison TEXT,
                    is_verified_deal BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # جدول تاريخ الأسعار
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asin TEXT NOT NULL,
                    price REAL NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT DEFAULT '00:00',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (asin) REFERENCES products (asin) ON DELETE CASCADE
                )
            ''')
            
            # جدول تحليلات AI
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS ai_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asin TEXT NOT NULL,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    market_average REAL,
                    best_alternative_price REAL,
                    best_alternative_website TEXT,
                    price_difference REAL,
                    price_difference_percent REAL,
                    confidence_score REAL,
                    is_good_deal BOOLEAN,
                    recommendations TEXT,
                    analysis_summary TEXT,
                    FOREIGN KEY (asin) REFERENCES products (asin) ON DELETE CASCADE
                )
            ''')
            
            # جدول إحصائيات الجلسة
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS session_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_date DATE DEFAULT CURRENT_DATE,
                    total_products INTEGER DEFAULT 0,
                    real_deals INTEGER DEFAULT 0,
                    fake_deals INTEGER DEFAULT 0,
                    ai_verified_deals INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.connection.commit()
    
    def _create_indexes(self):
        """إنشاء الفهارس لتحسين الأداء"""
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_products_asin ON products(asin)',
            'CREATE INDEX IF NOT EXISTS idx_products_section ON products(section)',
            'CREATE INDEX IF NOT EXISTS idx_products_discount ON products(discount_percent)',
            'CREATE INDEX IF NOT EXISTS idx_products_price ON products(current_price)',
            'CREATE INDEX IF NOT EXISTS idx_products_updated ON products(last_updated)',
            'CREATE INDEX IF NOT EXISTS idx_products_ai_score ON products(ai_score)',
            'CREATE INDEX IF NOT EXISTS idx_products_verified ON products(is_verified_deal)',
            
            'CREATE INDEX IF NOT EXISTS idx_price_history_asin ON price_history(asin)',
            'CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(date)',
            'CREATE INDEX IF NOT EXISTS idx_price_history_asin_date ON price_history(asin, date)',
            
            'CREATE INDEX IF NOT EXISTS idx_ai_analysis_asin ON ai_analysis(asin)',
            'CREATE INDEX IF NOT EXISTS idx_ai_analysis_date ON ai_analysis(analysis_date)',
            'CREATE INDEX IF NOT EXISTS idx_ai_analysis_good_deal ON ai_analysis(is_good_deal)',
            
            'CREATE INDEX IF NOT EXISTS idx_session_stats_date ON session_stats(session_date)'
        ]
        
        with self.lock:
            for index_sql in indexes:
                self.connection.execute(index_sql)
            self.connection.commit()
    
    def add_product(self, product: Product) -> bool:
        """إضافة منتج جديد"""
        try:
            with self.lock:
                self.connection.execute('''
                    INSERT OR REPLACE INTO products 
                    (asin, name, url, img, section, current_price, strike_price, 
                     discount_percent, last_updated, ai_score, market_comparison, is_verified_deal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product.asin, product.name, product.url, product.img, product.section,
                    product.current_price, product.strike_price, product.discount_percent,
                    product.last_updated, product.ai_score, product.market_comparison,
                    product.is_verified_deal
                ))
                self.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding product {product.asin}: {e}")
            return False
    
    def update_product_price(self, asin: str, new_price: float, 
                           strike_price: Optional[float] = None) -> bool:
        """تحديث سعر المنتج"""
        try:
            with self.lock:
                # حساب نسبة الخصم
                discount_percent = 0
                if strike_price and strike_price > new_price:
                    discount_percent = ((strike_price - new_price) / strike_price) * 100
                
                self.connection.execute('''
                    UPDATE products 
                    SET current_price = ?, strike_price = ?, discount_percent = ?, 
                        last_updated = CURRENT_TIMESTAMP
                    WHERE asin = ?
                ''', (new_price, strike_price, discount_percent, asin))
                
                # إضافة إلى تاريخ الأسعار
                now = datetime.now()
                self.connection.execute('''
                    INSERT INTO price_history (asin, price, date, time)
                    VALUES (?, ?, ?, ?)
                ''', (asin, new_price, now.strftime('%Y-%m-%d'), now.strftime('%H:%M')))
                
                self.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating product price {asin}: {e}")
            return False
    
    def get_product(self, asin: str) -> Optional[Product]:
        """الحصول على منتج واحد"""
        try:
            with self.lock:
                cursor = self.connection.execute('''
                    SELECT asin, name, url, img, section, current_price, strike_price,
                           discount_percent, last_updated, created_at, ai_score,
                           market_comparison, is_verified_deal
                    FROM products WHERE asin = ?
                ''', (asin,))
                
                row = cursor.fetchone()
                if row:
                    return Product(
                        asin=row[0], name=row[1], url=row[2], img=row[3], section=row[4],
                        current_price=row[5], strike_price=row[6], discount_percent=row[7],
                        last_updated=datetime.fromisoformat(row[8]),
                        created_at=datetime.fromisoformat(row[9]),
                        ai_score=row[10], market_comparison=row[11], is_verified_deal=bool(row[12])
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting product {asin}: {e}")
            return None
    
    def get_deals(self, min_discount: float = 20, limit: int = 50, 
                  verified_only: bool = False) -> List[Product]:
        """الحصول على العروض المخفضة"""
        try:
            with self.lock:
                query = '''
                    SELECT asin, name, url, img, section, current_price, strike_price,
                           discount_percent, last_updated, created_at, ai_score,
                           market_comparison, is_verified_deal
                    FROM products 
                    WHERE discount_percent >= ? AND discount_percent <= 95
                '''
                params = [min_discount]
                
                if verified_only:
                    query += ' AND is_verified_deal = TRUE'
                
                query += ' ORDER BY ai_score DESC NULLS LAST, discount_percent DESC, current_price ASC LIMIT ?'
                params.append(limit)
                
                cursor = self.connection.execute(query, params)
                products = []
                
                for row in cursor.fetchall():
                    products.append(Product(
                        asin=row[0], name=row[1], url=row[2], img=row[3], section=row[4],
                        current_price=row[5], strike_price=row[6], discount_percent=row[7],
                        last_updated=datetime.fromisoformat(row[8]),
                        created_at=datetime.fromisoformat(row[9]),
                        ai_score=row[10], market_comparison=row[11], is_verified_deal=bool(row[12])
                    ))
                
                return products
        except Exception as e:
            logger.error(f"Error getting deals: {e}")
            return []
    
    def get_price_history(self, asin: str, days: int = 30) -> List[PriceHistory]:
        """الحصول على تاريخ أسعار المنتج"""
        try:
            with self.lock:
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                
                cursor = self.connection.execute('''
                    SELECT id, asin, price, date, time, created_at
                    FROM price_history 
                    WHERE asin = ? AND date >= ?
                    ORDER BY date DESC, time DESC
                ''', (asin, start_date))
                
                history = []
                for row in cursor.fetchall():
                    history.append(PriceHistory(
                        id=row[0], asin=row[1], price=row[2], date=row[3], time=row[4],
                        created_at=datetime.fromisoformat(row[5])
                    ))
                
                return history
        except Exception as e:
            logger.error(f"Error getting price history for {asin}: {e}")
            return []
    
    def save_ai_analysis(self, asin: str, analysis_data: dict) -> bool:
        """حفظ تحليل AI"""
        try:
            with self.lock:
                self.connection.execute('''
                    INSERT INTO ai_analysis 
                    (asin, market_average, best_alternative_price, best_alternative_website,
                     price_difference, price_difference_percent, confidence_score,
                     is_good_deal, recommendations, analysis_summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    asin, analysis_data.get('market_average'), 
                    analysis_data.get('best_alternative_price'),
                    analysis_data.get('best_alternative_website'),
                    analysis_data.get('price_difference'),
                    analysis_data.get('price_difference_percent'),
                    analysis_data.get('confidence_score'),
                    analysis_data.get('is_good_deal'),
                    json.dumps(analysis_data.get('recommendations', [])),
                    analysis_data.get('analysis_summary')
                ))
                
                # تحديث المنتج بدرجة AI
                self.connection.execute('''
                    UPDATE products 
                    SET ai_score = ?, market_comparison = ?, is_verified_deal = ?
                    WHERE asin = ?
                ''', (
                    analysis_data.get('confidence_score'),
                    analysis_data.get('analysis_summary'),
                    analysis_data.get('is_good_deal', False),
                    asin
                ))
                
                self.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving AI analysis for {asin}: {e}")
            return False
    
    def get_database_stats(self) -> dict:
        """الحصول على إحصائيات قاعدة البيانات"""
        try:
            with self.lock:
                stats = {}
                
                # إجمالي المنتجات
                cursor = self.connection.execute("SELECT COUNT(*) FROM products")
                stats['total_products'] = cursor.fetchone()[0]
                
                # المنتجات المخفضة
                cursor = self.connection.execute("SELECT COUNT(*) FROM products WHERE discount_percent >= 20")
                stats['discounted_products'] = cursor.fetchone()[0]
                
                # العروض المصدقة
                cursor = self.connection.execute("SELECT COUNT(*) FROM products WHERE is_verified_deal = TRUE")
                stats['verified_deals'] = cursor.fetchone()[0]
                
                # أعلى خصم
                cursor = self.connection.execute("SELECT MAX(discount_percent) FROM products WHERE discount_percent < 99")
                stats['max_discount'] = cursor.fetchone()[0] or 0
                
                # آخر تحديث
                cursor = self.connection.execute("SELECT MAX(last_updated) FROM products")
                stats['last_update'] = cursor.fetchone()[0]
                
                # إحصائيات AI
                cursor = self.connection.execute("SELECT COUNT(*) FROM ai_analysis WHERE is_good_deal = TRUE")
                stats['ai_good_deals'] = cursor.fetchone()[0]
                
                return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def migrate_from_json(self, json_file: str, batch_size: int = 1000) -> bool:
        """نقل البيانات من JSON إلى SQLite"""
        try:
            if not os.path.exists(json_file):
                logger.error(f"JSON file not found: {json_file}")
                return False
            
            logger.info(f"Starting migration from {json_file}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Found {len(data)} products in JSON")
            
            products_batch = []
            history_batch = []
            processed = 0
            
            for asin, product_data in data.items():
                try:
                    # بيانات المنتج
                    products_batch.append((
                        asin,
                        product_data.get('name', ''),
                        product_data.get('url', ''),
                        product_data.get('img', ''),
                        product_data.get('section', 'Unknown'),
                        product_data.get('price', 0),
                        product_data.get('strike_price'),
                        product_data.get('discount_percent', 0)
                    ))
                    
                    # تاريخ الأسعار
                    price_history = product_data.get('price_history', [])
                    for entry in price_history:
                        history_batch.append((
                            asin,
                            entry.get('price', 0),
                            entry.get('date', ''),
                            entry.get('time', '00:00')
                        ))
                    
                    # حفظ دفعي
                    if len(products_batch) >= batch_size:
                        self._save_batch(products_batch, history_batch)
                        products_batch = []
                        history_batch = []
                        processed += batch_size
                        logger.info(f"Processed {processed} products")
                
                except Exception as e:
                    logger.error(f"Error processing product {asin}: {e}")
                    continue
            
            # حفظ الباقي
            if products_batch:
                self._save_batch(products_batch, history_batch)
            
            logger.info("Migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def _save_batch(self, products_batch: List[Tuple], history_batch: List[Tuple]):
        """حفظ دفعة من البيانات"""
        with self.lock:
            # حفظ المنتجات
            self.connection.executemany('''
                INSERT OR REPLACE INTO products 
                (asin, name, url, img, section, current_price, strike_price, discount_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', products_batch)
            
            # حفظ تاريخ الأسعار
            if history_batch:
                self.connection.executemany('''
                    INSERT INTO price_history (asin, price, date, time)
                    VALUES (?, ?, ?, ?)
                ''', history_batch)
            
            self.connection.commit()
    
    def export_to_json(self, output_file: str = "amz_products_export.json") -> bool:
        """تصدير البيانات إلى JSON"""
        try:
            with self.lock:
                cursor = self.connection.execute('''
                    SELECT asin, name, url, img, section, current_price, strike_price,
                           discount_percent, last_updated, ai_score, market_comparison, is_verified_deal
                    FROM products
                ''')
                
                products = {}
                for row in cursor.fetchall():
                    asin = row[0]
                    products[asin] = {
                        'name': row[1],
                        'url': row[2],
                        'img': row[3],
                        'section': row[4],
                        'price': row[5],
                        'strike_price': row[6],
                        'discount_percent': row[7],
                        'last_updated': row[8],
                        'ai_score': row[9],
                        'market_comparison': row[10],
                        'is_verified_deal': bool(row[11])
                    }
                    
                    # إضافة تاريخ الأسعار
                    history_cursor = self.connection.execute('''
                        SELECT price, date, time FROM price_history 
                        WHERE asin = ? ORDER BY date DESC, time DESC
                    ''', (asin,))
                    
                    products[asin]['price_history'] = [
                        {
                            'price': h[0],
                            'date': h[1],
                            'time': h[2]
                        }
                        for h in history_cursor.fetchall()
                    ]
                
                # حفظ إلى ملف
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(products, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Exported {len(products)} products to {output_file}")
                return True
                
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def close(self):
        """إغلاق قاعدة البيانات"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

# مثال للاستخدام
if __name__ == "__main__":
    # إنشاء مدير قاعدة البيانات
    db = EnhancedDatabaseManager()
    
    # عرض الإحصائيات
    stats = db.get_database_stats()
    print(f"Database Stats: {stats}")
    
    # إغلاق قاعدة البيانات
    db.close()