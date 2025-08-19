# real_working_system.py
# نظام يعمل مع بيانات تجريبية واقعية

import asyncio
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import time
import random

class RealPriceSearcher:
    """محلل أسعار مع بيانات تجريبية واقعية"""
    
    def __init__(self):
        # بيانات تجريبية واقعية للأسعار المصرية
        self.mock_prices = {
            "Samsung Galaxy A54 5G": {
                "Noon": 11200,
                "Kanbkam": 10800,
                "Pricena": 11500,
                "Carrefour": 12000
            },
            "iPhone 15 Pro 128GB": {
                "Noon": 52000,
                "Kanbkam": 51000,
                "Pricena": 53000,
                "Carrefour": 54000
            },
            "Sony WH-1000XM5 Headphones": {
                "Noon": 7200,
                "Kanbkam": 7000,
                "Pricena": 7500,
                "Carrefour": 7800
            },
            "MacBook Air M2": {
                "Noon": 45000,
                "Kanbkam": 44000,
                "Pricena": 46000,
                "Carrefour": 47000
            },
            "iPad Pro 11": {
                "Noon": 28000,
                "Kanbkam": 27500,
                "Pricena": 28500,
                "Carrefour": 29000
            },
            "Apple Watch Series 9": {
                "Noon": 8500,
                "Kanbkam": 8300,
                "Pricena": 8700,
                "Carrefour": 9000
            },
            "Samsung Galaxy S24": {
                "Noon": 18000,
                "Kanbkam": 17500,
                "Pricena": 18200,
                "Carrefour": 18500
            },
            "AirPods Pro 2": {
                "Noon": 4500,
                "Kanbkam": 4300,
                "Pricena": 4600,
                "Carrefour": 4800
            }
        }
    
    def find_similar_product(self, product_name: str) -> Optional[str]:
        """البحث عن منتج مشابه في قاعدة البيانات"""
        product_name_lower = product_name.lower()
        
        for mock_product in self.mock_prices.keys():
            mock_lower = mock_product.lower()
            
            # حساب التشابه البسيط
            common_words = 0
            total_words = 0
            
            for word in product_name_lower.split():
                if len(word) > 2:  # تجاهل الكلمات القصيرة
                    total_words += 1
                    if word in mock_lower:
                        common_words += 1
            
            if total_words > 0 and (common_words / total_words) >= 0.3:  # 30% تشابه
                return mock_product
        
        return None
    
    async def search_working_retailers(self, product_name: str) -> Dict:
        """البحث في المواقع مع بيانات تجريبية"""
        print(f"🔍 البحث عن: {product_name}")
        start_time = time.time()
        
        # البحث عن منتج مشابه
        similar_product = self.find_similar_product(product_name)
        
        if similar_product:
            prices = self.mock_prices[similar_product].copy()
            
            # إضافة بعض التغييرات العشوائية للواقعية
            for retailer in prices:
                # تغيير عشوائي ±5%
                variation = random.uniform(-0.05, 0.05)
                prices[retailer] = int(prices[retailer] * (1 + variation))
            
            # محاكاة بعض المواقع التي لا تعمل
            if random.random() < 0.2:  # 20% احتمال
                if "Pricena" in prices:
                    del prices["Pricena"]
            
            if random.random() < 0.15:  # 15% احتمال
                if "Carrefour" in prices:
                    del prices["Carrefour"]
            
            # عرض النتائج
            retailers = ["Noon", "Kanbkam", "Pricena", "Carrefour"]
            for retailer in retailers:
                if retailer in prices:
                    print(f"✅ {retailer}: {prices[retailer]:,.0f} جنيه")
                else:
                    print(f"⚠️ {retailer}: لا توجد نتائج")
            
            search_time = time.time() - start_time
            print(f"⏱️ وقت البحث: {search_time:.2f}s")
            
            return {
                "prices": prices,
                "search_time": search_time,
                "total_found": len(prices),
                "similar_product": similar_product
            }
        else:
            # لا يوجد منتج مشابه
            print("⚠️ Noon: لا توجد نتائج")
            print("⚠️ Kanbkam: لا توجد نتائج")
            print("⚠️ Pricena: لا توجد نتائج")
            print("⚠️ Carrefour: لا توجد نتائج")
            
            search_time = time.time() - start_time
            print(f"⏱️ وقت البحث: {search_time:.2f}s")
            
            return {
                "prices": {},
                "search_time": search_time,
                "total_found": 0,
                "similar_product": None
            }

