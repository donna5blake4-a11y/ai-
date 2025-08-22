#!/usr/bin/env python3
# correct_simple_test.py - اختبار بسيط للنظام بدون مكتبات خارجية

import json
import os
from datetime import datetime

def print_banner():
    print("=" * 60)
    print("  النظام الذكي لفلترة العروض - اختبار بسيط")
    print("  يحول 1000+ عرض وهمي إلى 15 عرض موثوق يومياً")
    print("=" * 60)

class SimpleDealFilter:
    def __init__(self):
        # إعدادات الفلترة
        self.min_discount = 20
        self.max_discount = 80
        self.min_price = 30
        self.max_price = 5000
        
        # فئات موثوقة
        self.trusted_categories = [
            'Electronics', 'Home & Kitchen', 'Beauty', 'Health & Household Products',
            'Tools & Home Improvement', 'Automotive', 'Fashion', 'Grocery'
        ]
        
        # كلمات مشبوهة
        self.suspicious_words = [
            'fake', 'replica', 'copy', 'imitation', 'used', 'damaged', 'broken'
        ]
        
        # مؤشرات الجودة
        self.quality_indicators = [
            'original', 'authentic', 'genuine', 'warranty', 'new', 'brand new', 'authorized'
        ]
    
    def filter_deals_simple(self, products_list, target_count=15):
        print(f"بدء فلترة {len(products_list)} منتج للحصول على أفضل {target_count} عرض...")
        
        # المرحلة 1: الفلترة الأساسية
        basic_filtered = self.basic_filter(products_list)
        print(f"المرحلة 1: تم فلترة {len(basic_filtered)} منتج من الفلترة الأساسية")
        
        # المرحلة 2: التحليل النصي
        text_filtered = self.text_analysis_filter(basic_filtered)
        print(f"المرحلة 2: تم فلترة {len(text_filtered)} منتج من التحليل النصي")
        
        # المرحلة 3: تحليل الأسعار التاريخية
        price_filtered = self.price_analysis_filter(text_filtered)
        print(f"المرحلة 3: تم فلترة {len(price_filtered)} منتج من تحليل الأسعار")
        
        # المرحلة 4: الترتيب النهائي
        final_deals = self.final_ranking(price_filtered, target_count)
        print(f"النتيجة النهائية: {len(final_deals)} عرض عالي الجودة")
        
        return final_deals
    
    def basic_filter(self, products):
        filtered = []
        
        for product in products:
            # فلتر السعر
            price = product.get('price', 0)
            if not (self.min_price <= price <= self.max_price):
                continue
            
            # فلتر الخصم
            discount = product.get('discount_percent', 0)
            if not (self.min_discount <= discount <= self.max_discount):
                continue
            
            # فلتر الفئة
            category = product.get('section', '')
            if category not in self.trusted_categories:
                continue
            
            # فلتر السعر الأصلي
            strike_price = product.get('strike_price', 0)
            if strike_price <= 0 or strike_price <= price:
                continue
            
            filtered.append(product)
        
        return filtered
    
    def text_analysis_filter(self, products):
        filtered = []
        
        for product in products:
            name = product.get('name', '').lower()
            
            # فحص الكلمات المشبوهة
            suspicious_count = sum(1 for word in self.suspicious_words if word in name)
            if suspicious_count > 0:
                continue
            
            # فحص مؤشرات الجودة
            quality_count = sum(1 for indicator in self.quality_indicators if indicator in name)
            
            # حساب نقاط النص
            text_score = quality_count * 10 - suspicious_count * 20
            product['text_score'] = text_score
            
            if text_score >= 0:
                filtered.append(product)
        
        return filtered
    
    def price_analysis_filter(self, products):
        filtered = []
        
        for product in products:
            price_history = product.get('price_history', [])
            price_score = 0
            
            if len(price_history) >= 3:
                prices = [h.get('price', 0) for h in price_history if h.get('price', 0) > 0]
                
                if prices:
                    avg_price = sum(prices) / len(prices)
                    current_price = product.get('price', 0)
                    
                    if current_price < avg_price * 0.85:
                        price_score += 30
                    elif current_price < avg_price:
                        price_score += 15
                    
                    price_variance = (max(prices) - min(prices)) / avg_price
                    if price_variance < 0.3:
                        price_score += 10
            
            # فحص منطقية السعر
            discount = product.get('discount_percent', 0)
            price = product.get('price', 0)
            strike_price = product.get('strike_price', 0)
            
            calculated_discount = ((strike_price - price) / strike_price) * 100
            if abs(calculated_discount - discount) <= 2:
                price_score += 20
            
            product['price_score'] = price_score
            
            if price_score >= 15:
                filtered.append(product)
        
        return filtered
    
    def final_ranking(self, products, target_count):
        for product in products:
            final_score = 0
            
            # نقاط الخصم (40%)
            discount = product.get('discount_percent', 0)
            final_score += min(40, discount * 0.6)
            
            # نقاط تحليل النص (30%)
            text_score = product.get('text_score', 0)
            final_score += min(30, max(0, text_score))
            
            # نقاط تحليل السعر (30%)
            price_score = product.get('price_score', 0)
            final_score += min(30, price_score)
            
            product['final_score'] = final_score
        
        # ترتيب حسب النقاط
        sorted_products = sorted(products, key=lambda x: x['final_score'], reverse=True)
        
        return sorted_products[:target_count]

