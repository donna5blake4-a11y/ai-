# simple_gui.py
# واجهة مستخدم بسيطة وجميلة

import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
import time
import random
from datetime import datetime

class SimpleAIDealsGUI:
    """واجهة مستخدم بسيطة لنظام AI العروض"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LAQTA AI - محلل العروض الذكي")
        self.root.geometry("1000x800")
        self.root.configure(bg='#1a1f2e')
        
        # بيانات تجريبية
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
        
        self.setup_ui()
    
    def setup_ui(self):
        """إعداد الواجهة"""
        # العنوان الرئيسي
        title_frame = tk.Frame(self.root, bg='#1a1f2e')
        title_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        title_label = tk.Label(
            title_frame,
            text="LAQTA AI",
            font=("Arial Black", 36, "bold"),
            fg="#54fac8",
            bg='#1a1f2e'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="محلل العروض الذكي - درجة ثقة 70%+",
            font=("Arial", 14),
            fg="#59ff9d",
            bg='#1a1f2e'
        )
        subtitle_label.pack()
        
        # إطار التحليل
        analysis_frame = tk.Frame(self.root, bg='#232d3a', relief='raised', bd=2)
        analysis_frame.pack(fill='x', padx=20, pady=10)
        
        # عنوان التحليل
        analysis_title = tk.Label(
            analysis_frame,
            text="🔍 تحليل منتج جديد",
            font=("Arial", 18, "bold"),
            fg="#54fac8",
            bg='#232d3a'
        )
        analysis_title.pack(pady=(15, 10))
        
        # حقول الإدخال
        input_frame = tk.Frame(analysis_frame, bg='#232d3a')
        input_frame.pack(fill='x', padx=20, pady=10)
        
        # اسم المنتج
        tk.Label(input_frame, text="اسم المنتج:", font=("Arial", 12), fg="white", bg='#232d3a').pack(anchor="w")
        self.product_name_entry = tk.Entry(
            input_frame,
            font=("Arial", 12),
            bg='#1a1f2e',
            fg='white',
            insertbackground='white',
            relief='flat',
            bd=5
        )
        self.product_name_entry.pack(fill='x', pady=(5, 15))
        self.product_name_entry.insert(0, "Samsung Galaxy A54 5G")
        
        # إطار الأسعار
        price_frame = tk.Frame(input_frame, bg='#232d3a')
        price_frame.pack(fill='x', pady=5)
        
        # السعر الحالي
        tk.Label(price_frame, text="السعر الحالي (جنيه):", font=("Arial", 12), fg="white", bg='#232d3a').grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.current_price_entry = tk.Entry(
            price_frame,
            font=("Arial", 12),
            bg='#1a1f2e',
            fg='white',
            insertbackground='white',
            relief='flat',
            bd=5
        )
        self.current_price_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.current_price_entry.insert(0, "8500")
        
        # السعر الأصلي
        tk.Label(price_frame, text="السعر الأصلي (جنيه):", font=("Arial", 12), fg="white", bg='#232d3a').grid(row=0, column=1, sticky="w", padx=10)
        self.original_price_entry = tk.Entry(
            price_frame,
            font=("Arial", 12),
            bg='#1a1f2e',
            fg='white',
            insertbackground='white',
            relief='flat',
            bd=5
        )
        self.original_price_entry.grid(row=1, column=1, sticky="ew", padx=10)
        self.original_price_entry.insert(0, "12000")
        
        price_frame.columnconfigure(0, weight=1)
        price_frame.columnconfigure(1, weight=1)
        
        # زر التحليل
        analyze_btn = tk.Button(
            analysis_frame,
            text="🤖 تحليل العرض",
            command=self.analyze_product,
            font=("Arial", 14, "bold"),
            bg="#54fac8",
            fg="#1a1f2e",
            relief='flat',
            bd=0,
            padx=30,
            pady=10,
            cursor='hand2'
        )
        analyze_btn.pack(pady=20)
        
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
            font=("Consolas", 11),
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
    
    def analyze_product(self):
        """تحليل المنتج"""
        # الحصول على البيانات
        product_name = self.product_name_entry.get().strip()
        current_price = self.current_price_entry.get().strip()
        original_price = self.original_price_entry.get().strip()
        
        if not product_name or not current_price or not original_price:
            messagebox.showerror("خطأ", "يرجى ملء جميع الحقول المطلوبة")
            return
        
        try:
            current_price = float(current_price)
            original_price = float(original_price)
        except ValueError:
            messagebox.showerror("خطأ", "يرجى إدخال أسعار صحيحة")
            return
        
        # حساب نسبة الخصم
        discount_percent = ((original_price - current_price) / original_price) * 100
        
        # بدء التحليل في thread منفصل
        threading.Thread(target=self.run_analysis, args=(product_name, current_price, original_price, discount_percent), daemon=True).start()
    
    def run_analysis(self, product_name, current_price, original_price, discount_percent):
        """تشغيل التحليل"""
        try:
            # محاكاة وقت التحليل
            time.sleep(1)
            
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
                savings = ((market_avg - current_price) / market_avg) * 100
                competitors_count = len(prices)
                
                # حساب درجة العرض
                deal_score = self.calculate_deal_score(discount_percent, savings, competitors_count)
                
                # تحديد إذا العرض حقيقي
                is_real_deal = self.is_real_deal(deal_score, competitors_count, savings)
                
                # حساب درجة الثقة
                confidence = self.calculate_confidence(competitors_count, len(prices), similar_product)
                
                # إنشاء التوصية
                recommendation = self.generate_recommendation(deal_score, savings, competitors_count)
                
                # تحديد المخاطر
                risk_factors = self.identify_risks(current_price, discount_percent, prices)
                
                # عرض النتائج
                self.root.after(0, lambda: self.display_results(
                    product_name, current_price, original_price, discount_percent,
                    market_avg, savings, competitors_count, deal_score, is_real_deal,
                    confidence, recommendation, prices, similar_product, risk_factors
                ))
            else:
                # لا يوجد منتج مشابه
                self.root.after(0, lambda: self.display_no_results(
                    product_name, current_price, original_price, discount_percent
                ))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("خطأ", f"خطأ في التحليل: {e}"))
    
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
    
    def calculate_confidence(self, competitors, total_searched, similar_product):
        """حساب درجة الثقة"""
        if total_searched == 0:
            return 0
        
        success_rate = competitors / total_searched
        competitor_factor = min(competitors / 4, 1.0)
        similarity_factor = 1.0 if similar_product else 0.5
        
        return (success_rate * 0.5) + (competitor_factor * 0.3) + (similarity_factor * 0.2)
    
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
    
    def identify_risks(self, amazon_price, amazon_discount, prices):
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
    
    def display_results(self, product_name, current_price, original_price, discount_percent,
                       market_avg, savings, competitors_count, deal_score, is_real_deal,
                       confidence, recommendation, prices, similar_product, risk_factors):
        """عرض النتائج"""
        self.results_text.delete("1.0", "end")
        
        report = f"""
