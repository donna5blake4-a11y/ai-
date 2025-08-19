# enhanced_amz_scraper.py
# محرك الكشط المحسن مع AI محلل الأسعار

import asyncio
import sqlite3
import json
import gzip
from datetime import datetime
from typing import Dict, List, Optional, Callable
from ai_price_analyzer import AIPriceAnalyzer, DealAnalysis
from egyptian_retailers import EGYPTIAN_RETAILERS

class DatabaseManager:
    """مدير قاعدة البيانات المحسن"""
    
    def __init__(self, db_path="amz_products.db"):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA cache_size=50000")
        self.init_database()
    
    def init_database(self):
        """تهيئة قاعدة البيانات"""
        cursor = self.connection.cursor()
        
        # جدول المنتجات المحسن
        cursor.execute('''
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
        
        # جدول تاريخ الأسعار
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT,
                price REAL,
                date TEXT,
                time TEXT,
                FOREIGN KEY (asin) REFERENCES products (asin)
            )
        ''')
        
        # جدول التحليل الذكي
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deal_score REAL,
                is_real_deal BOOLEAN,
                confidence REAL,
                recommendation TEXT,
                average_market_price REAL,
                competitor_count INTEGER,
                risk_factors TEXT,
                FOREIGN KEY (asin) REFERENCES products (asin)
            )
        ''')
        
        # إنشاء الفهارس
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_asin ON products(asin)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_section ON products(section)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_discount ON products(discount_percent)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_deal_score ON products(deal_score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_real_deal ON products(is_real_deal)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_analyzed ON products(ai_analyzed)')
        
        self.connection.commit()
    
    def save_product(self, product_data: dict):
        """حفظ منتج في قاعدة البيانات"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO products 
            (asin, name, url, img, section, current_price, strike_price, discount_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_data.get('asin'),
            product_data.get('name'),
            product_data.get('url'),
            product_data.get('img'),
            product_data.get('section'),
            product_data.get('price'),
            product_data.get('strike_price'),
            product_data.get('discount_percent', 0)
        ))
        
        # حفظ تاريخ السعر
        if product_data.get('price'):
            now = datetime.now()
            cursor.execute('''
                INSERT INTO price_history (asin, price, date, time)
                VALUES (?, ?, ?, ?)
            ''', (
                product_data.get('asin'),
                product_data.get('price'),
                now.strftime('%Y-%m-%d'),
                now.strftime('%H:%M')
            ))
        
        self.connection.commit()
    
    def update_ai_analysis(self, asin: str, analysis: DealAnalysis):
        """تحديث نتائج التحليل الذكي"""
        cursor = self.connection.cursor()
        
        # تحديث جدول المنتجات
        cursor.execute('''
            UPDATE products 
            SET ai_analyzed = TRUE, deal_score = ?, is_real_deal = ?, 
                confidence = ?, recommendation = ?
            WHERE asin = ?
        ''', (
            analysis.deal_score,
            analysis.is_real_deal,
            analysis.confidence,
            analysis.recommendation,
            asin
        ))
        
        # حفظ التحليل التفصيلي
        cursor.execute('''
            INSERT INTO ai_analysis 
            (asin, deal_score, is_real_deal, confidence, recommendation, 
             average_market_price, competitor_count, risk_factors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            asin,
            analysis.deal_score,
            analysis.is_real_deal,
            analysis.confidence,
            analysis.recommendation,
            analysis.average_market_price,
            len(analysis.competitor_prices),
            json.dumps(analysis.risk_factors)
        ))
        
        self.connection.commit()
    
    def get_unanalyzed_products(self, limit: int = 50) -> List[dict]:
        """جلب المنتجات غير المحللة"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT asin, name, url, img, section, current_price, strike_price, discount_percent
            FROM products 
            WHERE ai_analyzed = FALSE AND discount_percent >= 20
            ORDER BY discount_percent DESC, last_updated DESC
            LIMIT ?
        ''', (limit,))
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'asin': row[0],
                'name': row[1],
                'url': row[2],
                'img': row[3],
                'section': row[4],
                'price': row[5],
                'strike_price': row[6],
                'discount_percent': row[7]
            })
        
        return products
    
    def get_real_deals(self, min_score: float = 60, limit: int = 20) -> List[dict]:
        """جلب العروض الحقيقية فقط"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT asin, name, url, img, section, current_price, strike_price, 
                   discount_percent, deal_score, confidence, recommendation
            FROM products 
            WHERE is_real_deal = TRUE AND deal_score >= ? AND ai_analyzed = TRUE
            ORDER BY deal_score DESC, discount_percent DESC
            LIMIT ?
        ''', (min_score, limit))
        
        deals = []
        for row in cursor.fetchall():
            deals.append({
                'asin': row[0],
                'name': row[1],
                'url': row[2],
                'img': row[3],
                'section': row[4],
                'price': row[5],
                'strike_price': row[6],
                'discount_percent': row[7],
                'deal_score': row[8],
                'confidence': row[9],
                'recommendation': row[10]
            })
        
        return deals

class EnhancedScraper:
    """كاشف محسن مع AI"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.ai_analyzer = AIPriceAnalyzer()
        self.analysis_queue = asyncio.Queue()
        self.analysis_worker = None
    
    async def start_analysis_worker(self):
        """بدء عامل تحليل الخلفية"""
        if not self.analysis_worker:
            self.analysis_worker = asyncio.create_task(self._analysis_worker())
    
    async def stop_analysis_worker(self):
        """إيقاف عامل التحليل"""
        if self.analysis_worker:
            self.analysis_worker.cancel()
            try:
                await self.analysis_worker
            except asyncio.CancelledError:
                pass
            self.analysis_worker = None
    
    async def _analysis_worker(self):
        """عامل تحليل الخلفية"""
        while True:
            try:
                # انتظار منتج للتحليل
                product_data = await self.analysis_queue.get()
                
                # تحليل المنتج
                analysis = await self.ai_analyzer.analyze_deal(product_data)
                
                # حفظ النتائج
                self.db_manager.update_ai_analysis(product_data['asin'], analysis)
                
                # إرسال تنبيه إذا كان العرض حقيقي
                if analysis.is_real_deal and analysis.deal_score >= 70:
                    await self._send_smart_alert(product_data, analysis)
                
                self.analysis_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Analysis worker error: {e}")
                continue
    
    async def _send_smart_alert(self, product_data: dict, analysis: DealAnalysis):
        """إرسال تنبيه ذكي"""
        # هنا يمكن إضافة كود إرسال التليجرام المحسن
        alert_message = f"""
🎯 **عرض حقيقي مضمون!**

{self.ai_analyzer.get_analysis_summary(analysis)}

🔗 **المنتج**: {product_data['name']}
💰 **السعر**: {product_data['price']:,.0f} جنيه
📉 **الخصم**: {product_data['discount_percent']:.1f}%
⭐ **درجة العرض**: {analysis.deal_score:.1f}/100

{product_data['url']}
        """
        
        # إرسال عبر التليجرام (سيتم تنفيذه لاحقاً)
        print("SMART ALERT:", alert_message)
    
    async def process_product(self, product_data: dict):
        """معالجة منتج جديد"""
        # حفظ في قاعدة البيانات
        self.db_manager.save_product(product_data)
        
        # إضافة للتحليل الذكي (في الخلفية)
        await self.analysis_queue.put(product_data)
    
    async def analyze_pending_products(self, limit: int = 20):
        """تحليل المنتجات المعلقة"""
        products = self.db_manager.get_unanalyzed_products(limit)
        
        for product in products:
            try:
                analysis = await self.ai_analyzer.analyze_deal(product)
                self.db_manager.update_ai_analysis(product['asin'], analysis)
                
                print(f"✅ Analyzed: {product['name'][:50]}... (Score: {analysis.deal_score:.1f})")
                
                # تأخير لتجنب الحظر
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Analysis failed for {product['asin']}: {e}")
                continue
    
    def get_smart_deals_summary(self) -> dict:
        """ملخص العروض الذكية"""
        real_deals = self.db_manager.get_real_deals(min_score=60)
        
        summary = {
            'total_real_deals': len(real_deals),
            'excellent_deals': len([d for d in real_deals if d['deal_score'] >= 80]),
            'good_deals': len([d for d in real_deals if 60 <= d['deal_score'] < 80]),
            'average_deal_score': sum(d['deal_score'] for d in real_deals) / len(real_deals) if real_deals else 0,
            'top_deals': sorted(real_deals, key=lambda x: x['deal_score'], reverse=True)[:5]
        }
        
        return summary

# دالة التصدير المحسنة
def export_to_json(filename: str = None, compress: bool = True):
    """تصدير البيانات مع التحليل الذكي"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"smart_products_{timestamp}.json"
        if compress:
            filename += ".gz"
    
    db_manager = DatabaseManager()
    real_deals = db_manager.get_real_deals(min_score=50, limit=1000)
    
    export_data = {
        'export_date': datetime.now().isoformat(),
        'total_real_deals': len(real_deals),
        'products': real_deals
    }
    
    if compress:
        with gzip.open(filename, 'wt', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    else:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Exported {len(real_deals)} smart deals to {filename}")

# دالة الكشط المحسنة (ستتم دمجها مع الكود الحالي)
async def scrape_section_enhanced(section: str, section_url: str, start_page: int, 
                                end_page: int, db: dict, log_fn: Callable = None,
                                progress_fn: Callable = None, stop_flag: dict = None,
                                discount_alert_cb: Callable = None, 
                                discount_threshold: float = 20.0):
    """كشط محسن مع AI"""
    
    # إنشاء مدير قاعدة البيانات المحسن
    db_manager = DatabaseManager()
    enhanced_scraper = EnhancedScraper(db_manager)
    
    # بدء عامل التحليل
    await enhanced_scraper.start_analysis_worker()
    
    try:
        # هنا سيتم دمج كود الكشط الحالي مع المعالجة المحسنة
        # سيتم استدعاء enhanced_scraper.process_product() لكل منتج
        
        # مثال على المعالجة
        for page in range(start_page, end_page + 1):
            if stop_flag and stop_flag.get("stop"):
                break
            
            # كشط الصفحة (سيتم دمج الكود الحالي هنا)
            # products = await scrape_single_page(...)
            
            # معالجة المنتجات مع AI
            # for product in products:
            #     await enhanced_scraper.process_product(product)
            
            if progress_fn:
                progress_fn(page)
            
            if log_fn:
                log_fn(f"Processed page {page}")
        
        # تحليل المنتجات المعلقة
        await enhanced_scraper.analyze_pending_products()
        
        # ملخص العروض الذكية
        summary = enhanced_scraper.get_smart_deals_summary()
        if log_fn:
            log_fn(f"Smart Analysis Complete: {summary['total_real_deals']} real deals found")
        
    finally:
        await enhanced_scraper.stop_analysis_worker()
        await enhanced_scraper.ai_analyzer.close_session()