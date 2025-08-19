# ai_price_analyzer.py
# محرك AI ذكي لتحليل الأسعار ومقارنتها

import asyncio
import aiohttp
import re
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup
import sqlite3
from egyptian_retailers import EGYPTIAN_RETAILERS, get_search_query

@dataclass
class PriceComparison:
    """نتيجة مقارنة السعر"""
    retailer: str
    price: float
    currency: str = "EGP"
    confidence: float = 0.0
    url: str = ""
    in_stock: bool = True
    shipping_cost: float = 0.0

@dataclass
class DealAnalysis:
    """تحليل شامل للعرض"""
    amazon_price: float
    amazon_original_price: float
    amazon_discount: float
    competitor_prices: List[PriceComparison]
    average_market_price: float
    price_rank: int  # ترتيب أمازون بين المنافسين
    deal_score: float  # من 0 إلى 100
    is_real_deal: bool
    confidence: float
    recommendation: str
    risk_factors: List[str]

class AIPriceAnalyzer:
    """محلل الأسعار الذكي"""
    
    def __init__(self, db_path="price_analysis.db"):
        self.db_path = db_path
        self.session = None
        self.init_database()
        
    def init_database(self):
        """تهيئة قاعدة البيانات للتحليل"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول نتائج التحليل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT,
                product_name TEXT,
                amazon_price REAL,
                amazon_original_price REAL,
                amazon_discount REAL,
                average_market_price REAL,
                deal_score REAL,
                is_real_deal BOOLEAN,
                confidence REAL,
                recommendation TEXT,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول أسعار المنافسين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitor_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER,
                retailer TEXT,
                price REAL,
                confidence REAL,
                url TEXT,
                FOREIGN KEY (analysis_id) REFERENCES price_analysis (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def start_session(self):
        """بدء جلسة HTTP"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        """إغلاق جلسة HTTP"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def search_product_on_retailer(self, retailer_name: str, product_name: str, 
                                       category: str = None) -> List[PriceComparison]:
        """البحث عن منتج في موقع معين"""
        if retailer_name not in EGYPTIAN_RETAILERS:
            return []
        
        retailer = EGYPTIAN_RETAILERS[retailer_name]
        search_query = get_search_query(product_name, category)
        search_url = retailer["search_url"].format(query=search_query)
        
        try:
            await self.start_session()
            async with self.session.get(search_url, headers=retailer["headers"]) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                return self.parse_retailer_results(html, retailer, retailer_name)
                
        except Exception as e:
            print(f"Error searching {retailer_name}: {e}")
            return []
    
    def parse_retailer_results(self, html: str, retailer: dict, retailer_name: str) -> List[PriceComparison]:
        """تحليل نتائج البحث من موقع معين"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # البحث عن المنتجات في الصفحة
        product_elements = soup.select(retailer.get("product_container", ".product, .item"))
        
        for element in product_elements[:5]:  # أخذ أول 5 نتائج
            try:
                # استخراج السعر
                price_el = element.select_one(retailer["price_selector"])
                if not price_el:
                    continue
                
                price_text = price_el.get_text().strip()
                price = self.extract_price(price_text)
                if not price:
                    continue
                
                # استخراج الاسم
                name_el = element.select_one(retailer["name_selector"])
                name = name_el.get_text().strip() if name_el else ""
                
                # استخراج الرابط
                link_el = element.select_one(retailer["link_selector"])
                url = ""
                if link_el:
                    href = link_el.get("href", "")
                    if href.startswith("/"):
                        url = retailer["base_url"] + href
                    else:
                        url = href
                
                # حساب الثقة بناءً على تطابق الاسم
                confidence = self.calculate_name_similarity(name, product_name)
                
                if confidence > 0.3:  # فقط النتائج المتطابقة نسبياً
                    results.append(PriceComparison(
                        retailer=retailer_name,
                        price=price,
                        confidence=confidence,
                        url=url
                    ))
                    
            except Exception as e:
                print(f"Error parsing {retailer_name} result: {e}")
                continue
        
        return results
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """استخراج السعر من النص"""
        # إزالة الرموز والمسافات
        cleaned = re.sub(r'[^\d.,]', '', price_text)
        
        # تحويل الفاصلة العشرية
        if ',' in cleaned and '.' in cleaned:
            # تنسيق أوروبي: 1.234,56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            # تنسيق أمريكي: 1,234.56
            cleaned = cleaned.replace(',', '')
        
        try:
            return float(cleaned)
        except:
            return None
    
    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """حساب درجة تطابق الأسماء"""
        # تحويل إلى أحرف صغيرة
        name1 = name1.lower()
        name2 = name2.lower()
        
        # استخراج الكلمات المهمة
        words1 = set(re.findall(r'\b\w{3,}\b', name1))
        words2 = set(re.findall(r'\b\w{3,}\b', name2))
        
        if not words1 or not words2:
            return 0.0
        
        # حساب التداخل
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    async def analyze_deal(self, product_data: dict) -> DealAnalysis:
        """تحليل شامل للعرض"""
        product_name = product_data.get("name", "")
        amazon_price = product_data.get("price", 0)
        amazon_original_price = product_data.get("strike_price", amazon_price)
        amazon_discount = product_data.get("discount_percent", 0)
        category = product_data.get("section", "")
        
        # البحث في جميع المواقع
        all_prices = []
        tasks = []
        
        for retailer_name in EGYPTIAN_RETAILERS.keys():
            task = self.search_product_on_retailer(retailer_name, product_name, category)
            tasks.append(task)
        
        # انتظار جميع النتائج
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_prices.extend(result)
        
        # فلترة النتائج عالية الثقة
        high_confidence_prices = [p for p in all_prices if p.confidence > 0.5]
        
        if not high_confidence_prices:
            # إذا لم نجد نتائج عالية الثقة، نأخذ الأفضل
            high_confidence_prices = sorted(all_prices, key=lambda x: x.confidence, reverse=True)[:3]
        
        # حساب متوسط السعر في السوق
        if high_confidence_prices:
            market_prices = [p.price for p in high_confidence_prices if p.price > 0]
            average_market_price = sum(market_prices) / len(market_prices)
        else:
            average_market_price = amazon_price
        
        # ترتيب أمازون بين المنافسين
        price_rank = 1
        for price_comp in high_confidence_prices:
            if price_comp.price < amazon_price:
                price_rank += 1
        
        # حساب درجة العرض
        deal_score = self.calculate_deal_score(
            amazon_price, amazon_original_price, average_market_price,
            len(high_confidence_prices), price_rank
        )
        
        # تحديد ما إذا كان العرض حقيقي
        is_real_deal = self.is_real_deal(
            amazon_price, amazon_original_price, average_market_price,
            deal_score, len(high_confidence_prices)
        )
        
        # حساب مستوى الثقة
        confidence = self.calculate_confidence(high_confidence_prices, amazon_price)
        
        # التوصية
        recommendation = self.generate_recommendation(
            deal_score, price_rank, amazon_discount, len(high_confidence_prices)
        )
        
        # عوامل المخاطرة
        risk_factors = self.identify_risk_factors(
            amazon_price, amazon_original_price, high_confidence_prices
        )
        
        return DealAnalysis(
            amazon_price=amazon_price,
            amazon_original_price=amazon_original_price,
            amazon_discount=amazon_discount,
            competitor_prices=high_confidence_prices,
            average_market_price=average_market_price,
            price_rank=price_rank,
            deal_score=deal_score,
            is_real_deal=is_real_deal,
            confidence=confidence,
            recommendation=recommendation,
            risk_factors=risk_factors
        )
    
    def calculate_deal_score(self, current_price: float, original_price: float, 
                           market_price: float, competitors_count: int, 
                           price_rank: int) -> float:
        """حساب درجة العرض من 0 إلى 100"""
        score = 0.0
        
        # عامل الخصم (40%)
        if original_price > current_price:
            discount_percent = ((original_price - current_price) / original_price) * 100
            score += min(discount_percent * 0.4, 40)
        
        # عامل السعر مقارنة بالسوق (30%)
        if market_price > 0:
            market_savings = ((market_price - current_price) / market_price) * 100
            score += max(market_savings * 0.3, 0)
        
        # عامل عدد المنافسين (15%)
        score += min(competitors_count * 3, 15)
        
        # عامل الترتيب (15%)
        rank_score = max(15 - (price_rank - 1) * 2, 0)
        score += rank_score
        
        return min(score, 100)
    
    def is_real_deal(self, current_price: float, original_price: float, 
                    market_price: float, deal_score: float, 
                    competitors_count: int) -> bool:
        """تحديد ما إذا كان العرض حقيقي"""
        # شروط العرض الحقيقي
        conditions = [
            deal_score >= 60,  # درجة عالية
            competitors_count >= 2,  # مقارنة مع موقعين على الأقل
            current_price > 10,  # سعر معقول
            current_price < original_price * 0.9,  # خصم حقيقي
        ]
        
        # إذا كان السعر أقل من متوسط السوق
        if market_price > 0:
            conditions.append(current_price <= market_price * 0.95)
        
        return all(conditions)
    
    def calculate_confidence(self, competitor_prices: List[PriceComparison], 
                           amazon_price: float) -> float:
        """حساب مستوى الثقة في التحليل"""
        if not competitor_prices:
            return 0.3
        
        # متوسط ثقة النتائج
        avg_confidence = sum(p.confidence for p in competitor_prices) / len(competitor_prices)
        
        # عدد النتائج
        count_factor = min(len(competitor_prices) / 5, 1.0)
        
        # تناسق الأسعار
        prices = [p.price for p in competitor_prices if p.price > 0]
        if len(prices) > 1:
            price_variance = (max(prices) - min(prices)) / (sum(prices) / len(prices))
            consistency_factor = max(1 - price_variance, 0.5)
        else:
            consistency_factor = 0.7
        
        return (avg_confidence * 0.5 + count_factor * 0.3 + consistency_factor * 0.2)
    
    def generate_recommendation(self, deal_score: float, price_rank: int, 
                              discount_percent: float, competitors_count: int) -> str:
        """توليد توصية ذكية"""
        if deal_score >= 80:
            return "🔥 عرض استثنائي! سارع بالشراء"
        elif deal_score >= 60:
            return "🎉 عرض ممتاز، أنصح بالشراء"
        elif deal_score >= 40:
            return "✨ عرض جيد، فكر في الشراء"
        elif deal_score >= 20:
            return "📊 عرض عادي، انتظر عروض أفضل"
        else:
            return "⚠️ عرض ضعيف، لا أنصح بالشراء"
    
    def identify_risk_factors(self, current_price: float, original_price: float,
                            competitor_prices: List[PriceComparison]) -> List[str]:
        """تحديد عوامل المخاطرة"""
        risks = []
        
        if current_price < 20:
            risks.append("سعر منخفض جداً - قد يكون منتج رديء")
        
        if original_price > current_price * 3:
            risks.append("خصم كبير جداً - تحقق من جودة المنتج")
        
        if not competitor_prices:
            risks.append("لا توجد مقارنة كافية مع منافسين")
        
        # تحقق من تناسق الأسعار
        if competitor_prices:
            prices = [p.price for p in competitor_prices if p.price > 0]
            if len(prices) > 1:
                price_range = max(prices) - min(prices)
                if price_range > min(prices) * 0.5:
                    risks.append("تفاوت كبير في الأسعار بين المنافسين")
        
        return risks
    
    def save_analysis(self, asin: str, product_name: str, analysis: DealAnalysis):
        """حفظ نتائج التحليل في قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # حفظ التحليل الرئيسي
        cursor.execute('''
            INSERT INTO price_analysis 
            (asin, product_name, amazon_price, amazon_original_price, amazon_discount,
             average_market_price, deal_score, is_real_deal, confidence, recommendation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            asin, product_name, analysis.amazon_price, analysis.amazon_original_price,
            analysis.amazon_discount, analysis.average_market_price, analysis.deal_score,
            analysis.is_real_deal, analysis.confidence, analysis.recommendation
        ))
        
        analysis_id = cursor.lastrowid
        
        # حفظ أسعار المنافسين
        for comp in analysis.competitor_prices:
            cursor.execute('''
                INSERT INTO competitor_prices 
                (analysis_id, retailer, price, confidence, url)
                VALUES (?, ?, ?, ?, ?)
            ''', (analysis_id, comp.retailer, comp.price, comp.confidence, comp.url))
        
        conn.commit()
        conn.close()
    
    def get_analysis_summary(self, analysis: DealAnalysis) -> str:
        """توليد ملخص التحليل"""
        summary = f"""
🔍 **تحليل العرض الذكي**

💰 **السعر في أمازون**: {analysis.amazon_price:,.0f} جنيه
📉 **السعر الأصلي**: {analysis.amazon_original_price:,.0f} جنيه  
🎯 **نسبة الخصم**: {analysis.amazon_discount:.1f}%

📊 **مقارنة السوق**:
• متوسط السعر في السوق: {analysis.average_market_price:,.0f} جنيه
• ترتيب أمازون: {analysis.price_rank} من {len(analysis.competitor_prices) + 1}
• درجة العرض: {analysis.deal_score:.1f}/100

🎯 **التوصية**: {analysis.recommendation}

✅ **العرض حقيقي**: {'نعم' if analysis.is_real_deal else 'لا'}
🔒 **مستوى الثقة**: {analysis.confidence:.1%}

📋 **أسعار المنافسين**:
"""
        
        for comp in analysis.competitor_prices:
            summary += f"• {comp.retailer}: {comp.price:,.0f} جنيه (ثقة: {comp.confidence:.1%})\n"
        
        if analysis.risk_factors:
            summary += "\n⚠️ **عوامل المخاطرة**:\n"
            for risk in analysis.risk_factors:
                summary += f"• {risk}\n"
        
        return summary