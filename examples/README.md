# Examples - أمثلة الاستخدام

مجموعة من الأمثلة العملية لاستخدام AI Deals Manager.

## 📁 محتويات المجلد

### 🚀 أمثلة أساسية
- `basic_usage.py` - الاستخدام الأساسي
- `telegram_bot_example.py` - مثال بوت تليجرام
- `database_example.py` - مثال قاعدة البيانات
- `ai_analysis_example.py` - مثال تحليل AI

### 🔧 أمثلة متقدمة
- `custom_analyzer.py` - محلل مخصص
- `batch_processing.py` - معالجة دفعية
- `scheduled_tasks.py` - مهام مجدولة
- `web_interface.py` - واجهة ويب بسيطة

### 📊 أمثلة تحليل البيانات
- `data_export.py` - تصدير البيانات
- `statistics.py` - إحصائيات متقدمة
- `price_trends.py` - تحليل اتجاهات الأسعار
- `market_analysis.py` - تحليل السوق

## 🎯 كيفية الاستخدام

### تشغيل الأمثلة
```bash
# مثال أساسي
python examples/basic_usage.py

# مثال بوت تليجرام
python examples/telegram_bot_example.py

# مثال قاعدة البيانات
python examples/database_example.py
```

### تخصيص الأمثلة
1. انسخ الملف المطلوب
2. عدّل الإعدادات حسب احتياجاتك
3. شغل المثال

## 📋 قائمة الأمثلة

### 1. الاستخدام الأساسي
```python
# examples/basic_usage.py
from ai_deals_manager import AIDealsManager

# إنشاء مدير العروض
manager = AIDealsManager()

# تشغيل تحليل واحد
deals = manager.run_single_analysis(limit=10)

# عرض النتائج
for deal in deals:
    print(f"{deal['name']} - {deal['price']} EGP")
```

### 2. بوت تليجرام مخصص
```python
# examples/telegram_bot_example.py
from enhanced_telegram_bot import EnhancedTelegramBot

# إنشاء بوت مخصص
bot = EnhancedTelegramBot()

# تخصيص الإعدادات
bot.update_settings(
    daily_limit=20,
    min_ai_confidence=0.8,
    verified_only=True
)

# إرسال رسالة مخصصة
bot.send_custom_message("مرحباً! النظام يعمل بشكل ممتاز!")
```

### 3. قاعدة البيانات المتقدمة
```python
# examples/database_example.py
from enhanced_database import EnhancedDatabaseManager

# إنشاء مدير قاعدة البيانات
db = EnhancedDatabaseManager()

# عمليات متقدمة
stats = db.get_database_stats()
print(f"إجمالي المنتجات: {stats['total_products']}")

# تصدير البيانات
db.export_to_json("my_export.json")
```

### 4. تحليل AI مخصص
```python
# examples/ai_analysis_example.py
from ai_price_analyzer import AIPriceAnalyzer

# إنشاء محلل مخصص
analyzer = AIPriceAnalyzer()

# تحليل منتج معين
product_data = {
    "name": "منتج تجريبي",
    "price": 1000,
    "discount_percent": 25
}

analysis = analyzer.analyze_deal(product_data)
print(f"تحليل AI: {analysis.analysis_summary}")
```

## 🔧 أمثلة متقدمة

### محلل مخصص
```python
# examples/custom_analyzer.py
class CustomAnalyzer(AIPriceAnalyzer):
    def __init__(self):
        super().__init__()
        self.custom_sites = {
            'my_site': {
                'base_url': 'https://mysite.com',
                'search_url': 'https://mysite.com/search?q={query}',
                'enabled': True
            }
        }
    
    def analyze_custom_deal(self, product):
        # تحليل مخصص
        return self.analyze_deal(product)
```

### معالجة دفعية
```python
# examples/batch_processing.py
import asyncio
from ai_deals_manager import AIDealsManager

async def process_batch():
    manager = AIDealsManager()
    
    # معالجة دفعات كبيرة
    for i in range(0, 1000, 100):
        deals = manager.get_deals_batch(offset=i, limit=100)
        await process_deals(deals)

async def process_deals(deals):
    # معالجة العروض
    for deal in deals:
        # تحليل AI
        analysis = manager.analyze_product_with_ai(deal)
        
        # إرسال إذا كان جيد
        if analysis and analysis['is_good_deal']:
            manager.telegram_bot.send_ai_enhanced_alert(deal, analysis)
```

