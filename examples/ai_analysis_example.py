#!/usr/bin/env python3
"""
AI Analysis Example - مثال تحليل الذكاء الاصطناعي
"""

import sys
import os

# إضافة المجلد الأب إلى Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_price_analyzer import AIPriceAnalyzer

def main():
    """مثال تحليل AI للأسعار"""
    
    print("🤖 AI Deals Manager - AI Analysis Example")
    print("=" * 50)
    
    try:
        # إنشاء محلل AI
        print("🧠 Creating AI Price Analyzer...")
        analyzer = AIPriceAnalyzer()
        
        # منتجات تجريبية للتحليل
        test_products = [
            {
                "name": "ماكينة حلاقة متعددة الاستخدامات 10 في 1 للرجال من بيبي ليس، مجموعة أدوات تهذيب وحلاقة لاسلكية من التيتانيوم الكربوني مع شفرات بعرض 34 ملم، مرفقات للأنف/الأذن/الجسم ورؤوس قابلة للغسيل",
                "price": 847.92,
                "discount_percent": 30
            },
            {
                "name": "سماعات بلوتوث لاسلكية Anker Soundcore",
                "price": 299.99,
                "discount_percent": 40
            },
            {
                "name": "هاتف ذكي Samsung Galaxy",
                "price": 8999.99,
                "discount_percent": 25
            },
            {
                "name": "لابتوب Dell Inspiron",
                "price": 15999.99,
                "discount_percent": 15
            },
            {
                "name": "ساعة ذكية Apple Watch",
                "price": 4999.99,
                "discount_percent": 50
            }
        ]
        
        print(f"\n📦 Analyzing {len(test_products)} products...")
        
        # تحليل كل منتج
        for i, product_data in enumerate(test_products, 1):
            print(f"\n🔍 Analyzing product {i}: {product_data['name'][:50]}...")
            
            try:
                # تحليل المنتج
                analysis = analyzer.analyze_deal(product_data)
                
                # عرض النتائج
                print(f"   💰 Amazon Price: {product_data['price']:,.0f} EGP")
                print(f"   📉 Discount: {product_data['discount_percent']:.1f}%")
                print(f"   📊 Market Average: {analysis.market_average:,.0f} EGP")
                print(f"   🏪 Best Alternative: {analysis.best_alternative_price:,.0f} EGP ({analysis.best_alternative_website})")
                print(f"   💡 Price Difference: {analysis.price_difference_percent:+.1f}%")
                print(f"   🎯 AI Confidence: {analysis.confidence_score:.2f}")
                print(f"   ✅ Is Good Deal: {'Yes' if analysis.is_good_deal else 'No'}")
                
                # عرض التوصيات
                if analysis.recommendations:
                    print(f"   💡 AI Recommendations:")
                    for rec in analysis.recommendations:
                        print(f"      • {rec}")
                
                print(f"   📝 Summary: {analysis.analysis_summary}")
                
                # تقييم جودة التحليل
                if analysis.confidence_score >= 0.8:
                    print(f"   🎯 High confidence analysis")
                elif analysis.confidence_score >= 0.6:
                    print(f"   ✅ Good confidence analysis")
                else:
                    print(f"   ⚠️ Low confidence analysis")
                
            except Exception as e:
                print(f"   ❌ Analysis failed: {e}")
        
        # تحليل إحصائي
        print(f"\n📈 Analysis Summary:")
        print(f"   Total products analyzed: {len(test_products)}")
        
        # حساب متوسط درجة الثقة
        confidence_scores = []
        good_deals = 0
        
        for product_data in test_products:
            try:
                analysis = analyzer.analyze_deal(product_data)
                confidence_scores.append(analysis.confidence_score)
                if analysis.is_good_deal:
                    good_deals += 1
            except:
                pass
        
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            print(f"   Average AI confidence: {avg_confidence:.2f}")
            print(f"   Good deals found: {good_deals}/{len(test_products)}")
            print(f"   Success rate: {(good_deals/len(test_products)*100):.1f}%")
        
        # اختبار الحصول على أفضل العروض
        print(f"\n🏆 Getting top AI deals...")
        try:
            top_deals = analyzer.get_top_deals(min_discount=20, limit=3)
            if top_deals:
                print(f"   Found {len(top_deals)} top deals:")
                for i, deal in enumerate(top_deals, 1):
                    print(f"   {i}. {deal.product_name[:50]}...")
                    print(f"      💰 Price: {deal.amazon_price:,.0f} EGP")
                    print(f"      🎯 AI Score: {deal.confidence_score:.2f}")
            else:
                print("   No top deals found in database")
        except Exception as e:
            print(f"   ❌ Failed to get top deals: {e}")
        
        print(f"\n✅ AI analysis example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)