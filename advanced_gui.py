# advanced_gui.py - واجهة متقدمة مع إعدادات شاملة

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import sqlite3
from datetime import datetime, timedelta
import webbrowser
import os
import time

# استيراد النظام الأصلي المحسن
try:
    from original_system_with_json import OriginalSystemWithJSON
except ImportError:
    OriginalSystemWithJSON = None

class AdvancedGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LAQTA Advanced Control Panel")
        self.root.geometry("1100x750")
        self.root.configure(bg="#1a1a2e")
        
        # متغيرات النظام
        self.system = None
        self.is_running = False
        self.auto_run_enabled = False
        self.auto_run_thread = None
        
        # إعدادات النظام (قابلة للتعديل)
        self.settings = {
            'min_discount': 12,
            'max_discount': 90,
            'min_price': 20,
            'max_price': 12000,
            'target_deals': 15,
            'min_quality_score': 50,
            'auto_run_interval': 60,  # دقيقة
            'send_with_images': True,
            'auto_send_telegram': True,
            'max_deals_per_category': 4,
            'enable_json_enhancement': True
        }
        
        # إعداد الواجهة
        self.setup_advanced_gui()
        
        # تهيئة النظام
        if OriginalSystemWithJSON:
            self.system = OriginalSystemWithJSON()
            self.apply_settings_to_system()
    
    def setup_advanced_gui(self):
        """إعداد الواجهة المتقدمة"""
        
        # إنشاء Notebook للتبويبات
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # تبويب التحكم الرئيسي
        self.setup_main_control_tab(notebook)
        
        # تبويب الإعدادات
        self.setup_settings_tab(notebook)
        
        # تبويب النتائج
        self.setup_results_tab(notebook)
        
        # تبويب الإحصائيات
        self.setup_statistics_tab(notebook)
    
    def setup_main_control_tab(self, notebook):
        """إعداد تبويب التحكم الرئيسي"""
        
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="🚀 التحكم الرئيسي")
        
        # العنوان
        title_label = tk.Label(
            main_frame,
            text="🤖 LAQTA Advanced Control Panel",
            font=("Arial", 20, "bold"),
            bg="#1a1a2e",
            fg="#00ff88"
        )
        title_label.pack(pady=15)
        
        # معلومات النظام
        info_frame = tk.Frame(main_frame, bg="#1a1a2e")
        info_frame.pack(fill="x", padx=20, pady=10)
        
        self.system_info_label = tk.Label(
            info_frame,
            text="📊 جاري تحميل النظام...",
            font=("Arial", 12, "bold"),
            bg="#1a1a2e",
            fg="#ffff00"
        )
        self.system_info_label.pack()
        
        # أزرار التحكم الرئيسية
        main_controls_frame = tk.Frame(main_frame, bg="#1a1a2e")
        main_controls_frame.pack(fill="x", padx=20, pady=20)
        
        # زر البدء
        self.start_btn = tk.Button(
            main_controls_frame,
            text="🚀 Start System",
            command=self.start_system,
            font=("Arial", 16, "bold"),
            bg="#00ff88",
            fg="#000000",
            width=20,
            height=3
        )
        self.start_btn.pack(side="left", padx=10)
        
        # زر الإيقاف
        self.stop_btn = tk.Button(
            main_controls_frame,
            text="⏹️ Stop System",
            command=self.stop_system,
            font=("Arial", 16, "bold"),
            bg="#ff4444",
            fg="#ffffff",
            width=20,
            height=3,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=10)
        
        # التشغيل التلقائي
        auto_frame = tk.Frame(main_frame, bg="#1a1a2e")
        auto_frame.pack(fill="x", padx=20, pady=10)
        
        self.auto_run_var = tk.BooleanVar()
        auto_checkbox = tk.Checkbutton(
            auto_frame,
            text="🔄 تشغيل تلقائي كل ساعة",
            variable=self.auto_run_var,
            command=self.toggle_auto_run,
            font=("Arial", 12, "bold"),
            bg="#1a1a2e",
            fg="#ffffff",
            selectcolor="#333333"
        )
        auto_checkbox.pack(side="left")
        
        # معلومات التشغيل التلقائي
        self.auto_info_label = tk.Label(
            auto_frame,
            text="⏸️ التشغيل التلقائي معطل",
            font=("Arial", 10),
            bg="#1a1a2e",
            fg="#888888"
        )
        self.auto_info_label.pack(side="left", padx=20)
        
        # شريط التقدم
        progress_frame = tk.Frame(main_frame, bg="#1a1a2e")
        progress_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(
            progress_frame,
            text="التقدم:",
            font=("Arial", 11, "bold"),
            bg="#1a1a2e",
            fg="#ffffff"
        ).pack(side="left")
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode="indeterminate",
            length=600
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=10)
        
        # منطقة السجل
        log_frame = tk.Frame(main_frame, bg="#1a1a2e")
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(
            log_frame,
            text="📝 سجل النظام:",
            font=("Arial", 12, "bold"),
            bg="#1a1a2e",
            fg="#ffffff"
        ).pack(anchor="w")
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 10),
            bg="#0d1117",
            fg="#ffffff",
            insertbackground="#ffffff",
            height=15
        )
        self.log_text.pack(fill="both", expand=True, pady=(5, 0))
        
        # رسالة ترحيب
        self.show_welcome_message()
        
        # تحديث معلومات النظام
        self.update_system_info()
    
    def setup_settings_tab(self, notebook):
        """إعداد تبويب الإعدادات"""
        
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="⚙️ الإعدادات")
        
        # إطار التمرير
        canvas = tk.Canvas(settings_frame, bg="#1a1a2e")
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1a1a2e")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # العنوان
        title_label = tk.Label(
            scrollable_frame,
            text="⚙️ إعدادات النظام المتقدمة",
            font=("Arial", 18, "bold"),
            bg="#1a1a2e",
            fg="#ffaa00"
        )
        title_label.pack(pady=15)
        
        # إعدادات الفلترة
        filter_frame = tk.LabelFrame(
            scrollable_frame,
            text="🎯 إعدادات الفلترة",
            font=("Arial", 14, "bold"),
            bg="#1a1a2e",
            fg="#ffffff"
        )
        filter_frame.pack(fill="x", padx=20, pady=10)
        
        # نسبة الخصم
        self.create_setting_row(filter_frame, "حد أدنى للخصم (%):", 'min_discount', 0, 1, 0, 100)
        self.create_setting_row(filter_frame, "حد أقصى للخصم (%):", 'max_discount', 1, 1, 0, 100)
        
        # نطاق الأسعار
        self.create_setting_row(filter_frame, "حد أدنى للسعر (جنيه):", 'min_price', 2, 1, 1, 50000)
        self.create_setting_row(filter_frame, "حد أقصى للسعر (جنيه):", 'max_price', 3, 1, 100, 50000)
        
        # عدد العروض
        self.create_setting_row(filter_frame, "عدد العروض المطلوبة:", 'target_deals', 4, 1, 5, 50)
        self.create_setting_row(filter_frame, "حد أدنى لنقاط الجودة:", 'min_quality_score', 5, 1, 30, 100)
        
        # إعدادات التشغيل التلقائي
        auto_frame = tk.LabelFrame(
            scrollable_frame,
            text="🔄 التشغيل التلقائي",
            font=("Arial", 14, "bold"),
            bg="#1a1a2e",
            fg="#ffffff"
        )
        auto_frame.pack(fill="x", padx=20, pady=10)
        
        self.create_setting_row(auto_frame, "فترة التشغيل التلقائي (دقيقة):", 'auto_run_interval', 0, 1, 30, 1440)
        self.create_setting_row(auto_frame, "حد أقصى عروض لكل فئة:", 'max_deals_per_category', 1, 1, 1, 10)
        
        # إعدادات الإرسال
        send_frame = tk.LabelFrame(
            scrollable_frame,
            text="📱 إعدادات الإرسال",
            font=("Arial", 14, "bold"),
            bg="#1a1a2e",
            fg="#ffffff"
        )
        send_frame.pack(fill="x", padx=20, pady=10)
        
        # خيارات الإرسال
        self.send_images_var = tk.BooleanVar(value=self.settings['send_with_images'])
        send_images_cb = tk.Checkbutton(
            send_frame,
            text="📸 إرسال مع الصور",
            variable=self.send_images_var,
            font=("Arial", 11),
            bg="#1a1a2e",
            fg="#ffffff",
            selectcolor="#333333"
        )
        send_images_cb.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.auto_send_var = tk.BooleanVar(value=self.settings['auto_send_telegram'])
        auto_send_cb = tk.Checkbutton(
            send_frame,
            text="📱 إرسال تلقائي للتليجرام",
            variable=self.auto_send_var,
            font=("Arial", 11),
            bg="#1a1a2e",
            fg="#ffffff",
            selectcolor="#333333"
        )
        auto_send_cb.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        self.json_enhance_var = tk.BooleanVar(value=self.settings['enable_json_enhancement'])
        json_enhance_cb = tk.Checkbutton(
            send_frame,
            text="🧠 تفعيل تحسينات JSON",
            variable=self.json_enhance_var,
            font=("Arial", 11),
            bg="#1a1a2e",
            fg="#ffffff",
            selectcolor="#333333"
        )
        json_enhance_cb.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        
        # أزرار حفظ وإعادة تعيين
        buttons_frame = tk.Frame(scrollable_frame, bg="#1a1a2e")
        buttons_frame.pack(fill="x", padx=20, pady=20)
        
        save_btn = tk.Button(
            buttons_frame,
            text="💾 حفظ الإعدادات",
            command=self.save_settings,
            font=("Arial", 12, "bold"),
            bg="#00ff88",
            fg="#000000",
            width=20
        )
        save_btn.pack(side="left", padx=10)
        
        reset_btn = tk.Button(
            buttons_frame,
            text="🔄 إعادة تعيين",
            command=self.reset_settings,
            font=("Arial", 12, "bold"),
            bg="#ff8800",
            fg="#ffffff",
            width=20
        )
        reset_btn.pack(side="left", padx=10)
        
        test_btn = tk.Button(
            buttons_frame,
            text="🧪 اختبار الإعدادات",
            command=self.test_settings,
            font=("Arial", 12, "bold"),
            bg="#4488ff",
            fg="#ffffff",
            width=20
        )
        test_btn.pack(side="left", padx=10)
    
    def create_setting_row(self, parent, label_text, setting_key, row, col, min_val, max_val):
        """إنشاء صف إعدادات"""
        
        tk.Label(
            parent,
            text=label_text,
            font=("Arial", 11),
            bg="#1a1a2e",
            fg="#ffffff"
        ).grid(row=row, column=col*2, sticky="w", padx=10, pady=8)
        
        # متغير للقيمة
        var = tk.StringVar(value=str(self.settings[setting_key]))
        setattr(self, f"{setting_key}_var", var)
        
        # صندوق الإدخال
        entry = tk.Entry(
            parent,
            textvariable=var,
            font=("Arial", 11),
            width=10
        )
        entry.grid(row=row, column=col*2+1, padx=10, pady=8)
        
        # شريط التمرير
        scale = tk.Scale(
            parent,
            from_=min_val,
            to=max_val,
            orient="horizontal",
            variable=var,
            length=200,
            bg="#1a1a2e",
            fg="#ffffff",
            highlightthickness=0
        )
        scale.grid(row=row, column=col*2+2, padx=10, pady=8)
    
    def setup_results_tab(self, notebook):
        """إعداد تبويب النتائج"""
        
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="📋 النتائج")
        
        # العنوان
        title_label = tk.Label(
            results_frame,
            text="📋 نتائج النظام",
            font=("Arial", 16, "bold"),
            bg="#1a1a2e",
            fg="#4488ff"
        )
        title_label.pack(pady=10)
        
        # أزرار التحكم
        controls_frame = tk.Frame(results_frame, bg="#1a1a2e")
        controls_frame.pack(fill="x", padx=20, pady=5)
        
        refresh_btn = tk.Button(
            controls_frame,
            text="🔄 تحديث النتائج",
            command=self.refresh_results,
            font=("Arial", 11, "bold"),
            bg="#4488ff",
            fg="#ffffff"
        )
        refresh_btn.pack(side="left", padx=5)
        
        export_btn = tk.Button(
            controls_frame,
            text="💾 تصدير الكل",
            command=self.export_all_results,
            font=("Arial", 11, "bold"),
            bg="#ff8800",
            fg="#ffffff"
        )
        export_btn.pack(side="left", padx=5)
        
        send_best_btn = tk.Button(
            controls_frame,
            text="📱 إرسال أفضل 15",
            command=self.send_best_deals,
            font=("Arial", 11, "bold"),
            bg="#0088ff",
            fg="#ffffff"
        )
        send_best_btn.pack(side="left", padx=5)
        
        # جدول النتائج
        self.results_tree = ttk.Treeview(
            results_frame,
            columns=("الاسم", "السعر", "الخصم", "النقاط", "المصدر", "الفئة", "التاريخ"),
            show="headings",
            height=20
        )
        
        # تحديد عناوين الأعمدة
        for col in self.results_tree['columns']:
            self.results_tree.heading(col, text=col)
        
        # تحديد عرض الأعمدة
        self.results_tree.column("الاسم", width=200)
        self.results_tree.column("السعر", width=80)
        self.results_tree.column("الخصم", width=70)
        self.results_tree.column("النقاط", width=80)
        self.results_tree.column("المصدر", width=100)
        self.results_tree.column("الفئة", width=100)
        self.results_tree.column("التاريخ", width=120)
        
        # scrollbar للجدول
        results_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_tree.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=10)
        results_scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=10)
        
        # ربط النقر المزدوج
        self.results_tree.bind("<Double-1>", self.open_product_link)
    
    def setup_statistics_tab(self, notebook):
        """إعداد تبويب الإحصائيات"""
        
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="📊 الإحصائيات")
        
        # العنوان
        title_label = tk.Label(
            stats_frame,
            text="📊 إحصائيات مفصلة",
            font=("Arial", 16, "bold"),
            bg="#1a1a2e",
            fg="#ff8800"
        )
        title_label.pack(pady=15)
        
        # إطار الإحصائيات
        self.stats_text = scrolledtext.ScrolledText(
            stats_frame,
            font=("Consolas", 11),
            bg="#0d1117",
            fg="#ffffff",
            height=25,
            wrap="word"
        )
        self.stats_text.pack(fill="both", expand=True, padx=20, pady=10)
        
        # زر تحديث الإحصائيات
        update_stats_btn = tk.Button(
            stats_frame,
            text="🔄 تحديث الإحصائيات",
            command=self.update_statistics,
            font=("Arial", 12, "bold"),
            bg="#ff8800",
            fg="#ffffff"
        )
        update_stats_btn.pack(pady=10)
    
    def show_welcome_message(self):
        """عرض رسالة الترحيب"""
        
        welcome_msg = """🤖 LAQTA Advanced Control Panel - مرحباً!

✨ النظام المتقدم مع تحكم شامل:
• ⚙️ إعدادات قابلة للتعديل بالكامل
• 🔄 تشغيل تلقائي قابل للجدولة
• 📊 إحصائيات مفصلة ومباشرة
• 📱 تحكم كامل في الإرسال
• 🧠 تحسينات JSON اختيارية

🎯 النظام الأصلي الشغال + تحكم متقدم

📋 استخدم التبويبات للتنقل بين الوظائف:
• 🚀 التحكم الرئيسي: تشغيل النظام
• ⚙️ الإعدادات: تخصيص كامل
• 📋 النتائج: عرض وإدارة العروض
• 📊 الإحصائيات: تحليلات مفصلة

"""
        self.log_text.insert("end", welcome_msg)
        self.log_text.see("end")
    
    def update_system_info(self):
        """تحديث معلومات النظام"""
        
        if self.system:
            json_count = len(self.system.products_data) if self.system.products_data else 0
            telegram_users = len(self.system.users) if self.system.users else 0
            
            if json_count > 0:
                info_text = f"📊 النظام جاهز | JSON: {json_count:,} منتج | تليجرام: {telegram_users} مستخدم"
            else:
                info_text = f"📊 النظام جاهز | كشط مباشر | تليجرام: {telegram_users} مستخدم"
            
            self.system_info_label.config(text=info_text)
            
            # رسالة في السجل
            if json_count > 0:
                self.log_message(f"✅ JSON: {json_count:,} منتج متاح للتحسين")
            
            self.log_message(f"✅ إعدادات التليجرام: {telegram_users} مستخدم")
            self.log_message("💡 استخدم تبويب 'الإعدادات' لتخصيص النظام")
        else:
            self.system_info_label.config(text="❌ النظام غير متاح")
    
    def apply_settings_to_system(self):
        """تطبيق الإعدادات على النظام"""
        
        if not self.system:
            return
        
        try:
            # تطبيق الإعدادات
            self.system.min_discount = self.settings['min_discount']
            self.system.max_discount = self.settings['max_discount']
            self.system.min_price = self.settings['min_price']
            self.system.max_price = self.settings['max_price']
            
            self.log_message("✅ تم تطبيق الإعدادات على النظام")
            
        except Exception as e:
            self.log_message(f"⚠️ خطأ في تطبيق الإعدادات: {e}")
    
    def save_settings(self):
        """حفظ الإعدادات"""
        
        try:
            # تحديث الإعدادات من الواجهة
            for key in self.settings.keys():
                if hasattr(self, f"{key}_var"):
                    var = getattr(self, f"{key}_var")
                    try:
                        self.settings[key] = float(var.get()) if '.' in var.get() else int(var.get())
                    except:
                        pass
            
            # تحديث الإعدادات المنطقية
            self.settings['send_with_images'] = self.send_images_var.get()
            self.settings['auto_send_telegram'] = self.auto_send_var.get()
            self.settings['enable_json_enhancement'] = self.json_enhance_var.get()
            
            # حفظ في ملف
            with open('advanced_settings.json', 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            
            # تطبيق على النظام
            self.apply_settings_to_system()
            
            self.log_message("💾 تم حفظ الإعدادات بنجاح")
            messagebox.showinfo("نجح", "تم حفظ الإعدادات بنجاح!")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في حفظ الإعدادات: {e}")
    
    def reset_settings(self):
        """إعادة تعيين الإعدادات للافتراضية"""
        
        default_settings = {
            'min_discount': 12,
            'max_discount': 90,
            'min_price': 20,
            'max_price': 12000,
            'target_deals': 15,
            'min_quality_score': 50,
            'auto_run_interval': 60,
            'send_with_images': True,
            'auto_send_telegram': True,
            'max_deals_per_category': 4,
            'enable_json_enhancement': True
        }
        
        self.settings = default_settings
        
        # تحديث الواجهة
        for key, value in default_settings.items():
            if hasattr(self, f"{key}_var"):
                getattr(self, f"{key}_var").set(str(value))
        
        self.send_images_var.set(True)
        self.auto_send_var.set(True)
        self.json_enhance_var.set(True)
        
        self.log_message("🔄 تم إعادة تعيين الإعدادات للافتراضية")
        messagebox.showinfo("تم", "تم إعادة تعيين الإعدادات للقيم الافتراضية")
    
    def test_settings(self):
        """اختبار الإعدادات"""
        
        try:
            # تحديث الإعدادات
            for key in self.settings.keys():
                if hasattr(self, f"{key}_var"):
                    var = getattr(self, f"{key}_var")
                    try:
                        value = float(var.get()) if '.' in var.get() else int(var.get())
                        self.settings[key] = value
                    except:
                        pass
            
            # عرض الإعدادات الحالية
            test_msg = f"""🧪 اختبار الإعدادات:

🎯 فلترة العروض:
• خصم: {self.settings['min_discount']}% - {self.settings['max_discount']}%
• سعر: {self.settings['min_price']} - {self.settings['max_price']} جنيه
• عدد العروض: {self.settings['target_deals']}
• حد أدنى للجودة: {self.settings['min_quality_score']} نقطة

🔄 التشغيل التلقائي:
• الفترة: {self.settings['auto_run_interval']} دقيقة
• عروض لكل فئة: {self.settings['max_deals_per_category']}

📱 الإرسال:
• مع الصور: {'نعم' if self.settings['send_with_images'] else 'لا'}
• تلقائي للتليجرام: {'نعم' if self.settings['auto_send_telegram'] else 'لا'}
• تحسينات JSON: {'نعم' if self.settings['enable_json_enhancement'] else 'لا'}

✅ الإعدادات صحيحة ومناسبة!"""
            
            self.log_message(test_msg)
            messagebox.showinfo("اختبار الإعدادات", "✅ الإعدادات صحيحة ومناسبة!")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في اختبار الإعدادات: {e}")
    
    def toggle_auto_run(self):
        """تفعيل/إلغاء التشغيل التلقائي"""
        
        self.auto_run_enabled = self.auto_run_var.get()
        
        if self.auto_run_enabled:
            self.auto_info_label.config(
                text=f"🔄 التشغيل التلقائي مفعل (كل {self.settings['auto_run_interval']} دقيقة)",
                fg="#00ff88"
            )
            self.start_auto_run()
        else:
            self.auto_info_label.config(
                text="⏸️ التشغيل التلقائي معطل",
                fg="#888888"
            )
            self.stop_auto_run()
    
    def start_auto_run(self):
        """بدء التشغيل التلقائي"""
        
        if self.auto_run_thread and self.auto_run_thread.is_alive():
            return
        
        self.auto_run_thread = threading.Thread(target=self.auto_run_loop, daemon=True)
        self.auto_run_thread.start()
        
        self.log_message(f"🔄 تم تفعيل التشغيل التلقائي (كل {self.settings['auto_run_interval']} دقيقة)")
    
    def stop_auto_run(self):
        """إيقاف التشغيل التلقائي"""
        
        self.auto_run_enabled = False
        self.log_message("⏸️ تم إيقاف التشغيل التلقائي")
    
    def auto_run_loop(self):
        """حلقة التشغيل التلقائي"""
        
        while self.auto_run_enabled:
            try:
                if not self.is_running:  # تشغيل فقط إذا لم يكن النظام يعمل
                    self.log_message("🔄 بدء التشغيل التلقائي...")
                    
                    # تشغيل النظام
                    self.root.after(0, self.start_system)
                    
                    # انتظار انتهاء التشغيل
                    while self.is_running:
                        time.sleep(5)
                    
                    self.log_message(f"⏰ التشغيل التالي خلال {self.settings['auto_run_interval']} دقيقة")
                
                # انتظار الفترة المحددة
                for _ in range(self.settings['auto_run_interval'] * 60):  # تحويل لثواني
                    if not self.auto_run_enabled:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.log_message(f"❌ خطأ في التشغيل التلقائي: {e}")
                time.sleep(60)  # انتظار دقيقة قبل المحاولة مرة أخرى
    
    def start_system(self):
        """بدء النظام"""
        
        if self.is_running:
            if not self.auto_run_enabled:  # عرض تحذير فقط للتشغيل اليدوي
                messagebox.showwarning("تحذير", "النظام يعمل بالفعل!")
            return
        
        if not self.system:
            messagebox.showerror("خطأ", "النظام غير متاح!")
            return
        
        # تطبيق الإعدادات الحالية
        self.apply_settings_to_system()
        
        # تغيير حالة الأزرار
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.is_running = True
        
        # بدء شريط التقدم
        self.progress_bar.start()
        
        # تشغيل في thread منفصل
        system_thread = threading.Thread(target=self.run_system_thread, daemon=True)
        system_thread.start()
        
        current_time = datetime.now().strftime("%H:%M:%S")
        self.log_message(f"🚀 [{current_time}] بدء النظام بالإعدادات المحدثة...")
    
    def run_system_thread(self):
        """تشغيل النظام في thread منفصل"""
        
        try:
            # تخصيص دالة التسجيل
            original_print = print
            
            def custom_print(message):
                self.log_message(str(message))
                original_print(message)
            
            # استبدال print مؤقتاً
            import builtins
            builtins.print = custom_print
            
            # تشغيل النظام
            self.update_system_info_status("🔍 جاري الكشط والتحليل...")
            
            deals = self.system.run_system()
            
            # استعادة print الأصلي
            builtins.print = original_print
            
            # تحديث النتائج
            if deals:
                json_enhanced = sum(1 for d in deals if 'json' in d.get('source', ''))
                
                info_text = f"✅ تم إرسال {len(deals)} عرض"
                if json_enhanced > 0:
                    info_text += f" ({json_enhanced} محسن بـ JSON)"
                
                self.update_system_info_status(info_text)
                self.log_message(f"🎯 تم الانتهاء بنجاح - {len(deals)} عرض مرسل")
                
                # تحديث النتائج تلقائياً
                self.root.after(2000, self.refresh_results)
                
            else:
                self.update_system_info_status("❌ لم يتم العثور على عروض مناسبة")
                self.log_message("❌ لا توجد عروض مناسبة بالإعدادات الحالية")
            
        except Exception as e:
            self.log_message(f"❌ خطأ في النظام: {e}")
            self.update_system_info_status("❌ حدث خطأ في النظام")
        
        finally:
            # إعادة تعيين الأزرار
            self.root.after(0, self.system_finished)
    
    def update_system_info_status(self, status_text):
        """تحديث حالة النظام"""
        
        def update():
            self.system_info_label.config(text=status_text)
        
        self.root.after(0, update)
    
    def system_finished(self):
        """انتهاء تشغيل النظام"""
        
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.is_running = False
        self.progress_bar.stop()
    
    def stop_system(self):
        """إيقاف النظام"""
        
        self.is_running = False
        self.auto_run_enabled = False
        self.auto_run_var.set(False)
        
        self.log_message("⏹️ تم إيقاف النظام والتشغيل التلقائي")
        self.system_finished()
    
    def refresh_results(self):
        """تحديث النتائج"""
        
        if not self.system:
            return
        
        try:
            # مسح النتائج الحالية
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            # جلب النتائج الجديدة
            conn = sqlite3.connect(self.system.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, price, discount_percent, quality_score, url, asin, 
                       section, source, date_found
                FROM deals 
                ORDER BY date_found DESC, quality_score DESC
                LIMIT 50
            ''')
            
            deals = cursor.fetchall()
            conn.close()
            
            # إضافة النتائج للجدول
            for deal in deals:
                name = deal[0][:40] + "..." if len(deal[0]) > 40 else deal[0]
                price = f"{deal[1]:.0f}"
                discount = f"{deal[2]:.1f}%"
                score = f"{deal[3]:.1f}"
                
                source = deal[7] if len(deal) > 7 else "scraping"
                source_text = "🧠 JSON" if 'json' in source else "🔍 كشط"
                
                category = deal[6] if len(deal) > 6 else "غير محدد"
                date_found = deal[8][:16] if len(deal) > 8 else ""
                
                self.results_tree.insert("", "end", values=(
                    name, price, discount, score, source_text, category, date_found
                ))
            
            self.log_message(f"🔄 تم تحديث النتائج - {len(deals)} عرض")
            
        except Exception as e:
            self.log_message(f"❌ خطأ في تحديث النتائج: {e}")
    
    def update_statistics(self):
        """تحديث الإحصائيات"""
        
        if not self.system:
            return
        
        try:
            conn = sqlite3.connect(self.system.db_file)
            cursor = conn.cursor()
            
            # إحصائيات شاملة
            stats_text = f"""📊 إحصائيات النظام المفصلة
{'='*60}
تاريخ التحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📦 إحصائيات العروض:
"""
            
            # إجمالي العروض
            cursor.execute("SELECT COUNT(*) FROM deals")
            total_deals = cursor.fetchone()[0]
            stats_text += f"   • إجمالي العروض: {total_deals:,}\n"
            
            # عروض اليوم
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT COUNT(*) FROM deals WHERE date_found LIKE ?", (f'{today}%',))
            today_deals = cursor.fetchone()[0]
            stats_text += f"   • عروض اليوم: {today_deals:,}\n"
            
            # العروض المرسلة
            cursor.execute("SELECT COUNT(*) FROM deals WHERE is_sent = 1")
            sent_deals = cursor.fetchone()[0]
            stats_text += f"   • عروض مرسلة: {sent_deals:,}\n"
            
            # العروض المحسنة بـ JSON
            cursor.execute("SELECT COUNT(*) FROM deals WHERE source LIKE '%json%'")
            json_enhanced = cursor.fetchone()[0]
            stats_text += f"   • محسن بـ JSON: {json_enhanced:,}\n\n"
            
            # إحصائيات الجودة
            stats_text += "⭐ إحصائيات الجودة:\n"
            
            cursor.execute("SELECT AVG(quality_score) FROM deals WHERE quality_score > 0")
            avg_score = cursor.fetchone()[0] or 0
            stats_text += f"   • متوسط النقاط: {avg_score:.1f}\n"
            
            cursor.execute("SELECT MAX(quality_score) FROM deals")
            max_score = cursor.fetchone()[0] or 0
            stats_text += f"   • أعلى نقاط: {max_score:.1f}\n"
            
            cursor.execute("SELECT COUNT(*) FROM deals WHERE quality_score >= 80")
            excellent_deals = cursor.fetchone()[0]
            stats_text += f"   • عروض ممتازة (80+): {excellent_deals:,}\n\n"
            
            # إحصائيات الفئات
            stats_text += "🏷️ إحصائيات الفئات:\n"
            
            cursor.execute('''
                SELECT section, COUNT(*) as count, AVG(quality_score) as avg_score
                FROM deals 
                GROUP BY section 
                ORDER BY count DESC
                LIMIT 10
            ''')
            
            categories = cursor.fetchall()
            for cat, count, avg in categories:
                stats_text += f"   • {cat}: {count:,} عرض (متوسط: {avg:.1f})\n"
            
            # إحصائيات الأسعار
            stats_text += "\n💰 إحصائيات الأسعار:\n"
            
            cursor.execute("SELECT AVG(price), MIN(price), MAX(price) FROM deals WHERE price > 0")
            price_stats = cursor.fetchone()
            if price_stats[0]:
                stats_text += f"   • متوسط السعر: {price_stats[0]:.0f} جنيه\n"
                stats_text += f"   • أقل سعر: {price_stats[1]:.0f} جنيه\n"
                stats_text += f"   • أعلى سعر: {price_stats[2]:.0f} جنيه\n"
            
            cursor.execute("SELECT AVG(discount_percent) FROM deals WHERE discount_percent > 0")
            avg_discount = cursor.fetchone()[0] or 0
            stats_text += f"   • متوسط الخصم: {avg_discount:.1f}%\n\n"
            
            # معلومات النظام
            stats_text += "🤖 معلومات النظام:\n"
            stats_text += f"   • بيانات JSON: {len(self.system.products_data):,} منتج\n"
            stats_text += f"   • مستخدمي التليجرام: {len(self.system.users)}\n"
            stats_text += f"   • التشغيل التلقائي: {'مفعل' if self.auto_run_enabled else 'معطل'}\n"
            
            conn.close()
            
            # عرض الإحصائيات
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, stats_text)
            
            self.log_message("📊 تم تحديث الإحصائيات")
            
        except Exception as e:
            self.log_message(f"❌ خطأ في الإحصائيات: {e}")
    
    def open_product_link(self, event):
        """فتح رابط المنتج"""
        
        selection = self.results_tree.selection()
        if selection:
            item = selection[0]
            values = self.results_tree.item(item, "values")
            
            try:
                conn = sqlite3.connect(self.system.db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT url, asin FROM deals WHERE name LIKE ?", (f"%{values[0][:20]}%",))
                result = cursor.fetchone()
                conn.close()
                
                if result and result[0]:
                    webbrowser.open(result[0])
                    self.log_message(f"🔗 فتح رابط: {values[0][:30]}...")
                elif result and result[1]:
                    webbrowser.open(f"https://www.amazon.eg/dp/{result[1]}")
                    self.log_message(f"🔗 فتح رابط: {values[0][:30]}...")
                    
            except Exception as e:
                self.log_message(f"❌ خطأ في فتح الرابط: {e}")
    
    def send_best_deals(self):
        """إرسال أفضل العروض"""
        
        try:
            conn = sqlite3.connect(self.system.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, price, discount_percent, quality_score, asin, section
                FROM deals 
                ORDER BY quality_score DESC
                LIMIT ?
            ''', (self.settings['target_deals'],))
            
            deals = cursor.fetchall()
            conn.close()
            
            if deals:
                # تحويل وإرسال
                deals_list = []
                for deal in deals:
                    deals_list.append({
                        'name': deal[0],
                        'price': deal[1],
                        'strike_price': deal[1] * 1.3,
                        'discount_percent': deal[2],
                        'quality_score': deal[3],
                        'asin': deal[4],
                        'section': deal[5]
                    })
                
                self.system.send_deals_to_telegram(deals_list)
                self.log_message(f"📱 تم إرسال {len(deals)} عرض للتليجرام")
                messagebox.showinfo("نجح", f"تم إرسال {len(deals)} عرض!")
            else:
                messagebox.showinfo("تنبيه", "لا توجد عروض للإرسال")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في الإرسال: {e}")
    
    def export_all_results(self):
        """تصدير جميع النتائج"""
        
        try:
            conn = sqlite3.connect(self.system.db_file)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM deals ORDER BY quality_score DESC")
            all_deals = cursor.fetchall()
            conn.close()
            
            if all_deals:
                filename = f"all_deals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                export_data = []
                for deal in all_deals:
                    export_data.append({
                        'asin': deal[1],
                        'name': deal[2],
                        'price': deal[3],
                        'discount_percent': deal[5],
                        'quality_score': deal[9],
                        'section': deal[6],
                        'source': deal[10],
                        'date_found': deal[11]
                    })
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                self.log_message(f"💾 تم تصدير {len(all_deals)} عرض إلى {filename}")
                messagebox.showinfo("نجح", f"تم تصدير جميع العروض إلى:\n{filename}")
            else:
                messagebox.showinfo("تنبيه", "لا توجد نتائج للتصدير")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في التصدير: {e}")
    
    def log_message(self, message):
        """إضافة رسالة للسجل"""
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        def update_log():
            self.log_text.insert("end", f"[{timestamp}] {message}\n")
            self.log_text.see("end")
        
        self.root.after(0, update_log)
    
    def run(self):
        """تشغيل الواجهة"""
        
        try:
            self.log_message("✅ تم تشغيل لوحة التحكم المتقدمة")
            self.log_message("💡 استخدم التبويبات للتنقل بين الوظائف")
            
            # تحديث الإحصائيات عند البدء
            self.root.after(1000, self.update_statistics)
            
            self.root.mainloop()
            
        except Exception as e:
            print(f"خطأ في تشغيل الواجهة: {e}")

if __name__ == "__main__":
    try:
        app = AdvancedGUI()
        app.run()
    except Exception as e:
        print(f"خطأ في إنشاء الواجهة: {e}")
        import traceback
        traceback.print_exc()