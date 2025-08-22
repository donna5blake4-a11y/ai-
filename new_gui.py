# new_gui.py - واجهة جديدة للنظام الأصلي المحسن

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import sqlite3
from datetime import datetime
import webbrowser
import os

# استيراد النظام الأصلي المحسن
try:
    from original_system_with_json import OriginalSystemWithJSON
except ImportError:
    OriginalSystemWithJSON = None

class NewGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LAQTA Original System + JSON Enhanced")
        self.root.geometry("950x650")
        self.root.configure(bg="#1e1e2e")
        
        # متغيرات النظام
        self.system = None
        self.is_running = False
        
        # إعداد الواجهة
        self.setup_gui()
        
        # تهيئة النظام
        if OriginalSystemWithJSON:
            self.system = OriginalSystemWithJSON()
    
    def setup_gui(self):
        """إعداد الواجهة"""
        
        # العنوان الرئيسي
        title_frame = tk.Frame(self.root, bg="#1e1e2e")
        title_frame.pack(fill="x", padx=15, pady=15)
        
        title_label = tk.Label(
            title_frame,
            text="🤖 LAQTA Original System Enhanced",
            font=("Arial", 18, "bold"),
            bg="#1e1e2e",
            fg="#00ff88"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="النظام الأصلي الشغال + تحسينات JSON",
            font=("Arial", 12),
            bg="#1e1e2e",
            fg="#ffffff"
        )
        subtitle_label.pack()
        
        # معلومات النظام
        info_frame = tk.Frame(self.root, bg="#1e1e2e")
        info_frame.pack(fill="x", padx=15, pady=5)
        
        self.info_label = tk.Label(
            info_frame,
            text="📊 جاري تحميل النظام...",
            font=("Arial", 11, "bold"),
            bg="#1e1e2e",
            fg="#ffff00"
        )
        self.info_label.pack()
        
        # أزرار التحكم
        controls_frame = tk.Frame(self.root, bg="#1e1e2e")
        controls_frame.pack(fill="x", padx=15, pady=10)
        
        # زر البدء الرئيسي
        self.start_btn = tk.Button(
            controls_frame,
            text="🚀 Start Original System",
            command=self.start_system,
            font=("Arial", 14, "bold"),
            bg="#00ff88",
            fg="#000000",
            width=25,
            height=2
        )
        self.start_btn.pack(side="left", padx=5)
        
        # زر الإيقاف
        self.stop_btn = tk.Button(
            controls_frame,
            text="⏹️ Stop",
            command=self.stop_system,
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
        
        # زر الإحصائيات
        self.stats_btn = tk.Button(
            controls_frame,
            text="📊 Statistics",
            command=self.show_statistics,
            font=("Arial", 12, "bold"),
            bg="#ff8800",
            fg="#ffffff",
            width=15,
            height=2
        )
        self.stats_btn.pack(side="left", padx=5)
        
        # شريط التقدم
        progress_frame = tk.Frame(self.root, bg="#1e1e2e")
        progress_frame.pack(fill="x", padx=15, pady=5)
        
        tk.Label(
            progress_frame,
            text="التقدم:",
            font=("Arial", 10),
            bg="#1e1e2e",
            fg="#ffffff"
        ).pack(side="left")
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode="indeterminate",
            length=500
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=10)
        
        # منطقة السجل
        log_frame = tk.Frame(self.root, bg="#1e1e2e")
        log_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        tk.Label(
            log_frame,
            text="📝 سجل النظام:",
            font=("Arial", 12, "bold"),
            bg="#1e1e2e",
            fg="#ffffff"
        ).pack(anchor="w")
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 10),
            bg="#0d1117",
            fg="#ffffff",
            insertbackground="#ffffff",
            height=20
        )
        self.log_text.pack(fill="both", expand=True, pady=(5, 0))
        
        # رسالة ترحيب
        self.show_welcome_message()
        
        # تحديث معلومات النظام
        self.update_system_info()
    
    def show_welcome_message(self):
        """عرض رسالة الترحيب"""
        
        welcome_msg = """🤖 LAQTA Original System Enhanced - مرحباً!

✨ النظام الأصلي الشغال مع تحسينات:
• 🔍 كشط مباشر من أمازون (نفس النظام الشغال)
• 📂 قراءة ملف JSON تلقائياً للتحسين
• 🧠 تحسين البيانات (أسماء، صور، روابط)
• 📈 نقاط إضافية للعروض المحسنة
• 📱 إرسال تلقائي للتليجرام

🎯 الهدف: 15 عرض موثوق بدلاً من مئات العروض الوهمية

🚀 اضغط 'Start Original System' للبدء!

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
            
            self.info_label.config(text=info_text)
            
            # رسالة في السجل
            if json_count > 0:
                self.log_message(f"✅ تم تحميل {json_count:,} منتج من JSON للتحسين")
            else:
                self.log_message("💡 سيعمل النظام بالكشط المباشر فقط")
                
            self.log_message(f"✅ إعدادات التليجرام: {telegram_users} مستخدم")
        else:
            self.info_label.config(text="❌ النظام غير متاح")
    
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
    
    def start_system(self):
        """بدء النظام الأصلي"""
        
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
        system_thread = threading.Thread(
            target=self.run_system_thread,
            daemon=True
        )
        system_thread.start()
        
        self.log_message("🚀 بدء النظام الأصلي المحسن...")
    
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
            
            # تشغيل النظام الأصلي
            self.update_info("🔍 جاري الكشط والتحليل...")
            
            deals = self.system.run_system()
            
            # استعادة print الأصلي
            builtins.print = original_print
            
            # تحديث النتائج
            if deals:
                json_enhanced = sum(1 for d in deals if 'json' in d.get('source', ''))
                
                if json_enhanced > 0:
                    self.update_info(f"✅ تم إرسال {len(deals)} عرض ({json_enhanced} محسن بـ JSON)")
                else:
                    self.update_info(f"✅ تم إرسال {len(deals)} عرض عالي الجودة")
                
                self.log_message(f"🎯 تم الانتهاء بنجاح - {len(deals)} عرض مرسل")
                
                if json_enhanced > 0:
                    self.log_message(f"🧠 تم تحسين {json_enhanced} عرض بواسطة JSON")
                
            else:
                self.update_info("❌ لم يتم العثور على عروض مناسبة")
                self.log_message("❌ لا توجد عروض مناسبة اليوم")
            
        except Exception as e:
            self.log_message(f"❌ خطأ في النظام: {e}")
            self.update_info("❌ حدث خطأ في النظام")
        
        finally:
            # إعادة تعيين الأزرار
            self.root.after(0, self.system_finished)
    
    def system_finished(self):
        """انتهاء تشغيل النظام"""
        
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.is_running = False
        self.progress_bar.stop()
    
    def stop_system(self):
        """إيقاف النظام"""
        
        self.is_running = False
        self.log_message("⏹️ تم إيقاف النظام بواسطة المستخدم")
        self.system_finished()
    
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
                SELECT name, price, discount_percent, quality_score, url, asin, 
                       section, source, date_found
                FROM deals 
                WHERE date_found LIKE ? 
                ORDER BY quality_score DESC
                LIMIT 30
            ''', (f'{today}%',))
            
            deals = cursor.fetchall()
            conn.close()
            
            if deals:
                self.show_results_window(deals)
            else:
                messagebox.showinfo("النتائج", "لا توجد نتائج لليوم الحالي")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في عرض النتائج: {e}")
    
    def show_results_window(self, deals):
        """عرض نافذة النتائج"""
        
        results_window = tk.Toplevel(self.root)
        results_window.title("نتائج النظام الأصلي المحسن")
        results_window.geometry("900x600")
        results_window.configure(bg="#1e1e2e")
        
        # العنوان
        title_label = tk.Label(
            results_window,
            text=f"🏆 نتائج اليوم ({len(deals)} عرض)",
            font=("Arial", 16, "bold"),
            bg="#1e1e2e",
            fg="#00ff88"
        )
        title_label.pack(pady=10)
        
        # إطار القائمة
        list_frame = tk.Frame(results_window, bg="#1e1e2e")
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Treeview للعروض
        columns = ("الاسم", "السعر", "الخصم", "النقاط", "المصدر", "الفئة")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=18)
        
        # تحديد عناوين الأعمدة
        tree.heading("الاسم", text="اسم المنتج")
        tree.heading("السعر", text="السعر (جنيه)")
        tree.heading("الخصم", text="الخصم (%)")
        tree.heading("النقاط", text="نقاط الجودة")
        tree.heading("المصدر", text="المصدر")
        tree.heading("الفئة", text="الفئة")
        
        # تحديد عرض الأعمدة
        tree.column("الاسم", width=250)
        tree.column("السعر", width=100)
        tree.column("الخصم", width=80)
        tree.column("النقاط", width=100)
        tree.column("المصدر", width=120)
        tree.column("الفئة", width=120)
        
        # إضافة البيانات
        for deal in deals:
            name = deal[0][:45] + "..." if len(deal[0]) > 45 else deal[0]
            price = f"{deal[1]:.0f}"
            discount = f"{deal[2]:.1f}%"
            score = f"{deal[3]:.1f}/100"
            
            # تحديد المصدر
            source = deal[7] if len(deal) > 7 else "scraping"
            if 'json' in source:
                source_text = "🧠 محسن بـ JSON"
            else:
                source_text = "🔍 كشط مباشر"
            
            category = deal[6] if len(deal) > 6 else "غير محدد"
            
            # إضافة الصف مع تلوين حسب النقاط
            item_id = tree.insert("", "end", values=(name, price, discount, score, source_text, category))
            
            # تلوين حسب الجودة
            if deal[3] >= 80:
                tree.set(item_id, "النقاط", f"⭐ {score}")
            elif deal[3] >= 65:
                tree.set(item_id, "النقاط", f"✅ {score}")
            else:
                tree.set(item_id, "النقاط", f"📊 {score}")
        
        # إضافة scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
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
        buttons_frame = tk.Frame(results_window, bg="#1e1e2e")
        buttons_frame.pack(fill="x", padx=15, pady=10)
        
        # زر إرسال للتليجرام
        send_telegram_btn = tk.Button(
            buttons_frame,
            text="📱 Send to Telegram",
            command=lambda: self.manual_send_to_telegram(deals[:15]),
            font=("Arial", 11, "bold"),
            bg="#0088ff",
            fg="#ffffff"
        )
        send_telegram_btn.pack(side="left", padx=5)
        
        # زر تصدير
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
    
    def show_statistics(self):
        """عرض الإحصائيات"""
        
        if not self.system:
            messagebox.showerror("خطأ", "النظام غير متاح!")
            return
        
        try:
            conn = sqlite3.connect(self.system.db_file)
            cursor = conn.cursor()
            
            # إحصائيات عامة
            cursor.execute("SELECT COUNT(*) FROM deals")
            total_deals = cursor.fetchone()[0]
            
            # عروض اليوم
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT COUNT(*) FROM deals WHERE date_found LIKE ?", (f'{today}%',))
            today_deals = cursor.fetchone()[0]
            
            # العروض المحسنة بـ JSON
            cursor.execute("SELECT COUNT(*) FROM deals WHERE source LIKE '%json%'")
            json_enhanced = cursor.fetchone()[0]
            
            # متوسط النقاط
            cursor.execute("SELECT AVG(quality_score) FROM deals WHERE quality_score > 0")
            avg_score = cursor.fetchone()[0] or 0
            
            conn.close()
            
            # عرض الإحصائيات
            stats_text = f"""📊 إحصائيات النظام:

