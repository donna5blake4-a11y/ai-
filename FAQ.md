# Frequently Asked Questions (FAQ)

## 🤔 الأسئلة الشائعة

### 📋 عام

#### Q: ما هو AI Deals Manager؟
**A**: نظام ذكي لتحليل العروض ومقارنة الأسعار مع المواقع المصرية المختلفة باستخدام الذكاء الاصطناعي.

#### Q: هل النظام مجاني؟
**A**: نعم، النظام مفتوح المصدر ومجاني للاستخدام الشخصي والتجاري.

#### Q: ما هي المتطلبات الأساسية؟
**A**: Python 3.8+، اتصال بالإنترنت، بوت تليجرام (اختياري).

#### Q: هل أحتاج خبرة برمجية؟
**A**: لا، النظام مصمم ليكون سهل الاستخدام مع واجهة بسيطة.

### 🚀 التثبيت والتشغيل

#### Q: كيف أثبت النظام؟
**A**: 
```bash
# الطريقة السريعة
./quick_start.sh

# أو يدوياً
pip install -r requirements.txt
python ai_deals_manager.py
```

#### Q: ما هو خطأ "ModuleNotFoundError"؟
**A**: تأكد من تثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

#### Q: كيف أنشئ بوت تليجرام؟
**A**: 
1. تحدث مع @BotFather على تليجرام
2. اكتب `/newbot`
3. اتبع التعليمات
4. احصل على token
5. أضفه في `telegram_config.json`

#### Q: كيف أحصل على User ID؟
**A**: 
1. أرسل رسالة لبوتك
2. اذهب إلى: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. ابحث عن `"id"` في الرد

### 🤖 الذكاء الاصطناعي

#### Q: كيف يعمل تحليل AI؟
**A**: النظام يقارن الأسعار مع المواقع المصرية (Jumia, Noon, Amazon Egypt) ويقيم جودة العرض بناءً على عدة معايير.

#### Q: ما هي درجة الثقة AI؟
**A**: تقييم من 0-1 لموثوقية التحليل:
- 0.9+: موثوق جداً
- 0.7-0.9: موثوق
- 0.5-0.7: مقبول
- <0.5: محدود

#### Q: لماذا لا يجد النظام أسعار بديلة؟
**A**: قد يكون المنتج غير متوفر في المواقع الأخرى، أو اسم المنتج غير واضح للبحث.

#### Q: كيف أحسن دقة التحليل؟
**A**: 
- تأكد من اتصال الإنترنت
- تحقق من إعدادات المواقع في `ai_config.json`
- أضف مواقع جديدة للمقارنة

### 📊 قاعدة البيانات

#### Q: أين تُحفظ البيانات؟
**A**: في ملف SQLite `amz_products.db` في نفس مجلد المشروع.

#### Q: كيف أنقل بياناتي من JSON؟
**A**: 
```bash
# تلقائياً عند التشغيل
python ai_deals_manager.py

# أو يدوياً
python -c "from ai_deals_manager import AIDealsManager; m = AIDealsManager(); m.migrate_json_data()"
```

#### Q: كيف أحذف قاعدة البيانات؟
**A**: 
```bash
rm amz_products.db
```

#### Q: كيف أصدّر البيانات؟
**A**: 
```python
from enhanced_database import EnhancedDatabaseManager
db = EnhancedDatabaseManager()
db.export_to_json("my_export.json")
```

### 🤖 بوت تليجرام

#### Q: لماذا لا يرسل البوت رسائل؟
**A**: تحقق من:
1. صحة `bot_token`
2. صحة `user_id`
3. تفعيل البوت
4. إرسال `/start` للبوت

#### Q: كيف أغير عدد الرسائل اليومية؟
**A**: عدّل `daily_limit` في `ai_config.json` أو في الكود:
```python
manager.update_settings(daily_limit=20)
```

#### Q: كيف أوقف الرسائل؟
**A**: 
```python
manager.telegram_bot.update_settings(ai_enabled=False)
```

#### Q: كيف أضيف مستخدمين جدد؟
**A**: أضف `user_id` في قائمة `users` في `telegram_config.json`:
```json
{
  "users": ["USER_ID_1", "USER_ID_2", "USER_ID_3"]
}
```

### ⚙️ الإعدادات

#### Q: كيف أغير معايير التقييم؟
**A**: عدّل `ai_config.json`:
```json
{
  "min_discount": 30,
  "min_ai_confidence": 0.8,
  "verified_only": true
}
```

