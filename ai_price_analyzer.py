# ai_price_analyzer.py
import google.generativeai as genai
import requests
import json
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import quote
import sqlite3
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import Dict, List, Tuple, Optional

# إعداد الـ logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIAnalyzer:
    """نظام AI لتحليل العروض ومقارنة الأسعار"""
    
    def __init__(self, api_key: str):
        """تهيئة نظام AI"""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.lock = threading.Lock()
        
        # مواقع مقارنة الأسعار المصرية
        self.egyptian_sites = {
            'jumia': 'https://www.jumia.com.eg/catalog/?q={}',
            'noon': 'https://www.noon.com/egypt-en/search?q={}',
            'btech': 'https://www.b-tech.com.eg/search?q={}',
            'amazon': 'https://www.amazon.eg/s?k={}',
            'souq': 'https://egypt.souq.com/eg-en/search/?q={}',
            'carrefour': 'https://www.carrefouregypt.com/mafegy/en/search/?text={}',
            'spinneys': 'https://spinneys-egypt.com/search?q={}',
            'kazyon': 'https://kazyon.com/search?q={}'
        }
        
        # headers للـ requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive',
        }
    
    def analyze_deal_quality(self, product_data: Dict) -> Dict:
        """تحليل جودة العرض باستخدام AI"""
        try:
            product_name = product_data.get('name', '')
            current_price = product_data.get('current_price', 0)
            strike_price = product_data.get('strike_price', 0)
            discount_percent = product_data.get('discount_percent', 0)
            section = product_data.get('section', '')
            
            # إنشاء prompt للـ AI
            prompt = f"""
            أنت خبير في تحليل العروض والأسعار في السوق المصري. 
            قم بتحليل هذا المنتج وتحديد ما إذا كان العرض حقيقي أم وهمي:

            اسم المنتج: {product_name}
            القسم: {section}
            السعر الحالي: {current_price} جنيه مصري
            السعر المشطوب: {strike_price} جنيه مصري  
            نسبة الخصم: {discount_percent:.1f}%

            أريد منك تحليل العرض من النواحي التالية:
            1. هل نسبة الخصم منطقية أم مبالغ فيها؟
            2. هل السعر الحالي معقول لهذا النوع من المنتجات؟
            3. هل يبدو العرض حقيقي أم مجرد خدعة تسويقية؟
            4. ما هو تقييمك للعرض من 1 إلى 10؟

            أجب بتنسيق JSON:
            {{
                "is_real_deal": true/false,
                "quality_score": 1-10,
                "analysis": "تحليل مفصل",
                "recommendation": "توصية للمشتري",
                "price_range": "النطاق السعري المتوقع",
                "deal_type": "نوع العرض (ممتاز/جيد/عادي/مشكوك)"
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # استخراج JSON من الاستجابة
            response_text = response.text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                try:
                    analysis = json.loads(json_match.group())
                    return analysis
                except json.JSONDecodeError:
                    logger.error("Error parsing AI response JSON")
                    return self._default_analysis()
            else:
                logger.error("No JSON found in AI response")
                return self._default_analysis()
                
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return self._default_analysis()
    
    def _default_analysis(self) -> Dict:
        """تحليل افتراضي في حالة فشل AI"""
        return {
            "is_real_deal": False,
            "quality_score": 1,
            "analysis": "فشل في التحليل - يحتاج مراجعة يدوية",
            "recommendation": "ينصح بمراجعة السعر يدوياً",
            "price_range": "غير محدد",
            "deal_type": "غير محدد"
        }
    
    def search_product_prices(self, product_name: str, max_sites: int = 5) -> List[Dict]:
        """البحث عن أسعار المنتج في المواقع المصرية"""
        search_results = []
        product_keywords = self._extract_keywords(product_name)
        
        def search_site(site_name, search_url):
            try:
                formatted_url = search_url.format(quote(product_keywords))
                response = requests.get(formatted_url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    price_info = self._extract_price_from_site(site_name, soup)
                    
                    if price_info:
                        return {
                            'site': site_name,
                            'price': price_info['price'],
                            'url': formatted_url,
                            'product_title': price_info.get('title', ''),
                            'availability': price_info.get('availability', 'unknown')
                        }
                        
            except Exception as e:
                logger.error(f"Error searching {site_name}: {e}")
                
            return None
        
        # البحث المتوازي في المواقع
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            sites_to_search = list(self.egyptian_sites.items())[:max_sites]
            
            for site_name, search_url in sites_to_search:
                future = executor.submit(search_site, site_name, search_url)
                futures.append(future)
            
            for future in as_completed(futures, timeout=30):
                try:
                    result = future.result()
                    if result:
                        search_results.append(result)
                except Exception as e:
                    logger.error(f"Future execution error: {e}")
        
        return search_results
    
    def _extract_keywords(self, product_name: str) -> str:
        """استخراج الكلمات المفتاحية من اسم المنتج"""
        # إزالة الكلمات غير المهمة
        stop_words = ['من', 'في', 'على', 'مع', 'إلى', 'عن', 'كما', 'هذا', 'هذه', 'ذلك', 'تلك']
        
        # تنظيف النص
        cleaned_name = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', product_name)
        words = cleaned_name.split()
        
        # الاحتفاظ بالكلمات المهمة فقط (أول 5 كلمات غير محذوفة)
        keywords = [word for word in words if word.lower() not in stop_words][:5]
        
        return ' '.join(keywords)
    
    def _extract_price_from_site(self, site_name: str, soup: BeautifulSoup) -> Optional[Dict]:
        """استخراج السعر من موقع معين"""
        price_selectors = {
            'jumia': ['.prc', '.price', '.product-price'],
            'noon': ['.priceNow', '.price-now', '.price'],
            'btech': ['.price', '.product-price', '.current-price'],
            'amazon': ['.a-price-whole', '.a-offscreen', '.price'],
            'souq': ['.price', '.product-price'],
            'carrefour': ['.price', '.product-price'],
            'spinneys': ['.price', '.product-price'],
            'kazyon': ['.price', '.product-price']
        }
        
        selectors = price_selectors.get(site_name, ['.price', '.product-price'])
        
        for selector in selectors:
            price_elements = soup.select(selector)
            if price_elements:
                for element in price_elements[:3]:  # فحص أول 3 عناصر
                    price_text = element.get_text(strip=True)
                    price = self._extract_price_number(price_text)
                    if price and price > 0:
                        title_element = soup.find('h1') or soup.find('title') or soup.find('.product-title')
                        title = title_element.get_text(strip=True) if title_element else ''
                        
                        return {
                            'price': price,
                            'title': title[:100],
                            'availability': 'available'
                        }
        
        return None
    
    def _extract_price_number(self, price_text: str) -> Optional[float]:
        """استخراج رقم السعر من النص"""
        try:
            # إزالة العملات والرموز
            cleaned_text = re.sub(r'[^\d.,]', '', price_text)
            cleaned_text = cleaned_text.replace(',', '')
            
            # البحث عن أرقام
            numbers = re.findall(r'\d+\.?\d*', cleaned_text)
            if numbers:
                return float(numbers[0])
                
        except Exception:
            pass
            
        return None
    
    def compare_prices_with_ai(self, product_name: str, amazon_price: float, 
                              comparison_results: List[Dict]) -> Dict:
        """مقارنة الأسعار باستخدام AI"""
        try:
            if not comparison_results:
                return {
                    "comparison": "لم يتم العثور على أسعار للمقارنة",
                    "verdict": "غير قابل للمقارنة",
                    "score": 5
                }
            
            # إنشاء قائمة الأسعار
            prices_text = f"سعر أمازون: {amazon_price} جنيه\n"
            for result in comparison_results:
                prices_text += f"{result['site']}: {result['price']} جنيه\n"
            
            prompt = f"""
            قم بمقارنة أسعار هذا المنتج في المواقع المصرية:
            
            المنتج: {product_name}
            
            الأسعار:
            {prices_text}
            
            أريد منك تحليل:
            1. هل سعر أمازون جيد مقارنة بالمواقع الأخرى؟
            2. ما هو أفضل سعر متاح؟
            3. هل يستحق الشراء من أمازون؟
            4. تقييم العرض من 1 إلى 10
            
            أجب بتنسيق JSON:
            {{
                "comparison": "مقارنة مفصلة",
                "verdict": "الحكم النهائي",
                "best_price": "أفضل سعر وموقعه",
                "amazon_rank": "ترتيب أمازون بين الأسعار",
                "score": 1-10,
                "recommendation": "التوصية"
            }}
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            return {
                "comparison": "تم العثور على أسعار أخرى للمقارنة",
                "verdict": "يحتاج مراجعة يدوية",
                "score": 5
            }
            
        except Exception as e:
            logger.error(f"AI price comparison error: {e}")
            return {
                "comparison": "خطأ في المقارنة",
                "verdict": "غير محدد",
                "score": 1
            }

