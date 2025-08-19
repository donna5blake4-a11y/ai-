# enhanced_scraper.py
# دمج النظام المحسن مع AI محلل الأسعار

import asyncio
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable
from ai_price_analyzer import AIPriceAnalyzer, DealAnalysis
from egyptian_retailers import EgyptianRetailerSearcher

class DatabaseManager:
    """مدير قاعدة البيانات المحسن"""
    
    def __init__(self, db_path="amz_products.db"):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.init_database()
    
    def init_database(self):
        """تهيئة قاعدة البيانات مع أعمدة AI"""
        # تحديث جدول المنتجات
        self.connection.execute('''
            ALTER TABLE products ADD COLUMN ai_analyzed BOOLEAN DEFAULT FALSE
        ''')
        self.connection.execute('''
            ALTER TABLE products ADD COLUMN deal_score REAL DEFAULT 0
        ''')
        self.connection.execute('''
            ALTER TABLE products ADD COLUMN is_real_deal BOOLEAN DEFAULT FALSE
        ''')
        self.connection.execute('''
            ALTER TABLE products ADD COLUMN confidence REAL DEFAULT 0
        ''')
        self.connection.execute('''
            ALTER TABLE products ADD COLUMN recommendation TEXT DEFAULT ''
        ''')
        
        # جدول تحليل AI
        self.connection.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT,
                analysis_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asin) REFERENCES products (asin)
            )
        ''')
        
        self.connection.commit()
    
    def save_product(self, product_data: dict):
        """حفظ منتج في قاعدة البيانات"""
        try:
            self.connection.execute('''
                INSERT OR REPLACE INTO products 
                (asin, name, url, img, section, current_price, strike_price, discount_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_data.get('asin'),
                product_data.get('name'),
                product_data.get('url'),
                product_data.get('img'),
                product_data.get('section'),
                product_data.get('current_price'),
                product_data.get('strike_price'),
                product_data.get('discount_percent', 0)
            ))
            self.connection.commit()
        except Exception as e:
            print(f"Error saving product: {e}")
    
    def update_ai_analysis(self, asin: str, analysis: DealAnalysis):
        """تحديث تحليل AI للمنتج"""
        try:
            # تحديث جدول المنتجات
            self.connection.execute('''
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
            analysis_data = {
                "amazon_price": analysis.amazon_price,
                "amazon_discount": analysis.amazon_discount,
                "market_avg_price": analysis.market_avg_price,
                "savings_percentage": analysis.savings_percentage,
                "competitors_count": analysis.competitors_count,
                "deal_score": analysis.deal_score,
                "is_real_deal": analysis.is_real_deal,
                "confidence": analysis.confidence,
                "recommendation": analysis.recommendation,
                "risk_factors": analysis.risk_factors,
                "price_comparisons": [
                    {
                        "retailer": p.retailer,
                        "price": p.price,
                        "similarity": p.similarity,
                        "confidence": p.confidence
                    } for p in analysis.price_comparisons
                ],
                "analysis_time": analysis.analysis_time
            }
            
            self.connection.execute('''
                INSERT OR REPLACE INTO ai_analysis (asin, analysis_data)
                VALUES (?, ?)
            ''', (asin, json.dumps(analysis_data)))
            
            self.connection.commit()
            
        except Exception as e:
            print(f"Error updating AI analysis: {e}")
    
    def get_unanalyzed_products(self, limit: int = 50) -> List[dict]:
        """الحصول على المنتجات غير المحللة"""
        cursor = self.connection.execute('''
            SELECT asin, name, url, img, section, current_price, strike_price, discount_percent
            FROM products 
            WHERE ai_analyzed = FALSE AND discount_percent >= 20
            ORDER BY discount_percent DESC
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
                'current_price': row[5],
                'strike_price': row[6],
                'discount_percent': row[7]
            })
        
        return products
    
    def get_real_deals(self, min_score: float = 70, limit: int = 100) -> List[dict]:
        """الحصول على العروض الحقيقية"""
        cursor = self.connection.execute('''
            SELECT p.asin, p.name, p.url, p.img, p.section, p.current_price, 
                   p.strike_price, p.discount_percent, p.deal_score, p.confidence, p.recommendation
            FROM products p
            WHERE p.is_real_deal = TRUE AND p.deal_score >= ?
            ORDER BY p.deal_score DESC, p.discount_percent DESC
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
                'current_price': row[5],
                'strike_price': row[6],
                'discount_percent': row[7],
                'deal_score': row[8],
                'confidence': row[9],
                'recommendation': row[10]
            })
        
        return deals

class EnhancedScraper:
    """محلل محسن مع AI"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.ai_analyzer = AIPriceAnalyzer()
        self.analysis_queue = asyncio.Queue()
        self.analysis_worker = None
        self.is_running = False
    
    async def start_analysis_worker(self):
        """بدء عامل تحليل AI"""
        self.is_running = True
        self.analysis_worker = asyncio.create_task(self._analysis_worker())
    
    async def stop_analysis_worker(self):
        """إيقاف عامل تحليل AI"""
        self.is_running = False
        if self.analysis_worker:
            self.analysis_worker.cancel()
            try:
                await self.analysis_worker
            except asyncio.CancelledError:
                pass
    
    async def _analysis_worker(self):
        """عامل تحليل AI في الخلفية"""
        while self.is_running:
            try:
                # انتظار منتج للتحليل
                product_data = await asyncio.wait_for(
                    self.analysis_queue.get(), 
                    timeout=1.0
                )
                
                # تحليل المنتج
                analysis = await self.ai_analyzer.analyze_deal(product_data)
                
                # حفظ النتيجة
                self.db_manager.update_ai_analysis(product_data['asin'], analysis)
                
                # إرسال تنبيه إذا كان عرض حقيقي
                if analysis.is_real_deal and analysis.confidence >= 0.7:
                    await self._send_smart_alert(product_data, analysis)
                
                # إشعار انتهاء التحليل
                self.analysis_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error in analysis worker: {e}")
                continue
    
    async def _send_smart_alert(self, product_data: dict, analysis: DealAnalysis):
        """إرسال تنبيه ذكي للعروض الحقيقية"""
        # هنا يمكن إضافة كود إرسال التليجرام
        print(f"🎯 عرض حقيقي: {product_data['name']}")
        print(f"💰 السعر: {analysis.amazon_price:,.0f} جنيه")
        print(f"📊 درجة العرض: {analysis.deal_score:.1f}/100")
        print(f"💡 التوصية: {analysis.recommendation}")
    
    async def process_product(self, product_data: dict):
        """معالجة منتج جديد"""
        # حفظ المنتج في قاعدة البيانات
        self.db_manager.save_product(product_data)
        
        # إضافة للتحليل AI
        await self.analysis_queue.put(product_data)
    
    async def analyze_pending_products(self, limit: int = 50):
        """تحليل المنتجات المعلقة"""
        products = self.db_manager.get_unanalyzed_products(limit)
        
        print(f"🔍 تحليل {len(products)} منتج معلق...")
        
        for i, product in enumerate(products):
            try:
                analysis = await self.ai_analyzer.analyze_deal(product)
                self.db_manager.update_ai_analysis(product['asin'], analysis)
                
                if (i + 1) % 10 == 0:
                    print(f"✅ تم تحليل {i + 1}/{len(products)} منتج")
                
                # تأخير قصير لتجنب الضغط على المواقع
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Error analyzing {product['asin']}: {e}")
                continue
        
        print(f"🎉 تم الانتهاء من تحليل {len(products)} منتج")
    
    def get_smart_deals_summary(self) -> dict:
        """ملخص العروض الذكية"""
        real_deals = self.db_manager.get_real_deals(min_score=70)
        
        total_products = self.db_manager.connection.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]
        
        analyzed_products = self.db_manager.connection.execute(
            "SELECT COUNT(*) FROM products WHERE ai_analyzed = TRUE"
        ).fetchone()[0]
        
        return {
            "total_products": total_products,
            "analyzed_products": analyzed_products,
            "real_deals": len(real_deals),
            "analysis_percentage": (analyzed_products / total_products * 100) if total_products > 0 else 0,
            "top_deals": real_deals[:5]  # أفضل 5 عروض
        }

def export_to_json(filename: str = None, min_score: float = 70):
    """تصدير العروض الحقيقية إلى JSON"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"real_deals_{timestamp}.json"
    
    db_manager = DatabaseManager()
    real_deals = db_manager.get_real_deals(min_score=min_score)
    
    # تحويل إلى تنسيق JSON
    deals_data = {}
    for deal in real_deals:
        deals_data[deal['asin']] = {
            'name': deal['name'],
            'url': deal['url'],
            'img': deal['img'],
            'section': deal['section'],
            'current_price': deal['current_price'],
            'strike_price': deal['strike_price'],
            'discount_percent': deal['discount_percent'],
            'deal_score': deal['deal_score'],
            'confidence': deal['confidence'],
            'recommendation': deal['recommendation'],
            'export_date': datetime.now().isoformat()
        }
    
    # حفظ الملف
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(deals_data, f, ensure_ascii=False, indent=2)
    
    print(f"📄 تم تصدير {len(real_deals)} عرض حقيقي إلى {filename}")
    return filename

# دالة مساعدة للاختبار
async def test_enhanced_system():
    """اختبار النظام المحسن"""
    print("🚀 اختبار النظام المحسن...")
    
    # إنشاء مدير قاعدة البيانات
    db_manager = DatabaseManager()
    
    # إنشاء المحلل المحسن
    scraper = EnhancedScraper(db_manager)
    
    # بدء عامل التحليل
    await scraper.start_analysis_worker()
    
    # منتج تجريبي
    test_product = {
        "asin": "B0C7CQT9ZS",
        "name": "Samsung Galaxy A54 5G",
        "url": "https://www.amazon.eg/test",
        "img": "https://test.com/image.jpg",
        "section": "Electronics",
        "current_price": 8500,
        "strike_price": 12000,
        "discount_percent": 29
    }
    
    # معالجة المنتج
    await scraper.process_product(test_product)
    
    # انتظار التحليل
    await asyncio.sleep(5)
    
    # عرض الملخص
    summary = scraper.get_smart_deals_summary()
    print(f"📊 ملخص النظام:")
    print(f"   إجمالي المنتجات: {summary['total_products']}")
    print(f"   المنتجات المحللة: {summary['analyzed_products']}")
    print(f"   العروض الحقيقية: {summary['real_deals']}")
    print(f"   نسبة التحليل: {summary['analysis_percentage']:.1f}%")
    
    # إيقاف النظام
    await scraper.stop_analysis_worker()

if __name__ == "__main__":
    asyncio.run(test_enhanced_system())