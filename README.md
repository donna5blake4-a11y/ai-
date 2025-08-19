# 🤖 AI-Enhanced Amazon Deal Analyzer

نظام ذكي متطور لتحليل العروض على أمازون مصر باستخدام الذكاء الاصطناعي ومقارنة الأسعار عبر المواقع المصرية الرئيسية.

## ✨ المميزات الرئيسية

### 🧠 نظام AI متقدم
- **تحليل ذكي للعروض**: يستخدم Gemini AI لتحديد العروض الحقيقية من الوهمية
- **مقارنة أسعار تلقائية**: يقارن الأسعار عبر جوميا، نون، B.Tech وغيرها
- **تقييم جودة العروض**: نظام نقاط من 1-10 لكل عرض
- **تحليل اتجاهات الأسعار**: متابعة تاريخ الأسعار وتوقع الاتجاهات

### 📊 قاعدة بيانات محسنة
- **SQLite محسن**: قاعدة بيانات سريعة مع فهارس متقدمة
- **تحويل JSON**: أداة تحويل 300 ألف منتج من JSON إلى SQLite
- **تتبع تاريخ الأسعار**: حفظ تاريخ كامل لجميع تغييرات الأسعار
- **إحصائيات متقدمة**: تحليلات شاملة للبيانات

### 🤖 بوت تليجرام ذكي
- **تقارير AI**: إرسال العروض المحللة بالذكاء الاصطناعي
- **تقارير يومية**: ملخص يومي للعروض الأفضل
- **تنبيهات فورية**: إشعارات عند انخفاض الأسعار
- **واجهة تفاعلية**: أزرار للتفاعل المباشر مع العروض

### 🖥️ واجهة مستخدم احترافية
- **لوحة تحكم شاملة**: إحصائيات ورسوم بيانية
- **إدارة AI**: تحكم كامل في نظام الذكاء الاصطناعي
- **مقارنة الأسعار**: بحث فوري في المواقع المصرية
- **إعدادات متقدمة**: تخصيص كامل للنظام

## 🚀 التثبيت والإعداد

### 1. متطلبات النظام
```bash
Python 3.8+
Chrome Browser (للـ web scraping)
```

### 2. تثبيت المكتبات
```bash
pip install -r requirements.txt
```

### 3. تثبيت ChromeDriver
```bash
# تلقائياً عبر webdriver-manager
# أو تحميل يدوي من https://chromedriver.chromium.org/
```

### 4. إعداد مفاتيح API

