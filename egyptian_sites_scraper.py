# egyptian_sites_scraper.py
import requests
import json
import re
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
import sqlite3
from datetime import datetime

# إعداد الـ logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EgyptianSitesScraper:
    """نظام scraping للمواقع المصرية الرئيسية"""
    
    def __init__(self, db_file: str = "amz_products.db"):
        self.db_file = db_file
        self.session = requests.Session()
        self.driver = None
        
        # Headers متنوعة للتخفي
        self.headers_list = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Connection': 'keep-alive',
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
        ]
        
        # معلومات المواقع المصرية
        self.sites_config = {
            'jumia': {
                'base_url': 'https://www.jumia.com.eg',
                'search_url': 'https://www.jumia.com.eg/catalog/?q={}',
                'selectors': {
                    'products': '.prd',
                    'name': '.name',
                    'price': '.prc',
                    'old_price': '.old',
                    'image': '.img',
                    'link': 'a'
                },
                'requires_js': False
            },
            'noon': {
                'base_url': 'https://www.noon.com',
                'search_url': 'https://www.noon.com/egypt-en/search?q={}',
                'selectors': {
                    'products': '[data-qa="product-name"]',
                    'name': '[data-qa="product-name"]',
                    'price': '.priceNow',
                    'old_price': '.priceWas',
                    'image': 'img',
                    'link': 'a'
                },
                'requires_js': True
            },
            'btech': {
                'base_url': 'https://www.b-tech.com.eg',
                'search_url': 'https://www.b-tech.com.eg/search?q={}',
                'selectors': {
                    'products': '.product-item',
                    'name': '.product-name',
                    'price': '.price',
                    'old_price': '.old-price',
                    'image': '.product-image img',
                    'link': 'a'
                },
                'requires_js': False
            },
            'carrefour': {
                'base_url': 'https://www.carrefouregypt.com',
                'search_url': 'https://www.carrefouregypt.com/mafegy/en/search/?text={}',
                'selectors': {
                    'products': '.product-item',
                    'name': '.product-name',
                    'price': '.price',
                    'old_price': '.was-price',
                    'image': '.product-image img',
                    'link': 'a'
                },
                'requires_js': True
            },
            'souq': {
                'base_url': 'https://egypt.souq.com',
                'search_url': 'https://egypt.souq.com/eg-en/search/?q={}',
                'selectors': {
                    'products': '.grid-list',
                    'name': '.itemTitle',
                    'price': '.price',
                    'old_price': '.was',
                    'image': '.productImg img',
                    'link': 'a'
                },
                'requires_js': False
            }
        }
    
    def init_selenium_driver(self):
        """تهيئة Selenium driver للمواقع التي تحتاج JavaScript"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Selenium driver initialized")
            return True
            
        except Exception as e:
            logger.error(f"Selenium driver initialization error: {e}")
            return False
    
    def get_random_headers(self) -> Dict:
        """الحصول على headers عشوائية"""
        return random.choice(self.headers_list)
    
    def extract_price_from_text(self, price_text: str) -> Optional[float]:
        """استخراج السعر من النص"""
        if not price_text:
            return None
        
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
    
    def scrape_jumia(self, search_query: str, max_results: int = 20) -> List[Dict]:
        """scraping موقع جوميا"""
        try:
            products = []
            config = self.sites_config['jumia']
            search_url = config['search_url'].format(quote(search_query))
            
            self.session.headers.update(self.get_random_headers())
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"Jumia request failed: {response.status_code}")
                return products
            
            soup = BeautifulSoup(response.content, 'html.parser')
            product_elements = soup.select(config['selectors']['products'])[:max_results]
            
            for element in product_elements:
                try:
                    # اسم المنتج
                    name_elem = element.select_one(config['selectors']['name'])
                    name = name_elem.get_text(strip=True) if name_elem else ""
                    
                    # السعر الحالي
                    price_elem = element.select_one(config['selectors']['price'])
                    current_price = self.extract_price_from_text(
                        price_elem.get_text(strip=True) if price_elem else ""
                    )
                    
                    # السعر القديم
                    old_price_elem = element.select_one(config['selectors']['old_price'])
                    old_price = self.extract_price_from_text(
                        old_price_elem.get_text(strip=True) if old_price_elem else ""
                    )
                    
                    # الرابط
                    link_elem = element.select_one(config['selectors']['link'])
                    link = urljoin(config['base_url'], link_elem['href']) if link_elem else ""
                    
                    # الصورة
                    img_elem = element.select_one(config['selectors']['image'])
                    image_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""
                    
                    # حساب نسبة الخصم
                    discount_percent = 0
                    if current_price and old_price and old_price > current_price:
                        discount_percent = ((old_price - current_price) / old_price) * 100
                    
                    if name and current_price:
                        products.append({
                            'site': 'jumia',
                            'name': name,
                            'current_price': current_price,
                            'old_price': old_price,
                            'discount_percent': discount_percent,
                            'url': link,
                            'image_url': image_url,
                            'search_query': search_query
                        })
                
                except Exception as e:
                    logger.error(f"Error processing Jumia product: {e}")
                    continue
            
            logger.info(f"Scraped {len(products)} products from Jumia")
            return products
            
        except Exception as e:
            logger.error(f"Jumia scraping error: {e}")
            return []
    
    def scrape_noon(self, search_query: str, max_results: int = 20) -> List[Dict]:
        """scraping موقع نون (يحتاج Selenium)"""
        try:
            products = []
            
            if not self.driver:
                if not self.init_selenium_driver():
                    return products
            
            config = self.sites_config['noon']
            search_url = config['search_url'].format(quote(search_query))
            
            self.driver.get(search_url)
            time.sleep(3)  # انتظار تحميل الصفحة
            
            # البحث عن المنتجات
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, config['selectors']['products']))
                )
            except TimeoutException:
                logger.warning("Noon products not found within timeout")
                return products
            
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, config['selectors']['products'])[:max_results]
            
            for element in product_elements:
                try:
                    # اسم المنتج
                    name = element.text.strip()
                    
                    # السعر (يحتاج البحث في العنصر الأب)
                    parent_element = element.find_element(By.XPATH, ".//ancestor::div[contains(@class, 'productContainer')]")
                    
                    price_elem = parent_element.find_element(By.CSS_SELECTOR, config['selectors']['price'])
                    current_price = self.extract_price_from_text(price_elem.text if price_elem else "")
                    
                    # السعر القديم
                    old_price = None
                    try:
                        old_price_elem = parent_element.find_element(By.CSS_SELECTOR, config['selectors']['old_price'])
                        old_price = self.extract_price_from_text(old_price_elem.text)
                    except NoSuchElementException:
                        pass
                    
                    # الرابط
                    link_elem = parent_element.find_element(By.TAG_NAME, "a")
                    link = link_elem.get_attribute('href') if link_elem else ""
                    
                    # الصورة
                    image_url = ""
                    try:
                        img_elem = parent_element.find_element(By.TAG_NAME, "img")
                        image_url = img_elem.get_attribute('src')
                    except NoSuchElementException:
                        pass
                    
                    # حساب نسبة الخصم
                    discount_percent = 0
                    if current_price and old_price and old_price > current_price:
                        discount_percent = ((old_price - current_price) / old_price) * 100
                    
                    if name and current_price:
                        products.append({
                            'site': 'noon',
                            'name': name,
                            'current_price': current_price,
                            'old_price': old_price,
                            'discount_percent': discount_percent,
                            'url': link,
                            'image_url': image_url,
                            'search_query': search_query
                        })
                
                except Exception as e:
                    logger.error(f"Error processing Noon product: {e}")
                    continue
            
            logger.info(f"Scraped {len(products)} products from Noon")
            return products
            
        except Exception as e:
            logger.error(f"Noon scraping error: {e}")
            return []
    
    def scrape_btech(self, search_query: str, max_results: int = 20) -> List[Dict]:
        """scraping موقع B.Tech"""
        try:
            products = []
            config = self.sites_config['btech']
            search_url = config['search_url'].format(quote(search_query))
            
            self.session.headers.update(self.get_random_headers())
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"B.Tech request failed: {response.status_code}")
                return products
            
            soup = BeautifulSoup(response.content, 'html.parser')
            product_elements = soup.select(config['selectors']['products'])[:max_results]
            
            for element in product_elements:
                try:
                    # اسم المنتج
                    name_elem = element.select_one(config['selectors']['name'])
                    name = name_elem.get_text(strip=True) if name_elem else ""
                    
                    # السعر الحالي
                    price_elem = element.select_one(config['selectors']['price'])
                    current_price = self.extract_price_from_text(
                        price_elem.get_text(strip=True) if price_elem else ""
                    )
                    
                    # السعر القديم
                    old_price_elem = element.select_one(config['selectors']['old_price'])
                    old_price = self.extract_price_from_text(
                        old_price_elem.get_text(strip=True) if old_price_elem else ""
                    )
                    
                    # الرابط
                    link_elem = element.select_one(config['selectors']['link'])
                    link = urljoin(config['base_url'], link_elem['href']) if link_elem else ""
                    
                    # الصورة
                    img_elem = element.select_one(config['selectors']['image'])
                    image_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""
                    
                    # حساب نسبة الخصم
                    discount_percent = 0
                    if current_price and old_price and old_price > current_price:
                        discount_percent = ((old_price - current_price) / old_price) * 100
                    
                    if name and current_price:
                        products.append({
                            'site': 'btech',
                            'name': name,
                            'current_price': current_price,
                            'old_price': old_price,
                            'discount_percent': discount_percent,
                            'url': link,
                            'image_url': image_url,
                            'search_query': search_query
                        })
                
                except Exception as e:
                    logger.error(f"Error processing B.Tech product: {e}")
                    continue
            
            logger.info(f"Scraped {len(products)} products from B.Tech")
            return products
            
        except Exception as e:
            logger.error(f"B.Tech scraping error: {e}")
            return []
    
    def search_all_sites(self, search_query: str, max_results_per_site: int = 10) -> Dict[str, List[Dict]]:
        """البحث في جميع المواقع بشكل متوازي"""
        results = {}
        
        def scrape_site(site_name: str):
            try:
                if site_name == 'jumia':
                    return site_name, self.scrape_jumia(search_query, max_results_per_site)
                elif site_name == 'noon':
                    return site_name, self.scrape_noon(search_query, max_results_per_site)
                elif site_name == 'btech':
                    return site_name, self.scrape_btech(search_query, max_results_per_site)
                else:
                    return site_name, []
            except Exception as e:
                logger.error(f"Error scraping {site_name}: {e}")
                return site_name, []
        
        # تشغيل متوازي للمواقع التي لا تحتاج Selenium
        static_sites = ['jumia', 'btech']
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for site in static_sites:
                future = executor.submit(scrape_site, site)
                futures.append(future)
            
            for future in as_completed(futures, timeout=60):
                try:
                    site_name, site_results = future.result()
                    results[site_name] = site_results
                except Exception as e:
                    logger.error(f"Future execution error: {e}")
        
        # تشغيل المواقع التي تحتاج Selenium بشكل منفصل
        js_sites = ['noon']
        for site in js_sites:
            site_name, site_results = scrape_site(site)
            results[site_name] = site_results
        
        return results
    
    def save_results_to_db(self, search_results: Dict[str, List[Dict]], amazon_asin: str = None):
        """حفظ نتائج البحث في قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            for site_name, products in search_results.items():
                for product in products:
                    cursor.execute('''
                        INSERT OR REPLACE INTO price_comparison 
                        (product_name, asin, site_name, price, url, last_checked)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        product['name'],
                        amazon_asin or '',
                        site_name,
                        product['current_price'],
                        product['url']
                    ))
            
            conn.commit()
            conn.close()
            
            total_products = sum(len(products) for products in search_results.values())
            logger.info(f"Saved {total_products} products to database")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
    
    def get_best_prices(self, search_query: str, save_to_db: bool = True, amazon_asin: str = None) -> Dict:
        """البحث عن أفضل الأسعار في جميع المواقع"""
        try:
            logger.info(f"Searching for: {search_query}")
            
            # البحث في جميع المواقع
            search_results = self.search_all_sites(search_query)
            
            # حفظ في قاعدة البيانات
            if save_to_db:
                self.save_results_to_db(search_results, amazon_asin)
            
            # تحليل النتائج
            all_products = []
            for site_name, products in search_results.items():
                all_products.extend(products)
            
            if not all_products:
                return {
                    'search_query': search_query,
                    'total_results': 0,
                    'best_price': None,
                    'results_by_site': search_results,
                    'summary': 'لم يتم العثور على نتائج'
                }
            
            # العثور على أفضل سعر
            best_product = min(all_products, key=lambda x: x['current_price'])
            
            # إحصائيات
            prices = [p['current_price'] for p in all_products]
            avg_price = sum(prices) / len(prices)
            
            return {
                'search_query': search_query,
                'total_results': len(all_products),
                'best_price': best_product,
                'average_price': avg_price,
                'price_range': {
                    'min': min(prices),
                    'max': max(prices)
                },
                'results_by_site': search_results,
                'summary': f'تم العثور على {len(all_products)} منتج في {len(search_results)} مواقع'
            }
            
        except Exception as e:
            logger.error(f"Error getting best prices: {e}")
            return {
                'search_query': search_query,
                'total_results': 0,
                'error': str(e)
            }
    
    def cleanup(self):
        """تنظيف الموارد"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Selenium driver closed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء scraper
    scraper = EgyptianSitesScraper()
    
    try:
        # البحث عن منتج
        search_query = "ماكينة حلاقة متعددة الاستخدامات"
        results = scraper.get_best_prices(search_query)
        
        print(f"نتائج البحث عن: {search_query}")
        print(f"إجمالي النتائج: {results['total_results']}")
        
        if results.get('best_price'):
            best = results['best_price']
            print(f"أفضل سعر: {best['current_price']} جنيه من {best['site']}")
            print(f"اسم المنتج: {best['name']}")
        
        print(f"متوسط الأسعار: {results.get('average_price', 0):.2f} جنيه")
        
        # عرض النتائج حسب الموقع
        for site, products in results.get('results_by_site', {}).items():
            print(f"\n{site.upper()}: {len(products)} منتج")
            for product in products[:3]:  # أول 3 منتجات
                print(f"  • {product['name'][:50]}... - {product['current_price']} جنيه")
    
    finally:
        # تنظيف الموارد
        scraper.cleanup()