def run_simple_test():
    print_banner()
    
    # بيانات تجريبية
    test_products = [
        {
            'asin': 'B08N5WRWNW',
            'name': 'Apple iPhone 14 Pro Max 256GB Deep Purple Original Warranty',
            'price': 25000,
            'strike_price': 30000,
            'discount_percent': 16.7,
            'section': 'Electronics',
            'url': 'https://amazon.eg/dp/B08N5WRWNW',
            'price_history': [
                {'date': '2024-01-01', 'price': 28000},
                {'date': '2024-01-15', 'price': 26000},
                {'date': '2024-01-30', 'price': 25000}
            ]
        },
        {
            'asin': 'B09JFGHIJK',
            'name': 'Samsung Galaxy S23 Ultra 512GB Phantom Black Genuine',
            'price': 22000,
            'strike_price': 28000,
            'discount_percent': 21.4,
            'section': 'Electronics',
            'url': 'https://amazon.eg/dp/B09JFGHIJK',
            'price_history': [
                {'date': '2024-01-01', 'price': 26000},
                {'date': '2024-01-15', 'price': 24000},
                {'date': '2024-01-30', 'price': 22000}
            ]
        },
        {
            'asin': 'B07FAKE123',
            'name': 'Fake iPhone Replica Copy Not Original',
            'price': 500,
            'strike_price': 1000,
            'discount_percent': 50.0,
            'section': 'Electronics',
            'url': 'https://amazon.eg/dp/B07FAKE123',
            'price_history': []
        },
        {
            'asin': 'B08KITCHEN',
            'name': 'Kitchen Knife Set Professional Stainless Steel',
            'price': 150,
            'strike_price': 200,
            'discount_percent': 25.0,
            'section': 'Home & Kitchen',
            'url': 'https://amazon.eg/dp/B08KITCHEN',
            'price_history': [
                {'date': '2024-01-01', 'price': 180},
                {'date': '2024-01-15', 'price': 165},
                {'date': '2024-01-30', 'price': 150}
            ]
        },
        {
            'asin': 'B09BEAUTY01',
            'name': 'L\'Oreal Paris Skin Care Set Original',
            'price': 89,
            'strike_price': 120,
            'discount_percent': 25.8,
            'section': 'Beauty',
            'url': 'https://amazon.eg/dp/B09BEAUTY01',
            'price_history': [
                {'date': '2024-01-01', 'price': 110},
                {'date': '2024-01-15', 'price': 95},
                {'date': '2024-01-30', 'price': 89}
            ]
        },
        {
            'asin': 'B10OVERPRICED',
            'name': 'Overpriced Headphones',
            'price': 8000,
            'strike_price': 10000,
            'discount_percent': 20.0,
            'section': 'Electronics',
            'url': 'https://amazon.eg/dp/B10OVERPRICED',
            'price_history': []
        }
    ]
    
    print(f"البيانات التجريبية: {len(test_products)} منتج")
    print("-" * 60)
    
    # عرض المنتجات قبل الفلترة
    print("المنتجات قبل الفلترة:")
    for i, product in enumerate(test_products, 1):
        name = product['name'][:40] + "..." if len(product['name']) > 40 else product['name']
        print(f"{i}. {name}")
        print(f"   السعر: {product['price']} جنيه | الخصم: {product['discount_percent']:.1f}%")
    
    print("\n" + "=" * 60)
    
    # تشغيل الفلترة
    filter_system = SimpleDealFilter()
    best_deals = filter_system.filter_deals_simple(test_products, target_count=15)
    
    if best_deals:
        print(f"\nأفضل العروض ({len(best_deals)}):")
        print("-" * 70)
        
        for i, deal in enumerate(best_deals, 1):
            name = deal['name'][:50] + "..." if len(deal['name']) > 50 else deal['name']
            price = deal['price']
            discount = deal['discount_percent']
            score = deal['final_score']
            
            print(f"{i:2d}. {name}")
            print(f"    السعر: {price:.0f} جنيه")
            print(f"    الخصم: {discount:.1f}%")
            print(f"    النقاط: {score:.1f}/100")
            print(f"    الرابط: {deal['url']}")
            print()
    else:
        print("لم يتم العثور على عروض تستوفي المعايير")
    
    print("انتهى الاختبار بنجاح!")
    print(f"الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        run_simple_test()
    except Exception as e:
        print(f"خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()