📦 إجمالي العروض: {total_deals:,}
🗓️ عروض اليوم: {today_deals:,}
🧠 محسن بـ JSON: {json_enhanced:,}
⭐ متوسط النقاط: {avg_score:.1f}

📂 بيانات JSON: {len(self.system.products_data):,} منتج
📱 مستخدمي التليجرام: {len(self.system.users)}

🎯 النظام الأصلي + تحسينات JSON"""
            
            self.log_message(stats_text)
            messagebox.showinfo("إحصائيات النظام", stats_text)
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في الإحصائيات: {e}")
    
    def manual_send_to_telegram(self, deals):
        """إرسال يدوي للتليجرام"""
        
        if not self.system or not deals:
            messagebox.showerror("خطأ", "لا توجد عروض للإرسال!")
            return
        
        try:
            # تحويل البيانات للتنسيق المطلوب
            deals_list = []
            for deal in deals:
                deals_list.append({
                    'name': deal[0],
                    'price': deal[1],
                    'strike_price': deal[1] * 1.3,  # افتراضي
                    'discount_percent': deal[2],
                    'quality_score': deal[3],
                    'asin': deal[5] if len(deal) > 5 else '',
                    'section': deal[6] if len(deal) > 6 else ''
                })
            
            # إرسال
            self.system.send_deals_to_telegram(deals_list)
            self.log_message(f"📱 تم إرسال {len(deals_list)} عرض للتليجرام")
            messagebox.showinfo("نجح", f"تم إرسال {len(deals_list)} عرض للتليجرام!")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في الإرسال: {e}")
    
    def export_deals(self, deals):
        """تصدير العروض"""
        
        try:
            export_data = []
            for deal in deals:
                export_data.append({
                    'name': deal[0],
                    'price': deal[1],
                    'discount_percent': deal[2],
                    'quality_score': deal[3],
                    'url': deal[4] if len(deal) > 4 else '',
                    'asin': deal[5] if len(deal) > 5 else '',
                    'section': deal[6] if len(deal) > 6 else '',
                    'source': deal[7] if len(deal) > 7 else '',
                    'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            filename = f"deals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.log_message(f"💾 تم تصدير {len(deals)} عرض إلى {filename}")
            messagebox.showinfo("نجح", f"تم تصدير العروض إلى:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في التصدير: {e}")
    
    def run(self):
        """تشغيل الواجهة"""
        
        try:
            self.log_message("✅ تم تشغيل الواجهة بنجاح")
            self.log_message("💡 اضغط 'Start Original System' لبدء النظام")
            
            self.root.mainloop()
            
        except Exception as e:
            print(f"خطأ في تشغيل الواجهة: {e}")

if __name__ == "__main__":
    try:
        app = NewGUI()
        app.run()
    except Exception as e:
        print(f"خطأ في إنشاء الواجهة: {e}")
        import traceback
        traceback.print_exc()