class DealQualityFilter:
    """نظام تصفية العروض وتحديد الجودة"""
    
    def __init__(self, ai_analyzer: AIAnalyzer, db_file: str = "amz_products.db"):
        self.ai_analyzer = ai_analyzer
        self.db_file = db_file
    
    def filter_high_quality_deals(self, min_score: float = 7.0, max_deals: int = 15) -> List[Dict]:
        """تصفية العروض عالية الجودة"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # الحصول على العروض التي لم يتم تحليلها بعد
            cursor.execute('''
                SELECT * FROM products 
                WHERE (ai_verified = FALSE OR ai_verified IS NULL)
                AND discount_percent > 15
                AND current_price > 0
                ORDER BY discount_percent DESC
                LIMIT 50
            ''')
            
            columns = [description[0] for description in cursor.description]
            products = []
            
            for row in cursor.fetchall():
                product = dict(zip(columns, row))
                products.append(product)
            
            conn.close()
            
            # تحليل المنتجات بـ AI
            high_quality_deals = []
            
            for product in products:
                if len(high_quality_deals) >= max_deals:
                    break
                
                try:
                    # تحليل جودة العرض
                    analysis = self.ai_analyzer.analyze_deal_quality(product)
                    
                    # البحث عن أسعار مقارنة
                    price_comparison = self.ai_analyzer.search_product_prices(
                        product['name'], max_sites=3
                    )
                    
                    # مقارنة الأسعار
                    comparison_analysis = self.ai_analyzer.compare_prices_with_ai(
                        product['name'], 
                        product['current_price'], 
                        price_comparison
                    )
                    
                    # حساب النقاط الإجمالية
                    total_score = (analysis.get('quality_score', 0) + 
                                 comparison_analysis.get('score', 0)) / 2
                    
                    if total_score >= min_score:
                        product['ai_analysis'] = analysis
                        product['price_comparison'] = price_comparison
                        product['comparison_analysis'] = comparison_analysis
                        product['total_ai_score'] = total_score
                        
                        high_quality_deals.append(product)
                        
                        # تحديث قاعدة البيانات
                        self._update_product_ai_data(product)
                        
                        logger.info(f"High quality deal found: {product['name'][:50]}... Score: {total_score}")
                    
                    # تأخير بين التحليلات
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error analyzing product {product.get('name', 'Unknown')}: {e}")
                    continue
            
            return high_quality_deals
            
        except Exception as e:
            logger.error(f"Error filtering deals: {e}")
            return []
    
    def _update_product_ai_data(self, product: Dict):
        """تحديث بيانات AI في قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            analysis_text = json.dumps(product.get('ai_analysis', {}), ensure_ascii=False)
            
            cursor.execute('''
                UPDATE products SET 
                ai_verified = TRUE,
                ai_score = ?,
                ai_analysis = ?
                WHERE asin = ?
            ''', (
                product.get('total_ai_score', 0),
                analysis_text,
                product['asin']
            ))
            
            # حفظ مقارنة الأسعار
            for comparison in product.get('price_comparison', []):
                cursor.execute('''
                    INSERT OR REPLACE INTO price_comparison 
                    (product_name, asin, site_name, price, url, last_checked)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    product['name'],
                    product['asin'],
                    comparison['site'],
                    comparison['price'],
                    comparison['url']
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating AI data: {e}")

# مثال على الاستخدام
if __name__ == "__main__":
    # ضع مفتاح Gemini API هنا
    API_KEY = "AIzaSyBN1VNJCi4xN3mVUMfWgOLXhOa5Qk8-demo"  # استبدل بمفتاحك الحقيقي
    
    # إنشاء محلل AI
    ai_analyzer = AIAnalyzer(API_KEY)
    
    # إنشاء مصفي العروض
    deal_filter = DealQualityFilter(ai_analyzer)
    
    # تصفية العروض عالية الجودة
    high_quality_deals = deal_filter.filter_high_quality_deals(min_score=6.0, max_deals=10)
    
    print(f"تم العثور على {len(high_quality_deals)} عرض عالي الجودة:")
    for deal in high_quality_deals:
        print(f"- {deal['name'][:60]}... النقاط: {deal['total_ai_score']:.1f}")