#### Gemini AI API
1. احصل على مفتاح API من [Google AI Studio](https://makersuite.google.com/app/apikey)
2. أدخل المفتاح في واجهة المستخدم

#### Telegram Bot
1. أنشئ بوت جديد عبر [@BotFather](https://t.me/botfather)
2. احصل على Bot Token
3. أضف المعرفات الخاصة بالمستخدمين

## 📖 دليل الاستخدام

### 1. تشغيل الواجهة الرئيسية
```bash
python ai_enhanced_gui.py
```

### 2. تحويل بيانات JSON إلى SQLite
```bash
python migrate_json_to_sqlite.py --json-file products.json --db-file amz_products.db
```

### 3. تشغيل تحليل AI مستقل
```bash
python ai_price_analyzer.py
```

### 4. اختبار بوت التليجرام
```bash
python enhanced_telegram_bot.py
```

## 🔧 الإعداد المتقدم

### إعدادات قاعدة البيانات
```python
# في ملف الإعدادات
DATABASE_CONFIG = {
    "file": "amz_products.db",
    "batch_size": 1000,
    "optimize": True,
    "backup_interval": 24  # ساعة
}
```

### إعدادات AI
```python
AI_CONFIG = {
    "model": "gemini-pro",
    "max_tokens": 1000,
    "temperature": 0.3,
    "min_score_threshold": 7.0,
    "max_deals_per_analysis": 20
}
```

### إعدادات Web Scraping
```python
SCRAPING_CONFIG = {
    "delay_between_requests": 2,  # ثانية
    "max_retries": 3,
    "timeout": 15,
    "user_agents": [...]  # قائمة User Agents
}
```

## 📁 هيكل المشروع

```
📦 AI-Enhanced-Amazon-Analyzer/
├── 🤖 ai_price_analyzer.py          # نظام AI لتحليل الأسعار
├── 🗄️ enhanced_amz_scraper.py       # محسن أمازون scraper
├── 📱 enhanced_telegram_bot.py      # بوت تليجرام ذكي
├── 🌐 egyptian_sites_scraper.py     # scraper المواقع المصرية
├── 🖥️ ai_enhanced_gui.py            # الواجهة الرئيسية
├── 🔄 migrate_json_to_sqlite.py     # أداة تحويل البيانات
├── ⚙️ categories.py                 # تصنيفات المنتجات
├── 📊 amz_products.db              # قاعدة البيانات
├── 📋 requirements.txt             # متطلبات المشروع
├── 🔧 telegram_config.json         # إعدادات التليجرام
├── ⚙️ app_settings.json            # إعدادات التطبيق
└── 📖 README.md                    # هذا الملف
```

## 🎯 كيفية عمل النظام

### 1. جمع البيانات
- **Amazon Scraping**: جمع المنتجات من أمازون مصر
- **Price Tracking**: تتبع تغييرات الأسعار بشكل مستمر
- **Historical Data**: حفظ تاريخ كامل للأسعار

### 2. تحليل AI
```python
# مثال على تحليل العرض
def analyze_deal(product):
    analysis = ai_analyzer.analyze_deal_quality(product)
    price_comparison = scraper.search_product_prices(product['name'])
    ai_score = calculate_final_score(analysis, price_comparison)
    return ai_score
```

### 3. مقارنة الأسعار
- **Multi-site Search**: البحث في 5+ مواقع مصرية
- **Price Comparison**: مقارنة تلقائية للأسعار
- **Best Deal Detection**: تحديد أفضل عرض متاح

### 4. التقارير الذكية
- **Daily Reports**: تقارير يومية مفصلة
- **AI Insights**: تحليلات ذكية للاتجاهات
- **Personalized Alerts**: تنبيهات مخصصة

## 🔍 مثال على تحليل AI

```json
{
  "product": "ماكينة حلاقة متعددة الاستخدامات 10 في 1",
  "amazon_price": 847.92,
  "ai_analysis": {
    "is_real_deal": true,
    "quality_score": 8.5,
    "deal_type": "ممتاز",
    "recommendation": "عرض ممتاز - السعر أقل من المتوسط بنسبة 25%"
  },
  "price_comparison": [
    {"site": "jumia", "price": 950.00},
    {"site": "noon", "price": 920.00},
    {"site": "btech", "price": 890.00}
  ],
  "final_verdict": "أمازون يقدم أفضل سعر - يُنصح بالشراء"
}
```

## 📊 الإحصائيات والتحليلات

### لوحة التحكم
- **إجمالي المنتجات**: عدد المنتجات في قاعدة البيانات
- **المحللة بـ AI**: المنتجات التي تم تحليلها
- **العروض عالية الجودة**: العروض بنقاط 7+ من 10
- **متوسط نقاط AI**: متوسط تقييم جودة العروض

### الرسوم البيانية
- **اتجاهات الأسعار**: رسم بياني لتطور الأسعار
- **توزيع العروض**: توزيع العروض حسب الفئات
- **أداء AI**: دقة تحليلات الذكاء الاصطناعي

## 🛠️ استكشاف الأخطاء

### مشاكل شائعة وحلولها

#### خطأ في API Key
```bash
Error: Invalid API key
الحل: تأكد من صحة مفتاح Gemini API
```

#### مشكلة في ChromeDriver
```bash
Error: ChromeDriver not found
الحل: pip install webdriver-manager
```

#### خطأ في قاعدة البيانات
```bash
Error: Database locked
الحل: أغلق جميع الاتصالات وأعد تشغيل التطبيق
```

#### مشكلة في بوت التليجرام
```bash
Error: Unauthorized
الحل: تحقق من Bot Token وUser IDs
```

## 🔒 الأمان والخصوصية

- **تشفير API Keys**: جميع المفاتيح محفوظة بشكل آمن
- **Rate Limiting**: تحكم في معدل الطلبات لتجنب الحظر
- **User Agent Rotation**: تدوير User Agents لتجنب الكشف
- **Error Handling**: معالجة شاملة للأخطاء

## 🚀 التطوير المستقبلي

### المميزات المخططة
- [ ] **تحليل المراجعات**: تحليل AI لمراجعات المنتجات
- [ ] **التنبؤ بالأسعار**: توقع اتجاهات الأسعار المستقبلية
- [ ] **API REST**: واجهة برمجية للتطبيقات الخارجية
- [ ] **تطبيق موبايل**: تطبيق Android/iOS
- [ ] **تحليل المنافسين**: مقارنة مع منصات أخرى

### التحسينات التقنية
- [ ] **Microservices**: تقسيم النظام إلى خدمات صغيرة
- [ ] **Docker**: دعم الحاويات
- [ ] **Cloud Deployment**: نشر على السحابة
- [ ] **Real-time Updates**: تحديثات فورية

## 🤝 المساهمة

نرحب بالمساهمات! يرجى اتباع هذه الخطوات:

1. Fork المشروع
2. إنشاء branch جديد (`git checkout -b feature/amazing-feature`)
3. Commit التغييرات (`git commit -m 'Add amazing feature'`)
4. Push إلى Branch (`git push origin feature/amazing-feature`)
5. فتح Pull Request

## 📄 الترخيص

هذا المشروع مرخص تحت رخصة MIT - راجع ملف [LICENSE](LICENSE) للتفاصيل.

## 👨‍💻 المطور

تم تطوير هذا النظام بواسطة فريق متخصص في الذكاء الاصطناعي وتحليل البيانات.

## 📞 الدعم التقني

لأي استفسارات أو مشاكل تقنية:
- 📧 Email: support@ai-deal-analyzer.com
- 💬 Telegram: @DealAnalyzerSupport
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/issues)

## 🙏 شكر خاص

- **Google AI**: لتوفير Gemini API
- **Amazon**: لتوفير البيانات المفتوحة
- **المجتمع المصري**: للدعم والتشجيع المستمر

---

<div align="center">
  <b>🚀 ابدأ رحلتك مع أذكى نظام لتحليل العروض في مصر! 🇪🇬</b>
</div>