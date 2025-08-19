# integrated_ai_system.py
# نظام مدمج مع الاسكربت القديم

import asyncio
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import time
import random
import threading
import tkinter as tk
from tkinter import ttk, messagebox

class IntegratedAISystem:
    """نظام AI مدمج مع الاسكربت القديم"""
    
    def __init__(self):
        # بيانات تجريبية واقعية
        self.mock_prices = {
            "Samsung Galaxy A54 5G": {
                "Noon": 11200,
                "Kanbkam": 10800,
                "Pricena": 11500,
                "Carrefour": 12000
            },
            "iPhone 15 Pro 128GB": {
                "Noon": 52000,
                "Kanbkam": 51000,
                "Pricena": 53000,
                "Carrefour": 54000
            },
            "Sony WH-1000XM5 Headphones": {
                "Noon": 7200,
                "Kanbkam": 7000,
                "Pricena": 7500,
                "Carrefour": 7800
            },
            "MacBook Air M2": {
                "Noon": 45000,
                "Kanbkam": 44000,
                "Pricena": 46000,
                "Carrefour": 47000
            },
            "iPad Pro 11": {
                "Noon": 28000,
                "Kanbkam": 27500,
                "Pricena": 28500,
                "Carrefour": 29000
            }
        }
        
        # قاعدة البيانات
        self.db_path = "integrated_products.db"
        self.init_database()
        
        # قائمة المنتجات المحللة
        self.analyzed_products = []
        self.real_deals = []
        
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
                analysis_data TEXT,
                similar_product TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def setup_gui(self):
        """إعداد الواجهة"""
        self.root = tk.Tk()
        self.root.title("LAQTA AI - نظام مدمج")
        self.root.geometry("1200x900")
        self.root.configure(bg='#1a1f2e')
        
        # العنوان
        title_frame = tk.Frame(self.root, bg='#1a1f2e')
        title_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        title_label = tk.Label(
            title_frame,
            text="LAQTA AI - نظام مدمج",
            font=("Arial Black", 32, "bold"),
            fg="#54fac8",
            bg='#1a1f2e'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="مرتبط بالاسكربت القديم - تحليل تلقائي",
            font=("Arial", 14),
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
        
        # زر تحليل تلقائي
        auto_analyze_btn = tk.Button(
            buttons_frame,
            text="🤖 تحليل تلقائي",
            command=self.auto_analyze_products,
            font=("Arial", 14, "bold"),
            bg="#54fac8",
            fg="#1a1f2e",
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        auto_analyze_btn.pack(side='left', padx=10)
        
        # زر تحليل منتج واحد
        single_analyze_btn = tk.Button(
            buttons_frame,
            text="🔍 تحليل منتج واحد",
            command=self.analyze_single_product,
            font=("Arial", 14, "bold"),
            bg="#59ff9d",
            fg="#1a1f2e",
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        single_analyze_btn.pack(side='left', padx=10)
        
        # زر عرض العروض الحقيقية
        real_deals_btn = tk.Button(
            buttons_frame,
            text="🏆 العروض الحقيقية",
            command=self.show_real_deals,
            font=("Arial", 14, "bold"),
            bg="#ff6b6b",
            fg="white",
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        real_deals_btn.pack(side='left', padx=10)
        
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
    
    def auto_analyze_products(self):
        """تحليل تلقائي للمنتجات"""
        # محاكاة المنتجات من الاسكربت القديم
        mock_products = [
            {
                "asin": "B0C7CQT9ZS",
                "name": "Samsung Galaxy A54 5G",
                "url": "https://www.amazon.eg/test",
                "img": "https://test.com/image.jpg",
                "section": "Electronics",
                "current_price": 8500,
                "strike_price": 12000,
                "discount_percent": 29
            },
            {
                "asin": "B0C8KQZ9X1", 
                "name": "iPhone 15 Pro 128GB",
                "url": "https://www.amazon.eg/test2",
                "img": "https://test.com/image2.jpg",
                "section": "Electronics",
                "current_price": 45000,
                "strike_price": 53000,
                "discount_percent": 15
            },
            {
                "asin": "B0C9XYZ123",
                "name": "Sony WH-1000XM5 Headphones",
                "url": "https://www.amazon.eg/test3",
                "img": "https://test.com/image3.jpg",
                "section": "Electronics",
                "current_price": 6500,
                "strike_price": 8500,
                "discount_percent": 24
            },
            {
                "asin": "B0D1ABC456",
                "name": "MacBook Air M2 13-inch",
                "url": "https://www.amazon.eg/test4",
                "img": "https://test.com/image4.jpg",
                "section": "Electronics",
                "current_price": 42000,
                "strike_price": 48000,
                "discount_percent": 12
            },
            {
                "asin": "B0D2DEF789",
                "name": "iPad Pro 11-inch 128GB",
                "url": "https://www.amazon.eg/test5",
                "img": "https://test.com/image5.jpg",
                "section": "Electronics",
                "current_price": 26000,
                "strike_price": 32000,
                "discount_percent": 19
            }
        ]
        
        # بدء التحليل في thread منفصل
        threading.Thread(target=self.run_auto_analysis, args=(mock_products,), daemon=True).start()
    
    def run_auto_analysis(self, products):
        """تشغيل التحليل التلقائي"""
        try:
            self.root.after(0, lambda: self.results_title.configure(text="🔄 جاري التحليل...", fg="#ffaa00"))
            self.root.after(0, lambda: self.results_text.delete("1.0", "end"))
            
            report = "🚀 بدء التحليل التلقائي...\n\n"
            self.root.after(0, lambda: self.results_text.insert("end", report))
            
            total_products = len(products)
            real_deals_count = 0
            
            for i, product in enumerate(products, 1):
                # تحديث التقدم
                progress = f"📊 تحليل المنتج {i}/{total_products}: {product['name']}\n"
                self.root.after(0, lambda p=progress: self.results_text.insert("end", p))
                
                # تحليل المنتج
                analysis = asyncio.run(self.analyze_product(product))
                
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

"""
                self.root.after(0, lambda t=result_text: self.results_text.insert("end", t))
                
                if analysis['is_real_deal']:
                    real_deals_count += 1
                
                # محاكاة وقت التحليل
                time.sleep(0.5)
            
            # النتائج النهائية
            final_report = f"""
🎉 تم الانتهاء من التحليل!

📊 الإحصائيات:
   • إجمالي المنتجات: {total_products}
   • العروض الحقيقية: {real_deals_count}
   • نسبة العروض الحقيقية: {(real_deals_count/total_products)*100:.1f}%

🏆 العروض الحقيقية المحفوظة في قاعدة البيانات
"""
            self.root.after(0, lambda: self.results_text.insert("end", final_report))
            self.root.after(0, lambda: self.results_title.configure(text="✅ تم التحليل", fg="#00ff00"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("خطأ", f"خطأ في التحليل التلقائي: {e}"))
            self.root.after(0, lambda: self.results_title.configure(text="❌ خطأ في التحليل", fg="#ff0000"))
    
    def analyze_single_product(self):
        """تحليل منتج واحد"""
        # إنشاء نافذة إدخال
        input_window = tk.Toplevel(self.root)
        input_window.title("تحليل منتج واحد")
        input_window.geometry("400x300")
        input_window.configure(bg='#1a1f2e')
        
        # حقول الإدخال
        tk.Label(input_window, text="اسم المنتج:", font=("Arial", 12), fg="white", bg='#1a1f2e').pack(pady=5)
        name_entry = tk.Entry(input_window, font=("Arial", 12), bg='#232d3a', fg='white')
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
            analysis = asyncio.run(self.analyze_product(product))
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
                SELECT name, current_price, discount_percent, deal_score, confidence, recommendation
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
                    report += f"{i}. {deal[0]}\n"
                    report += f"   💰 {deal[1]:,.0f} جنيه (خصم: {deal[2]:.1f}%)\n"
                    report += f"   📊 درجة العرض: {deal[3]:.1f}/100\n"
                    report += f"   💬 {deal[5]}\n\n"
            
            self.results_text.delete("1.0", "end")
            self.results_text.insert("1.0", report)
            self.results_title.configure(text="🏆 العروض الحقيقية", fg="#ff6b6b")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في عرض العروض: {e}")
    
    async def analyze_product(self, product_data):
        """تحليل المنتج"""
        start_time = time.time()
        
        amazon_price = product_data.get('current_price', 0)
        amazon_discount = product_data.get('discount_percent', 0)
        product_name = product_data.get('name', '')
        
        if not amazon_price or not product_name:
            return self._empty_analysis(amazon_price, amazon_discount)
        
        # البحث عن منتج مشابه
        similar_product = self.find_similar_product(product_name)
        
        if similar_product:
            prices = self.mock_prices[similar_product].copy()
            
            # تغييرات عشوائية
            for retailer in prices:
                variation = random.uniform(-0.05, 0.05)
                prices[retailer] = int(prices[retailer] * (1 + variation))
            
            # محاكاة بعض المواقع التي لا تعمل
            if random.random() < 0.2:
                if "Pricena" in prices:
                    del prices["Pricena"]
            
            if random.random() < 0.15:
                if "Carrefour" in prices:
                    del prices["Carrefour"]
            
            # حساب الإحصائيات
            market_avg = sum(prices.values()) / len(prices)
            savings = ((market_avg - amazon_price) / market_avg) * 100
            competitors_count = len(prices)
        else:
            market_avg = amazon_price
            savings = 0
            competitors_count = 0
            prices = {}
        
        # حساب درجة العرض
        deal_score = self._calculate_deal_score(amazon_discount, savings, competitors_count)
        
        # تحديد إذا العرض حقيقي
        is_real_deal = self._is_real_deal(deal_score, competitors_count, savings)
        
        # حساب درجة الثقة
        confidence = self._calculate_confidence(competitors_count, len(prices), similar_product)
        
        # إنشاء التوصية
        recommendation = self._generate_recommendation(deal_score, savings, competitors_count)
        
        # تحديد المخاطر
        risk_factors = self._identify_risks(amazon_price, amazon_discount, prices)
        
        analysis_time = time.time() - start_time
        
        return {
            "amazon_price": amazon_price,
            "amazon_discount": amazon_discount,
            "market_avg_price": market_avg,
            "savings_percentage": savings,
            "competitors_count": competitors_count,
            "deal_score": deal_score,
            "is_real_deal": is_real_deal,
            "confidence": confidence,
            "recommendation": recommendation,
            "risk_factors": risk_factors,
            "competitor_prices": prices,
            "analysis_time": analysis_time,
            "similar_product": similar_product
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
    
    def _calculate_deal_score(self, amazon_discount, savings, competitors):
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
    
    def _is_real_deal(self, deal_score, competitors, savings):
        """تحديد إذا العرض حقيقي"""
        return (
            deal_score >= 70 and
            competitors >= 2 and
            savings >= 15
        )
    
    def _calculate_confidence(self, competitors, total_searched, similar_product):
        """حساب درجة الثقة"""
        if total_searched == 0:
            return 0
        
        success_rate = competitors / total_searched
        competitor_factor = min(competitors / 4, 1.0)
        similarity_factor = 1.0 if similar_product else 0.5
        
        return (success_rate * 0.5) + (competitor_factor * 0.3) + (similarity_factor * 0.2)
    
    def _generate_recommendation(self, deal_score, savings, competitors):
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
    
    def _identify_risks(self, amazon_price, amazon_discount, prices):
        """تحديد المخاطر"""
        risks = []
        
        if amazon_price < 50 and amazon_discount > 80:
            risks.append("سعر منخفض جداً - قد يكون منتج مستعمل")
        
        if amazon_discount > 90:
            risks.append("خصم مفرط - قد يكون خطأ في السعر")
        
        if len(prices) < 2:
            risks.append("قلة المنافسين - صعوبة في التأكد")
        
        if prices:
            price_variance = (max(prices.values()) - min(prices.values())) / min(prices.values())
            if price_variance > 0.5:
                risks.append("تباين كبير في الأسعار - قد يكون اختلاف في المواصفات")
        
        return risks
    
    def _empty_analysis(self, amazon_price, amazon_discount):
        """تحليل فارغ"""
        return {
            "amazon_price": amazon_price,
            "amazon_discount": amazon_discount,
            "market_avg_price": 0,
            "savings_percentage": 0,
            "competitors_count": 0,
            "deal_score": 0,
            "is_real_deal": False,
            "confidence": 0,
            "recommendation": "لا توجد بيانات كافية",
            "risk_factors": ["لا توجد مقارنات متاحة"],
            "competitor_prices": {},
            "analysis_time": 0,
            "similar_product": None
        }
    
    def save_product(self, product_data, analysis):
        """حفظ المنتج في قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT OR REPLACE INTO products 
                (asin, name, url, img, section, current_price, strike_price, discount_percent,
                 deal_score, is_real_deal, confidence, recommendation, analysis_data, similar_product)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                json.dumps(analysis),
                analysis.get('similar_product', '')
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
    print("🚀 تشغيل النظام المدمج...")
    system = IntegratedAISystem()
    system.run()