### مهام مجدولة
```python
# examples/scheduled_tasks.py
import schedule
import time
from ai_deals_manager import AIDealsManager

def daily_analysis():
    manager = AIDealsManager()
    manager.run_single_analysis(limit=50)

def weekly_report():
    manager = AIDealsManager()
    manager.send_daily_summary()

# جدولة المهام
schedule.every().day.at("09:00").do(daily_analysis)
schedule.every().day.at("20:00").do(weekly_report)

# تشغيل المجدول
while True:
    schedule.run_pending()
    time.sleep(60)
```

## 📊 أمثلة تحليل البيانات

### تصدير البيانات
```python
# examples/data_export.py
from enhanced_database import EnhancedDatabaseManager
import json
import csv

def export_to_csv():
    db = EnhancedDatabaseManager()
    
    # جلب البيانات
    deals = db.get_deals(min_discount=20, limit=1000)
    
    # تصدير إلى CSV
    with open('deals.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Price', 'Discount', 'AI Score'])
        
        for deal in deals:
            writer.writerow([
                deal.name,
                deal.current_price,
                deal.discount_percent,
                deal.ai_score or 0
            ])

def export_to_json():
    db = EnhancedDatabaseManager()
    db.export_to_json("deals_export.json")
```

### إحصائيات متقدمة
```python
# examples/statistics.py
from enhanced_database import EnhancedDatabaseManager
import matplotlib.pyplot as plt

def generate_statistics():
    db = EnhancedDatabaseManager()
    
    # إحصائيات عامة
    stats = db.get_database_stats()
    
    # تحليل الخصومات
    deals = db.get_deals(min_discount=0, limit=1000)
    discounts = [deal.discount_percent for deal in deals]
    
    # رسم بياني
    plt.hist(discounts, bins=20)
    plt.title('توزيع الخصومات')
    plt.xlabel('نسبة الخصم')
    plt.ylabel('عدد المنتجات')
    plt.savefig('discounts_distribution.png')
```

### تحليل اتجاهات الأسعار
```python
# examples/price_trends.py
from enhanced_database import EnhancedDatabaseManager
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def analyze_price_trends():
    db = EnhancedDatabaseManager()
    
    # جلب تاريخ الأسعار
    asin = "B0C7CQT9ZS"  # مثال
    history = db.get_price_history(asin, days=30)
    
    # تحليل الاتجاه
    dates = [datetime.strptime(h.date, '%Y-%m-%d') for h in history]
    prices = [h.price for h in history]
    
    # رسم الاتجاه
    plt.plot(dates, prices)
    plt.title('اتجاه السعر')
    plt.xlabel('التاريخ')
    plt.ylabel('السعر')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('price_trend.png')
```

## 🌐 أمثلة الواجهات

### واجهة ويب بسيطة
```python
# examples/web_interface.py
from flask import Flask, render_template, jsonify
from ai_deals_manager import AIDealsManager

app = Flask(__name__)
manager = AIDealsManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/deals')
def get_deals():
    deals = manager.get_top_ai_deals(limit=20)
    return jsonify(deals)

@app.route('/api/stats')
def get_stats():
    stats = manager.get_stats()
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True)
```

## 🎯 نصائح للاستخدام

### 1. اختر المثال المناسب
- **مبتدئ**: `basic_usage.py`
- **متوسط**: `telegram_bot_example.py`
- **متقدم**: `custom_analyzer.py`

### 2. عدّل الإعدادات
- غيّر `daily_limit` حسب احتياجاتك
- عدّل `min_ai_confidence` للدقة
- أضف مواقع جديدة للمقارنة

### 3. راقب الأداء
- استخدم `manager.print_stats()`
- راقب ملفات السجل
- تحقق من استخدام الذاكرة

### 4. اختبر قبل النشر
- شغل الأمثلة في بيئة اختبار
- تحقق من صحة الإعدادات
- اختبر البوت قبل الإنتاج

## 📞 المساعدة

إذا واجهت مشاكل مع الأمثلة:
1. راجع [FAQ.md](../FAQ.md)
2. اطرح سؤال في [GitHub Discussions](https://github.com/your-repo/ai-deals-manager/discussions)
3. أرسل email إلى support@aideals.com

---

**🎯 هدف الأمثلة**: مساعدتك في فهم واستخدام النظام بفعالية!

**💡 نصيحة**: ابدأ بالأمثلة البسيطة ثم انتقل للمتقدمة تدريجياً.