class RealAIAnalyzer:
    """محلل AI مع بيانات واقعية"""
    
    def __init__(self):
        self.confidence_threshold = 0.70
        self.min_competitors = 2
        self.min_savings = 15
    
    async def analyze_deal(self, product_data: dict) -> Dict:
        """تحليل العرض"""
        start_time = time.time()
        
        amazon_price = product_data.get('current_price', 0)
        amazon_discount = product_data.get('discount_percent', 0)
        product_name = product_data.get('name', '')
        
        if not amazon_price or not product_name:
            return self._empty_analysis(amazon_price, amazon_discount)
        
        # البحث في المواقع
        searcher = RealPriceSearcher()
        search_results = await searcher.search_working_retailers(product_name)
        
        prices = search_results['prices']
        similar_product = search_results.get('similar_product')
        
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
        confidence = self._calculate_confidence(competitors_count, len(prices), similar_product)
        
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
            "search_time": search_results['search_time'],
            "similar_product": similar_product
        }
    
    def _calculate_deal_score(self, amazon_discount: float, savings: float, competitors: int) -> float:
        """حساب درجة العرض"""
        score = 0
        
        # خصم أمازون (25%)
        score += min(amazon_discount * 0.5, 25)
        
        # التوفير من السوق (35%)
        score += min(savings * 0.7, 35)
        
        # عدد المنافسين (25%)
        score += min(competitors * 5, 25)
        
        # عامل إضافي (15%)
        if competitors >= 3 and savings >= 20:
            score += 15
        
        return min(score, 100)
    
    def _is_real_deal(self, deal_score: float, competitors: int, savings: float) -> bool:
        """تحديد إذا العرض حقيقي"""
        return (
            deal_score >= 70 and
            competitors >= self.min_competitors and
            savings >= self.min_savings
        )
    
    def _calculate_confidence(self, competitors: int, total_searched: int, similar_product: str) -> float:
        """حساب درجة الثقة"""
        if total_searched == 0:
            return 0
        
        # نسبة النجاح في البحث
        success_rate = competitors / total_searched
        
        # عامل عدد المنافسين
        competitor_factor = min(competitors / 4, 1.0)
        
        # عامل تشابه المنتج
        similarity_factor = 1.0 if similar_product else 0.5
        
        return (success_rate * 0.5) + (competitor_factor * 0.3) + (similarity_factor * 0.2)
    
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
        
        if len(prices) < 2:
            risks.append("قلة المنافسين - صعوبة في التأكد")
        
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
            "search_time": 0,
            "similar_product": None
        }

class RealDatabaseManager:
    """مدير قاعدة بيانات واقعي"""
    
    def __init__(self, db_path="real_products.db"):
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
                similar_product TEXT,
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
                 deal_score, is_real_deal, confidence, recommendation, analysis_data, similar_product)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                json.dumps(analysis) if analysis else None,
                analysis.get('similar_product', '') if analysis else ''
            ))
            self.connection.commit()
        except Exception as e:
            print(f"Error saving product: {e}")
    
    def get_real_deals(self, min_score: float = 70) -> List[dict]:
        """الحصول على العروض الحقيقية"""
        cursor = self.connection.execute('''
            SELECT asin, name, url, img, section, current_price, strike_price, 
                   discount_percent, deal_score, confidence, recommendation, similar_product
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
                'recommendation': row[10],
                'similar_product': row[11]
            })
        
        return deals

# دالة اختبار شاملة
async def test_real_system():
    """اختبار النظام الواقعي"""
    print("🚀 اختبار النظام الواقعي...")
    
    # إنشاء المحلل
    analyzer = RealAIAnalyzer()
    db_manager = RealDatabaseManager()
    
    # منتجات تجريبية متنوعة
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
        },
        {
            "asin": "B0D1ABC456",
            "name": "MacBook Air M2 13-inch",
            "url": "https://www.amazon.eg/test4",
            "img": "https://test.com/image4.jpg",
            "section": "Electronics",
            "current_price": 42000,
            "strike_price": 48000,
            "discount_percent": 12
        },
        {
            "asin": "B0D2DEF789",
            "name": "iPad Pro 11-inch 128GB",
            "url": "https://www.amazon.eg/test5",
            "img": "https://test.com/image5.jpg",
            "section": "Electronics",
            "current_price": 26000,
            "strike_price": 32000,
            "discount_percent": 19
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
        
        if analysis['similar_product']:
            print(f"🔍 منتج مشابه: {analysis['similar_product']}")
        
        # عرض المنافسين
        if analysis['competitor_prices']:
            print(f"🏪 المنافسون ({analysis['competitors_count']}):")
            for retailer, price in analysis['competitor_prices'].items():
                print(f"   • {retailer}: {price:,.0f} جنيه")
        
        # عرض المخاطر
        if analysis['risk_factors']:
            print(f"⚠️ المخاطر:")
            for risk in analysis['risk_factors']:
                print(f"   • {risk}")
        
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
        if deal['similar_product']:
            print(f"     🔍 مشابه: {deal['similar_product']}")

if __name__ == "__main__":
    asyncio.run(test_real_system())