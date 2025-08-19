# improved_retailer_search.py
# محسن البحث في المواقع المصرية

import asyncio
import aiohttp
import json
import re
import time
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

class ImprovedRetailerSearch:
    """محسن البحث في المواقع المصرية"""
    
    def __init__(self):
        # إعدادات محسنة للمواقع
        self.retailers = {
            "Noon": {
                "base_url": "https://www.noon.com/egypt/search?q={query}",
                "alternative_urls": [
                    "https://www.noon.com/egypt/search?q={query}&sort=price_low_to_high",
                    "https://www.noon.com/egypt/search?q={query}&sort=relevance"
                ],
                "price_selectors": [
                    ".price", ".amount", "[data-testid='price']", ".product-price",
                    ".priceNow", ".current-price", ".sale-price", "[class*='price']",
                    ".product-price-now", ".price-current"
                ],
                "name_selectors": [
                    ".product-name", ".title", "h1", "h2", "h3", ".product-title",
                    ".item-name", ".product-heading", "[class*='title']"
                ],
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }
            },
            "Kanbkam": {
                "base_url": "https://www.kanbkam.com/search?q={query}",
                "alternative_urls": [
                    "https://www.kanbkam.com/search?q={query}&sort=price_asc",
                    "https://www.kanbkam.com/search?q={query}&sort=relevance"
                ],
                "price_selectors": [
                    ".price", ".amount", ".product-price", "[class*='price']",
                    ".current-price", ".sale-price", ".price-now", ".price-current",
                    ".product-price-now", ".price-value"
                ],
                "name_selectors": [
                    ".product-name", ".title", "h1", "h2", "h3", ".product-title",
                    ".item-name", ".product-heading", "[class*='title']"
                ],
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }
            },
            "Pricena": {
                "base_url": "https://egypt.pricena.com/search?q={query}",
                "alternative_urls": [
                    "https://egypt.pricena.com/search?q={query}&sort=price_asc",
                    "https://egypt.pricena.com/search?q={query}&sort=relevance"
                ],
                "price_selectors": [
                    ".price", ".amount", ".product-price", "[class*='price']",
                    ".current-price", ".sale-price", ".price-now", ".price-current",
                    ".product-price-now", ".price-value"
                ],
                "name_selectors": [
                    ".product-name", ".title", "h1", "h2", "h3", ".product-title",
                    ".item-name", ".product-heading", "[class*='title']"
                ],
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }
            },
            "Carrefour": {
                "base_url": "https://www.carrefour.eg/search?q={query}",
                "alternative_urls": [
                    "https://www.carrefour.eg/search?q={query}&sort=price_asc",
                    "https://www.carrefour.eg/search?q={query}&sort=relevance"
                ],
                "price_selectors": [
                    ".price", ".amount", ".product-price", "[class*='price']",
                    ".current-price", ".sale-price", ".price-now", ".price-current",
                    ".product-price-now", ".price-value"
                ],
                "name_selectors": [
                    ".product-name", ".title", "h1", "h2", "h3", ".product-title",
                    ".item-name", ".product-heading", "[class*='title']"
                ],
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }
            }
        }
        
        # إعدادات HTTP محسنة
        self.session_config = {
            "timeout": aiohttp.ClientTimeout(total=15, connect=10),
            "connector": aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30
            )
        }
    
    async def search_product(self, product_name: str) -> Dict[str, float]:
        """البحث عن منتج في جميع المواقع"""
        prices = {}
        query = self.clean_product_name(product_name)
        
        print(f"🔍 البحث عن: {query}")
        
        async with aiohttp.ClientSession(**self.session_config) as session:
            tasks = []
            for retailer_name, config in self.retailers.items():
                task = self.search_retailer_improved(session, retailer_name, config, query)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                retailer_name = list(self.retailers.keys())[i]
                if isinstance(result, dict) and 'price' in result:
                    prices[retailer_name] = result['price']
                    print(f"✅ {retailer_name}: {result['price']:,.0f} جنيه")
                else:
                    print(f"❌ {retailer_name}: فشل في البحث")
        
        return prices
    
    async def search_retailer_improved(self, session, retailer_name: str, config: dict, query: str) -> Dict:
        """البحث المحسن في موقع واحد"""
        # محاولة URLs متعددة
        urls_to_try = [config['base_url']] + config.get('alternative_urls', [])
        
        for url_template in urls_to_try:
            try:
                url = url_template.format(query=query)
                print(f"  🔗 محاولة: {url}")
                
                async with session.get(url, headers=config['headers']) as response:
                    if response.status == 200:
                        html = await response.text()
                        result = self.parse_html_improved(html, config, retailer_name)
                        if result:
                            return result
                    else:
                        print(f"    ❌ HTTP {response.status}")
                        
            except Exception as e:
                print(f"    ❌ خطأ: {str(e)[:50]}...")
                continue
        
        return {}
    
    def parse_html_improved(self, html: str, config: dict, retailer_name: str) -> Optional[Dict]:
        """تحليل HTML محسن"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # البحث عن الأسعار بطرق متعددة
            prices_found = []
            
            # 1. البحث باستخدام CSS selectors
            for selector in config['price_selectors']:
                elements = soup.select(selector)
                for element in elements[:5]:  # أول 5 عناصر
                    price_text = element.get_text(strip=True)
                    price = self.extract_price_improved(price_text)
                    if price:
                        prices_found.append(price)
            
            # 2. البحث في النص الكامل
            if not prices_found:
                full_text = soup.get_text()
                prices_found = self.extract_prices_from_text(full_text)
            
            # 3. البحث في attributes
            if not prices_found:
                prices_found = self.extract_prices_from_attributes(soup)
            
            # اختيار أفضل سعر
            if prices_found:
                # فلترة الأسعار المعقولة
                valid_prices = [p for p in prices_found if 50 <= p <= 100000]
                if valid_prices:
                    best_price = min(valid_prices)  # أرخص سعر
                    return {
                        "price": best_price,
                        "retailer": retailer_name,
                        "method": "improved_search"
                    }
            
            return None
            
        except Exception as e:
            print(f"    ❌ خطأ في التحليل: {str(e)[:50]}...")
            return None
    
    def extract_price_improved(self, text: str) -> Optional[float]:
        """استخراج سعر محسن من النص"""
        if not text:
            return None
        
        # أنماط محسنة للأسعار
        patterns = [
            # جنيه مصري
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:جنيه|ج\.م|EGP|LE|L\.E|جنية|جنيهات)',
            r'(?:جنيه|ج\.م|EGP|LE|L\.E|جنية|جنيهات)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            
            # أرقام مع فواصل
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            
            # أرقام بدون فواصل
            r'(\d{4,6})',  # أرقام من 4-6 خانات
            
            # أرقام مع رموز
            r'(\d+(?:\.\d{2})?)\s*(?:EGP|LE|L\.E)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    price_str = str(match).replace(',', '').replace(' ', '')
                    price = float(price_str)
                    if 50 <= price <= 100000:  # نطاق معقول
                        return price
                except (ValueError, AttributeError):
                    continue
        
        return None
    
    def extract_prices_from_text(self, text: str) -> List[float]:
        """استخراج جميع الأسعار من النص"""
        prices = []
        
        # البحث عن أنماط الأسعار
        patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:جنيه|ج\.م|EGP|LE|L\.E)',
            r'(\d{4,6})',  # أرقام من 4-6 خانات
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    price_str = str(match).replace(',', '')
                    price = float(price_str)
                    if 50 <= price <= 100000:
                        prices.append(price)
                except ValueError:
                    continue
        
        return prices
    
    def extract_prices_from_attributes(self, soup) -> List[float]:
        """استخراج الأسعار من attributes"""
        prices = []
        
        # البحث في data attributes
        for element in soup.find_all(attrs={"data-price": True}):
            try:
                price = float(element.get("data-price"))
                if 50 <= price <= 100000:
                    prices.append(price)
            except (ValueError, TypeError):
                continue
        
        # البحث في content attributes
        for element in soup.find_all(attrs={"content": True}):
            content = element.get("content", "")
            if "price" in content.lower():
                price = self.extract_price_improved(content)
                if price:
                    prices.append(price)
        
        return prices
    
    def clean_product_name(self, name: str) -> str:
        """تنظيف اسم المنتج للبحث"""
        # إزالة الكلمات غير المهمة
        stop_words = [
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", 
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "this", "that", "these", "those"
        ]
        
        # تنظيف النص
        words = name.lower().split()
        important_words = []
        
        for word in words:
            # إزالة الأحرف الخاصة
            clean_word = re.sub(r'[^\w\s]', '', word)
            if (len(clean_word) > 2 and 
                clean_word not in stop_words and 
                not clean_word.isdigit()):
                important_words.append(clean_word)
        
        # أخذ أول 4 كلمات مهمة
        return " ".join(important_words[:4])
    
    async def test_search(self, product_name: str):
        """اختبار البحث"""
        print(f"🧪 اختبار البحث: {product_name}")
        start_time = time.time()
        
        prices = await self.search_product(product_name)
        
        end_time = time.time()
        print(f"⏱️ وقت البحث: {end_time - start_time:.2f}s")
        
        if prices:
            print(f"🏪 متوسط السوق: {sum(prices.values()) / len(prices):,.0f} جنيه")
            print(f"📊 عدد المنافسين: {len(prices)}")
        else:
            print("❌ لم يتم العثور على أسعار")
        
        return prices

# اختبار النظام
async def main():
    searcher = ImprovedRetailerSearch()
    
    test_products = [
        "Samsung Galaxy A54 5G",
        "iPhone 15 Pro 128GB",
        "Sony WH-1000XM5 Headphones"
    ]
    
    for product in test_products:
        print(f"\n{'='*50}")
        await searcher.test_search(product)
        print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(main())