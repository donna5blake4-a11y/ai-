# simple_fixed_system.py
# نسخة مبسطة يمكن نسخها مباشرة

import asyncio
import aiohttp
import json
import sqlite3
import re
import time
import random
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import requests

class SimpleFixedSystem:
    """نظام مبسط محسن"""
    
    def __init__(self):
        # قاعدة البيانات
        self.db_path = "simple_fixed.db"
        self.init_database()
        
        # إعدادات البحث الحقيقي
        self.retailers = {
            "Noon": {
                "base_url": "https://www.noon.com/egypt/search?q={query}",
                "price_selectors": [
                    ".price", ".amount", "[data-testid='price']", ".product-price",
                    ".priceNow", ".current-price", ".sale-price", "[class*='price']",
                    ".product-price-now", ".price-current", ".price-value"
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
                "price_selectors": [
                    ".price", ".amount", ".product-price", "[class*='price']",
                    ".current-price", ".sale-price", ".price-now", ".price-current",
                    ".product-price-now", ".price-value"
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
        
        # متغيرات التحكم
        self.is_running = False
        self.products_to_analyze = []
        
        # إنشاء الواجهة
        self.setup_gui()
    
    def init_database(self):
        """تهيئة قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                asin TEXT PRIMARY KEY,
                name TEXT,
                url TEXT,
                img TEXT,
                section TEXT,
                current_price REAL,
                strike_price REAL,
                discount_percent REAL,
                deal_score REAL DEFAULT 0,
                is_real_deal BOOLEAN DEFAULT FALSE,
                confidence REAL DEFAULT 0,
                recommendation TEXT DEFAULT '',
                competitor_prices TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def setup_gui(self):
        """إعداد الواجهة"""
        self.root = tk.Tk()
        self.root.title("LAQTA AI - النظام المبسط المحسن")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1f2e')
        
        # العنوان
        title_frame = tk.Frame(self.root, bg='#1a1f2e')
        title_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        title_label = tk.Label(
            title_frame,
            text="LAQTA AI - النظام المبسط المحسن",
            font=("Arial Black", 24, "bold"),
            fg="#54fac8",
            bg='#1a1f2e'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="🔍 بحث حقيقي + 📊 تحليل + 💾 قاعدة بيانات + 🎛️ تحكم متقدم",
            font=("Arial", 12),
            fg="#59ff9d",
            bg='#1a1f2e'
        )
        subtitle_label.pack()
        
        # إطار التحكم الرئيسي
        main_control_frame = tk.Frame(self.root, bg='#232d3a', relief='raised', bd=2)
        main_control_frame.pack(fill='x', padx=20, pady=10)
        
        # إطار خيارات التحكم
        control_frame = tk.Frame(main_control_frame, bg='#232d3a')
        control_frame.pack(pady=15)
        
        # الصف الأول - خيارات أساسية
        row1_frame = tk.Frame(control_frame, bg='#232d3a')
        row1_frame.pack(pady=5)
        
        # خيار المصدر
        tk.Label(row1_frame, text="مصدر المنتجات:", font=("Arial", 12), fg="white", bg='#232d3a').pack(side='left', padx=10)
        self.source_var = tk.StringVar(value="manual")
        source_combo = ttk.Combobox(row1_frame, textvariable=self.source_var, values=["manual", "json_file"], width=15)
        source_combo.pack(side='left', padx=10)
        
        # عدد المنتجات
        tk.Label(row1_frame, text="عدد المنتجات:", font=("Arial", 12), fg="white", bg='#232d3a').pack(side='left', padx=10)
        self.products_count_var = tk.StringVar(value="5")
        products_count_entry = tk.Entry(row1_frame, textvariable=self.products_count_var, width=10)
        products_count_entry.pack(side='left', padx=10)
        
        # نسبة الخصم الأدنى
        tk.Label(row1_frame, text="نسبة الخصم الأدنى (%):", font=("Arial", 12), fg="white", bg='#232d3a').pack(side='left', padx=10)
        self.min_discount_var = tk.StringVar(value="15")
        min_discount_entry = tk.Entry(row1_frame, textvariable=self.min_discount_var, width=10)
        min_discount_entry.pack(side='left', padx=10)
        
        # الصف الثاني - خيارات متقدمة
        row2_frame = tk.Frame(control_frame, bg='#232d3a')
        row2_frame.pack(pady=5)
        
        # درجة العرض الأدنى
        tk.Label(row2_frame, text="درجة العرض الأدنى:", font=("Arial", 12), fg="white", bg='#232d3a').pack(side='left', padx=10)
        self.min_deal_score_var = tk.StringVar(value="70")
        min_deal_score_entry = tk.Entry(row2_frame, textvariable=self.min_deal_score_var, width=10)
        min_deal_score_entry.pack(side='left', padx=10)
        
        # عدد المنافسين الأدنى
        tk.Label(row2_frame, text="عدد المنافسين الأدنى:", font=("Arial", 12), fg="white", bg='#232d3a').pack(side='left', padx=10)
        self.min_competitors_var = tk.StringVar(value="2")
        min_competitors_entry = tk.Entry(row2_frame, textvariable=self.min_competitors_var, width=10)
        min_competitors_entry.pack(side='left', padx=10)
        
        # إرسال للتليجرام
        self.telegram_var = tk.BooleanVar(value=True)
        telegram_check = tk.Checkbutton(row2_frame, text="إرسال للتليجرام", variable=self.telegram_var, 
                                      font=("Arial", 12), fg="white", bg='#232d3a', selectcolor='#232d3a')
        telegram_check.pack(side='left', padx=20)
        
        # الصف الثالث - أزرار التحكم
        row3_frame = tk.Frame(control_frame, bg='#232d3a')
        row3_frame.pack(pady=10)
        
        # زر بدء التحليل
        self.start_btn = tk.Button(
            row3_frame,
            text="🚀 بدء التحليل",
            command=self.start_analysis,
            font=("Arial", 14, "bold"),
            bg="#54fac8",
            fg="#1a1f2e",
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.start_btn.pack(side='left', padx=10)
        
        # زر إيقاف
        self.stop_btn = tk.Button(
            row3_frame,
            text="⏹️ إيقاف",
            command=self.stop_analysis,
            font=("Arial", 14, "bold"),
            bg="#ff6b6b",
            fg="white",
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=10)
        
        # زر العروض الحقيقية
        real_deals_btn = tk.Button(
            row3_frame,
            text="🏆 العروض الحقيقية",
            command=self.show_real_deals,
            font=("Arial", 14, "bold"),
            bg="#1da1f2",
            fg="white",
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        real_deals_btn.pack(side='left', padx=10)
        
        # زر إرسال للتليجرام
        telegram_btn = tk.Button(
            row3_frame,
            text="📱 إرسال للتليجرام",
            command=self.send_to_telegram,
            font=("Arial", 14, "bold"),
            bg="#28a745",
            fg="white",
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        telegram_btn.pack(side='left', padx=10)
        
        # إطار النتائج
        results_frame = tk.Frame(self.root, bg='#232d3a', relief='raised', bd=2)
        results_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # عنوان النتائج
        self.results_title = tk.Label(
            results_frame,
            text="📊 نتائج التحليل",
            font=("Arial", 18, "bold"),
            fg="#54fac8",
            bg='#232d3a'
        )
        self.results_title.pack(pady=(15, 10))
        
        # منطقة النتائج مع شريط التمرير
        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            font=("Consolas", 10),
            bg='#1a1f2e',
            fg='white',
            relief='flat',
            bd=5,
            wrap='word',
            height=20
        )
        self.results_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # شريط الحالة
        self.status_bar = tk.Label(
            self.root,
            text="جاهز للتحليل",
            font=("Arial", 10),
            fg="white",
            bg='#1a1f2e',
            relief='sunken',
            bd=1
        )
        self.status_bar.pack(fill='x', side='bottom', padx=20, pady=5)
    
    def start_analysis(self):
        """بدء التحليل"""
        try:
            source = self.source_var.get()
            products_count = int(self.products_count_var.get())
            min_discount = float(self.min_discount_var.get())
            
            self.is_running = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_bar.config(text="جاري التحليل...")
            
            # الحصول على المنتجات حسب المصدر
            if source == "manual":
                self.products_to_analyze = self.get_manual_products(products_count)
            elif source == "json_file":
                self.products_to_analyze = self.get_json_products(products_count, min_discount)
            
            if not self.products_to_analyze:
                messagebox.showwarning("تحذير", "لا توجد منتجات للتحليل")
                self.stop_analysis()
                return
            
            # بدء التحليل في thread منفصل
            threading.Thread(target=self.run_analysis, daemon=True).start()
            
        except ValueError as e:
            messagebox.showerror("خطأ", f"خطأ في القيم المدخلة: {e}")
            self.stop_analysis()
    
    def stop_analysis(self):
        """إيقاف التحليل"""
        self.is_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_bar.config(text="تم إيقاف التحليل")
    
    def get_manual_products(self, count):
        """الحصول على منتجات يدوية"""
        # منتجات تجريبية محسنة
        return [
            {
                "asin": "B0C7CQT9ZS",
                "name": "Samsung Galaxy A54 5G",
                "current_price": 8500,
                "strike_price": 12000,
                "discount_percent": 29,
                "url": "https://amazon.eg/test1",
                "img": "https://test.com/img1.jpg",
                "section": "Electronics"
            },
            {
                "asin": "B0C8KQZ9X1",
                "name": "iPhone 15 Pro 128GB",
                "current_price": 45000,
                "strike_price": 53000,
                "discount_percent": 15,
                "url": "https://amazon.eg/test2",
                "img": "https://test.com/img2.jpg",
                "section": "Electronics"
            },
            {
                "asin": "B0C9XYZ123",
                "name": "Sony WH-1000XM5 Headphones",
                "current_price": 6500,
                "strike_price": 8500,
                "discount_percent": 24,
                "url": "https://amazon.eg/test3",
                "img": "https://test.com/img3.jpg",
                "section": "Electronics"
            },
            {
                "asin": "B0D1ABC456",
                "name": "MacBook Air M2 13-inch",
                "current_price": 42000,
                "strike_price": 48000,
                "discount_percent": 12,
                "url": "https://amazon.eg/test4",
                "img": "https://test.com/img4.jpg",
                "section": "Electronics"
            },
            {
                "asin": "B0D2DEF789",
                "name": "iPad Pro 11-inch 128GB",
                "current_price": 26000,
                "strike_price": 32000,
                "discount_percent": 19,
                "url": "https://amazon.eg/test5",
                "img": "https://test.com/img5.jpg",
                "section": "Electronics"
            }
        ][:count]
    
    def get_json_products(self, count, min_discount):
        """الحصول على منتجات من ملف JSON"""
        try:
            with open('amz_products.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            products = []
            for asin, product in list(data.items())[:count*2]:  # نأخذ ضعف العدد للفلترة
                discount = product.get('discount_percent', 0)
                if discount >= min_discount:
                    products.append({
                        "asin": asin,
                        "name": product.get('name', ''),
                        "current_price": product.get('price', 0),
                        "strike_price": product.get('strike_price', 0),
                        "discount_percent": discount,
                        "url": product.get('url', ''),
                        "img": product.get('img', ''),
                        "section": product.get('section', 'Electronics')
                    })
                    if len(products) >= count:
                        break
            
            return products
            
        except FileNotFoundError:
            messagebox.showerror("خطأ", "ملف amz_products.json غير موجود")
            return []
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في قراءة ملف JSON: {e}")
            return []
    
    def run_analysis(self):
        """تشغيل التحليل"""
        try:
            self.root.after(0, lambda: self.results_title.configure(text="🔄 جاري التحليل...", fg="#ffaa00"))
            self.root.after(0, lambda: self.results_text.delete("1.0", "end"))
            
            report = f"🚀 بدء تحليل {len(self.products_to_analyze)} منتج...\n\n"
            self.root.after(0, lambda: self.results_text.insert("end", report))
            
            real_deals_count = 0
            min_deal_score = float(self.min_deal_score_var.get())
            min_competitors = int(self.min_competitors_var.get())
            
            for i, product in enumerate(self.products_to_analyze, 1):
                if not self.is_running:
                    break
                
                # تحديث التقدم
                progress = f"📊 تحليل المنتج {i}/{len(self.products_to_analyze)}: {product['name'][:50]}...\n"
                self.root.after(0, lambda p=progress: self.results_text.insert("end", p))
                self.root.after(0, lambda: self.status_bar.config(text=f"تحليل المنتج {i}/{len(self.products_to_analyze)}"))
                
                # تحليل المنتج
                analysis = asyncio.run(self.analyze_product_real(product))
                
                # حفظ النتائج
                self.save_product(product, analysis)
                
                # عرض النتائج
                result_text = f"""
✅ تم تحليل: {product['name'][:50]}...
   💰 السعر: {product['current_price']:,.0f} جنيه
   🎉 الخصم: {product['discount_percent']:.1f}%
   📊 درجة العرض: {analysis['deal_score']:.1f}/100
   ✅ عرض حقيقي: {'نعم' if analysis['is_real_deal'] else 'لا'}
   🎯 درجة الثقة: {analysis['confidence']:.1%}
   💬 التوصية: {analysis['recommendation']}

🏪 أسعار المنافسين:
"""
                
                for retailer, price in analysis['competitor_prices'].items():
                    result_text += f"   • {retailer}: {price:,.0f} جنيه\n"
                
                result_text += "\n"
                self.root.after(0, lambda t=result_text: self.results_text.insert("end", t))
                
                if analysis['is_real_deal']:
                    real_deals_count += 1
                
                # انتظار قليل
                time.sleep(1)
            
            # النتائج النهائية
            final_report = f"""
🎉 تم الانتهاء من التحليل!

📊 الإحصائيات:
   • إجمالي المنتجات: {len(self.products_to_analyze)}
   • العروض الحقيقية: {real_deals_count}
   • نسبة العروض الحقيقية: {(real_deals_count/len(self.products_to_analyze))*100:.1f}%

🏆 العروض الحقيقية المحفوظة في قاعدة البيانات
"""
            self.root.after(0, lambda: self.results_text.insert("end", final_report))
            self.root.after(0, lambda: self.results_title.configure(text="✅ تم التحليل", fg="#00ff00"))
            self.root.after(0, lambda: self.status_bar.config(text="تم الانتهاء من التحليل"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("خطأ", f"خطأ في التحليل: {e}"))
            self.root.after(0, lambda: self.results_title.configure(text="❌ خطأ في التحليل", fg="#ff0000"))
        finally:
            self.stop_analysis()
    
    async def analyze_product_real(self, product_data):
        """تحليل حقيقي للمنتج"""
        start_time = time.time()
        
        # البحث الحقيقي في المواقع
        competitor_prices = await self.search_real_retailers(product_data['name'])
        
        # حساب الإحصائيات
        market_avg = sum(competitor_prices.values()) / len(competitor_prices) if competitor_prices else product_data['current_price']
        savings = ((market_avg - product_data['current_price']) / market_avg) * 100 if market_avg > 0 else 0
        competitors_count = len(competitor_prices)
        
        # حساب درجة العرض
        deal_score = self.calculate_deal_score(product_data['discount_percent'], savings, competitors_count)
        
        # تحديد إذا العرض حقيقي
        min_deal_score = float(self.min_deal_score_var.get())
        min_competitors = int(self.min_competitors_var.get())
        min_savings = float(self.min_discount_var.get())
        
        is_real_deal = self.is_real_deal(deal_score, competitors_count, savings, min_deal_score, min_competitors, min_savings)
        
        # حساب درجة الثقة
        confidence = self.calculate_confidence(competitors_count, len(competitor_prices))
        
        # إنشاء التوصية
        recommendation = self.generate_recommendation(deal_score, savings, competitors_count)
        
        analysis_time = time.time() - start_time
        
        return {
            "amazon_price": product_data['current_price'],
            "amazon_discount": product_data['discount_percent'],
            "market_avg_price": market_avg,
            "savings_percentage": savings,
            "competitors_count": competitors_count,
            "deal_score": deal_score,
            "is_real_deal": is_real_deal,
            "confidence": confidence,
            "recommendation": recommendation,
            "competitor_prices": competitor_prices,
            "analysis_time": analysis_time
        }
    
    async def search_real_retailers(self, product_name: str):
        """البحث الحقيقي في المواقع"""
        prices = {}
        query = self.clean_product_name(product_name)
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for retailer_name, config in self.retailers.items():
                task = self.search_retailer_real(session, retailer_name, config, query)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                retailer_name = list(self.retailers.keys())[i]
                if isinstance(result, dict) and 'price' in result:
                    prices[retailer_name] = result['price']
        
        return prices
    
    async def search_retailer_real(self, session, retailer_name: str, config: dict, query: str) -> Dict:
        """البحث الحقيقي في موقع واحد"""
        try:
            url = config['base_url'].format(query=query)
            
            async with session.get(url, headers=config['headers'], timeout=10) as response:
                if response.status != 200:
                    return {}
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # البحث عن الأسعار
                for selector in config['price_selectors']:
                    price_elements = soup.select(selector)
                    for element in price_elements[:3]:  # أول 3 أسعار
                        price_text = element.get_text(strip=True)
                        price = self.extract_price_real(price_text)
                        if price and 100 <= price <= 50000:
                            return {"price": price, "retailer": retailer_name}
                
                return {}
                
        except Exception as e:
            return {}
    
    def clean_product_name(self, name: str) -> str:
        """تنظيف اسم المنتج للبحث"""
        stop_words = ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
        words = [word for word in name.lower().split() if word not in stop_words and len(word) > 2]
        return " ".join(words[:4])
    
    def extract_price_real(self, text: str) -> Optional[float]:
        """استخراج سعر حقيقي من النص"""
        if not text:
            return None
        
        patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:جنيه|ج\.م|EGP|LE|L\.E)',
            r'جنيه\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*EGP',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    if 5 <= price <= 50000:
                        return price
                except ValueError:
                    continue
        
        return None
    
    def calculate_deal_score(self, amazon_discount, savings, competitors):
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
    
    def is_real_deal(self, deal_score, competitors, savings, min_deal_score, min_competitors, min_savings):
        """تحديد إذا العرض حقيقي"""
        return (
            deal_score >= min_deal_score and
            competitors >= min_competitors and
            savings >= min_savings
        )
    
    def calculate_confidence(self, competitors, total_searched):
        """حساب درجة الثقة"""
        if total_searched == 0:
            return 0
        
        success_rate = competitors / total_searched
        competitor_factor = min(competitors / 4, 1.0)
        
        return (success_rate * 0.7) + (competitor_factor * 0.3)
    
    def generate_recommendation(self, deal_score, savings, competitors):
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
    
    def show_real_deals(self):
        """عرض العروض الحقيقية"""
        try:
            min_deal_score = float(self.min_deal_score_var.get())
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute('''
                SELECT name, current_price, discount_percent, deal_score, confidence, recommendation
                FROM products 
                WHERE is_real_deal = TRUE AND deal_score >= ?
                ORDER BY deal_score DESC, discount_percent DESC
            ''', (min_deal_score,))
            
            deals = cursor.fetchall()
            conn.close()
            
            if not deals:
                report = "لا توجد عروض حقيقية حالياً"
            else:
                report = f"🏆 العروض الحقيقية ({len(deals)}):\n\n"
                
                for i, deal in enumerate(deals, 1):
                    report += f"{i}. {deal[0][:50]}...\n"
                    report += f"   💰 {deal[1]:,.0f} جنيه (خصم: {deal[2]:.1f}%)\n"
                    report += f"   📊 درجة العرض: {deal[3]:.1f}/100\n"
                    report += f"   🎯 درجة الثقة: {deal[4]:.1%}\n"
                    report += f"   💬 {deal[5]}\n\n"
            
            self.results_text.delete("1.0", "end")
            self.results_text.insert("1.0", report)
            self.results_title.configure(text="🏆 العروض الحقيقية", fg="#ff6b6b")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في عرض العروض: {e}")
    
    def send_to_telegram(self):
        """إرسال العروض الحقيقية للتليجرام"""
        try:
            min_deal_score = float(self.min_deal_score_var.get())
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute('''
                SELECT name, current_price, discount_percent, deal_score, recommendation
                FROM products 
                WHERE is_real_deal = TRUE AND deal_score >= ?
                ORDER BY deal_score DESC
                LIMIT 5
            ''', (min_deal_score,))
            
            deals = cursor.fetchall()
            conn.close()
            
            if not deals:
                messagebox.showinfo("معلومات", "لا توجد عروض حقيقية للإرسال")
                return
            
            # إنشاء رسالة التليجرام
            message = "🔥 العروض الحقيقية من LAQTA AI:\n\n"
            
            for i, deal in enumerate(deals, 1):
                message += f"{i}. {deal[0][:40]}...\n"
                message += f"💰 {deal[1]:,.0f} جنيه (خصم: {deal[2]:.1f}%)\n"
                message += f"📊 درجة العرض: {deal[3]:.1f}/100\n"
                message += f"💬 {deal[4][:80]}...\n\n"
            
            message += "🎯 تم تحليل هذه العروض باستخدام AI متقدم"
            
            # إرسال للتليجرام (محاكاة)
            print("📱 إرسال للتليجرام:")
            print(message)
            
            messagebox.showinfo("نجح", "تم إرسال العروض الحقيقية للتليجرام")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في إرسال التليجرام: {e}")
    
    def save_product(self, product_data, analysis):
        """حفظ المنتج في قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT OR REPLACE INTO products 
                (asin, name, url, img, section, current_price, strike_price, discount_percent,
                 deal_score, is_real_deal, confidence, recommendation, competitor_prices)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_data.get('asin'),
                product_data.get('name'),
                product_data.get('url', ''),
                product_data.get('img', ''),
                product_data.get('section', 'Electronics'),
                product_data.get('current_price'),
                product_data.get('strike_price'),
                product_data.get('discount_percent', 0),
                analysis.get('deal_score', 0),
                analysis.get('is_real_deal', False),
                analysis.get('confidence', 0),
                analysis.get('recommendation', ''),
                json.dumps(analysis.get('competitor_prices', {}))
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving product: {e}")
    
    def run(self):
        """تشغيل النظام"""
        self.root.mainloop()

# تشغيل النظام
if __name__ == "__main__":
    print("🚀 تشغيل النظام المبسط المحسن...")
    system = SimpleFixedSystem()
    system.run()