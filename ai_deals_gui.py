# ai_deals_gui.py
# واجهة مستخدم جميلة لنظام AI العروض

import customtkinter as ctk
import asyncio
import threading
import json
from datetime import datetime
from real_working_system import RealAIAnalyzer, RealDatabaseManager
import webbrowser

# إعداد الواجهة
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class AIDealsGUI:
    """واجهة مستخدم لنظام AI العروض"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("LAQTA AI - محلل العروض الذكي")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # إنشاء المحلل وقاعدة البيانات
        self.analyzer = RealAIAnalyzer()
        self.db_manager = RealDatabaseManager()
        
        # متغيرات
        self.current_analysis = None
        self.real_deals = []
        
        # إنشاء الواجهة
        self.setup_ui()
        self.load_real_deals()
    
    def setup_ui(self):
        """إعداد الواجهة"""
        # العنوان الرئيسي
        title_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="LAQTA AI",
            font=("Arial Black", 48, "bold"),
            text_color="#54fac8"
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="محلل العروض الذكي - درجة ثقة 70%+",
            font=("Arial", 16),
            text_color="#59ff9d"
        )
        subtitle_label.pack()
        
        # إطار التحليل
        analysis_frame = ctk.CTkFrame(self.root, fg_color="#1a1f2e")
        analysis_frame.pack(fill="x", padx=20, pady=10)
        
        # عنوان التحليل
        analysis_title = ctk.CTkLabel(
            analysis_frame,
            text="🔍 تحليل منتج جديد",
            font=("Arial", 20, "bold"),
            text_color="#54fac8"
        )
        analysis_title.pack(pady=(15, 10))
        
        # حقول الإدخال
        input_frame = ctk.CTkFrame(analysis_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=10)
        
        # اسم المنتج
        ctk.CTkLabel(input_frame, text="اسم المنتج:", font=("Arial", 14)).pack(anchor="w")
        self.product_name_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="مثال: Samsung Galaxy A54 5G",
            height=40,
            font=("Arial", 14)
        )
        self.product_name_entry.pack(fill="x", pady=(5, 15))
        
        # الأسعار
        price_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        price_frame.pack(fill="x", pady=5)
        price_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # السعر الحالي
        ctk.CTkLabel(price_frame, text="السعر الحالي (جنيه):", font=("Arial", 14)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.current_price_entry = ctk.CTkEntry(
            price_frame,
            placeholder_text="8500",
            height=35,
            font=("Arial", 14)
        )
        self.current_price_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        
        # السعر الأصلي
        ctk.CTkLabel(price_frame, text="السعر الأصلي (جنيه):", font=("Arial", 14)).grid(row=0, column=1, sticky="w", padx=10)
        self.original_price_entry = ctk.CTkEntry(
            price_frame,
            placeholder_text="12000",
            height=35,
            font=("Arial", 14)
        )
        self.original_price_entry.grid(row=1, column=1, sticky="ew", padx=10)
        
        # رابط المنتج
        ctk.CTkLabel(price_frame, text="رابط المنتج:", font=("Arial", 14)).grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.product_url_entry = ctk.CTkEntry(
            price_frame,
            placeholder_text="https://www.amazon.eg/...",
            height=35,
            font=("Arial", 14)
        )
        self.product_url_entry.grid(row=1, column=2, sticky="ew", padx=(10, 0))
        
        # زر التحليل
        analyze_btn = ctk.CTkButton(
            analysis_frame,
            text="🤖 تحليل العرض",
            command=self.analyze_product,
            height=50,
            font=("Arial", 16, "bold"),
            fg_color="#54fac8",
            text_color="#1a1f2e"
        )
        analyze_btn.pack(pady=20)
        
        # إطار النتائج
        self.results_frame = ctk.CTkFrame(self.root, fg_color="#1a1f2e")
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # عنوان النتائج
        self.results_title = ctk.CTkLabel(
            self.results_frame,
            text="📊 نتائج التحليل",
            font=("Arial", 20, "bold"),
            text_color="#54fac8"
        )
        self.results_title.pack(pady=(15, 10))
        
        # منطقة النتائج
        self.results_text = ctk.CTkTextbox(
            self.results_frame,
            font=("Consolas", 14),
            fg_color="#232d3a",
            text_color="#ffffff"
        )
        self.results_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # إطار العروض الحقيقية
        deals_frame = ctk.CTkFrame(self.root, fg_color="#1a1f2e")
        deals_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # عنوان العروض
        deals_title = ctk.CTkLabel(
            deals_frame,
            text="🏆 العروض الحقيقية",
            font=("Arial", 20, "bold"),
            text_color="#54fac8"
        )
        deals_title.pack(pady=(15, 10))
        
        # قائمة العروض
        self.deals_listbox = ctk.CTkTextbox(
            deals_frame,
            height=200,
            font=("Consolas", 12),
            fg_color="#232d3a",
            text_color="#ffffff"
        )
        self.deals_listbox.pack(fill="x", padx=20, pady=(0, 20))
    
    def analyze_product(self):
        """تحليل المنتج"""
        # الحصول على البيانات
        product_name = self.product_name_entry.get().strip()
        current_price = self.current_price_entry.get().strip()
        original_price = self.original_price_entry.get().strip()
        product_url = self.product_url_entry.get().strip()
        
        if not product_name or not current_price or not original_price:
            self.show_message("⚠️ يرجى ملء جميع الحقول المطلوبة")
            return
        
        try:
            current_price = float(current_price)
            original_price = float(original_price)
        except ValueError:
            self.show_message("⚠️ يرجى إدخال أسعار صحيحة")
            return
        
        # حساب نسبة الخصم
        discount_percent = ((original_price - current_price) / original_price) * 100
        
        # إنشاء بيانات المنتج
        product_data = {
            "asin": f"B{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": product_name,
            "url": product_url,
            "img": "",
            "section": "Electronics",
            "current_price": current_price,
            "strike_price": original_price,
            "discount_percent": discount_percent
        }
        
        # بدء التحليل في thread منفصل
        threading.Thread(target=self.run_analysis, args=(product_data,), daemon=True).start()
    
    def run_analysis(self, product_data):
        """تشغيل التحليل"""
        try:
            # تشغيل التحليل
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            analysis = loop.run_until_complete(self.analyzer.analyze_deal(product_data))
            loop.close()
            
            # حفظ النتائج
            self.db_manager.save_product(product_data, analysis)
            
            # عرض النتائج
            self.root.after(0, lambda: self.display_results(product_data, analysis))
            
            # تحديث قائمة العروض
            self.root.after(0, self.load_real_deals)
            
        except Exception as e:
            self.root.after(0, lambda: self.show_message(f"❌ خطأ في التحليل: {e}"))
    
    def display_results(self, product_data, analysis):
        """عرض نتائج التحليل"""
        self.results_text.delete("1.0", "end")
        
        # إنشاء التقرير
        report = f"""
