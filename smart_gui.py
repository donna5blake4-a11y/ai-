# smart_gui.py - واجهة النظام الذكي (بدون AI)

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import os
from datetime import datetime
import sqlite3

# استيراد النظام الذكي
from smart_amazon_system import SmartAmazonSystem

class SmartGUI:
    """واجهة النظام الذكي"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 نظام LAQTA الذكي - مقارنة أسعار + أمازون فقط")
        self.root.geometry("800x600")
        self.root.configure(bg='#1a1a1a')
        
        # متغيرات النظام
        self.system = None
        self.is_running = False
        
        # إعدادات قابلة للتعديل
        self.min_discount = tk.IntVar(value=15)
        self.max_discount = tk.IntVar(value=85)
        self.min_price = tk.IntVar(value=50)
        self.max_price = tk.IntVar(value=10000)
        self.min_quality_score = tk.IntVar(value=65)
        self.max_deals = tk.IntVar(value=15)
        self.send_images = tk.BooleanVar(value=True)
        
        self.setup_gui()
        self.check_system_status()
    
    def setup_gui(self):
        """إعداد واجهة المستخدم"""
        
        # إعداد الألوان
        self.colors = {
            'bg': '#1a1a1a',
            'card': '#2d2d2d',
            'accent': '#4CAF50',
            'warning': '#FF9800',
            'error': '#F44336',
            'text': '#ffffff'
        }
        
        # الشريط العلوي
        header_frame = tk.Frame(self.root, bg=self.colors['accent'], height=80)
        header_frame.pack(fill='x', padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🤖 نظام LAQTA الذكي",
            font=('Arial', 18, 'bold'),
            bg=self.colors['accent'],
            fg='white'
        )
        title_label.pack(pady=15)
        
        subtitle_label = tk.Label(
            header_frame,
            text="تحليل ذكي + مقارنة أسعار + أمازون فقط + إرسال فوري بالصور",
            font=('Arial', 10),
            bg=self.colors['accent'],
            fg='white'
        )
        subtitle_label.pack()
        
        # إطار التبويبات
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # تبويب التحكم الرئيسي
        self.setup_main_tab()
        
        # تبويب الإعدادات
        self.setup_settings_tab()
        
        # تبويب النتائج
        self.setup_results_tab()
    
    def setup_main_tab(self):
        """إعداد تبويب التحكم الرئيسي"""
        
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="🚀 التحكم الرئيسي")
        
        # حالة النظام
        status_frame = tk.Frame(main_frame, bg=self.colors['card'], relief='ridge', bd=2)
        status_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(
            status_frame,
            text="📊 حالة النظام",
            font=('Arial', 12, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(pady=5)
        
        self.status_label = tk.Label(
            status_frame,
            text="⏸️ متوقف",
            font=('Arial', 10),
            bg=self.colors['card'],
            fg=self.colors['warning']
        )
        self.status_label.pack(pady=5)
        
        # أزرار التحكم
        control_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        control_frame.pack(fill='x', padx=10, pady=10)
        
        # الصف الأول من الأزرار
        row1_frame = tk.Frame(control_frame, bg=self.colors['bg'])
        row1_frame.pack(fill='x', pady=5)
        
        self.start_btn = tk.Button(
            row1_frame,
            text="🚀 بدء النظام الذكي",
            font=('Arial', 12, 'bold'),
            bg=self.colors['accent'],
            fg='white',
            command=self.start_smart_system,
            height=2,
            relief='flat'
        )
        self.start_btn.pack(side='left', padx=5, fill='x', expand=True)
        
        self.stop_btn = tk.Button(
            row1_frame,
            text="⏹️ إيقاف النظام",
            font=('Arial', 12, 'bold'),
            bg=self.colors['error'],
            fg='white',
            command=self.stop_system,
            height=2,
            relief='flat',
            state='disabled'
        )
        self.stop_btn.pack(side='right', padx=5, fill='x', expand=True)
        
        # الصف الثاني من الأزرار
        row2_frame = tk.Frame(control_frame, bg=self.colors['bg'])
        row2_frame.pack(fill='x', pady=5)
        
        tk.Button(
            row2_frame,
            text="📊 عرض النتائج",
            font=('Arial', 11),
            bg=self.colors['warning'],
            fg='white',
            command=self.show_results,
            height=2,
            relief='flat'
        ).pack(side='left', padx=5, fill='x', expand=True)
        
        tk.Button(
            row2_frame,
            text="🌐 اختبار مقارنة أسعار",
            font=('Arial', 11),
            bg='#2196F3',
            fg='white',
            command=self.test_price_comparison,
            height=2,
            relief='flat'
        ).pack(side='right', padx=5, fill='x', expand=True)
        
        # سجل الأحداث
        log_frame = tk.Frame(main_frame, bg=self.colors['card'], relief='ridge', bd=2)
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(
            log_frame,
            text="📝 سجل الأحداث",
            font=('Arial', 12, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Consolas', 9),
            wrap='word'
        )
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def setup_settings_tab(self):
        """إعداد تبويب الإعدادات"""
        
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ الإعدادات")
        
        # إطار قابل للتمرير
        canvas = tk.Canvas(settings_frame, bg=self.colors['bg'])
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # إعدادات الخصم
        discount_frame = tk.LabelFrame(
            scrollable_frame,
            text="💰 إعدادات الخصم",
            font=('Arial', 11, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text'],
            relief='ridge',
            bd=2
        )
        discount_frame.pack(fill='x', padx=10, pady=10)
        
        # نسبة الخصم الدنيا
        self.min_discount_label = tk.Label(
            discount_frame,
            text=f"الحد الأدنى للخصم: {self.min_discount.get()}%",
            bg=self.colors['card'],
            fg=self.colors['text']
        )
        self.min_discount_label.pack(pady=5)
        
        min_discount_scale = tk.Scale(
            discount_frame,
            from_=5, to=50,
            orient='horizontal',
            variable=self.min_discount,
            bg=self.colors['card'],
            fg=self.colors['text'],
            highlightbackground=self.colors['card'],
            command=self.update_labels
        )
        min_discount_scale.pack(fill='x', padx=10, pady=5)
        
        # نسبة الخصم العليا
        self.max_discount_label = tk.Label(
            discount_frame,
            text=f"الحد الأعلى للخصم: {self.max_discount.get()}%",
            bg=self.colors['card'],
            fg=self.colors['text']
        )
        self.max_discount_label.pack(pady=5)
        
        max_discount_scale = tk.Scale(
            discount_frame,
            from_=50, to=95,
            orient='horizontal',
            variable=self.max_discount,
            bg=self.colors['card'],
            fg=self.colors['text'],
            highlightbackground=self.colors['card'],
            command=self.update_labels
        )
        max_discount_scale.pack(fill='x', padx=10, pady=5)
        
        # إعدادات السعر
        price_frame = tk.LabelFrame(
            scrollable_frame,
            text="💵 إعدادات السعر",
            font=('Arial', 11, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text'],
            relief='ridge',
            bd=2
        )
        price_frame.pack(fill='x', padx=10, pady=10)
        
        # الحد الأدنى للسعر
        self.min_price_label = tk.Label(
            price_frame,
            text=f"الحد الأدنى للسعر: {self.min_price.get()} جنيه",
            bg=self.colors['card'],
            fg=self.colors['text']
        )
        self.min_price_label.pack(pady=5)
        
        min_price_scale = tk.Scale(
            price_frame,
            from_=10, to=500,
            orient='horizontal',
            variable=self.min_price,
            bg=self.colors['card'],
            fg=self.colors['text'],
            highlightbackground=self.colors['card'],
            command=self.update_labels
        )
        min_price_scale.pack(fill='x', padx=10, pady=5)
        
        # الحد الأعلى للسعر
        self.max_price_label = tk.Label(
            price_frame,
            text=f"الحد الأعلى للسعر: {self.max_price.get()} جنيه",
            bg=self.colors['card'],
            fg=self.colors['text']
        )
        self.max_price_label.pack(pady=5)
        
        max_price_scale = tk.Scale(
            price_frame,
            from_=1000, to=20000,
            orient='horizontal',
            variable=self.max_price,
            bg=self.colors['card'],
            fg=self.colors['text'],
            highlightbackground=self.colors['card'],
            command=self.update_labels
        )
        max_price_scale.pack(fill='x', padx=10, pady=5)
        
        # إعدادات الجودة
        quality_frame = tk.LabelFrame(
            scrollable_frame,
            text="🎯 إعدادات الجودة",
            font=('Arial', 11, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text'],
            relief='ridge',
            bd=2
        )
        quality_frame.pack(fill='x', padx=10, pady=10)
        
        # الحد الأدنى للجودة
        self.quality_label = tk.Label(
            quality_frame,
            text=f"الحد الأدنى للجودة: {self.min_quality_score.get()}/100",
            bg=self.colors['card'],
            fg=self.colors['text']
        )
        self.quality_label.pack(pady=5)
        
        quality_scale = tk.Scale(
            quality_frame,
            from_=40, to=90,
            orient='horizontal',
            variable=self.min_quality_score,
            bg=self.colors['card'],
            fg=self.colors['text'],
            highlightbackground=self.colors['card'],
            command=self.update_labels
        )
        quality_scale.pack(fill='x', padx=10, pady=5)
        
        # عدد العروض المستهدف
        self.deals_label = tk.Label(
            quality_frame,
            text=f"عدد العروض المستهدف: {self.max_deals.get()} عرض",
            bg=self.colors['card'],
            fg=self.colors['text']
        )
        self.deals_label.pack(pady=5)
        
        deals_scale = tk.Scale(
            quality_frame,
            from_=5, to=30,
            orient='horizontal',
            variable=self.max_deals,
            bg=self.colors['card'],
            fg=self.colors['text'],
            highlightbackground=self.colors['card'],
            command=self.update_labels
        )
        deals_scale.pack(fill='x', padx=10, pady=5)
        
        # إرسال الصور
        tk.Checkbutton(
            quality_frame,
            text="📸 إرسال الصور مع العروض",
            variable=self.send_images,
            bg=self.colors['card'],
            fg=self.colors['text'],
            selectcolor=self.colors['accent'],
            font=('Arial', 10)
        ).pack(pady=10)
        
        # زر حفظ الإعدادات
        tk.Button(
            scrollable_frame,
            text="💾 حفظ الإعدادات",
            font=('Arial', 11, 'bold'),
            bg=self.colors['accent'],
            fg='white',
            command=self.save_settings,
            relief='flat',
            height=2
        ).pack(fill='x', padx=10, pady=20)
    
    def setup_results_tab(self):
        """إعداد تبويب النتائج"""
        
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="📊 النتائج")
        
        # أزرار التحكم بالنتائج
        results_control_frame = tk.Frame(results_frame, bg=self.colors['bg'])
        results_control_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Button(
            results_control_frame,
            text="🔄 تحديث النتائج",
            font=('Arial', 10),
            bg=self.colors['accent'],
            fg='white',
            command=self.refresh_results,
            relief='flat'
        ).pack(side='left', padx=5)
        
        tk.Button(
            results_control_frame,
            text="🗑️ مسح النتائج",
            font=('Arial', 10),
            bg=self.colors['error'],
            fg='white',
            command=self.clear_results,
            relief='flat'
        ).pack(side='right', padx=5)
        
        # عرض النتائج
        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Consolas', 9),
            wrap='word'
        )
        self.results_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def update_labels(self, value=None):
        """تحديث التسميات"""
        
        try:
            self.min_discount_label.config(text=f"الحد الأدنى للخصم: {self.min_discount.get()}%")
            self.max_discount_label.config(text=f"الحد الأعلى للخصم: {self.max_discount.get()}%")
            self.min_price_label.config(text=f"الحد الأدنى للسعر: {self.min_price.get()} جنيه")
            self.max_price_label.config(text=f"الحد الأعلى للسعر: {self.max_price.get()} جنيه")
            self.quality_label.config(text=f"الحد الأدنى للجودة: {self.min_quality_score.get()}/100")
            self.deals_label.config(text=f"عدد العروض المستهدف: {self.max_deals.get()} عرض")
        except:
            pass
    
    def check_system_status(self):
        """فحص حالة النظام"""
        
        try:
            # فحص ملفات الإعداد
            config_status = "❌"
            if os.path.exists('telegram_config.json'):
                config_status = "✅"
            
            # فحص ملف JSON
            json_status = "❌"
            json_files = [f for f in os.listdir('.') if f.endswith('.json') and 
                         f not in ['config.json', 'telegram_config.json']]
            if json_files:
                json_status = "✅"
            
            # تحديث حالة النظام
            if config_status == "✅" and json_status == "✅":
                self.status_label.config(text="✅ جاهز للتشغيل", fg=self.colors['accent'])
            else:
                status_text = f"الإعدادات: {config_status} | JSON: {json_status}"
                self.status_label.config(text=f"⚠️ {status_text}", fg=self.colors['warning'])
            
        except Exception as e:
            self.status_label.config(text="❌ خطأ في فحص النظام", fg=self.colors['error'])
    
    def start_smart_system(self):
        """بدء النظام الذكي"""
        
        if self.is_running:
            messagebox.showwarning("تحذير", "النظام قيد التشغيل بالفعل!")
            return
        
        self.is_running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_label.config(text="🚀 قيد التشغيل...", fg=self.colors['accent'])
        
        # بدء النظام في thread منفصل
        thread = threading.Thread(target=self.run_smart_system_thread, daemon=True)
        thread.start()
    
    def run_smart_system_thread(self):
        """تشغيل النظام في thread منفصل"""
        
        try:
            self.log("🚀 بدء النظام الذكي...")
            self.log("=" * 50)
            
            # إنشاء النظام مع الإعدادات الحالية
            self.system = SmartAmazonSystem()
            
            # تطبيق الإعدادات
            self.system.min_discount = self.min_discount.get()
            self.system.max_discount = self.max_discount.get()
            self.system.min_price = self.min_price.get()
            self.system.max_price = self.max_price.get()
            self.system.min_quality_score = self.min_quality_score.get()
            self.system.send_with_images = self.send_images.get()
            
            self.log(f"⚙️ الإعدادات: خصم {self.min_discount.get()}-{self.max_discount.get()}%, سعر {self.min_price.get()}-{self.max_price.get()} جنيه")
            self.log(f"🎯 الحد الأدنى للجودة: {self.min_quality_score.get()}/100")
            self.log(f"🎯 العروض المستهدفة: {self.max_deals.get()} عرض")
            
            # تشغيل النظام
            deals = self.system.run_smart_system()
            
            # عرض النتائج
            approved = [d for d in deals if d.get('is_approved', False)]
            
            self.log("=" * 50)
            self.log(f"✅ انتهى النظام!")
            self.log(f"📊 إجمالي العروض المكتشفة: {len(deals)}")
            self.log(f"🎯 العروض المعتمدة ذكياً: {len(approved)}")
            self.log(f"📤 العروض المرسلة: {len(approved)}")
            
            if approved:
                self.log("\n🎉 أفضل العروض المرسلة:")
                for i, deal in enumerate(approved[:5], 1):
                    name = deal.get('name', '')[:40]
                    price = deal.get('price', 0)
                    discount = deal.get('discount_percent', 0)
                    quality_score = deal.get('quality_score', 0)
                    self.log(f"   {i}. {name}... - {price:.0f} جنيه ({discount:.1f}%) - جودة: {quality_score:.0f}/100")
            
        except Exception as e:
            self.log(f"❌ خطأ في النظام: {e}")
            import traceback
            self.log(traceback.format_exc())
        
        finally:
            # إعادة تعيين حالة الأزرار
            self.root.after(0, self.reset_buttons)
    
    def stop_system(self):
        """إيقاف النظام"""
        
        self.is_running = False
        self.log("⏹️ تم إيقاف النظام")
        self.reset_buttons()
    
    def reset_buttons(self):
        """إعادة تعيين حالة الأزرار"""
        
        self.is_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_label.config(text="⏸️ متوقف", fg=self.colors['warning'])
    
    def test_price_comparison(self):
        """اختبار مقارنة الأسعار"""
        
        def test_thread():
            try:
                self.log("🌐 اختبار مقارنة الأسعار...")
                
                # إنشاء نظام للاختبار
                test_system = SmartAmazonSystem()
                
                # منتج تجريبي
                test_product = "Samsung Galaxy Buds"
                test_price = 1200
                
                self.log(f"🔍 البحث عن: {test_product}")
                self.log(f"💰 سعر أمازون: {test_price} جنيه")
                
                # مقارنة الأسعار
                comparison_data = test_system.compare_prices_online(test_product, test_price)
                
                if comparison_data:
                    self.log("✅ تمت مقارنة الأسعار بنجاح:")
                    for site, price in comparison_data.get('competitor_prices', {}).items():
                        self.log(f"   🏪 {site}: {price:.0f} جنيه")
                    
                    savings = comparison_data.get('savings_vs_avg', 0)
                    if savings > 0:
                        self.log(f"💰 توفير مقابل المتوسط: {savings:.0f} جنيه")
                    else:
                        self.log(f"❌ أغلى من المتوسط بـ {abs(savings):.0f} جنيه")
                else:
                    self.log("❌ فشل في مقارنة الأسعار")
                
            except Exception as e:
                self.log(f"❌ خطأ في اختبار مقارنة الأسعار: {e}")
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def show_results(self):
        """عرض النتائج"""
        
        def load_results():
            try:
                self.results_text.delete(1.0, tk.END)
                
                if not os.path.exists("smart_deals.db"):
                    self.results_text.insert(tk.END, "❌ لا توجد نتائج محفوظة\n")
                    return
                
                conn = sqlite3.connect("smart_deals.db")
                cursor = conn.cursor()
                
                # العروض المرسلة اليوم
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute('''
                    SELECT name, price, discount_percent, quality_score, section, is_verified_deal
                    FROM deals 
                    WHERE is_sent = 1 AND date_found LIKE ?
                    ORDER BY quality_score DESC
                ''', (f'{today}%',))
                
                results = cursor.fetchall()
                conn.close()
                
                if results:
                    self.results_text.insert(tk.END, f"📊 العروض المرسلة اليوم ({len(results)} عرض):\n")
                    self.results_text.insert(tk.END, "=" * 60 + "\n\n")
                    
                    for i, (name, price, discount, quality_score, section, verified) in enumerate(results, 1):
                        verified_text = "✅ محقق" if verified else "⚠️ غير محقق"
                        
                        self.results_text.insert(tk.END, f"{i}. {name[:50]}...\n")
                        self.results_text.insert(tk.END, f"   💰 {price:.0f} جنيه | 🎉 {discount:.1f}% | 🎯 جودة: {quality_score:.0f}/100\n")
                        self.results_text.insert(tk.END, f"   🏷️ {section} | {verified_text}\n\n")
                else:
                    self.results_text.insert(tk.END, "❌ لا توجد عروض مرسلة اليوم\n")
                
            except Exception as e:
                self.results_text.insert(tk.END, f"❌ خطأ في تحميل النتائج: {e}\n")
        
        threading.Thread(target=load_results, daemon=True).start()
    
    def refresh_results(self):
        """تحديث النتائج"""
        self.show_results()
    
    def clear_results(self):
        """مسح النتائج"""
        
        if messagebox.askyesno("تأكيد", "هل تريد مسح جميع النتائج المحفوظة؟"):
            try:
                if os.path.exists("smart_deals.db"):
                    conn = sqlite3.connect("smart_deals.db")
                    conn.execute("DELETE FROM deals")
                    conn.commit()
                    conn.close()
                    
                self.log("🗑️ تم مسح جميع النتائج")
                self.show_results()
                
            except Exception as e:
                self.log(f"❌ خطأ في مسح النتائج: {e}")
    
    def save_settings(self):
        """حفظ الإعدادات"""
        
        try:
            settings = {
                'min_discount': self.min_discount.get(),
                'max_discount': self.max_discount.get(),
                'min_price': self.min_price.get(),
                'max_price': self.max_price.get(),
                'min_quality_score': self.min_quality_score.get(),
                'max_deals': self.max_deals.get(),
                'send_images': self.send_images.get()
            }
            
            with open('smart_gui_settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            self.log("💾 تم حفظ الإعدادات")
            messagebox.showinfo("نجح", "تم حفظ الإعدادات بنجاح!")
            
        except Exception as e:
            self.log(f"❌ خطأ في حفظ الإعدادات: {e}")
            messagebox.showerror("خطأ", f"فشل في حفظ الإعدادات: {e}")
    
    def load_settings(self):
        """تحميل الإعدادات المحفوظة"""
        
        try:
            if os.path.exists('smart_gui_settings.json'):
                with open('smart_gui_settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.min_discount.set(settings.get('min_discount', 15))
                self.max_discount.set(settings.get('max_discount', 85))
                self.min_price.set(settings.get('min_price', 50))
                self.max_price.set(settings.get('max_price', 10000))
                self.min_quality_score.set(settings.get('min_quality_score', 65))
                self.max_deals.set(settings.get('max_deals', 15))
                self.send_images.set(settings.get('send_images', True))
                
                self.log("📂 تم تحميل الإعدادات المحفوظة")
                self.update_labels()
                
        except Exception as e:
            self.log(f"⚠️ خطأ في تحميل الإعدادات: {e}")
    
    def log(self, message):
        """إضافة رسالة للسجل"""
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def run(self):
        """تشغيل الواجهة"""
        
        self.load_settings()
        self.log("🚀 تم تشغيل واجهة النظام الذكي")
        self.log("🎯 النظام جاهز للاستخدام!")
        
        self.root.mainloop()

def main():
    """تشغيل الواجهة الرئيسية"""
    
    try:
        print("🚀 تشغيل واجهة النظام الذكي...")
        
        gui = SmartGUI()
        gui.run()
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل الواجهة: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()