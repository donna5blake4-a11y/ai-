# simple_gui.py - واجهة بسيطة للنظام الذكي

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import sqlite3
from datetime import datetime
import webbrowser

# استيراد النظام المحسن
try:
    from fixed_integrated_system import FixedSmartSystem
except ImportError:
    FixedSmartSystem = None

class SimpleSmartGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LAQTA Smart Deals System")
        self.root.geometry("900x700")
        self.root.configure(bg="#2b2b2b")
        
        # متغيرات النظام
        self.system = None
        self.is_running = False
        
        # إعداد الواجهة
        self.setup_gui()
        
        # تهيئة النظام
        if FixedSmartSystem:
            self.system = FixedSmartSystem()
    
    def setup_gui(self):
        """إعداد الواجهة"""
        
        # العنوان الرئيسي
        title_frame = tk.Frame(self.root, bg="#2b2b2b")
        title_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = tk.Label(
            title_frame,
            text="🤖 LAQTA Smart Deals System",
            font=("Arial", 18, "bold"),
            bg="#2b2b2b",
            fg="#00ff88"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="يحول 1000+ عرض وهمي إلى 15 عرض موثوق يومياً",
            font=("Arial", 12),
            bg="#2b2b2b",
            fg="#ffffff"
        )
        subtitle_label.pack()
        
        # أزرار التحكم
        controls_frame = tk.Frame(self.root, bg="#2b2b2b")
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        # زر البدء
        self.start_btn = tk.Button(
            controls_frame,
            text="🚀 Start Smart Analysis",
            command=self.start_analysis,
            font=("Arial", 12, "bold"),
            bg="#00ff88",
            fg="#000000",
            width=20,
            height=2
        )
        self.start_btn.pack(side="left", padx=5)
        
        # زر الإيقاف
        self.stop_btn = tk.Button(
            controls_frame,
            text="⏹️ Stop",
            command=self.stop_analysis,
            font=("Arial", 12, "bold"),
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
        
        # الإحصائيات
        stats_frame = tk.Frame(self.root, bg="#2b2b2b")
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.stats_label = tk.Label(
            stats_frame,
            text="📊 Ready to start - No data yet",
            font=("Arial", 11, "bold"),
            bg="#2b2b2b",
            fg="#ffff00"
        )
        self.stats_label.pack()
        
        # شريط التقدم
        progress_frame = tk.Frame(self.root, bg="#2b2b2b")
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(
            progress_frame,
            text="Progress:",
            font=("Arial", 10),
            bg="#2b2b2b",
            fg="#ffffff"
        ).pack(side="left")
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode="indeterminate",
            length=400
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=10)
        
        # منطقة السجل
        log_frame = tk.Frame(self.root, bg="#2b2b2b")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        tk.Label(
            log_frame,
            text="📝 System Log:",
            font=("Arial", 11, "bold"),
            bg="#2b2b2b",
            fg="#ffffff"
        ).pack(anchor="w")
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 10),
            bg="#1a1a1a",
            fg="#ffffff",
            insertbackground="#ffffff",
            height=20
        )
        self.log_text.pack(fill="both", expand=True, pady=(5, 0))
        
        # رسالة ترحيب
        welcome_msg = """🤖 LAQTA Smart Deals System - Ready!

✨ المميزات:
• 🧠 فلترة ذكية للعروض الحقيقية
• 🎯 نظام نقاط متطور (1-100)
• 📊 إحصائيات مباشرة
• 📱 إرسال تلقائي للتليجرام
• 🚀 أداء محسن

🎯 الهدف: 15 عرض موثوق يومياً بدلاً من 1000+ عرض وهمي

اضغط 'Start Smart Analysis' للبدء!

"""
        self.log_text.insert("end", welcome_msg)
        self.log_text.see("end")
    
    def log_message(self, message):
        """إضافة رسالة للسجل"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        def update_log():
            self.log_text.insert("end", f"[{timestamp}] {message}\n")
            self.log_text.see("end")
        
        # تحديث من thread آمن
        self.root.after(0, update_log)
    
    def update_stats(self, stats_text):
        """تحديث الإحصائيات"""
        def update():
            self.stats_label.config(text=stats_text)
        
        self.root.after(0, update)
    
    def start_analysis(self):
        """بدء التحليل الذكي"""
        
        if self.is_running:
            messagebox.showwarning("تحذير", "النظام يعمل بالفعل!")
            return
        
        if not self.system:
            messagebox.showerror("خطأ", "النظام غير متاح!")
            return
        
        # تغيير حالة الأزرار
        self.start_btn.config(state="disabled")
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
        
        self.log_message("🚀 بدء التحليل الذكي...")
    
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
            self.update_stats("📊 جاري الكشط والتحليل...")
            
            best_deals = self.system.run_complete_analysis()
            
            # استعادة print الأصلي
            builtins.print = original_print
            
            # تحديث النتائج
            if best_deals:
                self.update_stats(f"✅ تم العثور على {len(best_deals)} عرض عالي الجودة!")
                self.log_message(f"🎯 تم الانتهاء بنجاح - {len(best_deals)} عرض معتمد")
            else:
                self.update_stats("❌ لم يتم العثور على عروض تستوفي المعايير")
                self.log_message("❌ لا توجد عروض مناسبة اليوم")
            
        except Exception as e:
            self.log_message(f"❌ خطأ في التحليل: {e}")
            self.update_stats("❌ حدث خطأ في التحليل")
        
        finally:
            # إعادة تعيين الأزرار
            self.root.after(0, self.analysis_finished)
    
    def analysis_finished(self):
        """انتهاء التحليل"""
        self.start_btn.config(state="normal")
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
            messagebox.showerror("خطأ", "النظام غير متاح!")
            return
        
        try:
            # جلب النتائج من قاعدة البيانات
            conn = sqlite3.connect(self.system.db_file)
            cursor = conn.cursor()
            
            # جلب عروض اليوم
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT name, price, discount_percent, smart_score, url, asin
                FROM deals 
                WHERE date_added LIKE ? 
                ORDER BY smart_score DESC
                LIMIT 20
            ''', (f'{today}%',))
            
            deals = cursor.fetchall()
            conn.close()
            
            if deals:
                # إنشاء نافذة النتائج
                self.show_results_window(deals)
            else:
                messagebox.showinfo("النتائج", "لا توجد عروض لليوم الحالي")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في عرض النتائج: {e}")
    
    def show_results_window(self, deals):
        """عرض نافذة النتائج"""
        
        results_window = tk.Toplevel(self.root)
        results_window.title("أفضل العروض اليوم")
        results_window.geometry("800x600")
        results_window.configure(bg="#2b2b2b")
        
        # العنوان
        title_label = tk.Label(
            results_window,
            text=f"🏆 أفضل {len(deals)} عرض اليوم",
            font=("Arial", 16, "bold"),
            bg="#2b2b2b",
            fg="#00ff88"
        )
        title_label.pack(pady=10)
        
        # إطار القائمة
        list_frame = tk.Frame(results_window, bg="#2b2b2b")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview للعروض
        columns = ("الاسم", "السعر", "الخصم", "النقاط", "الإجراء")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # تحديد عناوين الأعمدة
        tree.heading("الاسم", text="اسم المنتج")
        tree.heading("السعر", text="السعر (جنيه)")
        tree.heading("الخصم", text="الخصم (%)")
        tree.heading("النقاط", text="نقاط الجودة")
        tree.heading("الإجراء", text="الإجراء")
        
        # تحديد عرض الأعمدة
        tree.column("الاسم", width=300)
        tree.column("السعر", width=100)
        tree.column("الخصم", width=80)
        tree.column("النقاط", width=100)
        tree.column("الإجراء", width=100)
        
        # إضافة البيانات
        for deal in deals:
            name = deal[0][:50] + "..." if len(deal[0]) > 50 else deal[0]
            price = f"{deal[1]:.0f}"
            discount = f"{deal[2]:.1f}%"
            score = f"{deal[3]:.1f}/100"
            action = "🔗 فتح"
            
            tree.insert("", "end", values=(name, price, discount, score, action))
        
        # إضافة scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ربط النقر المزدوج لفتح الرابط
        def on_double_click(event):
            item = tree.selection()[0]
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
                elif result and result[1]:
                    webbrowser.open(f"https://www.amazon.eg/dp/{result[1]}")
                else:
                    messagebox.showinfo("تنبيه", "الرابط غير متوفر")
                    
            except Exception as e:
                messagebox.showerror("خطأ", f"خطأ في فتح الرابط: {e}")
        
        tree.bind("<Double-1>", on_double_click)
        
        # أزرار إضافية
        buttons_frame = tk.Frame(results_window, bg="#2b2b2b")
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        # زر إرسال للتليجرام
        send_telegram_btn = tk.Button(
            buttons_frame,
            text="📱 Send to Telegram",
            command=lambda: self.send_to_telegram(deals),
            font=("Arial", 11, "bold"),
            bg="#0088ff",
            fg="#ffffff"
        )
        send_telegram_btn.pack(side="left", padx=5)
        
        # زر تصدير JSON
        export_btn = tk.Button(
            buttons_frame,
            text="💾 Export JSON",
            command=lambda: self.export_deals(deals),
            font=("Arial", 11, "bold"),
            bg="#ff8800",
            fg="#ffffff"
        )
        export_btn.pack(side="left", padx=5)
        
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
        settings_window.geometry("500x400")
        settings_window.configure(bg="#2b2b2b")
        
        # العنوان
        title_label = tk.Label(
            settings_window,
            text="⚙️ إعدادات النظام الذكي",
            font=("Arial", 14, "bold"),
            bg="#2b2b2b",
            fg="#ffaa00"
        )
        title_label.pack(pady=10)
        
        # إطار الإعدادات
        settings_frame = tk.Frame(settings_window, bg="#2b2b2b")
        settings_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # إعدادات الفلترة
        filter_frame = tk.LabelFrame(
            settings_frame,
            text="إعدادات الفلترة",
            font=("Arial", 11, "bold"),
            bg="#2b2b2b",
            fg="#ffffff"
        )
        filter_frame.pack(fill="x", pady=5)
        
        # حد أدنى للخصم
        tk.Label(filter_frame, text="حد أدنى للخصم (%):", bg="#2b2b2b", fg="#ffffff").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.min_discount_var = tk.StringVar(value="15")
        tk.Entry(filter_frame, textvariable=self.min_discount_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        # حد أدنى للسعر
        tk.Label(filter_frame, text="حد أدنى للسعر (جنيه):", bg="#2b2b2b", fg="#ffffff").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.min_price_var = tk.StringVar(value="20")
        tk.Entry(filter_frame, textvariable=self.min_price_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        
        # عدد العروض المطلوبة
        tk.Label(filter_frame, text="عدد العروض المطلوبة:", bg="#2b2b2b", fg="#ffffff").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.target_count_var = tk.StringVar(value="15")
        tk.Entry(filter_frame, textvariable=self.target_count_var, width=10).grid(row=2, column=1, padx=5, pady=5)
        
        # إعدادات التليجرام
        telegram_frame = tk.LabelFrame(
            settings_frame,
            text="إعدادات التليجرام",
            font=("Arial", 11, "bold"),
            bg="#2b2b2b",
            fg="#ffffff"
        )
        telegram_frame.pack(fill="x", pady=5)
        
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
            text=f"Bot Token: {bot_token[:20]}..." if len(bot_token) > 20 else bot_token,
            bg="#2b2b2b",
            fg="#ffffff"
        ).pack(anchor="w", padx=5, pady=2)
        
        tk.Label(
            telegram_frame,
            text=f"عدد المستخدمين: {users_count}",
            bg="#2b2b2b",
            fg="#ffffff"
        ).pack(anchor="w", padx=5, pady=2)
        
        # زر حفظ الإعدادات
        save_btn = tk.Button(
            settings_window,
            text="💾 Save Settings",
            command=lambda: self.save_settings(settings_window),
            font=("Arial", 12, "bold"),
            bg="#00ff88",
            fg="#000000"
        )
        save_btn.pack(pady=10)
    
    def save_settings(self, window):
        """حفظ الإعدادات"""
        try:
            # تحديث إعدادات النظام
            if self.system:
                self.system.min_discount = float(self.min_discount_var.get())
                self.system.min_price = float(self.min_price_var.get())
            
            messagebox.showinfo("نجح", "تم حفظ الإعدادات بنجاح!")
            window.destroy()
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في حفظ الإعدادات: {e}")
    
    def send_to_telegram(self, deals):
        """إرسال العروض للتليجرام"""
        
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
            messagebox.showinfo("نجح", "تم إرسال العروض للتليجرام!")
            
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
                    'url': deal[4] if len(deal) > 4 else '',
                    'asin': deal[5] if len(deal) > 5 else '',
                    'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # حفظ في ملف
            filename = f"exported_deals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("نجح", f"تم تصدير العروض إلى:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في التصدير: {e}")
    
    def run(self):
        """تشغيل الواجهة"""
        
        try:
            self.log_message("✅ تم تشغيل الواجهة بنجاح")
            self.log_message("💡 اضغط 'Start Smart Analysis' لبدء التحليل")
            
            self.root.mainloop()
            
        except Exception as e:
            print(f"خطأ في تشغيل الواجهة: {e}")

if __name__ == "__main__":
    try:
        app = SimpleSmartGUI()
        app.run()
    except Exception as e:
        print(f"خطأ في إنشاء الواجهة: {e}")
        import traceback
        traceback.print_exc()