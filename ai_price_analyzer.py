# ai_price_analyzer.py
# محلل AI سريع للعروض مع درجة ثقة 70%+

import asyncio
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from egyptian_retailers import EgyptianRetailerSearcher, calculate_name_similarity

@dataclass
class PriceComparison:
    """نتيجة مقارنة السعر"""
    retailer: str
    price: float
    similarity: float
    confidence: float

@dataclass
class DealAnalysis:
    """تحليل شامل للعرض"""
    amazon_price: float
    amazon_discount: float
    market_avg_price: float
    savings_percentage: float
    competitors_count: int
    deal_score: float
    is_real_deal: bool
    confidence: float
    recommendation: str
    risk_factors: List[str]
    price_comparisons: List[PriceComparison]
    analysis_time: float

class AIPriceAnalyzer:
    """محلل AI للأسعار والعروض"""
    
    def __init__(self, db_path="price_analysis.db"):
        self.db_path = db_path
        self.init_database()
        self.confidence_threshold = 0.70  # 70% درجة ثقة
        self.min_competitors = 2  # حد أدنى للمنافسين
        self.min_savings = 15  # حد أدنى للتوفير 15%
    
    def init_database(self):
        """تهيئة قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        
        # جدول تحليل الأسعار
        conn.execute('''
            CREATE TABLE IF NOT EXISTS price_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT,
                amazon_price REAL,
                amazon_discount REAL,
                market_avg_price REAL,
                savings_percentage REAL,
                competitors_count INTEGER,
                deal_score REAL,
                is_real_deal BOOLEAN,
                confidence REAL,
                recommendation TEXT,
                risk_factors TEXT,
                analysis_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول مقارنات الأسعار
        conn.execute('''
            CREATE TABLE IF NOT EXISTS competitor_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER,
                retailer TEXT,
                price REAL,
                similarity REAL,
                confidence REAL,
                FOREIGN KEY (analysis_id) REFERENCES price_analysis (id)
            )
        ''')
        
        # فهارس للسرعة
        conn.execute('CREATE INDEX IF NOT EXISTS idx_asin ON price_analysis(asin)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_score ON price_analysis(deal_score)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_is_real_deal ON price_analysis(is_real_deal)')
        
        conn.commit()
        conn.close()
    
    async def analyze_deal(self, product_data: dict) -> DealAnalysis:
        """تحليل شامل للعرض"""
        start_time = datetime.now()
        
        # استخراج بيانات المنتج
        asin = product_data.get('asin', '')
        product_name = product_data.get('name', '')
        amazon_price = product_data.get('current_price', 0)
        amazon_discount = product_data.get('discount_percent', 0)
        section = product_data.get('section', '')
        
        if not amazon_price or not product_name:
            return self._create_empty_analysis(amazon_price, amazon_discount)
        
        # البحث في المواقع المصرية
        async with EgyptianRetailerSearcher() as searcher:
            search_results = await searcher.search_all_retailers(product_name)
        
        # تحليل النتائج
        price_comparisons = self._analyze_search_results(search_results, product_name)
        
        # حساب الإحصائيات
        market_avg_price = self._calculate_market_average(price_comparisons)
        savings_percentage = self._calculate_savings(amazon_price, market_avg_price)
        competitors_count = len([p for p in price_comparisons if p.confidence >= self.confidence_threshold])
        
        # حساب درجة العرض
        deal_score = self._calculate_deal_score(
            amazon_discount, savings_percentage, competitors_count, price_comparisons
        )
        
        # تحديد إذا العرض حقيقي
        is_real_deal = self._is_real_deal(deal_score, competitors_count, savings_percentage)
        
        # حساب درجة الثقة
        confidence = self._calculate_confidence(price_comparisons, competitors_count)
        
        # إنشاء التوصية
        recommendation = self._generate_recommendation(deal_score, savings_percentage, competitors_count)
        
        # تحديد عوامل المخاطر
        risk_factors = self._identify_risk_factors(amazon_price, amazon_discount, price_comparisons)
        
        # حساب وقت التحليل
        analysis_time = (datetime.now() - start_time).total_seconds()
        
        # إنشاء نتيجة التحليل
        analysis = DealAnalysis(
            amazon_price=amazon_price,
            amazon_discount=amazon_discount,
            market_avg_price=market_avg_price,
            savings_percentage=savings_percentage,
            competitors_count=competitors_count,
            deal_score=deal_score,
            is_real_deal=is_real_deal,
            confidence=confidence,
            recommendation=recommendation,
            risk_factors=risk_factors,
            price_comparisons=price_comparisons,
            analysis_time=analysis_time
        )
        
        # حفظ التحليل
        self._save_analysis(asin, analysis)
        
        return analysis
    
    def _analyze_search_results(self, search_results: dict, product_name: str) -> List[PriceComparison]:
        """تحليل نتائج البحث"""
        price_comparisons = []
        
        for retailer, result in search_results['results'].items():
            if 'error' in result:
                continue
            
            best_match = result.get('best_match')
            if not best_match:
                continue
            
            # حساب درجة الثقة بناءً على التشابه
            similarity = best_match.get('similarity', 0)
            confidence = min(similarity * 1.2, 1.0)  # تحسين درجة الثقة
            
            # فلترة النتائج منخفضة الثقة
            if confidence < 0.3:  # 30% حد أدنى
                continue
            
            price_comparison = PriceComparison(
                retailer=retailer,
                price=best_match['price'],
                similarity=similarity,
                confidence=confidence
            )
            
            price_comparisons.append(price_comparison)
        
        # ترتيب حسب درجة الثقة
        price_comparisons.sort(key=lambda x: x.confidence, reverse=True)
        
        return price_comparisons
    
    def _calculate_market_average(self, price_comparisons: List[PriceComparison]) -> float:
        """حساب متوسط سعر السوق"""
        if not price_comparisons:
            return 0
        
        # استخدام فقط النتائج عالية الثقة
        high_confidence_prices = [
            p.price for p in price_comparisons 
            if p.confidence >= self.confidence_threshold
        ]
        
        if not high_confidence_prices:
            # استخدام جميع الأسعار إذا لم تكن هناك نتائج عالية الثقة
            high_confidence_prices = [p.price for p in price_comparisons]
        
        if not high_confidence_prices:
            return 0
        
        return sum(high_confidence_prices) / len(high_confidence_prices)
    
    def _calculate_savings(self, amazon_price: float, market_avg: float) -> float:
        """حساب نسبة التوفير"""
        if not market_avg or market_avg <= 0:
            return 0
        
        savings = ((market_avg - amazon_price) / market_avg) * 100
        return max(0, savings)
    
    def _calculate_deal_score(self, amazon_discount: float, savings_percentage: float, 
                            competitors_count: int, price_comparisons: List[PriceComparison]) -> float:
        """حساب درجة العرض (0-100)"""
        score = 0
        
        # 1. خصم أمازون (25%)
        amazon_discount_score = min(amazon_discount * 0.5, 25)
        score += amazon_discount_score
        
        # 2. التوفير من السوق (35%)
        market_savings_score = min(savings_percentage * 0.7, 35)
        score += market_savings_score
        
        # 3. عدد المنافسين (25%)
        competitors_score = min(competitors_count * 5, 25)
        score += competitors_score
        
        # 4. جودة المقارنة (15%)
        avg_confidence = sum(p.confidence for p in price_comparisons) / len(price_comparisons) if price_comparisons else 0
        confidence_score = avg_confidence * 15
        score += confidence_score
        
        return min(score, 100)
    
    def _is_real_deal(self, deal_score: float, competitors_count: int, savings_percentage: float) -> bool:
        """تحديد إذا العرض حقيقي"""
        # شروط العرض الحقيقي
        conditions = [
            deal_score >= 70,  # درجة عرض 70%+
            competitors_count >= self.min_competitors,  # 2+ منافس
            savings_percentage >= self.min_savings  # توفير 15%+
        ]
        
        return all(conditions)
    
    def _calculate_confidence(self, price_comparisons: List[PriceComparison], competitors_count: int) -> float:
        """حساب درجة الثقة الإجمالية"""
        if not price_comparisons:
            return 0
        
        # متوسط درجة الثقة للمقارنات
        avg_confidence = sum(p.confidence for p in price_comparisons) / len(price_comparisons)
        
        # عامل عدد المنافسين
        competitor_factor = min(competitors_count / 4, 1.0)
        
        # درجة الثقة النهائية
        final_confidence = (avg_confidence * 0.7) + (competitor_factor * 0.3)
        
        return min(final_confidence, 1.0)
    
    def _generate_recommendation(self, deal_score: float, savings_percentage: float, competitors_count: int) -> str:
        """إنشاء توصية ذكية"""
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
    
    def _identify_risk_factors(self, amazon_price: float, amazon_discount: float, 
                              price_comparisons: List[PriceComparison]) -> List[str]:
        """تحديد عوامل المخاطر"""
        risk_factors = []
        
        # سعر منخفض جداً
        if amazon_price < 50 and amazon_discount > 80:
            risk_factors.append("سعر منخفض جداً - قد يكون منتج مستعمل أو معيب")
        
        # خصم مفرط
        if amazon_discount > 90:
            risk_factors.append("خصم مفرط - قد يكون خطأ في السعر أو منتج منتهي الصلاحية")
        
        # قلة المنافسين
        high_confidence_count = len([p for p in price_comparisons if p.confidence >= self.confidence_threshold])
        if high_confidence_count < 2:
            risk_factors.append("قلة المنافسين - صعوبة في التأكد من جودة العرض")
        
        # تباين كبير في الأسعار
        if price_comparisons:
            prices = [p.price for p in price_comparisons if p.confidence >= 0.5]
            if len(prices) > 1:
                price_variance = (max(prices) - min(prices)) / min(prices)
                if price_variance > 0.5:  # تباين أكثر من 50%
                    risk_factors.append("تباين كبير في الأسعار - قد يكون اختلاف في المواصفات")
        
        return risk_factors
    
    def _create_empty_analysis(self, amazon_price: float, amazon_discount: float) -> DealAnalysis:
        """إنشاء تحليل فارغ"""
        return DealAnalysis(
            amazon_price=amazon_price,
            amazon_discount=amazon_discount,
            market_avg_price=0,
            savings_percentage=0,
            competitors_count=0,
            deal_score=0,
            is_real_deal=False,
            confidence=0,
            recommendation="لا توجد بيانات كافية للتحليل",
            risk_factors=["لا توجد مقارنات متاحة"],
            price_comparisons=[],
            analysis_time=0
        )
    
    def _save_analysis(self, asin: str, analysis: DealAnalysis):
        """حفظ التحليل في قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # حفظ التحليل الرئيسي
            cursor = conn.execute('''
                INSERT INTO price_analysis 
                (asin, amazon_price, amazon_discount, market_avg_price, savings_percentage,
                 competitors_count, deal_score, is_real_deal, confidence, recommendation,
                 risk_factors, analysis_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                asin, analysis.amazon_price, analysis.amazon_discount, analysis.market_avg_price,
                analysis.savings_percentage, analysis.competitors_count, analysis.deal_score,
                analysis.is_real_deal, analysis.confidence, analysis.recommendation,
                json.dumps(analysis.risk_factors), analysis.analysis_time
            ))
            
            analysis_id = cursor.lastrowid
            
            # حفظ مقارنات الأسعار
            for comparison in analysis.price_comparisons:
                conn.execute('''
                    INSERT INTO competitor_prices 
                    (analysis_id, retailer, price, similarity, confidence)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    analysis_id, comparison.retailer, comparison.price,
                    comparison.similarity, comparison.confidence
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error saving analysis: {e}")
    
    def get_analysis_summary(self, analysis: DealAnalysis) -> str:
        """إنشاء ملخص التحليل"""
        summary = f"""
🎯 تحليل العرض:
💰 سعر أمازون: {analysis.amazon_price:,.0f} جنيه
🎉 خصم أمازون: {analysis.amazon_discount:.1f}%
🏪 متوسط السوق: {analysis.market_avg_price:,.0f} جنيه
💡 التوفير: {analysis.savings_percentage:.1f}%
📊 درجة العرض: {analysis.deal_score:.1f}/100
✅ عرض حقيقي: {'نعم' if analysis.is_real_deal else 'لا'}
🎯 درجة الثقة: {analysis.confidence:.1%}
💬 التوصية: {analysis.recommendation}
⏱️ وقت التحليل: {analysis.analysis_time:.2f}s

🏪 المنافسون ({analysis.competitors_count}):
"""
        
        for comparison in analysis.price_comparisons[:3]:  # أول 3 منافسين
            summary += f"   • {comparison.retailer}: {comparison.price:,.0f} جنيه (ثقة: {comparison.confidence:.1%})\n"
        
        if analysis.risk_factors:
            summary += f"\n⚠️ عوامل المخاطر:\n"
            for risk in analysis.risk_factors:
                summary += f"   • {risk}\n"
        
        return summary

# دالة مساعدة للاختبار
async def test_analyzer():
    """اختبار المحلل"""
    analyzer = AIPriceAnalyzer()
    
    # منتج تجريبي
    test_product = {
        "asin": "B0C7CQT9ZS",
        "name": "Samsung Galaxy A54 5G",
        "current_price": 8500,
        "discount_percent": 25,
        "section": "Electronics"
    }
    
    print("🔍 بدء تحليل العرض...")
    analysis = await analyzer.analyze_deal(test_product)
    
    print(analyzer.get_analysis_summary(analysis))

if __name__ == "__main__":
    asyncio.run(test_analyzer())