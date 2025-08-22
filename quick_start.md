# 🚀 دليل البداية السريعة - AI Deal Analyzer

## 📋 التثبيت السريع (5 دقائق)

### 1️⃣ التحقق من المتطلبات
```bash
# تأكد من وجود Python 3.8+
python --version
# أو
python3 --version
```

### 2️⃣ التثبيت التلقائي

#### Windows:
```cmd
# انقر مرتين على run.bat
# أو من Command Prompt:
run.bat
```

#### Linux/Mac:
```bash
# اجعل الملف قابل للتنفيذ وشغله
chmod +x run.sh
./run.sh
```

#### التثبيت اليدوي:
```bash
# 1. تثبيت المتطلبات
pip install -r requirements.txt

# 2. إعداد النظام
python setup.py

# 3. تشغيل التطبيق
python main.py
```

## 🔑 إعداد مفاتيح API

### Gemini AI (مطلوب للتحليل الذكي):
1. اذهب إلى [Google AI Studio](https://makersuite.google.com/app/apikey)
2. أنشئ مفتاح API جديد
3. انسخ المفتاح
4. أدخله في الواجهة أو احفظه في `api_config.json`

### Telegram Bot (اختياري):
1. ابحث عن [@BotFather](https://t.me/botfather) في التليجرام
2. أرسل `/newbot` وتابع التعليمات
3. احصل على Bot Token
4. احصل على User ID من [@userinfobot](https://t.me/userinfobot)

## 🎯 الاستخدام السريع

### الواجهة الرسومية (الأسهل):
```bash
python main.py
# أو انقر على run.bat/run.sh
```

### تحليل AI من سطر الأوامر:
```bash
python main.py analyze --api-key YOUR_GEMINI_KEY --max-deals 10
```

### البحث عن أسعار منتج:
```bash
python main.py search --product "ماكينة حلاقة متعددة الاستخدامات"
```

### تشغيل بوت التليجرام:
```bash
python main.py telegram --api-key YOUR_GEMINI_KEY
```

### تحويل ملف JSON:
```bash
python main.py migrate --json-file products.json
```

## 📊 مثال على النتائج

```
🎯 Found 3 high quality deals:

1. ماكينة حلاقة متعددة الاستخدامات 10 في 1...
   💰 Price: 450 EGP
   ⚡ Discount: 25.0%
   🤖 AI Score: 8.5/10
   🔗 URL: https://amazon.eg/dp/B0SAMPLE01

2. سماعات بلوتوث لاسلكية عالية الجودة...
   💰 Price: 299 EGP
   ⚡ Discount: 33.6%
   🤖 AI Score: 7.8/10
   🔗 URL: https://amazon.eg/dp/B0SAMPLE02
```

## 🔧 حل المشاكل الشائعة

### خطأ في مفتاح API:
```
Error: Invalid API key
الحل: تأكد من صحة مفتاح Gemini API
```

### مشكلة ChromeDriver:
```bash
pip install webdriver-manager
```

### خطأ في قاعدة البيانات:
```bash
# احذف قاعدة البيانات وأعد إنشاءها
rm amz_products.db
python setup.py
```

### مشكلة في بوت التليجرام:
- تأكد من صحة Bot Token
- تأكد من صحة User IDs
- تأكد أن البوت يمكنه إرسال رسائل للمستخدمين

## 📱 رسائل التليجرام النموذجية

### عرض محلل بـ AI:
```
🌟 VERIFIED PREMIUM DEAL 🌟

ماكينة حلاقة متعددة الاستخدامات 10 في 1

🔗 عرض المنتج على أمازون
📦 القسم: Beauty

💰 600 EGP → 450 EGP
⚡ الخصم: 25.0%

🏆 نقاط AI: 8.5/10
🎯 نوع العرض: ممتاز
🏅 ترتيب أمازون: الأول

🤖 تحليل AI:
عرض ممتاز - السعر أقل من المتوسط بنسبة 25%

🔍 حكم المقارنة:
أمازون يقدم أفضل سعر مقارنة بالمواقع الأخرى

🔍 مقارنة الأسعار:
• Jumia: 520 EGP (توفر 70 جنيه)
• Noon: 480 EGP (توفر 30 جنيه)

⏰ تم التحقق: 2024-01-15 14:30
```

## 📈 الميزات المتقدمة

### لوحة التحكم:
- إحصائيات شاملة
- رسوم بيانية للأسعار
- جدول أفضل العروض
- مؤشرات حالة النظام

### تحليل AI:
- تقييم جودة العروض (1-10)
- كشف العروض الوهمية
- مقارنة تلقائية للأسعار
- توصيات ذكية

### بوت التليجرام:
- تقارير يومية تلقائية
- تنبيهات فورية للعروض
- أزرار تفاعلية
- إحصائيات متقدمة

## 🛠️ التخصيص

### إعدادات AI:
```python
AI_CONFIG = {
    "min_score_threshold": 7.0,    # الحد الأدنى للنقاط
    "max_deals_per_analysis": 20,  # عدد العروض القصوى
    "analysis_interval": 30        # فترة التحليل (دقيقة)
}
```

### إعدادات التليجرام:
```json
{
  "bot_token": "YOUR_BOT_TOKEN",
  "users": ["USER_ID_1", "USER_ID_2"],
  "daily_report_time": "09:00",
  "auto_reports": true
}
```

## 🎯 نصائح للحصول على أفضل النتائج

1. **استخدم مفتاح Gemini API صحيح** للحصول على تحليلات دقيقة
2. **فعّل التقارير اليومية** لمتابعة أفضل العروض
3. **اضبط الحد الأدنى للنقاط** حسب معايير الجودة المطلوبة
4. **استخدم البحث المتقدم** للعثور على منتجات محددة
5. **راجع تاريخ الأسعار** قبل اتخاذ قرار الشراء

## 🆘 الحصول على المساعدة

- 📖 **الدليل الكامل**: README.md
- 🐛 **الإبلاغ عن مشاكل**: GitHub Issues
- 💬 **الدعم التقني**: @DealAnalyzerSupport
- 📧 **البريد الإلكتروني**: support@ai-deal-analyzer.com

---

**🚀 استمتع بتجربة التسوق الذكي مع أحدث تقنيات الذكاء الاصطناعي! 🇪🇬**