import requests
import json
import sqlite3
import asyncio
import aiohttp
from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import time

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PriceComparison:
    """نتيجة مقارنة السعر"""
    website: str
    price: float
    currency: str = "EGP"
    availability: bool = True
    shipping_cost: float = 0.0
    total_price: float = 0.0
    confidence: float = 0.8
    last_checked: datetime = None
    
    def __post_init__(self):
        if self.last_checked is None:
            self.last_checked = datetime.now()
        self.total_price = self.price + self.shipping_cost

@dataclass
class DealAnalysis:
    """تحليل شامل للعرض"""
    product_name: str
    amazon_price: float
    market_average: float
    best_alternative_price: float
    best_alternative_website: str
    price_difference: float
    price_difference_percent: float
    is_good_deal: bool
    confidence_score: float
    recommendations: List[str]
    price_comparisons: List[PriceComparison]
    analysis_summary: str

class EgyptianMarketScraper:
    """سكرابر للمواقع المصرية الشهيرة"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # المواقع المصرية الشهيرة
        self.egyptian_sites = {
            'jumia': {
                'base_url': 'https://www.jumia.com.eg',
                'search_url': 'https://www.jumia.com.eg/catalog/?q={query}',
                'enabled': True
            },
            'noon': {
                'base_url': 'https://www.noon.com',
                'search_url': 'https://www.noon.com/egypt-en/search?q={query}',
                'enabled': True
            },
            'souq': {
                'base_url': 'https://egypt.souq.com',
                'search_url': 'https://egypt.souq.com/eg-en/search?q={query}',
                'enabled': False  # تم إغلاقه
            },
            'olx': {
                'base_url': 'https://www.olx.com.eg',
                'search_url': 'https://www.olx.com.eg/items/q-{query}',
                'enabled': True
            },
            'amazon_eg': {
                'base_url': 'https://www.amazon.eg',
                'search_url': 'https://www.amazon.eg/s?k={query}',
                'enabled': True
            }
        }
    
    async def search_product(self, product_name: str) -> List[PriceComparison]:
        """البحث عن المنتج في المواقع المصرية"""
        comparisons = []
        
        # تنظيف اسم المنتج للبحث
        search_query = self._clean_product_name(product_name)
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for site_name, site_config in self.egyptian_sites.items():
                if site_config['enabled']:
                    task = self._search_site(session, site_name, site_config, search_query)
                    tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, PriceComparison):
                    comparisons.append(result)
        
        return comparisons
    
    def _clean_product_name(self, name: str) -> str:
        """تنظيف اسم المنتج للبحث"""
        # إزالة الكلمات غير المهمة
        stop_words = ['من', 'لل', 'مع', 'و', 'في', 'على', 'إلى', 'عن', 'حول', 'خلال', 'أثناء']
        
        # إزالة الكلمات الإنجليزية غير المهمة
        english_stop_words = ['with', 'and', 'for', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'of']
        
        # تنظيف النص
        cleaned = re.sub(r'[^\w\s]', ' ', name)
        words = cleaned.split()
        
        # إزالة الكلمات القصيرة جداً
        words = [word for word in words if len(word) > 2]
        
        # إزالة الكلمات غير المهمة
        words = [word for word in words if word.lower() not in english_stop_words]
        
        return ' '.join(words[:5])  # أخذ أول 5 كلمات فقط
    
    async def _search_site(self, session: aiohttp.ClientSession, site_name: str, 
                          site_config: dict, query: str) -> Optional[PriceComparison]:
        """البحث في موقع محدد"""
        try:
            search_url = site_config['search_url'].format(query=query)
            
            async with session.get(search_url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_site_results(site_name, html, query)
                else:
                    logger.warning(f"Failed to search {site_name}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error searching {site_name}: {e}")
            return None
    
    def _parse_site_results(self, site_name: str, html: str, query: str) -> Optional[PriceComparison]:
        """تحليل نتائج البحث من الموقع"""
        try:
            if site_name == 'jumia':
                return self._parse_jumia(html)
            elif site_name == 'noon':
                return self._parse_noon(html)
            elif site_name == 'olx':
                return self._parse_olx(html)
            elif site_name == 'amazon_eg':
                return self._parse_amazon_eg(html)
            else:
                return None
        except Exception as e:
            logger.error(f"Error parsing {site_name}: {e}")
            return None
    
    def _parse_jumia(self, html: str) -> Optional[PriceComparison]:
        """تحليل نتائج Jumia"""
        try:
            # البحث عن السعر في HTML
            price_pattern = r'data-price="([^"]+)"'
            price_match = re.search(price_pattern, html)
            
            if price_match:
                price = float(price_match.group(1))
                return PriceComparison(
                    website="Jumia",
                    price=price,
                    confidence=0.9
                )
        except:
            pass
        return None
    
    def _parse_noon(self, html: str) -> Optional[PriceComparison]:
        """تحليل نتائج Noon"""
        try:
            # البحث عن السعر في HTML
            price_pattern = r'"price":\s*"([^"]+)"'
            price_match = re.search(price_pattern, html)
            
            if price_match:
                price = float(price_match.group(1))
                return PriceComparison(
                    website="Noon",
                    price=price,
                    confidence=0.85
                )
        except:
            pass
        return None
    
    def _parse_olx(self, html: str) -> Optional[PriceComparison]:
        """تحليل نتائج OLX"""
        try:
            # البحث عن السعر في HTML
            price_pattern = r'data-price="([^"]+)"'
            price_match = re.search(price_pattern, html)
            
            if price_match:
                price = float(price_match.group(1))
                return PriceComparison(
                    website="OLX",
                    price=price,
                    confidence=0.7  # ثقة أقل لأن OLX مستخدمين عاديين
                )
        except:
            pass
        return None
    
    def _parse_amazon_eg(self, html: str) -> Optional[PriceComparison]:
        """تحليل نتائج Amazon Egypt"""
        try:
            # البحث عن السعر في HTML
            price_pattern = r'data-price="([^"]+)"'
            price_match = re.search(price_pattern, html)
            
            if price_match:
                price = float(price_match.group(1))
                return PriceComparison(
                    website="Amazon Egypt",
                    price=price,
                    confidence=0.95
                )
        except:
            pass
        return None

class AIPriceAnalyzer:
    """محلل الأسعار الذكي"""
    
    def __init__(self, db_path: str = "amz_products.db"):
        self.db_path = db_path
        self.market_scraper = EgyptianMarketScraper()
        self.cache = {}
        self.cache_duration = timedelta(hours=1)
    
    def analyze_deal(self, product_data: dict) -> DealAnalysis:
        """تحليل شامل للعرض"""
        try:
            # استخراج البيانات الأساسية
            product_name = product_data.get('name', '')
            amazon_price = product_data.get('price', 0)
            discount_percent = product_data.get('discount_percent', 0)
            
            if not product_name or amazon_price <= 0:
                return self._create_empty_analysis(product_name, amazon_price)
            
            # البحث عن الأسعار في السوق المصري
            price_comparisons = asyncio.run(
                self.market_scraper.search_product(product_name)
            )
            
            # تحليل الأسعار
            analysis = self._analyze_prices(amazon_price, price_comparisons, discount_percent)
            
            # إنشاء التوصيات
            recommendations = self._generate_recommendations(analysis, price_comparisons)
            
            # إنشاء ملخص التحليل
            summary = self._create_analysis_summary(analysis, recommendations)
            
            return DealAnalysis(
                product_name=product_name,
                amazon_price=amazon_price,
                market_average=analysis['market_average'],
                best_alternative_price=analysis['best_alternative_price'],
                best_alternative_website=analysis['best_alternative_website'],
                price_difference=analysis['price_difference'],
                price_difference_percent=analysis['price_difference_percent'],
                is_good_deal=analysis['is_good_deal'],
                confidence_score=analysis['confidence_score'],
                recommendations=recommendations,
                price_comparisons=price_comparisons,
                analysis_summary=summary
            )
            
        except Exception as e:
            logger.error(f"Error analyzing deal: {e}")
            return self._create_empty_analysis(product_data.get('name', ''), product_data.get('price', 0))
    
    def _analyze_prices(self, amazon_price: float, comparisons: List[PriceComparison], 
                       discount_percent: float) -> dict:
        """تحليل الأسعار ومقارنتها"""
        
        if not comparisons:
            return {
                'market_average': amazon_price,
                'best_alternative_price': amazon_price,
                'best_alternative_website': 'Amazon',
                'price_difference': 0,
                'price_difference_percent': 0,
                'is_good_deal': discount_percent >= 30,
                'confidence_score': 0.5
            }
        
        # حساب المتوسط السوقي
        valid_prices = [comp.total_price for comp in comparisons if comp.total_price > 0]
        if valid_prices:
            market_average = sum(valid_prices) / len(valid_prices)
        else:
            market_average = amazon_price
        
        # أفضل سعر بديل
        best_comparison = min(comparisons, key=lambda x: x.total_price)
        best_alternative_price = best_comparison.total_price
        best_alternative_website = best_comparison.website
        
        # حساب الفرق
        price_difference = best_alternative_price - amazon_price
        price_difference_percent = (price_difference / best_alternative_price) * 100 if best_alternative_price > 0 else 0
        
        # تقييم العرض
        is_good_deal = self._evaluate_deal_quality(
            amazon_price, best_alternative_price, discount_percent, price_difference_percent
        )
        
        # حساب درجة الثقة
        confidence_score = self._calculate_confidence(comparisons)
        
        return {
            'market_average': market_average,
            'best_alternative_price': best_alternative_price,
            'best_alternative_website': best_alternative_website,
            'price_difference': price_difference,
            'price_difference_percent': price_difference_percent,
            'is_good_deal': is_good_deal,
            'confidence_score': confidence_score
        }
    
    def _evaluate_deal_quality(self, amazon_price: float, best_alternative: float, 
                              discount_percent: float, price_diff_percent: float) -> bool:
        """تقييم جودة العرض"""
        
        # معايير التقييم
        criteria = [
            discount_percent >= 25,  # خصم 25% على الأقل
            price_diff_percent >= 10,  # أرخص من السوق بـ 10% على الأقل
            amazon_price < best_alternative,  # أرخص من البديل
            discount_percent < 95  # ليس خصم مريب
        ]
        
        # يجب أن يتحقق 3 معايير على الأقل
        return sum(criteria) >= 3
    
    def _calculate_confidence(self, comparisons: List[PriceComparison]) -> float:
        """حساب درجة الثقة في التحليل"""
        if not comparisons:
            return 0.3
        
        # متوسط درجة الثقة
        avg_confidence = sum(comp.confidence for comp in comparisons) / len(comparisons)
        
        # تعديل حسب عدد المقارنات
        confidence_multiplier = min(len(comparisons) / 3, 1.0)
        
        return avg_confidence * confidence_multiplier
    
    def _generate_recommendations(self, analysis: dict, comparisons: List[PriceComparison]) -> List[str]:
        """إنشاء التوصيات"""
        recommendations = []
        
        if analysis['is_good_deal']:
            recommendations.append("✅ عرض ممتاز - سعر جيد مقارنة بالسوق")
            
            if analysis['price_difference_percent'] >= 20:
                recommendations.append("🔥 توفير كبير - أرخص من السوق بـ 20%+")
            
            if analysis['confidence_score'] >= 0.8:
                recommendations.append("🎯 تحليل موثوق - بيانات دقيقة")
        else:
            recommendations.append("⚠️ عرض عادي - يمكن إيجاد أفضل")
            
            if analysis['price_difference_percent'] < 0:
                recommendations.append("💸 أغلى من السوق - ابحث عن بدائل")
        
        # توصيات إضافية
        if len(comparisons) < 2:
            recommendations.append("📊 بيانات محدودة - تحقق من مواقع أخرى")
        
        return recommendations
    
    def _create_analysis_summary(self, analysis: dict, recommendations: List[str]) -> str:
        """إنشاء ملخص التحليل"""
        summary = f"تحليل السعر: {analysis['price_difference_percent']:.1f}% "
        
        if analysis['is_good_deal']:
            summary += "✅ عرض جيد"
        else:
            summary += "⚠️ عرض عادي"
        
        summary += f" | الثقة: {analysis['confidence_score']:.1f}"
        
        return summary
    
    def _create_empty_analysis(self, product_name: str, amazon_price: float) -> DealAnalysis:
        """إنشاء تحليل فارغ"""
        return DealAnalysis(
            product_name=product_name,
            amazon_price=amazon_price,
            market_average=amazon_price,
            best_alternative_price=amazon_price,
            best_alternative_website="Amazon",
            price_difference=0,
            price_difference_percent=0,
            is_good_deal=False,
            confidence_score=0.0,
            recommendations=["❌ لا توجد بيانات كافية للتحليل"],
            price_comparisons=[],
            analysis_summary="❌ تحليل غير متاح"
        )
    
    def get_top_deals(self, min_discount: float = 20, limit: int = 10) -> List[DealAnalysis]:
        """الحصول على أفضل العروض"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # جلب المنتجات المخفضة
            cursor.execute('''
                SELECT asin, name, url, img, section, current_price, 
                       strike_price, discount_percent, last_updated
                FROM products 
                WHERE discount_percent >= ? AND discount_percent <= 95
                ORDER BY discount_percent DESC, current_price ASC
                LIMIT ?
            ''', (min_discount, limit * 2))  # جلب ضعف العدد للتحليل
            
            products = cursor.fetchall()
            conn.close()
            
            # تحليل كل منتج
            analyzed_deals = []
            for product in products:
                product_data = {
                    'asin': product[0],
                    'name': product[1],
                    'url': product[2],
                    'img': product[3],
                    'section': product[4],
                    'price': product[5],
                    'strike_price': product[6],
                    'discount_percent': product[7]
                }
                
                analysis = self.analyze_deal(product_data)
                if analysis.is_good_deal:
                    analyzed_deals.append(analysis)
                
                # إيقاف مؤقت لتجنب حظر IP
                time.sleep(1)
            
            # ترتيب حسب جودة العرض
            analyzed_deals.sort(key=lambda x: x.confidence_score * x.price_difference_percent, reverse=True)
            
            return analyzed_deals[:limit]
            
        except Exception as e:
            logger.error(f"Error getting top deals: {e}")
            return []

# مثال للاستخدام
if __name__ == "__main__":
    analyzer = AIPriceAnalyzer()
    
    # تحليل منتج معين
    product_data = {
        "name": "ماكينة حلاقة متعددة الاستخدامات 10 في 1 للرجال من بيبي ليس",
        "price": 847.92,
        "discount_percent": 30
    }
    
    analysis = analyzer.analyze_deal(product_data)
    print(f"تحليل العرض: {analysis.analysis_summary}")
    print(f"التوصيات: {analysis.recommendations}")
    
    # الحصول على أفضل العروض
    top_deals = analyzer.get_top_deals(min_discount=25, limit=5)
    print(f"\nأفضل 5 عروض:")
    for i, deal in enumerate(top_deals, 1):
        print(f"{i}. {deal.product_name[:50]}... - {deal.analysis_summary}")