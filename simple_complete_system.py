# simple_complete_system.py
# نسخة مبسطة تعمل مباشرة

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
from bs4 import BeautifulSoup

class SimpleCompleteSystem:
    """نظام مبسط يعمل مباشرة"""
    
    def __init__(self):
        # قاعدة البيانات
        self.db_path = "simple_products.db"
        self.init_database()
        
        # إعدادات البحث المبسطة
        self.retailers = {
            "Noon": {
                "base_url": "https://www.noon.com/egypt/search?q={query}",
                "price_selectors": [".price", ".amount", "[data-testid='price']", ".product-price"],
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            },
            "Kanbkam": {
                "base_url": "https://www.kanbkam.com/search?q={query}",
                "price_selectors": [".price", ".amount", ".product-price", "[class*='price']"],
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            }
        }
        
        # بيانات تجريبية للاختبار
        self.mock_prices = {
            "Samsung Galaxy A54 5G": {
                "Noon": 11200,
                "Kanbkam": 10800
            },
            "iPhone 15 Pro 128GB": {
                "Noon": 52000,
                "Kanbkam": 51000
            },
            "Sony WH-1000XM5 Headphones": {
                "Noon": 7200,
                "Kanbkam": 7000
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
        self.root.title("LAQTA AI - النظام المبسط")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1a1f2e')
        
        # العنوان
        title_frame = tk.Frame(self.root, bg='#1a1f2e')
        title_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        title_label = tk.Label(
            title_frame,
            text="LAQTA AI - النظام المبسط",
            font=("Arial Black", 24, "bold"),
            fg="#54fac8",
            bg='#1a1f2e'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="🔍 بحث مبسط + 📊 تحليل + 💾 قاعدة بيانات",
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
        
        # زر تحليل تجريبي
        test_analyze_btn = tk.Button(
            buttons_frame,
            text="🧪 تحليل تجريبي",
            command=self.test_analysis,
            font=("Arial", 12, "bold"),
            bg="#54fac8",
            fg="#1a1f2e",
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2'
        )
        test_analyze_btn.pack(side='left', padx=5)
        
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
    
    def test_analysis(self):
        """تحليل تجريبي"""
        # منتجات تجريبية
        test_products = [
            {
                "asin": "B0C7CQT9ZS",
                "name": "Samsung Galaxy A54 5G",
                "current_price": 8500,
                "strike_price": 12000,
                "discount_percent": 29
            },
            {
                "asin": "B0C8KQZ9X1",
                "name": "iPhone 15 Pro 128GB",
                "current_price": 45000,
                "strike_price": 53000,
                "discount_percent": 15
            },
            {
                "asin": "B0C9XYZ123",
                "name": "Sony WH-1000XM5 Headphones",
                "current_price": 6500,
                "strike_price": 8500,
                "discount_percent": 24
            }
        ]
        
        # بدء التحليل
        threading.Thread(target=self.run_test_analysis, args=(test_products,), daemon=True).start()
    
    def run_test_analysis(self, products):
        """تشغيل التحليل التجريبي"""
        try:
            self.root.after(0, lambda: self.results_title.configure(text="🔄 جاري التحليل...", fg="#ffaa00"))
            self.root.after(0, lambda: self.results_text.delete("1.0", "end"))
            
            report = f"🚀 بدء تحليل {len(products)} منتج تجريبي...\n\n"
            self.root.after(0, lambda: self.results_text.insert("end", report))
            
            real_deals_count = 0
            
            for i, product in enumerate(products, 1):
                # تحديث التقدم
                progress = f"📊 تحليل المنتج {i}/{len(products)}: {product['name']}\n"
                self.root.after(0, lambda p=progress: self.results_text.insert("end", p))
                
                # تحليل المنتج
                analysis = self.analyze_product_simple(product)
                
                # حفظ النتائج
                self.save_product(product, analysis)
                
                # عرض النتائج
                result_text = f"""
✅ تم تحليل: {product['name']}
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
                time.sleep(0.5)
            
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
    
    def analyze_product_simple(self, product_data):
        """تحليل مبسط للمنتج"""
        # البحث عن منتج مشابه
        similar_product = self.find_similar_product(product_data['name'])
        
        if similar_product:
            prices = self.mock_prices[similar_product].copy()
            
            # تغييرات عشوائية
            for retailer in prices:
                variation = random.uniform(-0.05, 0.05)
                prices[retailer] = int(prices[retailer] * (1 + variation))
        else:
            prices = {}
        
        # حساب الإحصائيات
        market_avg = sum(prices.values()) / len(prices) if prices else product_data['current_price']
        savings = ((market_avg - product_data['current_price']) / market_avg) * 100 if market_avg > 0 else 0
        competitors_count = len(prices)
        
        # حساب درجة العرض
        deal_score = self.calculate_deal_score(product_data['discount_percent'], savings, competitors_count)
        
        # تحديد إذا العرض حقيقي
        is_real_deal = self.is_real_deal(deal_score, competitors_count, savings)
        
        # حساب درجة الثقة
        confidence = self.calculate_confidence(competitors_count, len(prices))
        
        # إنشاء التوصية
        recommendation = self.generate_recommendation(deal_score, savings, competitors_count)
        
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
            "competitor_prices": prices
        }
    
    def find_similar_product(self, product_name: str):
        """البحث عن منتج مشابه"""
        product_name_lower = product_name.lower()
        
        for mock_product in self.mock_prices.keys():
            mock_lower = mock_product.lower()
            
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
            analysis = self.analyze_product_simple(product)
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

💬 التوصية: {analysis['recommendation']}
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
                SELECT name, current_price, discount_percent, deal_score, recommendation
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
                    report += f"   💬 {deal[4]}\n\n"
            
            self.results_text.delete("1.0", "end")
            self.results_text.insert("1.0", report)
            self.results_title.configure(text="🏆 العروض الحقيقية", fg="#ff6b6b")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في عرض العروض: {e}")
    
    def save_product(self, product_data, analysis):
        """حفظ المنتج في قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT OR REPLACE INTO products 
                (asin, name, current_price, strike_price, discount_percent,
                 deal_score, is_real_deal, confidence, recommendation, competitor_prices)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_data.get('asin'),
                product_data.get('name'),
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
    print("🚀 تشغيل النظام المبسط...")
    system = SimpleCompleteSystem()
    system.run()