#### Q: كيف أضيف مواقع جديدة؟
**A**: أضف الموقع في `ai_price_analyzer.py` في قائمة `egyptian_sites`.

#### Q: كيف أغير فاصل التحليل؟
**A**: عدّل `analysis_interval` في `ai_config.json` (بالدقائق).

#### Q: كيف أفعّل/أوقف ميزات معينة؟
**A**: استخدم `update_settings()`:
```python
manager.update_settings(
    ai_enabled=True,
    verified_only=False,
    min_ai_confidence=0.6
)
```

### 🐛 استكشاف الأخطاء

#### Q: النظام بطيء جداً؟
**A**: 
- تحقق من اتصال الإنترنت
- قلل `analysis_interval`
- استخدم `verified_only=True`
- نظف قاعدة البيانات

#### Q: خطأ "Connection timeout"؟
**A**: 
- تحقق من اتصال الإنترنت
- زد `request_timeout` في الإعدادات
- جرب لاحقاً

#### Q: خطأ "Database locked"؟
**A**: 
- أغلق جميع البرامج التي تستخدم قاعدة البيانات
- أعد تشغيل النظام
- أو احذف ملف `.db-wal` و `.db-shm`

#### Q: خطأ "Permission denied"؟
**A**: 
```bash
chmod +x *.py
chmod +x *.sh
```

### 📈 الأداء

#### Q: كم منتج يمكن تحليله؟
**A**: يعتمد على:
- قوة المعالج
- سرعة الإنترنت
- حجم قاعدة البيانات
- عادة 1000+ منتج في الساعة

#### Q: كيف أحسن الأداء؟
**A**: 
- استخدم SSD
- زد ذاكرة RAM
- حسّن اتصال الإنترنت
- استخدم `verified_only=True`

#### Q: كم مساحة تحتاج قاعدة البيانات؟
**A**: حوالي 1-5 ميجابايت لكل 1000 منتج.

#### Q: هل النظام يستهلك الكثير من البيانات؟
**A**: لا، حوالي 1-2 ميجابايت في الساعة للتحليل.

### 🔒 الأمان

#### Q: هل بياناتي آمنة؟
**A**: نعم، البيانات محفوظة محلياً ولا تُرسل لأي طرف ثالث.

#### Q: كيف أحمي token البوت؟
**A**: 
- لا تشارك `telegram_config.json`
- أضف الملف لـ `.gitignore`
- استخدم متغيرات البيئة

#### Q: هل النظام آمن للاستخدام التجاري؟
**A**: نعم، لكن راجع [LICENSE](LICENSE) للتفاصيل.

### 🌐 النشر

#### Q: كيف أنشر النظام على خادم؟
**A**: 
```bash
# باستخدام Docker
docker-compose up -d

# أو يدوياً
nohup python ai_deals_manager.py &
```

#### Q: كيف أضيف واجهة ويب؟
**A**: يمكن إضافة Flask أو FastAPI. راجع [CONTRIBUTING.md](CONTRIBUTING.md).

#### Q: كيف أضيف SSL؟
**A**: استخدم Nginx مع Let's Encrypt. راجع `nginx.conf`.

### 🔄 التحديثات

#### Q: كيف أحدث النظام؟
**A**: 
```bash
git pull origin main
pip install -r requirements.txt
```

#### Q: هل التحديثات آمنة؟
**A**: نعم، لكن احتفظ بنسخة احتياطية من البيانات.

#### Q: كيف أعود لإصدار سابق؟
**A**: 
```bash
git checkout <version_tag>
```

### 📞 الدعم

#### Q: أين أحصل على مساعدة؟
**A**: 
- [GitHub Issues](https://github.com/your-repo/ai-deals-manager/issues)
- [SUPPORT.md](SUPPORT.md)
- support@aideals.com

#### Q: كيف أبلغ عن خطأ؟
**A**: 
1. ابحث في [Issues](https://github.com/your-repo/ai-deals-manager/issues)
2. أنشئ issue جديد
3. ارفق تفاصيل الخطأ والسجلات

#### Q: كيف أقترح ميزة جديدة؟
**A**: 
- [GitHub Discussions](https://github.com/your-repo/ai-deals-manager/discussions)
- أو أنشئ issue مع label "enhancement"

---

**❓ لم تجد إجابة؟** راجع [SUPPORT.md](SUPPORT.md) أو اطرح سؤالك في [GitHub Discussions](https://github.com/your-repo/ai-deals-manager/discussions).