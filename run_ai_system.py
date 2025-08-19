# run_ai_system.py
# ملف تشغيل مبسط لنظام AI العروض

import asyncio
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import time
import random

class SimplePriceSearcher:
    """محلل أسعار مبسط مع بيانات تجريبية"""
    
    def __init__(self):
        # بيانات تجريبية واقعية
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
            }
        }
    
    def find_similar_product(self, product_name: str) -> Optional[str]:
        """البحث عن منتج مشابه"""
        product_name_lower = product_name.lower()
        
        for mock_product in self.mock_prices.keys():
            mock_lower = mock_product.lower()
            
            # حساب التشابه
            common_words = 0
            total_words = 0
            
            for word in product_name_lower.split():
                if len(word) > 2:
                    total_words += 1
                    if word in mock_lower:
                        common_words += 1
            
            if total_words > 0 and (common_words / total_words) >= 0.3:
                return mock_product
        
        return None
    
    async def search_retailers(self, product_name: str) -> Dict:
        """البحث في المواقع"""
        print(f"🔍 البحث عن: {product_name}")
        start_time = time.time()
        
        similar_product = self.find_similar_product(product_name)
        
        if similar_product:
            prices = self.mock_prices[similar_product].copy()
            
            # تغييرات عشوائية للواقعية
            for retailer in prices:
                variation = random.uniform(-0.05, 0.05)
                prices[retailer] = int(prices[retailer] * (1 + variation))
            
            # محاكاة بعض المواقع التي لا تعمل
            if random.random() < 0.2:
                if "Pricena" in prices:
                    del prices["Pricena"]
            
            if random.random() < 0.15:
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

class SimpleAIAnalyzer:
    """محلل AI مبسط"""
    
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
        searcher = SimplePriceSearcher()
        search_results = await searcher.search_retailers(product_name)
        
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
        
        success_rate = competitors / total_searched
        competitor_factor = min(competitors / 4, 1.0)
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

def main():
    """الدالة الرئيسية"""
    print("🚀 LAQTA AI - محلل العروض الذكي")
    print("=" * 50)
    
    # إنشاء المحلل
    analyzer = SimpleAIAnalyzer()
    
    while True:
        print("\n🔍 تحليل منتج جديد:")
        print("-" * 30)
        
        # إدخال البيانات
        product_name = input("اسم المنتج: ").strip()
        if not product_name:
            print("❌ يرجى إدخال اسم المنتج")
            continue
        
        try:
            current_price = float(input("السعر الحالي (جنيه): ").strip())
            original_price = float(input("السعر الأصلي (جنيه): ").strip())
        except ValueError:
            print("❌ يرجى إدخال أسعار صحيحة")
            continue
        
        # حساب نسبة الخصم
        discount_percent = ((original_price - current_price) / original_price) * 100
        
        # إنشاء بيانات المنتج
        product_data = {
            "asin": f"B{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": product_name,
            "url": "",
            "img": "",
            "section": "Electronics",
            "current_price": current_price,
            "strike_price": original_price,
            "discount_percent": discount_percent
        }
        
        print(f"\n🎯 تحليل: {product_name}")
        print(f"💰 سعر أمازون: {current_price:,.0f} جنيه")
        print(f"🎉 خصم أمازون: {discount_percent:.1f}%")
        
        # تحليل المنتج
        analysis = asyncio.run(analyzer.analyze_deal(product_data))
        
        # عرض النتائج
        print(f"\n🏪 متوسط السوق: {analysis['market_avg_price']:,.0f} جنيه")
        print(f"💡 التوفير: {analysis['savings_percentage']:.1f}%")
        print(f"📊 درجة العرض: {analysis['deal_score']:.1f}/100")
        print(f"✅ عرض حقيقي: {'نعم' if analysis['is_real_deal'] else 'لا'}")
        print(f"🎯 درجة الثقة: {analysis['confidence']:.1%}")
        print(f"💬 التوصية: {analysis['recommendation']}")
        
        if analysis['similar_product']:
            print(f"🔍 منتج مشابه: {analysis['similar_product']}")
        
        # عرض المنافسين
        if analysis['competitor_prices']:
            print(f"\n🏪 المنافسون ({analysis['competitors_count']}):")
            for retailer, price in analysis['competitor_prices'].items():
                print(f"   • {retailer}: {price:,.0f} جنيه")
        
        # عرض المخاطر
        if analysis['risk_factors']:
            print(f"\n⚠️ المخاطر:")
            for risk in analysis['risk_factors']:
                print(f"   • {risk}")
        
        print(f"\n⏱️ وقت التحليل: {analysis['analysis_time']:.2f}s")
        print("=" * 50)
        
        # السؤال عن المتابعة
        continue_analysis = input("\nهل تريد تحليل منتج آخر؟ (y/n): ").strip().lower()
        if continue_analysis not in ['y', 'yes', 'نعم', 'ن']:
            break
    
    print("\n🎉 شكراً لاستخدام LAQTA AI!")

if __name__ == "__main__":
    main()