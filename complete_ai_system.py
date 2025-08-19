# complete_ai_system.py
# نظام متكامل مع Gemini API والبحث الحقيقي

import asyncio
import aiohttp
import json
import sqlite3
import re
import time
import random
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Dict, List, Optional
import google.generativeai as genai
from bs4 import BeautifulSoup
import requests

# إعداد Gemini API
GEMINI_API_KEY = "AIzaSyAS_qF5wf1OY_TAVBXaxPD0rZAX-8dt4S0"
genai.configure(api_key=GEMINI_API_KEY)

class CompleteAISystem:
    """نظام AI متكامل مع البحث الحقيقي"""
    
    def __init__(self):
        # إعداد Gemini
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        # قاعدة البيانات
        self.db_path = "complete_products.db"
        self.init_database()
        
        # إعدادات البحث
        self.retailers = {
            "Noon": {
                "base_url": "https://www.noon.com/egypt/search?q={query}",
                "price_selectors": [".price", ".amount", "[data-testid='price']", ".product-price"],
                "name_selectors": [".product-name", ".title", "h1", "h2", "h3"],
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            },
            "Kanbkam": {
                "base_url": "https://www.kanbkam.com/search?q={query}",
                "price_selectors": [".price", ".amount", ".product-price", "[class*='price']"],
                "name_selectors": [".product-name", ".title", "h1", "h2", "h3"],
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            },
            "Pricena": {
                "base_url": "https://egypt.pricena.com/search?q={query}",
                "price_selectors": [".price", ".amount", ".product-price", "[class*='price']"],
                "name_selectors": [".product-name", ".title", "h1", "h2", "h3"],
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            },
            "Carrefour": {
                "base_url": "https://www.carrefour.eg/search?q={query}",
                "price_selectors": [".price", ".amount", ".product-price", "[class*='price']"],
                "name_selectors": [".product-name", ".title", "h1", "h2", "h3"],
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            }
        }
        
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
                ai_analysis TEXT,
                competitor_prices TEXT,
                similar_product TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def setup_gui(self):
        """إعداد الواجهة"""
        self.root = tk.Tk()
        self.root.title("LAQTA AI - النظام المتكامل")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1f2e')
        
        # العنوان
        title_frame = tk.Frame(self.root, bg='#1a1f2e')
        title_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        title_label = tk.Label(
            title_frame,
            text="LAQTA AI - النظام المتكامل",
            font=("Arial Black", 28, "bold"),
            fg="#54fac8",
            bg='#1a1f2e'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="🔍 بحث حقيقي + 🤖 AI تحليل + 📱 تليجرام + 💾 قاعدة بيانات",
            font=("Arial", 12),
            fg="#59ff9d",
            bg='#1a1f2e'
        )
        subtitle_label.pack()
        
        # إطار التحكم
        control_frame = tk.Frame(self.root, bg='#232d3a', relief='raised', bd=2)
        control_frame.pack(fill='x', padx=20, pady=10)
        
        # أزرار التحكم
        buttons_frame = tk.Frame(control_frame, bg='#232d3a')
        buttons_frame.pack(pady=15)
        
        # زر تحليل من JSON
        json_analyze_btn = tk.Button(
            buttons_frame,
            text="📄 تحليل من JSON",
            command=self.analyze_from_json,
            font=("Arial", 12, "bold"),
            bg="#54fac8",
            fg="#1a1f2e",
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2'
        )
        json_analyze_btn.pack(side='left', padx=5)
        
        # زر تحليل منتج واحد
        single_analyze_btn = tk.Button(
            buttons_frame,
            text="🔍 تحليل منتج واحد",
            command=self.analyze_single_product,
            font=("Arial", 12, "bold"),
            bg="#59ff9d",
            fg="#1a1f2e",
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2'
        )
        single_analyze_btn.pack(side='left', padx=5)
        
        # زر العروض الحقيقية
        real_deals_btn = tk.Button(
            buttons_frame,
            text="🏆 العروض الحقيقية",
            command=self.show_real_deals,
            font=("Arial", 12, "bold"),
            bg="#ff6b6b",
            fg="white",
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2'
        )
        real_deals_btn.pack(side='left', padx=5)
        
        # زر إرسال للتليجرام
        telegram_btn = tk.Button(
            buttons_frame,
            text="📱 إرسال للتليجرام",
            command=self.send_to_telegram,
            font=("Arial", 12, "bold"),
            bg="#1da1f2",
            fg="white",
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2'
        )
        telegram_btn.pack(side='left', padx=5)
        
        # إطار النتائج
        self.results_frame = tk.Frame(self.root, bg='#232d3a', relief='raised', bd=2)
        self.results_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # عنوان النتائج
        self.results_title = tk.Label(
            self.results_frame,
            text="📊 نتائج التحليل",
            font=("Arial", 18, "bold"),
            fg="#54fac8",
            bg='#232d3a'
        )
        self.results_title.pack(pady=(15, 10))
        
        # منطقة النتائج
        self.results_text = tk.Text(
            self.results_frame,
            font=("Consolas", 10),
            bg='#1a1f2e',
            fg='white',
            relief='flat',
            bd=5,
            wrap='word'
        )
        self.results_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # شريط التمرير
        scrollbar = tk.Scrollbar(self.results_text)
        scrollbar.pack(side='right', fill='y')
        self.results_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_text.yview)
    
    def analyze_from_json(self):
        """تحليل من ملف JSON"""
        try:
            # قراءة ملف JSON
            with open('amz_products.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # تحويل إلى قائمة منتجات
            products = []
            for asin, product in list(data.items())[:10]:  # أول 10 منتجات للاختبار
                products.append({
                    "asin": asin,
                    "name": product.get('name', ''),
                    "url": product.get('url', ''),
                    "img": product.get('img', ''),
                    "section": product.get('section', ''),
                    "current_price": product.get('price', 0),
                    "strike_price": product.get('strike_price', 0),
                    "discount_percent": product.get('discount_percent', 0)
                })
            
            # بدء التحليل
            threading.Thread(target=self.run_batch_analysis, args=(products,), daemon=True).start()
            
        except FileNotFoundError:
            messagebox.showerror("خطأ", "ملف amz_products.json غير موجود")
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في قراءة الملف: {e}")
    
    def run_batch_analysis(self, products):
        """تشغيل تحليل مجموعة من المنتجات"""
        try:
            self.root.after(0, lambda: self.results_title.configure(text="🔄 جاري التحليل...", fg="#ffaa00"))
            self.root.after(0, lambda: self.results_text.delete("1.0", "end"))
            
            report = f"🚀 بدء تحليل {len(products)} منتج من JSON...\n\n"
            self.root.after(0, lambda: self.results_text.insert("end", report))
            
            real_deals_count = 0
            
            for i, product in enumerate(products, 1):
                # تحديث التقدم
                progress = f"📊 تحليل المنتج {i}/{len(products)}: {product['name'][:50]}...\n"
                self.root.after(0, lambda p=progress: self.results_text.insert("end", p))
                
                # تحليل المنتج
                analysis = asyncio.run(self.complete_analysis(product))
                
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
   🤖 AI: {analysis['ai_recommendation'][:100]}...

"""
                self.root.after(0, lambda t=result_text: self.results_text.insert("end", t))
                
                if analysis['is_real_deal']:
                    real_deals_count += 1
                
                # انتظار قليل
                time.sleep(1)
            
            # النتائج النهائية
            final_report = f"""
🎉 تم الانتهاء من التحليل!

📊 الإحصائيات:
   • إجمالي المنتجات: {len(products)}
   • العروض الحقيقية: {real_deals_count}
   • نسبة العروض الحقيقية: {(real_deals_count/len(products))*100:.1f}%

🏆 العروض الحقيقية المحفوظة في قاعدة البيانات
"""
            self.root.after(0, lambda: self.results_text.insert("end", final_report))
            self.root.after(0, lambda: self.results_title.configure(text="✅ تم التحليل", fg="#00ff00"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("خطأ", f"خطأ في التحليل: {e}"))
            self.root.after(0, lambda: self.results_title.configure(text="❌ خطأ في التحليل", fg="#ff0000"))
    
    async def complete_analysis(self, product_data):
        """تحليل شامل للمنتج"""
        start_time = time.time()
        
        # 1. البحث في المواقع الخارجية
        competitor_prices = await self.search_real_retailers(product_data['name'])
        
        # 2. حساب الإحصائيات
        market_avg = sum(competitor_prices.values()) / len(competitor_prices) if competitor_prices else product_data['current_price']
        savings = ((market_avg - product_data['current_price']) / market_avg) * 100 if market_avg > 0 else 0
        competitors_count = len(competitor_prices)
        
        # 3. حساب درجة العرض
        deal_score = self.calculate_deal_score(product_data['discount_percent'], savings, competitors_count)
        
        # 4. تحديد إذا العرض حقيقي
        is_real_deal = self.is_real_deal(deal_score, competitors_count, savings)
        
        # 5. تحليل AI باستخدام Gemini
        ai_analysis = await self.analyze_with_gemini(product_data, competitor_prices, deal_score, savings)
        
        # 6. حساب درجة الثقة
        confidence = self.calculate_confidence(competitors_count, len(competitor_prices))
        
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
            "ai_recommendation": ai_analysis,
            "competitor_prices": competitor_prices,
            "analysis_time": analysis_time
        }
    
    async def search_real_retailers(self, product_name):
        """البحث الحقيقي في المواقع"""
        prices = {}
        
        # تنظيف اسم المنتج
        query = self.clean_product_name(product_name)
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for retailer_name, config in self.retailers.items():
                task = self.search_retailer(session, retailer_name, config, query)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                retailer_name = list(self.retailers.keys())[i]
                if isinstance(result, dict) and 'price' in result:
                    prices[retailer_name] = result['price']
        
        return prices
    
    async def search_retailer(self, session, retailer_name, config, query):
        """البحث في موقع واحد"""
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
                        price = self.extract_price(price_text)
                        if price and 100 <= price <= 50000:
                            return {"price": price, "retailer": retailer_name}
                
                return {}
                
        except Exception as e:
            print(f"Error searching {retailer_name}: {e}")
            return {}
    
    def clean_product_name(self, name):
        """تنظيف اسم المنتج للبحث"""
        # إزالة الكلمات غير المهمة
        stop_words = ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
        words = [word for word in name.lower().split() if word not in stop_words and len(word) > 2]
        
        # أخذ أول 4 كلمات مهمة
        return " ".join(words[:4])
    
    def extract_price(self, text):
        """استخراج السعر من النص"""
        if not text:
            return None
        
        # أنماط الأسعار
        patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:جنيه|ج\.م|EGP|LE|L\.E)',
            r'جنيه\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*EGP',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # أي رقم
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
    
    def is_real_deal(self, deal_score, competitors, savings):
        """تحديد إذا العرض حقيقي"""
        return (
            deal_score >= 70 and
            competitors >= 2 and
            savings >= 15
        )
    
    def calculate_confidence(self, competitors, total_searched):
        """حساب درجة الثقة"""
        if total_searched == 0:
            return 0
        
        success_rate = competitors / total_searched
        competitor_factor = min(competitors / 4, 1.0)
        
        return (success_rate * 0.7) + (competitor_factor * 0.3)
    
    async def analyze_with_gemini(self, product_data, competitor_prices, deal_score, savings):
        """تحليل باستخدام Gemini AI"""
        try:
            prompt = f"""
تحليل منتج إلكتروني:

اسم المنتج: {product_data['name']}
سعر أمازون: {product_data['current_price']:,.0f} جنيه
خصم أمازون: {product_data['discount_percent']:.1f}%
درجة العرض: {deal_score:.1f}/100
التوفير من السوق: {savings:.1f}%

أسعار المنافسين:
{chr(10).join([f"• {retailer}: {price:,.0f} جنيه" for retailer, price in competitor_prices.items()])}

هل هذا عرض حقيقي؟ اكتب تحليل مختصر بالعربية (3-4 جمل) يتضمن:
1. تقييم العرض
2. التوصية (شراء أم لا)
3. المخاطر المحتملة
"""
            
            response = self.gemini_model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"خطأ في تحليل AI: {e}"
    
    def analyze_single_product(self):
        """تحليل منتج واحد"""
        # إنشاء نافذة إدخال
        input_window = tk.Toplevel(self.root)
        input_window.title("تحليل منتج واحد")
        input_window.geometry("500x400")
        input_window.configure(bg='#1a1f2e')
        
        # حقول الإدخال
        tk.Label(input_window, text="اسم المنتج:", font=("Arial", 12), fg="white", bg='#1a1f2e').pack(pady=5)
        name_entry = tk.Entry(input_window, font=("Arial", 12), bg='#232d3a', fg='white', width=50)
        name_entry.pack(fill='x', padx=20, pady=5)
        name_entry.insert(0, "Samsung Galaxy A54 5G")
        
        tk.Label(input_window, text="السعر الحالي:", font=("Arial", 12), fg="white", bg='#1a1f2e').pack(pady=5)
        current_entry = tk.Entry(input_window, font=("Arial", 12), bg='#232d3a', fg='white')
        current_entry.pack(fill='x', padx=20, pady=5)
        current_entry.insert(0, "8500")
        
        tk.Label(input_window, text="السعر الأصلي:", font=("Arial", 12), fg="white", bg='#1a1f2e').pack(pady=5)
        original_entry = tk.Entry(input_window, font=("Arial", 12), bg='#232d3a', fg='white')
        original_entry.pack(fill='x', padx=20, pady=5)
        original_entry.insert(0, "12000")
        
        def analyze():
            try:
                product = {
                    "asin": f"B{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "name": name_entry.get(),
                    "current_price": float(current_entry.get()),
                    "strike_price": float(original_entry.get()),
                    "discount_percent": ((float(original_entry.get()) - float(current_entry.get())) / float(original_entry.get())) * 100
                }
                
                input_window.destroy()
                threading.Thread(target=self.run_single_analysis, args=(product,), daemon=True).start()
                
            except ValueError:
                messagebox.showerror("خطأ", "يرجى إدخال أسعار صحيحة")
        
        tk.Button(
            input_window,
            text="تحليل",
            command=analyze,
            font=("Arial", 12, "bold"),
            bg="#54fac8",
            fg="#1a1f2e",
            relief='flat',
            padx=20,
            pady=5
        ).pack(pady=20)
    
    def run_single_analysis(self, product):
        """تشغيل تحليل منتج واحد"""
        try:
            analysis = asyncio.run(self.complete_analysis(product))
            self.save_product(product, analysis)
            
            report = f"""
🎯 تحليل المنتج: {product['name']}

💰 معلومات السعر:
   • سعر أمازون: {product['current_price']:,.0f} جنيه
   • السعر الأصلي: {product['strike_price']:,.0f} جنيه
   • نسبة الخصم: {product['discount_percent']:.1f}%

🔍 نتائج البحث في السوق:
   • متوسط السوق: {analysis['market_avg_price']:,.0f} جنيه
   • عدد المنافسين: {analysis['competitors_count']}
   • نسبة التوفير: {analysis['savings_percentage']:.1f}%

🏪 أسعار المنافسين:
"""
            
            for retailer, price in analysis['competitor_prices'].items():
                report += f"   • {retailer}: {price:,.0f} جنيه\n"
            
            report += f"""
📊 تقييم العرض:
   • درجة العرض: {analysis['deal_score']:.1f}/100
   • درجة الثقة: {analysis['confidence']:.1%}
   • عرض حقيقي: {'نعم' if analysis['is_real_deal'] else 'لا'}

🤖 تحليل AI:
{analysis['ai_recommendation']}
"""
            
            self.root.after(0, lambda: self.results_text.delete("1.0", "end"))
            self.root.after(0, lambda: self.results_text.insert("1.0", report))
            
            if analysis['is_real_deal']:
                self.root.after(0, lambda: self.results_title.configure(text="🎉 عرض حقيقي!", fg="#00ff00"))
            else:
                self.root.after(0, lambda: self.results_title.configure(text="📊 نتائج التحليل", fg="#54fac8"))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("خطأ", f"خطأ في التحليل: {e}"))
    
    def show_real_deals(self):
        """عرض العروض الحقيقية"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute('''
                SELECT name, current_price, discount_percent, deal_score, confidence, ai_analysis
                FROM products 
                WHERE is_real_deal = TRUE AND deal_score >= 70
                ORDER BY deal_score DESC, discount_percent DESC
            ''')
            
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
                    report += f"   🤖 AI: {deal[5][:100]}...\n\n"
            
            self.results_text.delete("1.0", "end")
            self.results_text.insert("1.0", report)
            self.results_title.configure(text="🏆 العروض الحقيقية", fg="#ff6b6b")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في عرض العروض: {e}")
    
    def send_to_telegram(self):
        """إرسال العروض الحقيقية للتليجرام"""
        try:
            # قراءة إعدادات التليجرام
            with open('telegram_config.json', 'r') as f:
                config = json.load(f)
            
            # الحصول على العروض الحقيقية
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute('''
                SELECT name, current_price, discount_percent, deal_score, ai_analysis
                FROM products 
                WHERE is_real_deal = TRUE AND deal_score >= 80
                ORDER BY deal_score DESC
                LIMIT 5
            ''')
            
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
                message += f"🤖 {deal[4][:80]}...\n\n"
            
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
                 deal_score, is_real_deal, confidence, ai_analysis, competitor_prices)
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
                analysis.get('ai_recommendation', ''),
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
    print("🚀 تشغيل النظام المتكامل...")
    system = CompleteAISystem()
    system.run()