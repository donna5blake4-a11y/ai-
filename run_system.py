#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_system.py
ملف تشغيل سريع للنظام المتكامل
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

def check_requirements():
    """فحص المكتبات المطلوبة"""
    required_packages = [
        'aiohttp',
        'beautifulsoup4', 
        'requests',
        'google-generativeai'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_packages(packages):
    """تثبيت المكتبات المفقودة"""
    try:
        for package in packages:
            print(f"📦 تثبيت {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def run_system():
    """تشغيل النظام"""
    try:
        print("🚀 تشغيل النظام المتكامل...")
        subprocess.run([sys.executable, "complete_ai_system.py"])
    except FileNotFoundError:
        print("❌ ملف complete_ai_system.py غير موجود")
        return False
    except Exception as e:
        print(f"❌ خطأ في التشغيل: {e}")
        return False

def show_gui():
    """عرض واجهة تشغيل"""
    root = tk.Tk()
    root.title("LAQTA AI - تشغيل النظام")
    root.geometry("400x300")
    root.configure(bg='#1a1f2e')
    
    # العنوان
    title_label = tk.Label(
        root,
        text="LAQTA AI - النظام المتكامل",
        font=("Arial Black", 16, "bold"),
        fg="#54fac8",
        bg='#1a1f2e'
    )
    title_label.pack(pady=20)
    
    # فحص المكتبات
    missing = check_requirements()
    
    if missing:
        status_text = f"❌ المكتبات المفقودة: {', '.join(missing)}"
        status_color = "#ff6b6b"
    else:
        status_text = "✅ جميع المكتبات متوفرة"
        status_color = "#59ff9d"
    
    status_label = tk.Label(
        root,
        text=status_text,
        font=("Arial", 12),
        fg=status_color,
        bg='#1a1f2e'
    )
    status_label.pack(pady=10)
    
    def install_and_run():
        """تثبيت المكتبات وتشغيل النظام"""
        if missing:
            if install_packages(missing):
                messagebox.showinfo("نجح", "تم تثبيت المكتبات بنجاح")
                root.destroy()
                run_system()
            else:
                messagebox.showerror("خطأ", "فشل في تثبيت المكتبات")
        else:
            root.destroy()
            run_system()
    
    def run_direct():
        """تشغيل مباشر"""
        root.destroy()
        run_system()
    
    # أزرار التحكم
    buttons_frame = tk.Frame(root, bg='#1a1f2e')
    buttons_frame.pack(pady=20)
    
    if missing:
        install_btn = tk.Button(
            buttons_frame,
            text="📦 تثبيت المكتبات وتشغيل",
            command=install_and_run,
            font=("Arial", 12, "bold"),
            bg="#54fac8",
            fg="#1a1f2e",
            relief='flat',
            padx=20,
            pady=10
        )
        install_btn.pack(pady=5)
    else:
        run_btn = tk.Button(
            buttons_frame,
            text="🚀 تشغيل النظام",
            command=run_direct,
            font=("Arial", 12, "bold"),
            bg="#59ff9d",
            fg="#1a1f2e",
            relief='flat',
            padx=20,
            pady=10
        )
        run_btn.pack(pady=5)
    
    # معلومات إضافية
    info_text = """
📋 متطلبات النظام:
• Python 3.7+
• اتصال بالإنترنت
• ملف amz_products.json (اختياري)

🎯 المميزات:
• بحث حقيقي في المواقع المصرية
• تحليل AI مع Gemini
• فلترة العروض الحقيقية
• إرسال للتليجرام
"""
    
    info_label = tk.Label(
        root,
        text=info_text,
        font=("Arial", 10),
        fg="white",
        bg='#1a1f2e',
        justify='left'
    )
    info_label.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    print("🚀 LAQTA AI - تشغيل النظام المتكامل")
    print("=" * 50)
    
    # فحص الملفات
    required_files = [
        "complete_ai_system.py",
        "requirements_complete.txt"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ الملفات المفقودة: {', '.join(missing_files)}")
        print("يرجى التأكد من وجود جميع الملفات في نفس المجلد")
        input("اضغط Enter للخروج...")
        sys.exit(1)
    
    # فحص المكتبات
    missing_packages = check_requirements()
    
    if missing_packages:
        print(f"❌ المكتبات المفقودة: {', '.join(missing_packages)}")
        print("جاري تثبيت المكتبات...")
        
        if install_packages(missing_packages):
            print("✅ تم تثبيت المكتبات بنجاح")
        else:
            print("❌ فشل في تثبيت المكتبات")
            print("يرجى تثبيت المكتبات يدوياً:")
            print("pip install -r requirements_complete.txt")
            input("اضغط Enter للخروج...")
            sys.exit(1)
    
    print("✅ جميع المتطلبات متوفرة")
    print("🚀 تشغيل النظام...")
    
    # تشغيل النظام
    run_system()