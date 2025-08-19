# egyptian_retailers.py
# إعداد المواقع المصرية للبحث المباشر

import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import time
import json

# إعداد المواقع المصرية
EGYPTIAN_RETAILERS = {
    "Noon": {
        "base_url": "https://www.noon.com",
        "search_url": "https://www.noon.com/egypt/search?q={query}",
        "price_selector": ".price, .amount, [data-testid='price']",
        "name_selector": ".product-name, .title, h1, h2, h3",
        "image_selector": "img[src*='noon'], .product-image img",
        "link_selector": "a[href*='/product/'], .product-link",
        "timeout": 2.0,
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
        "base_url": "https://www.kanbkam.com",
        "search_url": "https://www.kanbkam.com/search?q={query}",
        "price_selector": ".price, .amount, .product-price, [class*='price']",
        "name_selector": ".product-name, .title, .product-title, h1, h2, h3",
        "image_selector": "img[src*='kanbkam'], .product-image img, .image img",
        "link_selector": "a[href*='/product/'], .product-link, .link",
        "timeout": 1.5,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }
    },
    
    "Pricena": {
        "base_url": "https://egypt.pricena.com",
        "search_url": "https://egypt.pricena.com/search?q={query}",
        "price_selector": ".price, .amount, .product-price, [class*='price']",
        "name_selector": ".product-name, .title, .product-title, h1, h2, h3",
        "image_selector": "img[src*='pricena'], .product-image img, .image img",
        "link_selector": "a[href*='/product/'], .product-link, .link",
        "timeout": 1.5,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }
    },
    
    "Carrefour": {
        "base_url": "https://www.carrefour.eg",
        "search_url": "https://www.carrefour.eg/search?q={query}",
        "price_selector": ".price, .amount, .product-price, [class*='price']",
        "name_selector": ".product-name, .title, .product-title, h1, h2, h3",
        "image_selector": "img[src*='carrefour'], .product-image img, .image img",
        "link_selector": "a[href*='/product/'], .product-link, .link",
        "timeout": 2.5,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }
    }
}

# كلمات مهمة للمنتجات (لتحسين البحث)
IMPORTANT_WORDS = {
    "electronics": ["wireless", "bluetooth", "smart", "digital", "portable", "rechargeable"],
    "phones": ["mobile", "smartphone", "android", "iphone", "5g", "4g"],
    "laptops": ["laptop", "notebook", "computer", "intel", "amd", "ssd", "ram"],
    "headphones": ["headphones", "earphones", "earbuds", "wireless", "bluetooth", "noise"],
    "watches": ["watch", "smartwatch", "fitness", "tracker", "digital"],
    "cameras": ["camera", "digital", "mirrorless", "dslr", "lens", "photography"]
}

def get_search_query(product_name: str, category: str = None) -> str:
    """تحسين استعلام البحث"""
    
    # تنظيف اسم المنتج
    query = product_name.lower()
    
    # إزالة الكلمات غير المهمة
    stop_words = ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
    words = [word for word in query.split() if word not in stop_words and len(word) > 2]
    
    # إضافة كلمات مهمة حسب الفئة
    if category and category.lower() in IMPORTANT_WORDS:
        category_words = IMPORTANT_WORDS[category.lower()]
        # إضافة كلمة مهمة واحدة إذا لم تكن موجودة
        for word in category_words:
            if word not in query:
                words.append(word)
                break
    
    # أخذ أول 4 كلمات مهمة
    important_words = words[:4]
    
    return " ".join(important_words)

def extract_price_from_text(text: str) -> Optional[float]:
    """استخراج السعر من النص"""
    if not text:
        return None
    
    # أنماط مختلفة للأسعار
    price_patterns = [
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:جنيه|ج\.م|EGP|LE|L\.E)',
        r'جنيه\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*EGP',
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*LE',
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*L\.E',
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # أي رقم
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                price = float(price_str)
                # فلترة الأسعار المعقولة (5-50000 جنيه)
                if 5 <= price <= 50000:
                    return price
            except ValueError:
                continue
    
    return None

def calculate_name_similarity(name1: str, name2: str) -> float:
    """حساب تشابه أسماء المنتجات (Jaccard similarity)"""
    if not name1 or not name2:
        return 0.0
    
    # تنظيف الأسماء
    def clean_name(name):
        words = re.findall(r'\b\w+\b', name.lower())
        return set(word for word in words if len(word) > 2)
    
    words1 = clean_name(name1)
    words2 = clean_name(name2)
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

