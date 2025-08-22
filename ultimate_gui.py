# ultimate_gui.py - الواجهة النهائية مع اختيار الفئات

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import os
from datetime import datetime
import sqlite3

# استيراد النظام النهائي
from final_working_system import FinalWorkingSystem

class UltimateGUI:
    """الواجهة النهائية مع اختيار الفئات"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 نظام LAQTA النهائي - متحقق بالكامل")
        self.root.geometry("900x700")
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
        
        # متغيرات اختيار الفئات
        self.category_vars = {}
        self.all_categories = [
            'Electronics', 'Automotive', 'Beauty', 'Fashion',
            'Grocery', 'Health & Household Products', 
            'Home & Kitchen', 'Tools & Home Improvement'
        ]
        
        # تهيئة متغيرات الفئات (كلها مختارة افتراضياً)
        for category in self.all_categories:
            self.category_vars[category] = tk.BooleanVar(value=True)
        
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
            'info': '#2196F3',
            'text': '#ffffff'
        }
        
        # الشريط العلوي
        header_frame = tk.Frame(self.root, bg=self.colors['accent'], height=80)
        header_frame.pack(fill='x', padx=10, pady=5)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🤖 نظام LAQTA النهائي",
            font=('Arial', 18, 'bold'),
            bg=self.colors['accent'],
            fg='white'
        )
        title_label.pack(pady=15)
        
        subtitle_label = tk.Label(
            header_frame,
            text="تحقق مضاعف + مقارنة أسعار + أمازون فقط + اختيار الفئات",
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
        
        # تبويب اختيار الفئات
        self.setup_categories_tab()
        
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
        
        # معلومات سريعة
        info_frame = tk.Frame(main_frame, bg=self.colors['info'], relief='ridge', bd=2)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        self.info_label = tk.Label(
            info_frame,
            text="🎯 الفئات المختارة: جاري التحديث...",
            font=('Arial', 10),
            bg=self.colors['info'],
            fg='white'
        )
        self.info_label.pack(pady=5)
        
        # أزرار التحكم
        control_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        control_frame.pack(fill='x', padx=10, pady=10)
        
        # الصف الأول من الأزرار
        row1_frame = tk.Frame(control_frame, bg=self.colors['bg'])
        row1_frame.pack(fill='x', pady=5)
        
        self.start_btn = tk.Button(
            row1_frame,
            text="🚀 بدء النظام النهائي",
            font=('Arial', 12, 'bold'),
            bg=self.colors['accent'],
            fg='white',
            command=self.start_ultimate_system,
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
             bg='#9C27B0',
             fg='white',
             command=self.test_seller_verification,
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
            height=12,
            bg='#0d1117',
            fg='#f0f6fc',
            font=('Consolas', 9),
            wrap='word'
        )
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def setup_categories_tab(self):
        """إعداد تبويب اختيار الفئات"""
        
        categories_frame = ttk.Frame(self.notebook)
        self.notebook.add(categories_frame, text="📂 اختيار الفئات")
        
        # عنوان
        title_frame = tk.Frame(categories_frame, bg=self.colors['card'], relief='ridge', bd=2)
        title_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(
            title_frame,
            text="📂 اختيار فئات أمازون للفحص",
            font=('Arial', 14, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(pady=10)
        
        tk.Label(
            title_frame,
            text="اختر الفئات التي تريد فحصها (كلما قل العدد، كان الفحص أسرع وأدق)",
            font=('Arial', 10),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(pady=5)
        
        # أزرار التحكم السريع
        quick_control_frame = tk.Frame(categories_frame, bg=self.colors['bg'])
        quick_control_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(
            quick_control_frame,
            text="✅ اختيار الكل",
            font=('Arial', 10),
            bg=self.colors['accent'],
            fg='white',
            command=self.select_all_categories,
            relief='flat'
        ).pack(side='left', padx=5)
        
        tk.Button(
            quick_control_frame,
            text="❌ إلغاء الكل",
            font=('Arial', 10),
            bg=self.colors['error'],
            fg='white',
            command=self.deselect_all_categories,
            relief='flat'
        ).pack(side='left', padx=5)
        
        tk.Button(
            quick_control_frame,
            text="🎯 الأساسيات فقط",
            font=('Arial', 10),
            bg=self.colors['info'],
            fg='white',
            command=self.select_essential_categories,
            relief='flat'
        ).pack(side='left', padx=5)
        
        # قائمة الفئات
        categories_list_frame = tk.Frame(categories_frame, bg=self.colors['card'], relief='ridge', bd=2)
        categories_list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # إطار قابل للتمرير للفئات
        canvas = tk.Canvas(categories_list_frame, bg=self.colors['card'])
        scrollbar = ttk.Scrollbar(categories_list_frame, orient="vertical", command=canvas.yview)
        scrollable_categories = tk.Frame(canvas, bg=self.colors['card'])
        
        scrollable_categories.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_categories, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # إنشاء checkboxes للفئات
        category_emojis = {
            'Electronics': '📱',
            'Automotive': '🚗',
            'Beauty': '💄',
            'Fashion': '👕',
            'Grocery': '🛒',
            'Health & Household Products': '🏥',
            'Home & Kitchen': '🏠',
            'Tools & Home Improvement': '🔧'
        }
        
        for i, category in enumerate(self.all_categories):
            emoji = category_emojis.get(category, '📦')
            
            category_frame = tk.Frame(scrollable_categories, bg=self.colors['card'])
            category_frame.pack(fill='x', padx=20, pady=5)
            
            tk.Checkbutton(
                category_frame,
                text=f"{emoji} {category}",
                variable=self.category_vars[category],
                bg=self.colors['card'],
                fg=self.colors['text'],
                selectcolor=self.colors['accent'],
                font=('Arial', 11),
                command=self.update_categories_info
            ).pack(anchor='w')
        
        # زر تطبيق اختيار الفئات
        tk.Button(
            categories_frame,
            text="✅ تطبيق اختيار الفئات",
            font=('Arial', 12, 'bold'),
            bg=self.colors['accent'],
            fg='white',
            command=self.apply_categories_selection,
            relief='flat',
            height=2
        ).pack(fill='x', padx=10, pady=10)
    
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
    
    def select_all_categories(self):
        """اختيار جميع الفئات"""
        for var in self.category_vars.values():
            var.set(True)
        self.update_categories_info()
        self.log("✅ تم اختيار جميع الفئات")
    
    def deselect_all_categories(self):
        """إلغاء اختيار جميع الفئات"""
        for var in self.category_vars.values():
            var.set(False)
        self.update_categories_info()
        self.log("❌ تم إلغاء اختيار جميع الفئات")
    
    def select_essential_categories(self):
        """اختيار الفئات الأساسية فقط"""
        essentials = ['Electronics', 'Home & Kitchen', 'Beauty']
        
        for category, var in self.category_vars.items():
            var.set(category in essentials)
        
        self.update_categories_info()
        self.log("🎯 تم اختيار الفئات الأساسية فقط")
    
    def update_categories_info(self):
        """تحديث معلومات الفئات المختارة"""
        
        selected = [cat for cat, var in self.category_vars.items() if var.get()]
        count = len(selected)
        
        if count == 0:
            self.info_label.config(text="⚠️ لم يتم اختيار أي فئة!")
        elif count == len(self.all_categories):
            self.info_label.config(text="🎯 الفئات المختارة: جميع الفئات (8 فئات)")
        else:
            categories_text = ", ".join(selected[:3])
            if count > 3:
                categories_text += f" + {count-3} أخرى"
            self.info_label.config(text=f"🎯 الفئات المختارة: {categories_text} ({count} فئات)")
    
    def apply_categories_selection(self):
        """تطبيق اختيار الفئات"""
        
        selected = [cat for cat, var in self.category_vars.items() if var.get()]
        
        if not selected:
            messagebox.showwarning("تحذير", "يجب اختيار فئة واحدة على الأقل!")
            return
        
        self.log(f"✅ تم تطبيق اختيار {len(selected)} فئة")
        messagebox.showinfo("نجح", f"تم تطبيق اختيار {len(selected)} فئة بنجاح!")
    
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
            
            # تحديث معلومات الفئات
            self.update_categories_info()
            
        except Exception as e:
            self.status_label.config(text="❌ خطأ في فحص النظام", fg=self.colors['error'])
    
    def start_ultimate_system(self):
        """بدء النظام النهائي"""
        
        if self.is_running:
            messagebox.showwarning("تحذير", "النظام قيد التشغيل بالفعل!")
            return
        
        # فحص اختيار الفئات
        selected_categories = [cat for cat, var in self.category_vars.items() if var.get()]
        if not selected_categories:
            messagebox.showwarning("تحذير", "يجب اختيار فئة واحدة على الأقل!")
            return
        
        self.is_running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_label.config(text="🚀 قيد التشغيل...", fg=self.colors['accent'])
        
        # بدء النظام في thread منفصل
        thread = threading.Thread(target=self.run_ultimate_system_thread, daemon=True)
        thread.start()
    
    def run_ultimate_system_thread(self):
        """تشغيل النظام في thread منفصل"""
        
        try:
            self.log("🚀 بدء النظام النهائي المحسن...")
            self.log("=" * 50)
            
                         # إنشاء النظام مع الإعدادات الحالية
             self.system = FinalWorkingSystem()
            
            # تطبيق الإعدادات
            self.system.min_discount = self.min_discount.get()
            self.system.max_discount = self.max_discount.get()
            self.system.min_price = self.min_price.get()
            self.system.max_price = self.max_price.get()
            self.system.min_quality_score = self.min_quality_score.get()
            self.system.max_deals = self.max_deals.get()
            self.system.send_with_images = self.send_images.get()
            
            # تطبيق اختيار الفئات
            selected_categories = [cat for cat, var in self.category_vars.items() if var.get()]
            self.system.set_selected_categories(selected_categories)
            
            self.log(f"⚙️ الإعدادات: خصم {self.min_discount.get()}-{self.max_discount.get()}%, سعر {self.min_price.get()}-{self.max_price.get()} جنيه")
            self.log(f"🎯 الحد الأدنى للجودة: {self.min_quality_score.get()}/100")
            self.log(f"🎯 العروض المستهدفة: {self.max_deals.get()} عرض")
            self.log(f"📂 الفئات المختارة: {len(selected_categories)} فئة")
            
                         # تشغيل النظام
             deals = self.system.run_final_system()
            
            # عرض النتائج
            approved = [d for d in deals if d.get('is_approved', False)]
            
            self.log("=" * 50)
            self.log(f"✅ انتهى النظام!")
            self.log(f"📊 إجمالي العروض المكتشفة: {len(deals)}")
            self.log(f"🎯 العروض المعتمدة: {len(approved)}")
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
    
    def test_seller_verification(self):
        """اختبار التحقق من البائع"""
        
        def test_thread():
            try:
                self.log("🔍 اختبار التحقق من البائع...")
                
                                 # إنشاء نظام للاختبار
                 test_system = FinalWorkingSystem()
                
                # ASIN تجريبي
                test_asin = "B0C7CQT9ZS"
                test_url = f"https://www.amazon.eg/dp/{test_asin}"
                
                self.log(f"🔍 فحص ASIN: {test_asin}")
                self.log(f"🌐 الرابط: {test_url}")
                
                                 # اختبار مقارنة الأسعار بدلاً من التحقق من البائع
                 comparison_result = test_system.compare_prices_jumia_only("Samsung Galaxy Buds", 1200)
                
                                 if comparison_result:
                     jumia_price = comparison_result.get('jumia_price', 0)
                     savings = comparison_result.get('savings', 0)
                     self.log(f"✅ مقارنة ناجحة - Jumia: {jumia_price:.0f} جنيه")
                     self.log(f"💰 توفير: {savings:.0f} جنيه")
                 else:
                     self.log("❌ فشل في مقارنة الأسعار")
                
            except Exception as e:
                self.log(f"❌ خطأ في اختبار التحقق: {e}")
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def show_results(self):
        """عرض النتائج"""
        
        def load_results():
            try:
                self.results_text.delete(1.0, tk.END)
                
                                 if not os.path.exists("final_deals.db"):
                     self.results_text.insert(tk.END, "❌ لا توجد نتائج محفوظة\n")
                     return
                 
                 conn = sqlite3.connect("final_deals.db")
                cursor = conn.cursor()
                
                # العروض المرسلة اليوم
                today = datetime.now().strftime('%Y-%m-%d')
                                 cursor.execute('''
                     SELECT name, price, discount_percent, quality_score, section, 
                            is_verified_deal
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
                         self.results_text.insert(tk.END, f"   🏷️ {section} | {verified_text} | ✅ أمازون\n\n")
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
                                 if os.path.exists("final_deals.db"):
                     conn = sqlite3.connect("final_deals.db")
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
            selected_categories = [cat for cat, var in self.category_vars.items() if var.get()]
            
            settings = {
                'min_discount': self.min_discount.get(),
                'max_discount': self.max_discount.get(),
                'min_price': self.min_price.get(),
                'max_price': self.max_price.get(),
                'min_quality_score': self.min_quality_score.get(),
                'max_deals': self.max_deals.get(),
                'send_images': self.send_images.get(),
                'selected_categories': selected_categories
            }
            
            with open('ultimate_gui_settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            self.log("💾 تم حفظ الإعدادات والفئات المختارة")
            messagebox.showinfo("نجح", "تم حفظ الإعدادات بنجاح!")
            
        except Exception as e:
            self.log(f"❌ خطأ في حفظ الإعدادات: {e}")
            messagebox.showerror("خطأ", f"فشل في حفظ الإعدادات: {e}")
    
    def load_settings(self):
        """تحميل الإعدادات المحفوظة"""
        
        try:
            if os.path.exists('ultimate_gui_settings.json'):
                with open('ultimate_gui_settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.min_discount.set(settings.get('min_discount', 15))
                self.max_discount.set(settings.get('max_discount', 85))
                self.min_price.set(settings.get('min_price', 50))
                self.max_price.set(settings.get('max_price', 10000))
                self.min_quality_score.set(settings.get('min_quality_score', 65))
                self.max_deals.set(settings.get('max_deals', 15))
                self.send_images.set(settings.get('send_images', True))
                
                # تحميل الفئات المختارة
                selected_categories = settings.get('selected_categories', self.all_categories)
                for category, var in self.category_vars.items():
                    var.set(category in selected_categories)
                
                self.log("📂 تم تحميل الإعدادات والفئات المحفوظة")
                self.update_labels()
                self.update_categories_info()
                
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
        self.log("🚀 تم تشغيل الواجهة النهائية المحسنة")
        self.log("🎯 النظام جاهز للاستخدام!")
        self.log("📂 يمكنك اختيار الفئات من التبويب الثاني")
        
        self.root.mainloop()

def main():
    """تشغيل الواجهة الرئيسية"""
    
    try:
        print("🚀 تشغيل الواجهة النهائية...")
        
        gui = UltimateGUI()
        gui.run()
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل الواجهة: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()