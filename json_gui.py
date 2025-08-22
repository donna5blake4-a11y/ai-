# json_gui.py - واجهة للنظام المعتمد على JSON

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import json
import sqlite3
from datetime import datetime
import webbrowser
import os

# استيراد النظام المعتمد على JSON
try:
    from json_based_system import JSONBasedSmartSystem
except ImportError:
    JSONBasedSmartSystem = None

class JSONSmartGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LAQTA JSON Smart System")
        self.root.geometry("1000x700")
        self.root.configure(bg="#1a1a2e")
        
        # متغيرات النظام
        self.system = None
        self.is_running = False
        self.json_file = "products.json"
        
        # إعداد الواجهة
        self.setup_gui()
    
    def setup_gui(self):
        """إعداد الواجهة"""
        
        # العنوان الرئيسي
        title_frame = tk.Frame(self.root, bg="#1a1a2e")
        title_frame.pack(fill="x", padx=15, pady=15)
        
        title_label = tk.Label(
            title_frame,
            text="🤖 LAQTA JSON Smart System",
            font=("Arial", 20, "bold"),
            bg="#1a1a2e",
            fg="#00ff88"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="تحليل ذكي لملف JSON + فحص أسعار انتقائي",
            font=("Arial", 13),
            bg="#1a1a2e",
            fg="#ffffff"
        )
        subtitle_label.pack()
        
        # إطار اختيار الملف
        file_frame = tk.Frame(self.root, bg="#1a1a2e")
        file_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(
            file_frame,
            text="📂 ملف JSON:",
            font=("Arial", 11, "bold"),
            bg="#1a1a2e",
            fg="#ffffff"
        ).pack(side="left")
        
        self.file_label = tk.Label(
            file_frame,
            text="لم يتم اختيار ملف",
            font=("Arial", 10),
            bg="#1a1a2e",
            fg="#ffaa00"
        )
        self.file_label.pack(side="left", padx=10)
        
        select_file_btn = tk.Button(
            file_frame,
            text="📁 اختيار ملف JSON",
            command=self.select_json_file,
            font=("Arial", 10, "bold"),
            bg="#4488ff",
            fg="#ffffff"
        )
        select_file_btn.pack(side="right")
        
        # أزرار التحكم الرئيسية
        controls_frame = tk.Frame(self.root, bg="#1a1a2e")
        controls_frame.pack(fill="x", padx=15, pady=10)
        
        # زر التحليل الذكي
        self.analyze_btn = tk.Button(
            controls_frame,
            text="🧠 Start Smart Analysis",
            command=self.start_smart_analysis,
            font=("Arial", 14, "bold"),
            bg="#00ff88",
            fg="#000000",
            width=22,
            height=2
        )
        self.analyze_btn.pack(side="left", padx=5)
        
        # زر الإيقاف
        self.stop_btn = tk.Button(
            controls_frame,
            text="⏹️ Stop",
            command=self.stop_analysis,
            font=("Arial", 14, "bold"),
            bg="#ff4444",
            fg="#ffffff",
            width=15,
            height=2,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        # زر عرض النتائج
        self.results_btn = tk.Button(
            controls_frame,
            text="📋 Show Results",
            command=self.show_results,
            font=("Arial", 12, "bold"),
            bg="#4488ff",
            fg="#ffffff",
            width=15,
            height=2
        )
        self.results_btn.pack(side="left", padx=5)
        
        # زر الإعدادات
        self.settings_btn = tk.Button(
            controls_frame,
            text="⚙️ Settings",
            command=self.show_settings,
            font=("Arial", 12, "bold"),
            bg="#ffaa00",
            fg="#000000",
            width=15,
            height=2
        )
        self.settings_btn.pack(side="left", padx=5)
        
        # معلومات الملف
        info_frame = tk.Frame(self.root, bg="#1a1a2e")
        info_frame.pack(fill="x", padx=15, pady=5)
        
        self.info_label = tk.Label(
            info_frame,
            text="📊 اختر ملف JSON للبدء",
            font=("Arial", 11, "bold"),
            bg="#1a1a2e",
            fg="#ffff00"
        )
        self.info_label.pack()
        
        # شريط التقدم
        progress_frame = tk.Frame(self.root, bg="#1a1a2e")
        progress_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(
            progress_frame,
            text="التقدم:",
            font=("Arial", 10),
            bg="#1a1a2e",
            fg="#ffffff"
        ).pack(side="left")
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode="indeterminate",
            length=500
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=10)
        
        # منطقة السجل
        log_frame = tk.Frame(self.root, bg="#1a1a2e")
        log_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
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
            height=18
        )
        self.log_text.pack(fill="both", expand=True, pady=(5, 0))
        
        # رسالة ترحيب
        welcome_msg = """🤖 LAQTA JSON Smart System - مرحباً!

✨ كيف يعمل النظام:
• 📂 يحلل ملف JSON الضخم (250 ألف منتج)
• 🧠 يطبق فلترة ذكية متعددة المراحل
• 💰 يفحص الأسعار الحالية لأفضل العروض
• 🎯 يختار 15 عرض موثوق فقط
• 📱 يرسل النتائج للتليجرام تلقائياً

🎯 الهدف: تحويل آلاف العروض الوهمية إلى عروض حقيقية موثوقة

📋 الخطوات:
1. اختر ملف JSON الخاص بك
2. اضغط 'Start Smart Analysis'
3. انتظر النتائج (5-10 دقائق)
4. استمتع بأفضل العروض!

"""
        self.log_text.insert("end", welcome_msg)
        self.log_text.see("end")
    
    def select_json_file(self):
        """اختيار ملف JSON"""
        
        file_path = filedialog.askopenfilename(
            title="اختيار ملف JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            self.json_file = file_path
            
            # عرض معلومات الملف
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                products_count = len(data)
                
                self.file_label.config(
                    text=f"{os.path.basename(file_path)} ({products_count:,} منتج, {file_size:.1f} MB)",
                    fg="#00ff88"
                )
                
                self.info_label.config(
                    text=f"📊 تم تحميل {products_count:,} منتج - جاهز للتحليل!"
                )
                
                self.log_message(f"✅ تم اختيار الملف: {os.path.basename(file_path)}")
                self.log_message(f"📊 المحتوى: {products_count:,} منتج ({file_size:.1f} MB)")
                
                # تهيئة النظام مع الملف الجديد
                if JSONBasedSmartSystem:
                    self.system = JSONBasedSmartSystem(file_path)
                    self.log_message("🤖 تم تهيئة النظام الذكي بنجاح")
                
            except Exception as e:
                messagebox.showerror("خطأ", f"خطأ في قراءة الملف: {e}")
                self.file_label.config(text="خطأ في الملف", fg="#ff4444")
    
    def log_message(self, message):
        """إضافة رسالة للسجل"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        def update_log():
            self.log_text.insert("end", f"[{timestamp}] {message}\n")
            self.log_text.see("end")
        
        self.root.after(0, update_log)
    
    def update_info(self, info_text):
        """تحديث معلومات الحالة"""
        def update():
            self.info_label.config(text=info_text)
        
        self.root.after(0, update)
    
    def start_smart_analysis(self):
        """بدء التحليل الذكي"""
        
        if self.is_running:
            messagebox.showwarning("تحذير", "النظام يعمل بالفعل!")
            return
        
        if not self.system:
            messagebox.showerror("خطأ", "يرجى اختيار ملف JSON أولاً!")
            return
        
        # تغيير حالة الأزرار
        self.analyze_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.is_running = True
        
        # بدء شريط التقدم
        self.progress_bar.start()
        
        # تشغيل في thread منفصل
        analysis_thread = threading.Thread(
            target=self.run_analysis_thread,
            daemon=True
        )
        analysis_thread.start()
        
        self.log_message("🚀 بدء التحليل الذكي للملف...")
    
    def run_analysis_thread(self):
        """تشغيل التحليل في thread منفصل"""
        
        try:
            # تخصيص دالة التسجيل
            original_print = print
            
            def custom_print(message):
                self.log_message(str(message))
                original_print(message)
            
            # استبدال print مؤقتاً
            import builtins
            builtins.print = custom_print
            
            # تشغيل التحليل
            self.update_info("🧠 جاري التحليل الذكي...")
            
            best_deals = self.system.run_complete_analysis()
            
            # استعادة print الأصلي
            builtins.print = original_print
            
            # تحديث النتائج
            if best_deals:
                self.update_info(f"✅ تم العثور على {len(best_deals)} عرض عالي الجودة!")
                self.log_message(f"🎯 تم الانتهاء بنجاح - {len(best_deals)} عرض معتمد")
                
                # عرض ملخص سريع
                self.show_quick_summary(best_deals)
                
            else:
                self.update_info("❌ لم يتم العثور على عروض تستوفي المعايير")
                self.log_message("❌ لا توجد عروض مناسبة في البيانات")
            
        except Exception as e:
            self.log_message(f"❌ خطأ في التحليل: {e}")
            self.update_info("❌ حدث خطأ في التحليل")
        
        finally:
            # إعادة تعيين الأزرار
            self.root.after(0, self.analysis_finished)
    
    def show_quick_summary(self, deals):
        """عرض ملخص سريع للنتائج"""
        
        summary = f"\n🎯 ملخص النتائج:\n"
        summary += f"• تم العثور على {len(deals)} عرض عالي الجودة\n"
        
        # تجميع حسب الفئات
        categories = {}
        total_savings = 0
        
        for deal in deals:
            category = deal.get('section', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
            
            savings = deal.get('strike_price', 0) - deal.get('price', 0)
            total_savings += savings
        
        summary += f"• إجمالي التوفير المحتمل: {total_savings:.0f} جنيه\n"
        summary += f"• الفئات: {', '.join(categories.keys())}\n"
        
        # أفضل 3 عروض
        summary += f"\n🏆 أفضل 3 عروض:\n"
        for i, deal in enumerate(deals[:3], 1):
            name = deal.get('name', 'منتج')[:35] + "..."
            price = deal.get('price', 0)
            discount = deal.get('discount_percent', 0)
            summary += f"{i}. {name} - {price:.0f} جنيه ({discount:.1f}%)\n"
        
        self.log_message(summary)
    
    def analysis_finished(self):
        """انتهاء التحليل"""
        self.analyze_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.is_running = False
        self.progress_bar.stop()
    
    def stop_analysis(self):
        """إيقاف التحليل"""
        self.is_running = False
        self.log_message("⏹️ تم إيقاف التحليل بواسطة المستخدم")
        self.analysis_finished()
    
    def show_results(self):
        """عرض النتائج من قاعدة البيانات"""
        
        if not self.system:
            messagebox.showerror("خطأ", "يرجى اختيار ملف JSON وتشغيل التحليل أولاً!")
            return
        
        try:
            # جلب النتائج من قاعدة البيانات
            conn = sqlite3.connect(self.system.db_file)
            cursor = conn.cursor()
            
            # جلب جميع العروض مرتبة حسب التاريخ والنقاط
            cursor.execute('''
                SELECT name, price, discount_percent, smart_score, url, asin, 
                       section, quality_level, date_added
                FROM deals 
                ORDER BY date_added DESC, smart_score DESC
                LIMIT 50
            ''')
            
            deals = cursor.fetchall()
            conn.close()
            
            if deals:
                self.show_results_window(deals)
            else:
                messagebox.showinfo("النتائج", "لا توجد نتائج محفوظة")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في عرض النتائج: {e}")
    
    def show_results_window(self, deals):
        """عرض نافذة النتائج المفصلة"""
        
        results_window = tk.Toplevel(self.root)
        results_window.title("نتائج التحليل الذكي")
        results_window.geometry("1000x650")
        results_window.configure(bg="#1a1a2e")
        
        # العنوان
        title_label = tk.Label(
            results_window,
            text=f"🏆 نتائج التحليل الذكي ({len(deals)} عرض)",
            font=("Arial", 16, "bold"),
            bg="#1a1a2e",
            fg="#00ff88"
        )
        title_label.pack(pady=10)
        
        # إطار القائمة
        list_frame = tk.Frame(results_window, bg="#1a1a2e")
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Treeview للعروض
        columns = ("الاسم", "السعر", "الخصم", "النقاط", "الفئة", "الجودة", "التاريخ")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        # تحديد عناوين الأعمدة
        tree.heading("الاسم", text="اسم المنتج")
        tree.heading("السعر", text="السعر")
        tree.heading("الخصم", text="الخصم %")
        tree.heading("النقاط", text="النقاط")
        tree.heading("الفئة", text="الفئة")
        tree.heading("الجودة", text="مستوى الجودة")
        tree.heading("التاريخ", text="تاريخ الإضافة")
        
        # تحديد عرض الأعمدة
        tree.column("الاسم", width=250)
        tree.column("السعر", width=80)
        tree.column("الخصم", width=70)
        tree.column("النقاط", width=70)
        tree.column("الفئة", width=120)
        tree.column("الجودة", width=100)
        tree.column("التاريخ", width=150)
        
        # إضافة البيانات مع ألوان
        for deal in deals:
            name = deal[0][:40] + "..." if len(deal[0]) > 40 else deal[0]
            price = f"{deal[1]:.0f} جنيه"
            discount = f"{deal[2]:.1f}%"
            score = f"{deal[3]:.1f}"
            section = deal[6] if len(deal) > 6 else "غير محدد"
            quality = deal[7] if len(deal) > 7 else "غير محدد"
            date_added = deal[8][:16] if len(deal) > 8 else "غير محدد"  # أول 16 حرف من التاريخ
            
            # تحديد لون الصف حسب النقاط
            item_id = tree.insert("", "end", values=(name, price, discount, score, section, quality, date_added))
            
            # تلوين حسب الجودة
            if deal[3] >= 80:
                tree.set(item_id, "النقاط", f"⭐ {score}")
            elif deal[3] >= 60:
                tree.set(item_id, "النقاط", f"✅ {score}")
            else:
                tree.set(item_id, "النقاط", f"📊 {score}")
        
        # إضافة scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # ربط النقر المزدوج لفتح الرابط
        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = selection[0]
                values = tree.item(item, "values")
                
                # البحث عن ASIN من قاعدة البيانات
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
                    else:
                        messagebox.showinfo("تنبيه", "الرابط غير متوفر")
                        
                except Exception as e:
                    messagebox.showerror("خطأ", f"خطأ في فتح الرابط: {e}")
        
        tree.bind("<Double-1>", on_double_click)
        
        # أزرار إضافية
        buttons_frame = tk.Frame(results_window, bg="#1a1a2e")
        buttons_frame.pack(fill="x", padx=15, pady=10)
        
        # زر إرسال للتليجرام
        send_telegram_btn = tk.Button(
            buttons_frame,
            text="📱 Send Best 15 to Telegram",
            command=lambda: self.send_best_to_telegram(deals[:15]),
            font=("Arial", 11, "bold"),
            bg="#0088ff",
            fg="#ffffff"
        )
        send_telegram_btn.pack(side="left", padx=5)
        
        # زر تصدير JSON
        export_btn = tk.Button(
            buttons_frame,
            text="💾 Export to JSON",
            command=lambda: self.export_deals(deals),
            font=("Arial", 11, "bold"),
            bg="#ff8800",
            fg="#ffffff"
        )
        export_btn.pack(side="left", padx=5)
        
        # زر نسخ الروابط
        copy_links_btn = tk.Button(
            buttons_frame,
            text="📋 Copy Links",
            command=lambda: self.copy_links(deals[:15]),
            font=("Arial", 11, "bold"),
            bg="#aa88ff",
            fg="#ffffff"
        )
        copy_links_btn.pack(side="left", padx=5)
        
        # زر إغلاق
        close_btn = tk.Button(
            buttons_frame,
            text="❌ Close",
            command=results_window.destroy,
            font=("Arial", 11, "bold"),
            bg="#666666",
            fg="#ffffff"
        )
        close_btn.pack(side="right", padx=5)
    
    def show_settings(self):
        """عرض نافذة الإعدادات"""
        
        settings_window = tk.Toplevel(self.root)
        settings_window.title("إعدادات النظام")
        settings_window.geometry("550x450")
        settings_window.configure(bg="#1a1a2e")
        
        # العنوان
        title_label = tk.Label(
            settings_window,
            text="⚙️ إعدادات النظام الذكي",
            font=("Arial", 16, "bold"),
            bg="#1a1a2e",
            fg="#ffaa00"
        )
        title_label.pack(pady=15)
        
        # إطار الإعدادات
        settings_frame = tk.Frame(settings_window, bg="#1a1a2e")
        settings_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # إعدادات الفلترة
        filter_frame = tk.LabelFrame(
            settings_frame,
            text="🎯 إعدادات الفلترة",
            font=("Arial", 12, "bold"),
            bg="#1a1a2e",
            fg="#ffffff"
        )
        filter_frame.pack(fill="x", pady=10)
        
        # حد أدنى للخصم
        tk.Label(filter_frame, text="حد أدنى للخصم (%):", bg="#1a1a2e", fg="#ffffff", font=("Arial", 10)).grid(row=0, column=0, sticky="w", padx=10, pady=8)
        self.min_discount_var = tk.StringVar(value="15")
        tk.Entry(filter_frame, textvariable=self.min_discount_var, width=10, font=("Arial", 10)).grid(row=0, column=1, padx=10, pady=8)
        
        # حد أدنى للسعر
        tk.Label(filter_frame, text="حد أدنى للسعر (جنيه):", bg="#1a1a2e", fg="#ffffff", font=("Arial", 10)).grid(row=1, column=0, sticky="w", padx=10, pady=8)
        self.min_price_var = tk.StringVar(value="25")
        tk.Entry(filter_frame, textvariable=self.min_price_var, width=10, font=("Arial", 10)).grid(row=1, column=1, padx=10, pady=8)
        
        # حد أقصى للسعر
        tk.Label(filter_frame, text="حد أقصى للسعر (جنيه):", bg="#1a1a2e", fg="#ffffff", font=("Arial", 10)).grid(row=2, column=0, sticky="w", padx=10, pady=8)
        self.max_price_var = tk.StringVar(value="8000")
        tk.Entry(filter_frame, textvariable=self.max_price_var, width=10, font=("Arial", 10)).grid(row=2, column=1, padx=10, pady=8)
        
        # عدد العروض المطلوبة
        tk.Label(filter_frame, text="عدد العروض المطلوبة:", bg="#1a1a2e", fg="#ffffff", font=("Arial", 10)).grid(row=3, column=0, sticky="w", padx=10, pady=8)
        self.target_count_var = tk.StringVar(value="15")
        tk.Entry(filter_frame, textvariable=self.target_count_var, width=10, font=("Arial", 10)).grid(row=3, column=1, padx=10, pady=8)
        
        # إعدادات التليجرام
        telegram_frame = tk.LabelFrame(
            settings_frame,
            text="📱 إعدادات التليجرام",
            font=("Arial", 12, "bold"),
            bg="#1a1a2e",
            fg="#ffffff"
        )
        telegram_frame.pack(fill="x", pady=10)
        
        # عرض الإعدادات الحالية
        try:
            with open('telegram_config.json', 'r') as f:
                config = json.load(f)
                bot_token = config.get('bot_token', 'غير محدد')
                users_count = len(config.get('users', []))
        except:
            bot_token = 'غير محدد'
            users_count = 0
        
        tk.Label(
            telegram_frame,
            text=f"Bot Token: {bot_token[:25]}..." if len(bot_token) > 25 else bot_token,
            bg="#1a1a2e",
            fg="#ffffff",
            font=("Arial", 10)
        ).pack(anchor="w", padx=10, pady=5)
        
        tk.Label(
            telegram_frame,
            text=f"عدد المستخدمين المسموحين: {users_count}",
            bg="#1a1a2e",
            fg="#ffffff",
            font=("Arial", 10)
        ).pack(anchor="w", padx=10, pady=5)
        
        # معلومات ScraperAPI
        api_frame = tk.LabelFrame(
            settings_frame,
            text="🔑 ScraperAPI",
            font=("Arial", 12, "bold"),
            bg="#1a1a2e",
            fg="#ffffff"
        )
        api_frame.pack(fill="x", pady=10)
        
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                api_key = config.get('SCRAPER_API_KEY', 'غير محدد')
        except:
            api_key = 'غير محدد'
        
        tk.Label(
            api_frame,
            text=f"API Key: {api_key[:20]}..." if len(api_key) > 20 else api_key,
            bg="#1a1a2e",
            fg="#ffffff",
            font=("Arial", 10)
        ).pack(anchor="w", padx=10, pady=5)
        
        # أزرار حفظ وإغلاق
        buttons_frame = tk.Frame(settings_window, bg="#1a1a2e")
        buttons_frame.pack(fill="x", padx=20, pady=15)
        
        save_btn = tk.Button(
            buttons_frame,
            text="💾 حفظ الإعدادات",
            command=lambda: self.save_settings(settings_window),
            font=("Arial", 12, "bold"),
            bg="#00ff88",
            fg="#000000"
        )
        save_btn.pack(side="left", padx=5)
        
        close_settings_btn = tk.Button(
            buttons_frame,
            text="❌ إغلاق",
            command=settings_window.destroy,
            font=("Arial", 12, "bold"),
            bg="#666666",
            fg="#ffffff"
        )
        close_settings_btn.pack(side="right", padx=5)
    
    def save_settings(self, window):
        """حفظ الإعدادات"""
        try:
            # تحديث إعدادات النظام
            if self.system:
                self.system.min_discount = float(self.min_discount_var.get())
                self.system.min_price = float(self.min_price_var.get())
                self.system.max_price = float(self.max_price_var.get())
            
            self.log_message("💾 تم حفظ الإعدادات الجديدة")
            messagebox.showinfo("نجح", "تم حفظ الإعدادات بنجاح!")
            window.destroy()
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في حفظ الإعدادات: {e}")
    
    def send_best_to_telegram(self, deals):
        """إرسال أفضل العروض للتليجرام"""
        
        if not self.system:
            messagebox.showerror("خطأ", "النظام غير متاح!")
            return
        
        try:
            # تحويل البيانات للتنسيق المطلوب
            deals_list = []
            for deal in deals:
                deals_list.append({
                    'name': deal[0],
                    'price': deal[1],
                    'discount_percent': deal[2],
                    'final_score': deal[3],
                    'url': deal[4] if len(deal) > 4 else '',
                    'asin': deal[5] if len(deal) > 5 else ''
                })
            
            self.system.send_deals_to_telegram(deals_list)
            self.log_message(f"📱 تم إرسال {len(deals_list)} عرض للتليجرام")
            messagebox.showinfo("نجح", f"تم إرسال {len(deals_list)} عرض للتليجرام!")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في الإرسال: {e}")
    
    def export_deals(self, deals):
        """تصدير العروض إلى JSON"""
        
        try:
            # تحويل البيانات
            export_data = []
            for deal in deals:
                export_data.append({
                    'name': deal[0],
                    'price': deal[1],
                    'discount_percent': deal[2],
                    'smart_score': deal[3],
                    'section': deal[6] if len(deal) > 6 else '',
                    'quality_level': deal[7] if len(deal) > 7 else '',
                    'url': deal[4] if len(deal) > 4 else '',
                    'asin': deal[5] if len(deal) > 5 else '',
                    'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # حفظ في ملف
            filename = f"smart_deals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.log_message(f"💾 تم تصدير {len(deals)} عرض إلى {filename}")
            messagebox.showinfo("نجح", f"تم تصدير العروض إلى:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في التصدير: {e}")
    
    def copy_links(self, deals):
        """نسخ روابط العروض"""
        
        try:
            links = []
            for deal in deals:
                asin = deal[5] if len(deal) > 5 else ''
                if asin:
                    links.append(f"https://www.amazon.eg/dp/{asin}")
            
            links_text = '\n'.join(links)
            
            # نسخ للحافظة
            self.root.clipboard_clear()
            self.root.clipboard_append(links_text)
            
            self.log_message(f"📋 تم نسخ {len(links)} رابط للحافظة")
            messagebox.showinfo("نجح", f"تم نسخ {len(links)} رابط للحافظة!")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في نسخ الروابط: {e}")
    
    def run(self):
        """تشغيل الواجهة"""
        
        try:
            self.log_message("✅ تم تشغيل الواجهة بنجاح")
            self.log_message("💡 اختر ملف JSON أولاً ثم ابدأ التحليل")
            
            self.root.mainloop()
            
        except Exception as e:
            print(f"خطأ في تشغيل الواجهة: {e}")

if __name__ == "__main__":
    try:
        app = JSONSmartGUI()
        app.run()
    except Exception as e:
        print(f"خطأ في إنشاء الواجهة: {e}")
        import traceback
        traceback.print_exc()