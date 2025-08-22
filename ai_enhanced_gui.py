# ai_enhanced_gui.py
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import sqlite3
import json
import threading
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from PIL import Image, ImageTk
import requests
from io import BytesIO
import webbrowser
from ai_price_analyzer import AIAnalyzer, DealQualityFilter
from enhanced_telegram_bot import EnhancedTelegramBot
from egyptian_sites_scraper import EgyptianSitesScraper
from migrate_json_to_sqlite import JSONToSQLiteMigrator
import logging

# إعداد الـ logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# إعداد المظهر
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AIEnhancedGUI:
    """واجهة مستخدم احترافية مع نظام AI متكامل"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("🤖 AI-Enhanced Amazon Deal Analyzer")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # المتغيرات الأساسية
        self.db_file = "amz_products.db"
        self.ai_analyzer = None
        self.deal_filter = None
        self.telegram_bot = None
        self.scraper = None
        self.migrator = None
        
        # حالة النظام
        self.system_status = {
            'ai_enabled': False,
            'telegram_enabled': False,
            'scraping_active': False,
            'analysis_running': False
        }
        
        # إحصائيات
        self.stats = {
            'total_products': 0,
            'ai_verified': 0,
            'high_quality_deals': 0,
            'avg_ai_score': 0
        }
        
        # إنشاء الواجهة
        self.create_widgets()
        self.load_initial_data()
        
        # بدء تحديث الإحصائيات
        self.start_stats_update()
    
    def create_widgets(self):
        """إنشاء عناصر الواجهة"""
        
        # الشريط الجانبي
        self.create_sidebar()
        
        # المنطقة الرئيسية
        self.create_main_area()
        
        # شريط الحالة
        self.create_status_bar()
    
    def create_sidebar(self):
        """إنشاء الشريط الجانبي للتنقل"""
        self.sidebar = ctk.CTkFrame(self.root, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)
        
        # العنوان
        title_label = ctk.CTkLabel(
            self.sidebar, 
            text="🤖 AI Deal Analyzer", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # أزرار التنقل
        nav_buttons = [
            ("📊 Dashboard", self.show_dashboard),
            ("🤖 AI Analysis", self.show_ai_analysis),
            ("📈 Price Comparison", self.show_price_comparison),
            ("🔄 Data Migration", self.show_data_migration),
            ("⚙️ Settings", self.show_settings),
            ("📱 Telegram Bot", self.show_telegram_settings)
        ]
        
        self.nav_buttons = {}
        for i, (text, command) in enumerate(nav_buttons, 1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=command,
                height=40,
                font=ctk.CTkFont(size=14),
                anchor="w"
            )
            btn.grid(row=i, column=0, padx=20, pady=5, sticky="ew")
            self.nav_buttons[text] = btn
        
        # معلومات النظام
        system_frame = ctk.CTkFrame(self.sidebar)
        system_frame.grid(row=10, column=0, padx=20, pady=20, sticky="ew")
        
        system_title = ctk.CTkLabel(
            system_frame, 
            text="System Status", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        system_title.pack(pady=(10, 5))
        
        # مؤشرات الحالة
        self.status_indicators = {}
        status_items = [
            ("AI System", "ai_enabled"),
            ("Telegram Bot", "telegram_enabled"),
            ("Scraping", "scraping_active"),
            ("Analysis", "analysis_running")
        ]
        
        for name, key in status_items:
            frame = ctk.CTkFrame(system_frame, fg_color="transparent")
            frame.pack(fill="x", padx=10, pady=2)
            
            label = ctk.CTkLabel(frame, text=name, font=ctk.CTkFont(size=12))
            label.pack(side="left")
            
            indicator = ctk.CTkLabel(frame, text="●", text_color="red", font=ctk.CTkFont(size=16))
            indicator.pack(side="right")
            
            self.status_indicators[key] = indicator
    
    def create_main_area(self):
        """إنشاء المنطقة الرئيسية"""
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=10, pady=10)
        
        # تكوين الشبكة
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # إنشاء الصفحات المختلفة
        self.create_dashboard()
        self.create_ai_analysis_page()
        self.create_price_comparison_page()
        self.create_data_migration_page()
        self.create_settings_page()
        self.create_telegram_page()
        
        # عرض الـ dashboard بشكل افتراضي
        self.show_dashboard()
    
    def create_dashboard(self):
        """إنشاء لوحة التحكم الرئيسية"""
        self.dashboard_frame = ctk.CTkFrame(self.main_frame)
        
        # العنوان
        title = ctk.CTkLabel(
            self.dashboard_frame, 
            text="📊 Dashboard Overview", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # بطاقات الإحصائيات
        stats_container = ctk.CTkFrame(self.dashboard_frame)
        stats_container.pack(fill="x", padx=20, pady=10)
        
        self.stat_cards = {}
        stat_items = [
            ("Total Products", "total_products", "📦"),
            ("AI Verified", "ai_verified", "🤖"),
            ("High Quality Deals", "high_quality_deals", "⭐"),
            ("Avg AI Score", "avg_ai_score", "📈")
        ]
        
        for i, (title, key, icon) in enumerate(stat_items):
            card = self.create_stat_card(stats_container, title, "0", icon)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="ew")
            stats_container.grid_columnconfigure(i, weight=1)
            self.stat_cards[key] = card
        
        # الرسوم البيانية
        charts_frame = ctk.CTkFrame(self.dashboard_frame)
        charts_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # رسم بياني للأسعار
        self.create_price_chart(charts_frame)
        
        # جدول أفضل العروض
        self.create_top_deals_table(charts_frame)
    
    def create_stat_card(self, parent, title, value, icon):
        """إنشاء بطاقة إحصائية"""
        card = ctk.CTkFrame(parent)
        
        icon_label = ctk.CTkLabel(
            card, 
            text=icon, 
            font=ctk.CTkFont(size=30)
        )
        icon_label.pack(pady=(15, 5))
        
        value_label = ctk.CTkLabel(
            card, 
            text=value, 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        value_label.pack()
        
        title_label = ctk.CTkLabel(
            card, 
            text=title, 
            font=ctk.CTkFont(size=12)
        )
        title_label.pack(pady=(0, 15))
        
        # حفظ مرجع لتحديث القيمة
        card.value_label = value_label
        
        return card
    
    def create_price_chart(self, parent):
        """إنشاء رسم بياني للأسعار"""
        chart_frame = ctk.CTkFrame(parent)
        chart_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        chart_title = ctk.CTkLabel(
            chart_frame, 
            text="📈 Price Trends", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        chart_title.pack(pady=10)
        
        # إنشاء الرسم البياني
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        
        # بيانات تجريبية
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        prices = np.random.normal(1000, 100, 30).cumsum()
        
        ax.plot(dates, prices, color='#1f538d', linewidth=2)
        ax.set_title('Average Deal Prices Over Time', color='white')
        ax.set_xlabel('Date', color='white')
        ax.set_ylabel('Price (EGP)', color='white')
        ax.tick_params(colors='white')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_top_deals_table(self, parent):
        """إنشاء جدول أفضل العروض"""
        table_frame = ctk.CTkFrame(parent)
        table_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        table_title = ctk.CTkLabel(
            table_frame, 
            text="⭐ Top AI Verified Deals", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        table_title.pack(pady=10)
        
        # إنشاء جدول قابل للتمرير
        self.deals_scrollable = ctk.CTkScrollableFrame(table_frame)
        self.deals_scrollable.pack(fill="both", expand=True, padx=10, pady=10)
        
        # تحديث الجدول
        self.update_top_deals_table()
    
    def create_ai_analysis_page(self):
        """إنشاء صفحة تحليل AI"""
        self.ai_analysis_frame = ctk.CTkFrame(self.main_frame)
        
        title = ctk.CTkLabel(
            self.ai_analysis_frame, 
            text="🤖 AI Analysis Center", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # إعدادات AI
        settings_frame = ctk.CTkFrame(self.ai_analysis_frame)
        settings_frame.pack(fill="x", padx=20, pady=10)
        
        # API Key
        api_frame = ctk.CTkFrame(settings_frame)
        api_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(api_frame, text="Gemini API Key:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.api_key_entry = ctk.CTkEntry(api_frame, placeholder_text="Enter your Gemini API key...", show="*")
        self.api_key_entry.pack(fill="x", padx=10, pady=(0, 10))
        
        # أزرار التحكم
        controls_frame = ctk.CTkFrame(settings_frame)
        controls_frame.pack(fill="x", padx=20, pady=10)
        
        self.init_ai_btn = ctk.CTkButton(
            controls_frame, 
            text="🚀 Initialize AI System", 
            command=self.initialize_ai_system,
            height=40
        )
        self.init_ai_btn.pack(side="left", padx=10, pady=10)
        
        self.analyze_deals_btn = ctk.CTkButton(
            controls_frame, 
            text="🔍 Analyze Deals", 
            command=self.start_ai_analysis,
            height=40,
            state="disabled"
        )
        self.analyze_deals_btn.pack(side="left", padx=10, pady=10)
        
        # إعدادات التحليل
        analysis_settings_frame = ctk.CTkFrame(self.ai_analysis_frame)
        analysis_settings_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(analysis_settings_frame, text="Analysis Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        # عدد العروض
        deals_frame = ctk.CTkFrame(analysis_settings_frame, fg_color="transparent")
        deals_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(deals_frame, text="Max Deals to Analyze:").pack(side="left")
        self.max_deals_var = ctk.StringVar(value="20")
        max_deals_entry = ctk.CTkEntry(deals_frame, textvariable=self.max_deals_var, width=100)
        max_deals_entry.pack(side="right", padx=10)
        
        # الحد الأدنى للنقاط
        score_frame = ctk.CTkFrame(analysis_settings_frame, fg_color="transparent")
        score_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(score_frame, text="Minimum AI Score:").pack(side="left")
        self.min_score_var = ctk.StringVar(value="7.0")
        min_score_entry = ctk.CTkEntry(score_frame, textvariable=self.min_score_var, width=100)
        min_score_entry.pack(side="right", padx=10)
        
        # نتائج التحليل
        self.analysis_results = ctk.CTkScrollableFrame(self.ai_analysis_frame)
        self.analysis_results.pack(fill="both", expand=True, padx=20, pady=10)
    
    def create_price_comparison_page(self):
        """إنشاء صفحة مقارنة الأسعار"""
        self.price_comparison_frame = ctk.CTkFrame(self.main_frame)
        
        title = ctk.CTkLabel(
            self.price_comparison_frame, 
            text="📈 Price Comparison", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # البحث
        search_frame = ctk.CTkFrame(self.price_comparison_frame)
        search_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(search_frame, text="Search Product:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10, pady=(10, 5))
        
        search_input_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.search_entry = ctk.CTkEntry(search_input_frame, placeholder_text="Enter product name or keywords...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        search_btn = ctk.CTkButton(
            search_input_frame, 
            text="🔍 Search", 
            command=self.search_product_prices,
            width=100
        )
        search_btn.pack(side="right")
        
        # نتائج البحث
        self.search_results = ctk.CTkScrollableFrame(self.price_comparison_frame)
        self.search_results.pack(fill="both", expand=True, padx=20, pady=10)
    
    def create_data_migration_page(self):
        """إنشاء صفحة تحويل البيانات"""
        self.data_migration_frame = ctk.CTkFrame(self.main_frame)
        
        title = ctk.CTkLabel(
            self.data_migration_frame, 
            text="🔄 Data Migration", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # اختيار الملف
        file_frame = ctk.CTkFrame(self.data_migration_frame)
        file_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(file_frame, text="JSON File:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10, pady=(10, 5))
        
        file_input_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.json_file_var = ctk.StringVar(value="products.json")
        file_entry = ctk.CTkEntry(file_input_frame, textvariable=self.json_file_var)
        file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            file_input_frame, 
            text="📁 Browse", 
            command=self.browse_json_file,
            width=100
        )
        browse_btn.pack(side="right")
        
        # إعدادات التحويل
        migration_settings_frame = ctk.CTkFrame(self.data_migration_frame)
        migration_settings_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(migration_settings_frame, text="Migration Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        # حجم الدفعة
        batch_frame = ctk.CTkFrame(migration_settings_frame, fg_color="transparent")
        batch_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(batch_frame, text="Batch Size:").pack(side="left")
        self.batch_size_var = ctk.StringVar(value="1000")
        batch_entry = ctk.CTkEntry(batch_frame, textvariable=self.batch_size_var, width=100)
        batch_entry.pack(side="right", padx=10)
        
        # تحسين قاعدة البيانات
        self.optimize_db_var = ctk.BooleanVar(value=True)
        optimize_check = ctk.CTkCheckBox(
            migration_settings_frame, 
            text="Optimize Database After Migration", 
            variable=self.optimize_db_var
        )
        optimize_check.pack(anchor="w", padx=20, pady=5)
        
        # زر التحويل
        migrate_btn = ctk.CTkButton(
            self.data_migration_frame, 
            text="🚀 Start Migration", 
            command=self.start_migration,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        migrate_btn.pack(pady=20)
        
        # شريط التقدم
        self.migration_progress = ctk.CTkProgressBar(self.data_migration_frame)
        self.migration_progress.pack(fill="x", padx=20, pady=10)
        self.migration_progress.set(0)
        
        # سجل التحويل
        self.migration_log = ctk.CTkTextbox(self.data_migration_frame)
        self.migration_log.pack(fill="both", expand=True, padx=20, pady=10)
    
    def create_settings_page(self):
        """إنشاء صفحة الإعدادات"""
        self.settings_frame = ctk.CTkFrame(self.main_frame)
        
        title = ctk.CTkLabel(
            self.settings_frame, 
            text="⚙️ Settings", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # إعدادات قاعدة البيانات
        db_frame = ctk.CTkFrame(self.settings_frame)
        db_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(db_frame, text="Database Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        db_path_frame = ctk.CTkFrame(db_frame, fg_color="transparent")
        db_path_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(db_path_frame, text="Database Path:").pack(side="left")
        self.db_path_var = ctk.StringVar(value=self.db_file)
        db_entry = ctk.CTkEntry(db_path_frame, textvariable=self.db_path_var)
        db_entry.pack(side="right", fill="x", expand=True, padx=10)
        
        # إعدادات AI
        ai_settings_frame = ctk.CTkFrame(self.settings_frame)
        ai_settings_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(ai_settings_frame, text="AI Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        # تفعيل التحليل التلقائي
        self.auto_analysis_var = ctk.BooleanVar(value=False)
        auto_check = ctk.CTkCheckBox(
            ai_settings_frame, 
            text="Enable Automatic AI Analysis", 
            variable=self.auto_analysis_var
        )
        auto_check.pack(anchor="w", padx=20, pady=5)
        
        # فترة التحليل
        interval_frame = ctk.CTkFrame(ai_settings_frame, fg_color="transparent")
        interval_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(interval_frame, text="Analysis Interval (minutes):").pack(side="left")
        self.analysis_interval_var = ctk.StringVar(value="30")
        interval_entry = ctk.CTkEntry(interval_frame, textvariable=self.analysis_interval_var, width=100)
        interval_entry.pack(side="right", padx=10)
        
        # أزرار الإجراءات
        actions_frame = ctk.CTkFrame(self.settings_frame)
        actions_frame.pack(fill="x", padx=20, pady=20)
        
        save_btn = ctk.CTkButton(
            actions_frame, 
            text="💾 Save Settings", 
            command=self.save_settings,
            height=40
        )
        save_btn.pack(side="left", padx=10, pady=10)
        
        reset_btn = ctk.CTkButton(
            actions_frame, 
            text="🔄 Reset to Default", 
            command=self.reset_settings,
            height=40
        )
        reset_btn.pack(side="left", padx=10, pady=10)
    
    def create_telegram_page(self):
        """إنشاء صفحة إعدادات Telegram"""
        self.telegram_frame = ctk.CTkFrame(self.main_frame)
        
        title = ctk.CTkLabel(
            self.telegram_frame, 
            text="📱 Telegram Bot Settings", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # إعدادات البوت
        bot_settings_frame = ctk.CTkFrame(self.telegram_frame)
        bot_settings_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(bot_settings_frame, text="Bot Configuration", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        # Bot Token
        token_frame = ctk.CTkFrame(bot_settings_frame, fg_color="transparent")
        token_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(token_frame, text="Bot Token:").pack(anchor="w")
        self.bot_token_entry = ctk.CTkEntry(token_frame, placeholder_text="Enter Telegram bot token...", show="*")
        self.bot_token_entry.pack(fill="x", pady=5)
        
        # User IDs
        users_frame = ctk.CTkFrame(bot_settings_frame, fg_color="transparent")
        users_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(users_frame, text="User IDs (comma separated):").pack(anchor="w")
        self.user_ids_entry = ctk.CTkEntry(users_frame, placeholder_text="123456789, 987654321")
        self.user_ids_entry.pack(fill="x", pady=5)
        
        # أزرار التحكم
        bot_controls_frame = ctk.CTkFrame(self.telegram_frame)
        bot_controls_frame.pack(fill="x", padx=20, pady=10)
        
        self.init_bot_btn = ctk.CTkButton(
            bot_controls_frame, 
            text="🚀 Initialize Bot", 
            command=self.initialize_telegram_bot,
            height=40
        )
        self.init_bot_btn.pack(side="left", padx=10, pady=10)
        
        self.test_bot_btn = ctk.CTkButton(
            bot_controls_frame, 
            text="🧪 Test Bot", 
            command=self.test_telegram_bot,
            height=40,
            state="disabled"
        )
        self.test_bot_btn.pack(side="left", padx=10, pady=10)
        
        self.send_report_btn = ctk.CTkButton(
            bot_controls_frame, 
            text="📊 Send Report", 
            command=self.send_telegram_report,
            height=40,
            state="disabled"
        )
        self.send_report_btn.pack(side="left", padx=10, pady=10)
        
        # إعدادات التقارير
        report_settings_frame = ctk.CTkFrame(self.telegram_frame)
        report_settings_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(report_settings_frame, text="Report Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        
        # تفعيل التقارير التلقائية
        self.auto_reports_var = ctk.BooleanVar(value=False)
        auto_reports_check = ctk.CTkCheckBox(
            report_settings_frame, 
            text="Enable Automatic Daily Reports", 
            variable=self.auto_reports_var
        )
        auto_reports_check.pack(anchor="w", padx=20, pady=5)
        
        # وقت الإرسال
        time_frame = ctk.CTkFrame(report_settings_frame, fg_color="transparent")
        time_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(time_frame, text="Report Time (24h format):").pack(side="left")
        self.report_time_var = ctk.StringVar(value="09:00")
        time_entry = ctk.CTkEntry(time_frame, textvariable=self.report_time_var, width=100)
        time_entry.pack(side="right", padx=10)
        
        # سجل البوت
        self.bot_log = ctk.CTkTextbox(self.telegram_frame)
        self.bot_log.pack(fill="both", expand=True, padx=20, pady=10)
    
    def create_status_bar(self):
        """إنشاء شريط الحالة"""
        self.status_bar = ctk.CTkFrame(self.root, height=30, corner_radius=0)
        self.status_bar.grid(row=3, column=0, columnspan=2, sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            self.status_bar, 
            text="Ready", 
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        self.time_label = ctk.CTkLabel(
            self.status_bar, 
            text="", 
            font=ctk.CTkFont(size=12)
        )
        self.time_label.pack(side="right", padx=10, pady=5)
    
    # دوال التنقل
    def show_dashboard(self):
        self.hide_all_frames()
        self.dashboard_frame.pack(fill="both", expand=True)
        self.update_status("Dashboard loaded")
    
    def show_ai_analysis(self):
        self.hide_all_frames()
        self.ai_analysis_frame.pack(fill="both", expand=True)
        self.update_status("AI Analysis page loaded")
    
    def show_price_comparison(self):
        self.hide_all_frames()
        self.price_comparison_frame.pack(fill="both", expand=True)
        self.update_status("Price Comparison page loaded")
    
    def show_data_migration(self):
        self.hide_all_frames()
        self.data_migration_frame.pack(fill="both", expand=True)
        self.update_status("Data Migration page loaded")
    
    def show_settings(self):
        self.hide_all_frames()
        self.settings_frame.pack(fill="both", expand=True)
        self.update_status("Settings page loaded")
    
    def show_telegram_settings(self):
        self.hide_all_frames()
        self.telegram_frame.pack(fill="both", expand=True)
        self.update_status("Telegram settings loaded")
    
    def hide_all_frames(self):
        """إخفاء جميع الإطارات"""
        frames = [
            self.dashboard_frame,
            self.ai_analysis_frame,
            self.price_comparison_frame,
            self.data_migration_frame,
            self.settings_frame,
            self.telegram_frame
        ]
        for frame in frames:
            frame.pack_forget()
    
    # دوال الوظائف
    def initialize_ai_system(self):
        """تهيئة نظام AI"""
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter Gemini API key")
            return
        
        try:
            self.update_status("Initializing AI system...")
            self.ai_analyzer = AIAnalyzer(api_key)
            self.deal_filter = DealQualityFilter(self.ai_analyzer, self.db_file)
            
            self.system_status['ai_enabled'] = True
            self.update_status_indicators()
            self.analyze_deals_btn.configure(state="normal")
            
            messagebox.showinfo("Success", "AI system initialized successfully!")
            self.update_status("AI system ready")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize AI system: {e}")
            self.update_status("AI initialization failed")
    
    def start_ai_analysis(self):
        """بدء تحليل AI"""
        if not self.ai_analyzer:
            messagebox.showerror("Error", "Please initialize AI system first")
            return
        
        def run_analysis():
            try:
                self.system_status['analysis_running'] = True
                self.update_status_indicators()
                self.update_status("Running AI analysis...")
                
                max_deals = int(self.max_deals_var.get())
                min_score = float(self.min_score_var.get())
                
                deals = self.deal_filter.filter_high_quality_deals(min_score, max_deals)
                
                # عرض النتائج
                self.root.after(0, lambda: self.display_analysis_results(deals))
                
                self.system_status['analysis_running'] = False
                self.update_status_indicators()
                self.update_status(f"Analysis completed - Found {len(deals)} high quality deals")
                
            except Exception as e:
                self.system_status['analysis_running'] = False
                self.update_status_indicators()
                messagebox.showerror("Error", f"Analysis failed: {e}")
        
        threading.Thread(target=run_analysis, daemon=True).start()
    
    def display_analysis_results(self, deals):
        """عرض نتائج التحليل"""
        # مسح النتائج السابقة
        for widget in self.analysis_results.winfo_children():
            widget.destroy()
        
        if not deals:
            no_results_label = ctk.CTkLabel(
                self.analysis_results, 
                text="No high quality deals found", 
                font=ctk.CTkFont(size=16)
            )
            no_results_label.pack(pady=20)
            return
        
        for i, deal in enumerate(deals):
            deal_frame = ctk.CTkFrame(self.analysis_results)
            deal_frame.pack(fill="x", padx=10, pady=5)
            
            # اسم المنتج
            name_label = ctk.CTkLabel(
                deal_frame, 
                text=deal['name'][:80] + "..." if len(deal['name']) > 80 else deal['name'],
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            name_label.pack(fill="x", padx=10, pady=(10, 5))
            
            # معلومات العرض
            info_frame = ctk.CTkFrame(deal_frame, fg_color="transparent")
            info_frame.pack(fill="x", padx=10, pady=5)
            
            price_label = ctk.CTkLabel(
                info_frame, 
                text=f"💰 {int(deal['current_price']):,} EGP",
                font=ctk.CTkFont(size=12)
            )
            price_label.pack(side="left")
            
            discount_label = ctk.CTkLabel(
                info_frame, 
                text=f"⚡ {deal['discount_percent']:.1f}% OFF",
                font=ctk.CTkFont(size=12)
            )
            discount_label.pack(side="left", padx=10)
            
            score_label = ctk.CTkLabel(
                info_frame, 
                text=f"🤖 AI Score: {deal.get('total_ai_score', 0):.1f}/10",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="green"
            )
            score_label.pack(side="right")
            
            # أزرار الإجراءات
            actions_frame = ctk.CTkFrame(deal_frame, fg_color="transparent")
            actions_frame.pack(fill="x", padx=10, pady=(5, 10))
            
            view_btn = ctk.CTkButton(
                actions_frame, 
                text="👁️ View", 
                command=lambda url=deal.get('url', ''): webbrowser.open(url) if url else None,
                width=80,
                height=30
            )
            view_btn.pack(side="left", padx=5)
            
            telegram_btn = ctk.CTkButton(
                actions_frame, 
                text="📱 Send to Telegram", 
                command=lambda d=deal: self.send_deal_to_telegram(d),
                width=120,
                height=30
            )
            telegram_btn.pack(side="left", padx=5)
    
    def search_product_prices(self):
        """البحث عن أسعار المنتج"""
        search_query = self.search_entry.get().strip()
        if not search_query:
            messagebox.showerror("Error", "Please enter a product name")
            return
        
        def run_search():
            try:
                self.update_status(f"Searching for: {search_query}")
                
                if not self.scraper:
                    self.scraper = EgyptianSitesScraper(self.db_file)
                
                results = self.scraper.get_best_prices(search_query)
                
                # عرض النتائج
                self.root.after(0, lambda: self.display_search_results(results))
                
                self.update_status("Search completed")
                
            except Exception as e:
                messagebox.showerror("Error", f"Search failed: {e}")
                self.update_status("Search failed")
        
        threading.Thread(target=run_search, daemon=True).start()
    
    def display_search_results(self, results):
        """عرض نتائج البحث"""
        # مسح النتائج السابقة
        for widget in self.search_results.winfo_children():
            widget.destroy()
        
        if results.get('total_results', 0) == 0:
            no_results_label = ctk.CTkLabel(
                self.search_results, 
                text="No results found", 
                font=ctk.CTkFont(size=16)
            )
            no_results_label.pack(pady=20)
            return
        
        # ملخص النتائج
        summary_frame = ctk.CTkFrame(self.search_results)
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        summary_label = ctk.CTkLabel(
            summary_frame, 
            text=f"📊 Found {results['total_results']} products across multiple sites",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        summary_label.pack(pady=10)
        
        if results.get('best_price'):
            best = results['best_price']
            best_label = ctk.CTkLabel(
                summary_frame, 
                text=f"🏆 Best Price: {int(best['current_price']):,} EGP from {best['site'].title()}",
                font=ctk.CTkFont(size=14),
                text_color="green"
            )
            best_label.pack(pady=5)
        
        # النتائج حسب الموقع
        for site_name, products in results.get('results_by_site', {}).items():
            if not products:
                continue
            
            site_frame = ctk.CTkFrame(self.search_results)
            site_frame.pack(fill="x", padx=10, pady=5)
            
            site_title = ctk.CTkLabel(
                site_frame, 
                text=f"🌐 {site_name.title()} ({len(products)} products)",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            site_title.pack(anchor="w", padx=10, pady=(10, 5))
            
            for product in products[:3]:  # أول 3 منتجات
                product_frame = ctk.CTkFrame(site_frame)
                product_frame.pack(fill="x", padx=10, pady=2)
                
                product_info = ctk.CTkLabel(
                    product_frame,
                    text=f"{product['name'][:60]}... - {int(product['current_price']):,} EGP",
                    anchor="w"
                )
                product_info.pack(side="left", fill="x", expand=True, padx=10, pady=5)
                
                if product.get('url'):
                    view_btn = ctk.CTkButton(
                        product_frame,
                        text="View",
                        command=lambda url=product['url']: webbrowser.open(url),
                        width=60,
                        height=25
                    )
                    view_btn.pack(side="right", padx=10, pady=5)
    
    def browse_json_file(self):
        """اختيار ملف JSON"""
        file_path = filedialog.askopenfilename(
            title="Select JSON file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.json_file_var.set(file_path)
    
    def start_migration(self):
        """بدء تحويل البيانات"""
        json_file = self.json_file_var.get().strip()
        if not json_file:
            messagebox.showerror("Error", "Please select a JSON file")
            return
        
        def run_migration():
            try:
                self.update_status("Starting data migration...")
                self.migration_progress.set(0.1)
                
                batch_size = int(self.batch_size_var.get())
                optimize = self.optimize_db_var.get()
                
                self.migrator = JSONToSQLiteMigrator(json_file, self.db_file)
                
                # تحديث السجل
                self.root.after(0, lambda: self.migration_log.insert("end", f"Starting migration from {json_file}\\n"))
                
                self.migration_progress.set(0.3)
                
                stats = self.migrator.migrate(batch_size=batch_size, optimize=optimize)
                
                self.migration_progress.set(1.0)
                
                # عرض النتائج
                self.root.after(0, lambda: self.display_migration_results(stats))
                
                self.update_status("Migration completed successfully")
                
            except Exception as e:
                self.migration_progress.set(0)
                error_msg = f"Migration failed: {e}"
                self.root.after(0, lambda: self.migration_log.insert("end", f"ERROR: {error_msg}\\n"))
                messagebox.showerror("Error", error_msg)
                self.update_status("Migration failed")
        
        threading.Thread(target=run_migration, daemon=True).start()
    
    def display_migration_results(self, stats):
        """عرض نتائج التحويل"""
        results_text = f"""
