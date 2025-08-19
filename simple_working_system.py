# simple_working_system.py
# نظام مبسط يعمل مع المواقع المتاحة

import asyncio
import aiohttp
import re
import json
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import time

class SimplePriceSearcher:
    """محلل أسعار مبسط يعمل مع المواقع المتاحة"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_noon(self, product_name: str) -> Optional[float]:
        """البحث في Noon"""
        try:
            query = self.clean_product_name(product_name)
            url = f"https://www.noon.com/egypt/search?q={query}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # البحث عن الأسعار في النص
                price_pattern = re.compile(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:جنيه|ج\.م|EGP|LE)')
                matches = price_pattern.findall(html)
                
                for match in matches[:5]:
                    try:
                        price = float(match.replace(',', ''))
                        if 100 <= price <= 50000:
                            return price
                    except:
                        continue
                
                return None
                
        except Exception as e:
            print(f"Noon error: {e}")
            return None
    
    async def search_kanbkam(self, product_name: str) -> Optional[float]:
        """البحث في Kanbkam"""
        try:
            query = self.clean_product_name(product_name)
            url = f"https://www.kanbkam.com/search?q={query}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                
                # البحث عن الأسعار في النص
                price_pattern = re.compile(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:جنيه|ج\.م|EGP|LE)')
                matches = price_pattern.findall(html)
                
                for match in matches[:5]:
                    try:
                        price = float(match.replace(',', ''))
                        if 100 <= price <= 50000:
                            return price
                    except:
                        continue
                
                return None
                
        except Exception as e:
            print(f"Kanbkam error: {e}")
            return None
    
    def clean_product_name(self, name: str) -> str:
        """تنظيف اسم المنتج للبحث"""
        # إزالة الكلمات غير المهمة
        stop_words = ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
        words = [word for word in name.lower().split() if word not in stop_words and len(word) > 2]
        
        # أخذ أول 3 كلمات مهمة
        return " ".join(words[:3])
    
    async def search_working_retailers(self, product_name: str) -> Dict:
        """البحث في المواقع التي تعمل"""
        print(f"🔍 البحث عن: {product_name}")
        start_time = time.time()
        
        # البحث في المواقع التي تعمل
        tasks = [
            self.search_noon(product_name),
            self.search_kanbkam(product_name)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # تجميع النتائج
        retailers = ["Noon", "Kanbkam"]
        prices = {}
        
        for i, result in enumerate(results):
            retailer = retailers[i]
            if isinstance(result, Exception):
                print(f"❌ {retailer}: {result}")
            elif result:
                prices[retailer] = result
                print(f"✅ {retailer}: {result:,.0f} جنيه")
            else:
                print(f"⚠️ {retailer}: لا توجد نتائج")
        
        search_time = time.time() - start_time
        print(f"⏱️ وقت البحث: {search_time:.2f}s")
        
        return {
            "prices": prices,
            "search_time": search_time,
            "total_found": len(prices)
        }

class SimpleAIAnalyzer:
    """محلل AI مبسط"""
    
    def __init__(self):
        self.confidence_threshold = 0.70
        self.min_competitors = 1  # تخفيض لأننا نبحث في موقعين فقط
        self.min_savings = 10  # تخفيض قليلاً
    
    async def analyze_deal(self, product_data: dict) -> Dict:
        """تحليل العرض"""
        start_time = time.time()
        
        amazon_price = product_data.get('current_price', 0)
        amazon_discount = product_data.get('discount_percent', 0)
        product_name = product_data.get('name', '')
        
        if not amazon_price or not product_name:
            return self._empty_analysis(amazon_price, amazon_discount)
        
        # البحث في المواقع المتاحة
        async with SimplePriceSearcher() as searcher:
            search_results = await searcher.search_working_retailers(product_name)
        
        prices = search_results['prices']
        
        # حساب الإحصائيات
        if prices:
            market_avg = sum(prices.values()) / len(prices)
            savings = ((market_avg - amazon_price) / market_avg) * 100
            competitors_count = len(prices)
        else:
            market_avg = amazon_price
            savings = 0
            competitors_count = 0
        
        # حساب درجة العرض
        deal_score = self._calculate_deal_score(amazon_discount, savings, competitors_count)
        
        # تحديد إذا العرض حقيقي
        is_real_deal = self._is_real_deal(deal_score, competitors_count, savings)
        
        # حساب درجة الثقة
        confidence = self._calculate_confidence(competitors_count, len(prices))
        
        # إنشاء التوصية
        recommendation = self._generate_recommendation(deal_score, savings, competitors_count)
        
        # تحديد المخاطر
        risk_factors = self._identify_risks(amazon_price, amazon_discount, prices)
        
        analysis_time = time.time() - start_time
        
        return {
            "amazon_price": amazon_price,
            "amazon_discount": amazon_discount,
            "market_avg_price": market_avg,
            "savings_percentage": savings,
            "competitors_count": competitors_count,
            "deal_score": deal_score,
            "is_real_deal": is_real_deal,
            "confidence": confidence,
            "recommendation": recommendation,
            "risk_factors": risk_factors,
            "competitor_prices": prices,
            "analysis_time": analysis_time,
            "search_time": search_results['search_time']
        }
    
    def _calculate_deal_score(self, amazon_discount: float, savings: float, competitors: int) -> float:
        """حساب درجة العرض"""
        score = 0
        
        # خصم أمازون (30%)
        score += min(amazon_discount * 0.6, 30)
        
        # التوفير من السوق (40%)
        score += min(savings * 0.8, 40)
        
        # عدد المنافسين (20%)
        score += min(competitors * 10, 20)
        
        # عامل إضافي (10%)
        if competitors >= 2 and savings >= 15:
            score += 10
        
        return min(score, 100)
    
    def _is_real_deal(self, deal_score: float, competitors: int, savings: float) -> bool:
        """تحديد إذا العرض حقيقي"""
        return (
            deal_score >= 70 and
            competitors >= self.min_competitors and
            savings >= self.min_savings
        )
    
    def _calculate_confidence(self, competitors: int, total_searched: int) -> float:
        """حساب درجة الثقة"""
        if total_searched == 0:
            return 0
        
        # نسبة النجاح في البحث
        success_rate = competitors / total_searched
        
        # عامل عدد المنافسين
        competitor_factor = min(competitors / 2, 1.0)  # تعديل لأننا نبحث في موقعين فقط
        
        return (success_rate * 0.7) + (competitor_factor * 0.3)
    
    def _generate_recommendation(self, deal_score: float, savings: float, competitors: int) -> str:
        """إنشاء توصية"""
        if deal_score >= 90:
            return "🔥 عرض استثنائي! لا تفوت هذه الفرصة"
        elif deal_score >= 80:
            return "💥 عرض ممتاز! أمازون أرخص بكثير من السوق"
        elif deal_score >= 70:
            return "🎉 عرض جيد! توفير حقيقي من السوق"
        elif deal_score >= 60:
            return "✨ عرض مقبول، لكن يمكن انتظار خصم أكبر"
        elif deal_score >= 50:
            return "📊 عرض عادي، الأسعار متقاربة"
        else:
            return "⚠️ عرض ضعيف، الأسعار متشابهة أو أعلى"
    
    def _identify_risks(self, amazon_price: float, amazon_discount: float, prices: Dict) -> List[str]:
        """تحديد المخاطر"""
        risks = []
        
        if amazon_price < 50 and amazon_discount > 80:
            risks.append("سعر منخفض جداً - قد يكون منتج مستعمل")
        
        if amazon_discount > 90:
            risks.append("خصم مفرط - قد يكون خطأ في السعر")
        
        if len(prices) < 1:
            risks.append("لا توجد مقارنات متاحة")
        
        if prices:
            price_variance = (max(prices.values()) - min(prices.values())) / min(prices.values())
            if price_variance > 0.5:
                risks.append("تباين كبير في الأسعار - قد يكون اختلاف في المواصفات")
        
        return risks
    
    def _empty_analysis(self, amazon_price: float, amazon_discount: float) -> Dict:
        """تحليل فارغ"""
        return {
            "amazon_price": amazon_price,
            "amazon_discount": amazon_discount,
            "market_avg_price": 0,
            "savings_percentage": 0,
            "competitors_count": 0,
            "deal_score": 0,
            "is_real_deal": False,
            "confidence": 0,
            "recommendation": "لا توجد بيانات كافية",
            "risk_factors": ["لا توجد مقارنات متاحة"],
            "competitor_prices": {},
            "analysis_time": 0,
            "search_time": 0
        }

class SimpleDatabaseManager:
    """مدير قاعدة بيانات مبسط"""
    
    def __init__(self, db_path="simple_products.db"):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.init_database()
    
    def init_database(self):
        """تهيئة قاعدة البيانات"""
        self.connection.execute('''
            CREATE TABLE IF NOT EXISTS products (
                asin TEXT PRIMARY KEY,
                name TEXT,
                url TEXT,
                img TEXT,
                section TEXT,
                current_price REAL,
                strike_price REAL,
                discount_percent REAL,
                deal_score REAL DEFAULT 0,
                is_real_deal BOOLEAN DEFAULT FALSE,
                confidence REAL DEFAULT 0,
                recommendation TEXT DEFAULT '',
                analysis_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.connection.commit()
    
    def save_product(self, product_data: dict, analysis: dict = None):
        """حفظ منتج مع تحليل"""
        try:
            self.connection.execute('''
                INSERT OR REPLACE INTO products 
                (asin, name, url, img, section, current_price, strike_price, discount_percent,
                 deal_score, is_real_deal, confidence, recommendation, analysis_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_data.get('asin'),
                product_data.get('name'),
                product_data.get('url'),
                product_data.get('img'),
                product_data.get('section'),
                product_data.get('current_price'),
                product_data.get('strike_price'),
                product_data.get('discount_percent', 0),
                analysis.get('deal_score', 0) if analysis else 0,
                analysis.get('is_real_deal', False) if analysis else False,
                analysis.get('confidence', 0) if analysis else 0,
                analysis.get('recommendation', '') if analysis else '',
                json.dumps(analysis) if analysis else None
            ))
            self.connection.commit()
        except Exception as e:
            print(f"Error saving product: {e}")
    
    def get_real_deals(self, min_score: float = 70) -> List[dict]:
        """الحصول على العروض الحقيقية"""
        cursor = self.connection.execute('''
            SELECT asin, name, url, img, section, current_price, strike_price, 
                   discount_percent, deal_score, confidence, recommendation
            FROM products 
            WHERE is_real_deal = TRUE AND deal_score >= ?
            ORDER BY deal_score DESC, discount_percent DESC
        ''', (min_score,))
        
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

# دالة اختبار شاملة
async def test_simple_system():
    """اختبار النظام المبسط"""
    print("🚀 اختبار النظام المبسط...")
    
    # إنشاء المحلل
    analyzer = SimpleAIAnalyzer()
    db_manager = SimpleDatabaseManager()
    
    # منتجات تجريبية
    test_products = [
        {
            "asin": "B0C7CQT9ZS",
            "name": "Samsung Galaxy A54 5G",
            "url": "https://www.amazon.eg/test",
            "img": "https://test.com/image.jpg",
            "section": "Electronics",
            "current_price": 8500,
            "strike_price": 12000,
            "discount_percent": 29
        },
        {
            "asin": "B0C8KQZ9X1", 
            "name": "iPhone 15 Pro 128GB",
            "url": "https://www.amazon.eg/test2",
            "img": "https://test.com/image2.jpg",
            "section": "Electronics",
            "current_price": 45000,
            "strike_price": 53000,
            "discount_percent": 15
        },
        {
            "asin": "B0C9XYZ123",
            "name": "Sony WH-1000XM5 Headphones",
            "url": "https://www.amazon.eg/test3",
            "img": "https://test.com/image3.jpg",
            "section": "Electronics",
            "current_price": 6500,
            "strike_price": 8500,
            "discount_percent": 24
        }
    ]
    
    for product in test_products:
        print(f"\n🎯 تحليل: {product['name']}")
        print(f"💰 سعر أمازون: {product['current_price']:,.0f} جنيه")
        print(f"🎉 خصم أمازون: {product['discount_percent']:.1f}%")
        
        # تحليل المنتج
        analysis = await analyzer.analyze_deal(product)
        
        # عرض النتائج
        print(f"🏪 متوسط السوق: {analysis['market_avg_price']:,.0f} جنيه")
        print(f"💡 التوفير: {analysis['savings_percentage']:.1f}%")
        print(f"📊 درجة العرض: {analysis['deal_score']:.1f}/100")
        print(f"✅ عرض حقيقي: {'نعم' if analysis['is_real_deal'] else 'لا'}")
        print(f"🎯 درجة الثقة: {analysis['confidence']:.1%}")
        print(f"💬 التوصية: {analysis['recommendation']}")
        
        # عرض المنافسين
        if analysis['competitor_prices']:
            print(f"🏪 المنافسون ({analysis['competitors_count']}):")
            for retailer, price in analysis['competitor_prices'].items():
                print(f"   • {retailer}: {price:,.0f} جنيه")
        
        # حفظ في قاعدة البيانات
        db_manager.save_product(product, analysis)
        
        print(f"⏱️ وقت التحليل: {analysis['analysis_time']:.2f}s")
        print("-" * 50)
    
    # عرض العروض الحقيقية
    real_deals = db_manager.get_real_deals()
    print(f"\n🏆 العروض الحقيقية ({len(real_deals)}):")
    for deal in real_deals:
        print(f"   • {deal['name']}")
        print(f"     💰 {deal['current_price']:,.0f} جنيه (خصم: {deal['discount_percent']:.1f}%)")
        print(f"     📊 درجة العرض: {deal['deal_score']:.1f}/100")
        print(f"     💬 {deal['recommendation']}")

if __name__ == "__main__":
    asyncio.run(test_simple_system())