class EgyptianRetailerSearcher:
    """محلل البحث في المواقع المصرية"""
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_duration = 1800  # 30 minutes
    
    async def __aenter__(self):
        """بدء الجلسة"""
        timeout = aiohttp.ClientTimeout(total=5)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """إغلاق الجلسة"""
        if self.session:
            await self.session.close()
    
    def get_cached_result(self, key: str) -> Optional[Dict]:
        """الحصول على نتيجة محفوظة"""
        if key in self.cache:
            timestamp, result = self.cache[key]
            if time.time() - timestamp < self.cache_duration:
                return result
        return None
    
    def cache_result(self, key: str, result: Dict):
        """حفظ النتيجة"""
        self.cache[key] = (time.time(), result)
    
    async def search_retailer(self, retailer_name: str, product_name: str) -> Dict:
        """البحث في موقع واحد"""
        retailer_config = EGYPTIAN_RETAILERS.get(retailer_name)
        if not retailer_config:
            return {"error": f"Retailer {retailer_name} not configured"}
        
        # فحص الكاش
        cache_key = f"{retailer_name}_{product_name}"
        cached_result = self.get_cached_result(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # تحسين استعلام البحث
            search_query = get_search_query(product_name)
            search_url = retailer_config["search_url"].format(query=search_query)
            
            # إرسال الطلب
            async with self.session.get(
                search_url, 
                headers=retailer_config["headers"],
                timeout=aiohttp.ClientTimeout(total=retailer_config["timeout"])
            ) as response:
                
                if response.status != 200:
                    return {"error": f"HTTP {response.status}"}
                
                html = await response.text()
                
                # تحليل HTML
                soup = BeautifulSoup(html, 'html.parser')
                
                # البحث عن المنتجات
                products = []
                
                # البحث عن الأسعار
                price_elements = soup.select(retailer_config["price_selector"])
                name_elements = soup.select(retailer_config["name_selector"])
                
                # مطابقة المنتجات مع الأسعار
                for i, price_elem in enumerate(price_elements[:5]):  # أول 5 نتائج
                    price_text = price_elem.get_text(strip=True)
                    price = extract_price_from_text(price_text)
                    
                    if price:
                        # البحث عن اسم المنتج المقابل
                        product_name_found = ""
                        if i < len(name_elements):
                            product_name_found = name_elements[i].get_text(strip=True)
                        
                        # حساب تشابه الاسم
                        similarity = calculate_name_similarity(product_name, product_name_found)
                        
                        products.append({
                            "name": product_name_found,
                            "price": price,
                            "similarity": similarity,
                            "source": retailer_name
                        })
                
                # ترتيب النتائج حسب التشابه
                products.sort(key=lambda x: x["similarity"], reverse=True)
                
                result = {
                    "retailer": retailer_name,
                    "products": products,
                    "best_match": products[0] if products else None,
                    "total_found": len(products)
                }
                
                # حفظ في الكاش
                self.cache_result(cache_key, result)
                
                return result
                
        except asyncio.TimeoutError:
            return {"error": "Timeout"}
        except Exception as e:
            return {"error": str(e)}
    
    async def search_all_retailers(self, product_name: str) -> Dict:
        """البحث في جميع المواقع"""
        start_time = time.time()
        
        # إنشاء مهام البحث المتوازي
        tasks = []
        for retailer_name in EGYPTIAN_RETAILERS.keys():
            task = self.search_retailer(retailer_name, product_name)
            tasks.append(task)
        
        # تنفيذ البحث المتوازي
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # تجميع النتائج
        all_results = {}
        for i, result in enumerate(results):
            retailer_name = list(EGYPTIAN_RETAILERS.keys())[i]
            if isinstance(result, Exception):
                all_results[retailer_name] = {"error": str(result)}
            else:
                all_results[retailer_name] = result
        
        search_time = time.time() - start_time
        
        return {
            "search_time": search_time,
            "results": all_results,
            "total_retailers": len(EGYPTIAN_RETAILERS)
        }

# دالة مساعدة للاختبار
async def test_search():
    """اختبار البحث"""
    async with EgyptianRetailerSearcher() as searcher:
        test_product = "Samsung Galaxy A54"
        print(f"🔍 Testing search for: {test_product}")
        
        results = await searcher.search_all_retailers(test_product)
        
        print(f"⏱️ Search completed in {results['search_time']:.2f}s")
        print(f"📊 Results from {results['total_retailers']} retailers:")
        
        for retailer, result in results['results'].items():
            if 'error' in result:
                print(f"❌ {retailer}: {result['error']}")
            else:
                best_match = result.get('best_match')
                if best_match:
                    print(f"✅ {retailer}: {best_match['price']} EGP (similarity: {best_match['similarity']:.2f})")
                else:
                    print(f"⚠️ {retailer}: No matches found")

if __name__ == "__main__":
    # اختبار سريع
    asyncio.run(test_search())