🎯 تحليل المنتج: {product_name}

💰 معلومات السعر:
   • سعر أمازون: {current_price:,.0f} جنيه
   • السعر الأصلي: {original_price:,.0f} جنيه
   • نسبة الخصم: {discount_percent:.1f}%

🔍 نتائج البحث في السوق:
   • متوسط السوق: {market_avg:,.0f} جنيه
   • عدد المنافسين: {competitors_count}
   • نسبة التوفير: {savings:.1f}%

🏪 أسعار المنافسين:
"""
        
        for retailer, price in prices.items():
            report += f"   • {retailer}: {price:,.0f} جنيه\n"
        
        report += f"""
📊 تقييم العرض:
   • درجة العرض: {deal_score:.1f}/100
   • درجة الثقة: {confidence:.1%}
   • عرض حقيقي: {'نعم' if is_real_deal else 'لا'}

💬 التوصية: {recommendation}
"""
        
        if similar_product:
            report += f"🔍 منتج مشابه: {similar_product}\n"
        
        if risk_factors:
            report += "\n⚠️ عوامل المخاطر:\n"
            for risk in risk_factors:
                report += f"   • {risk}\n"
        
        # عرض التقرير
        self.results_text.insert("1.0", report)
        
        # تغيير لون العنوان
        if is_real_deal:
            self.results_title.configure(text="🎉 عرض حقيقي! - نتائج التحليل", fg="#00ff00")
        else:
            self.results_title.configure(text="📊 نتائج التحليل", fg="#54fac8")
    
    def display_no_results(self, product_name, current_price, original_price, discount_percent):
        """عرض النتائج عندما لا توجد مقارنات"""
        self.results_text.delete("1.0", "end")
        
        report = f"""
🎯 تحليل المنتج: {product_name}

💰 معلومات السعر:
   • سعر أمازون: {current_price:,.0f} جنيه
   • السعر الأصلي: {original_price:,.0f} جنيه
   • نسبة الخصم: {discount_percent:.1f}%

🔍 نتائج البحث في السوق:
   • لا توجد مقارنات متاحة
   • لا يمكن تحديد جودة العرض

📊 تقييم العرض:
   • درجة العرض: 0/100
   • درجة الثقة: 0%
   • عرض حقيقي: لا

💬 التوصية: لا توجد بيانات كافية للتحليل

⚠️ عوامل المخاطر:
   • لا توجد مقارنات متاحة
   • صعوبة في التأكد من جودة العرض
"""
        
        self.results_text.insert("1.0", report)
        self.results_title.configure(text="📊 نتائج التحليل", fg="#54fac8")
    
    def run(self):
        """تشغيل الواجهة"""
        self.root.mainloop()

# تشغيل الواجهة
if __name__ == "__main__":
    print("🚀 تشغيل واجهة AI العروض...")
    app = SimpleAIDealsGUI()
    app.run()