🎯 تحليل المنتج: {product_data['name']}

💰 معلومات السعر:
   • سعر أمازون: {product_data['current_price']:,.0f} جنيه
   • السعر الأصلي: {product_data['strike_price']:,.0f} جنيه
   • نسبة الخصم: {product_data['discount_percent']:.1f}%

🔍 نتائج البحث في السوق:
"""
        
        if analysis['competitor_prices']:
            report += f"   • متوسط السوق: {analysis['market_avg_price']:,.0f} جنيه\n"
            report += f"   • عدد المنافسين: {analysis['competitors_count']}\n"
            report += f"   • نسبة التوفير: {analysis['savings_percentage']:.1f}%\n\n"
            
            report += "🏪 أسعار المنافسين:\n"
            for retailer, price in analysis['competitor_prices'].items():
                report += f"   • {retailer}: {price:,.0f} جنيه\n"
        else:
            report += "   • لا توجد مقارنات متاحة\n"
        
        report += f"""
📊 تقييم العرض:
   • درجة العرض: {analysis['deal_score']:.1f}/100
   • درجة الثقة: {analysis['confidence']:.1%}
   • عرض حقيقي: {'نعم' if analysis['is_real_deal'] else 'لا'}

💬 التوصية: {analysis['recommendation']}
"""
        
        if analysis['similar_product']:
            report += f"🔍 منتج مشابه: {analysis['similar_product']}\n"
        
        if analysis['risk_factors']:
            report += "\n⚠️ عوامل المخاطر:\n"
            for risk in analysis['risk_factors']:
                report += f"   • {risk}\n"
        
        report += f"\n⏱️ وقت التحليل: {analysis['analysis_time']:.2f}s"
        
        # عرض التقرير
        self.results_text.insert("1.0", report)
        
        # تغيير لون العنوان حسب النتيجة
        if analysis['is_real_deal']:
            self.results_title.configure(text="🎉 عرض حقيقي! - نتائج التحليل", text_color="#00ff00")
        else:
            self.results_title.configure(text="📊 نتائج التحليل", text_color="#54fac8")
    
    def load_real_deals(self):
        """تحميل العروض الحقيقية"""
        try:
            self.real_deals = self.db_manager.get_real_deals()
            self.update_deals_display()
        except Exception as e:
            print(f"Error loading deals: {e}")
    
    def update_deals_display(self):
        """تحديث عرض العروض"""
        self.deals_listbox.delete("1.0", "end")
        
        if not self.real_deals:
            self.deals_listbox.insert("1.0", "لا توجد عروض حقيقية حالياً")
            return
        
        deals_text = f"تم العثور على {len(self.real_deals)} عرض حقيقي:\n\n"
        
        for i, deal in enumerate(self.real_deals, 1):
            deals_text += f"{i}. {deal['name']}\n"
            deals_text += f"   💰 {deal['current_price']:,.0f} جنيه (خصم: {deal['discount_percent']:.1f}%)\n"
            deals_text += f"   📊 درجة العرض: {deal['deal_score']:.1f}/100\n"
            deals_text += f"   💬 {deal['recommendation']}\n"
            if deal['similar_product']:
                deals_text += f"   🔍 مشابه: {deal['similar_product']}\n"
            deals_text += "\n"
        
        self.deals_listbox.insert("1.0", deals_text)
    
    def show_message(self, message):
        """عرض رسالة"""
        # يمكن إضافة نافذة منبثقة هنا
        print(message)
    
    def run(self):
        """تشغيل الواجهة"""
        self.root.mainloop()

# دالة تشغيل سريعة
def quick_test():
    """اختبار سريع"""
    print("🚀 تشغيل واجهة AI العروض...")
    app = AIDealsGUI()
    app.run()

if __name__ == "__main__":
    quick_test()