Migration completed successfully!

📊 Statistics:
• Total Products: {stats.get('total_products', 0):,}
• Products with Discount: {stats.get('products_with_discount', 0):,}
• Average Discount: {stats.get('average_discount', 0)}%
• Max Discount: {stats.get('max_discount', 0)}%
• Price History Records: {stats.get('price_history_records', 0):,}

📂 Top Sections:
"""
        
        for section, count in stats.get('sections', [])[:5]:
            results_text += f"• {section}: {count:,} products\\n"
        
        self.migration_log.insert("end", results_text)
        
        # تحديث الإحصائيات
        self.stats['total_products'] = stats.get('total_products', 0)
        self.update_stats_display()
    
    def initialize_telegram_bot(self):
        """تهيئة بوت Telegram"""
        bot_token = self.bot_token_entry.get().strip()
        user_ids_text = self.user_ids_entry.get().strip()
        
        if not bot_token or not user_ids_text:
            messagebox.showerror("Error", "Please enter bot token and user IDs")
            return
        
        try:
            # حفظ الإعدادات
            config = {
                "bot_token": bot_token,
                "users": [uid.strip() for uid in user_ids_text.split(',')]
            }
            
            with open('telegram_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            # تهيئة البوت
            self.telegram_bot = EnhancedTelegramBot()
            
            if self.ai_analyzer:
                self.telegram_bot.init_ai_system(self.api_key_entry.get().strip())
            
            self.system_status['telegram_enabled'] = True
            self.update_status_indicators()
            
            self.test_bot_btn.configure(state="normal")
            self.send_report_btn.configure(state="normal")
            
            messagebox.showinfo("Success", "Telegram bot initialized successfully!")
            self.bot_log.insert("end", f"Bot initialized at {datetime.now()}\\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize bot: {e}")
            self.bot_log.insert("end", f"ERROR: {e}\\n")
    
    def test_telegram_bot(self):
        """اختبار بوت Telegram"""
        if not self.telegram_bot:
            messagebox.showerror("Error", "Please initialize bot first")
            return
        
        test_message = "🧪 Test message from AI Deal Analyzer\\n\\n" + \
                      f"System is working properly!\\n" + \
                      f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        success = False
        for user_id in self.telegram_bot.users:
            if self.telegram_bot.send_message(user_id, test_message):
                success = True
        
        if success:
            messagebox.showinfo("Success", "Test message sent successfully!")
            self.bot_log.insert("end", f"Test message sent at {datetime.now()}\\n")
        else:
            messagebox.showerror("Error", "Failed to send test message")
            self.bot_log.insert("end", f"Test message failed at {datetime.now()}\\n")
    
    def send_telegram_report(self):
        """إرسال تقرير Telegram"""
        if not self.telegram_bot:
            messagebox.showerror("Error", "Please initialize bot first")
            return
        
        def send_report():
            try:
                success = self.telegram_bot.send_daily_summary_report()
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Report sent successfully!"))
                    self.root.after(0, lambda: self.bot_log.insert("end", f"Report sent at {datetime.now()}\\n"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to send report"))
                    self.root.after(0, lambda: self.bot_log.insert("end", f"Report sending failed at {datetime.now()}\\n"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Report error: {e}"))
        
        threading.Thread(target=send_report, daemon=True).start()
    
    def send_deal_to_telegram(self, deal):
        """إرسال عرض إلى Telegram"""
        if not self.telegram_bot:
            messagebox.showerror("Error", "Please initialize Telegram bot first")
            return
        
        def send_deal():
            try:
                success = self.telegram_bot.send_ai_verified_deal(deal)
                if success:
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Deal sent to Telegram!"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Failed to send deal"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Send error: {e}"))
        
        threading.Thread(target=send_deal, daemon=True).start()
    
    def save_settings(self):
        """حفظ الإعدادات"""
        settings = {
            'db_path': self.db_path_var.get(),
            'auto_analysis': self.auto_analysis_var.get(),
            'analysis_interval': self.analysis_interval_var.get(),
            'auto_reports': self.auto_reports_var.get(),
            'report_time': self.report_time_var.get()
        }
        
        try:
            with open('app_settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def reset_settings(self):
        """إعادة تعيين الإعدادات"""
        self.db_path_var.set("amz_products.db")
        self.auto_analysis_var.set(False)
        self.analysis_interval_var.set("30")
        self.auto_reports_var.set(False)
        self.report_time_var.set("09:00")
        
        messagebox.showinfo("Success", "Settings reset to default")
    
    # دوال المساعدة
    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        try:
            # تحميل الإحصائيات من قاعدة البيانات
            self.update_stats_from_db()
            
            # تحميل إعدادات التطبيق
            try:
                with open('app_settings.json', 'r') as f:
                    settings = json.load(f)
                    self.db_path_var.set(settings.get('db_path', 'amz_products.db'))
                    self.auto_analysis_var.set(settings.get('auto_analysis', False))
                    self.analysis_interval_var.set(settings.get('analysis_interval', '30'))
                    self.auto_reports_var.set(settings.get('auto_reports', False))
                    self.report_time_var.set(settings.get('report_time', '09:00'))
            except FileNotFoundError:
                pass
            
            # تحميل إعدادات Telegram
            try:
                with open('telegram_config.json', 'r') as f:
                    config = json.load(f)
                    self.bot_token_entry.insert(0, config.get('bot_token', ''))
                    self.user_ids_entry.insert(0, ', '.join(config.get('users', [])))
            except FileNotFoundError:
                pass
                
        except Exception as e:
            logger.error(f"Error loading initial data: {e}")
    
    def update_stats_from_db(self):
        """تحديث الإحصائيات من قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # إجمالي المنتجات
            cursor.execute("SELECT COUNT(*) FROM products")
            self.stats['total_products'] = cursor.fetchone()[0] or 0
            
            # المنتجات المحللة بـ AI
            cursor.execute("SELECT COUNT(*) FROM products WHERE ai_verified = TRUE")
            self.stats['ai_verified'] = cursor.fetchone()[0] or 0
            
            # العروض عالية الجودة
            cursor.execute("SELECT COUNT(*) FROM products WHERE ai_score >= 7")
            self.stats['high_quality_deals'] = cursor.fetchone()[0] or 0
            
            # متوسط نقاط AI
            cursor.execute("SELECT AVG(ai_score) FROM products WHERE ai_score > 0")
            result = cursor.fetchone()[0]
            self.stats['avg_ai_score'] = round(result, 1) if result else 0
            
            conn.close()
            
            # تحديث العرض
            self.update_stats_display()
            
        except Exception as e:
            logger.error(f"Error updating stats from DB: {e}")
    
    def update_stats_display(self):
        """تحديث عرض الإحصائيات"""
        try:
            self.stat_cards['total_products'].value_label.configure(text=f"{self.stats['total_products']:,}")
            self.stat_cards['ai_verified'].value_label.configure(text=f"{self.stats['ai_verified']:,}")
            self.stat_cards['high_quality_deals'].value_label.configure(text=f"{self.stats['high_quality_deals']:,}")
            self.stat_cards['avg_ai_score'].value_label.configure(text=f"{self.stats['avg_ai_score']}")
        except Exception as e:
            logger.error(f"Error updating stats display: {e}")
    
    def update_top_deals_table(self):
        """تحديث جدول أفضل العروض"""
        try:
            # مسح الجدول الحالي
            for widget in self.deals_scrollable.winfo_children():
                widget.destroy()
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name, current_price, discount_percent, ai_score, url
                FROM products 
                WHERE ai_score >= 7
                ORDER BY ai_score DESC, discount_percent DESC 
                LIMIT 10
            """)
            
            deals = cursor.fetchall()
            conn.close()
            
            if not deals:
                no_deals_label = ctk.CTkLabel(
                    self.deals_scrollable, 
                    text="No high quality deals available", 
                    font=ctk.CTkFont(size=14)
                )
                no_deals_label.pack(pady=20)
                return
            
            for i, (name, price, discount, score, url) in enumerate(deals, 1):
                deal_frame = ctk.CTkFrame(self.deals_scrollable)
                deal_frame.pack(fill="x", padx=5, pady=3)
                
                rank_label = ctk.CTkLabel(
                    deal_frame, 
                    text=f"#{i}", 
                    font=ctk.CTkFont(size=12, weight="bold"),
                    width=30
                )
                rank_label.pack(side="left", padx=5, pady=5)
                
                info_frame = ctk.CTkFrame(deal_frame, fg_color="transparent")
                info_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)
                
                name_label = ctk.CTkLabel(
                    info_frame, 
                    text=name[:40] + "..." if len(name) > 40 else name,
                    anchor="w",
                    font=ctk.CTkFont(size=11)
                )
                name_label.pack(anchor="w")
                
                details_label = ctk.CTkLabel(
                    info_frame, 
                    text=f"{int(price):,} EGP • {discount:.1f}% OFF • AI: {score:.1f}",
                    anchor="w",
                    font=ctk.CTkFont(size=10),
                    text_color="gray"
                )
                details_label.pack(anchor="w")
                
                if url:
                    view_btn = ctk.CTkButton(
                        deal_frame, 
                        text="View", 
                        command=lambda u=url: webbrowser.open(u),
                        width=60,
                        height=25,
                        font=ctk.CTkFont(size=10)
                    )
                    view_btn.pack(side="right", padx=5, pady=5)
                    
        except Exception as e:
            logger.error(f"Error updating top deals table: {e}")
    
    def update_status_indicators(self):
        """تحديث مؤشرات الحالة"""
        for key, indicator in self.status_indicators.items():
            if self.system_status.get(key, False):
                indicator.configure(text_color="green")
            else:
                indicator.configure(text_color="red")
    
    def update_status(self, message):
        """تحديث شريط الحالة"""
        self.status_label.configure(text=message)
        logger.info(message)
    
    def start_stats_update(self):
        """بدء تحديث الإحصائيات الدوري"""
        def update_loop():
            while True:
                try:
                    # تحديث الوقت
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.root.after(0, lambda: self.time_label.configure(text=current_time))
                    
                    # تحديث الإحصائيات كل 5 دقائق
                    if datetime.now().minute % 5 == 0:
                        self.root.after(0, self.update_stats_from_db)
                        self.root.after(0, self.update_top_deals_table)
                    
                    time.sleep(60)  # تحديث كل دقيقة
                    
                except Exception as e:
                    logger.error(f"Stats update error: {e}")
                    time.sleep(60)
        
        threading.Thread(target=update_loop, daemon=True).start()
    
    def run(self):
        """تشغيل التطبيق"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Application stopped by user")
        finally:
            # تنظيف الموارد
            if self.scraper:
                self.scraper.cleanup()

if __name__ == "__main__":
    app = AIEnhancedGUI()
    app.run()