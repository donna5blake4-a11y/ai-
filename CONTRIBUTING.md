# Contributing to AI Deals Manager

شكراً لاهتمامك بالمساهمة في مشروع AI Deals Manager! هذا الدليل سيساعدك على البدء.

## 🚀 كيفية المساهمة

### 1. الإبلاغ عن الأخطاء
- استخدم [GitHub Issues](https://github.com/your-repo/ai-deals-manager/issues)
- اكتب وصفاً مفصلاً للمشكلة
- أرفق لقطات شاشة إذا أمكن
- اذكر خطوات إعادة إنتاج المشكلة

### 2. اقتراح ميزات جديدة
- اكتب وصفاً واضحاً للميزة المطلوبة
- اشرح لماذا هذه الميزة مفيدة
- اقترح كيفية تنفيذها إذا أمكن

### 3. المساهمة بالكود
- Fork المشروع
- أنشئ branch جديد للميزة
- اكتب الكود مع التعليقات
- اكتب اختبارات للكود الجديد
- أرسل Pull Request

## 🛠️ إعداد بيئة التطوير

### المتطلبات
- Python 3.8+
- Git
- Virtual environment

### خطوات الإعداد
```bash
# Clone المشروع
git clone https://github.com/your-repo/ai-deals-manager.git
cd ai-deals-manager

# إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows

# تثبيت المتطلبات
pip install -r requirements.txt
pip install -r requirements-dev.txt  # للتطوير

# تشغيل الاختبارات
python -m pytest
```

## 📝 معايير الكود

### تنسيق الكود
- استخدم [Black](https://black.readthedocs.io/) لتنسيق الكود
- استخدم [flake8](https://flake8.pycqa.org/) للتحقق من الجودة
- اتبع [PEP 8](https://www.python.org/dev/peps/pep-0008/)

```bash
# تنسيق الكود
black .

# فحص جودة الكود
flake8 .
```

### التعليقات والوثائق
- اكتب تعليقات باللغة العربية أو الإنجليزية
- استخدم docstrings للدوال
- اكتب README للميزات الجديدة

### الاختبارات
- اكتب اختبارات لكل دالة جديدة
- تأكد من تغطية الاختبارات 80% على الأقل
- شغل الاختبارات قبل إرسال PR

```bash
# تشغيل الاختبارات
python -m pytest

# مع التغطية
python -m pytest --cov=.
```

## 🏗️ بنية المشروع

```
ai-deals-manager/
├── ai_deals_manager.py      # المدير الرئيسي
├── ai_price_analyzer.py     # محلل الأسعار الذكي
├── enhanced_database.py     # قاعدة البيانات المحسنة
├── enhanced_telegram_bot.py # بوت تليجرام محسن
├── test_ai_system.py        # اختبارات النظام
├── run_ai_system.py         # سكريبت التشغيل السريع
├── requirements.txt         # المتطلبات
├── requirements-dev.txt     # متطلبات التطوير
├── setup.py                 # إعداد التثبيت
├── README.md               # التوثيق الرئيسي
├── CHANGELOG.md            # سجل التغييرات
├── CONTRIBUTING.md         # هذا الملف
├── LICENSE                 # الترخيص
└── .gitignore             # تجاهل الملفات
```

## 🎯 مجالات المساهمة

### 1. تحسين محلل AI
- إضافة مواقع جديدة للمقارنة
- تحسين خوارزميات التحليل
- إضافة معايير تقييم جديدة

### 2. تحسين قاعدة البيانات
- تحسين الأداء
- إضافة فهارس جديدة
- تحسين استعلامات SQL

### 3. تحسين بوت تليجرام
- إضافة ميزات جديدة
- تحسين الرسائل
- إضافة أزرار تفاعلية

### 4. تحسين الواجهة
- إضافة واجهة ويب
- تحسين واجهة المستخدم
- إضافة رسوم بيانية

### 5. التوثيق
- تحسين README
- إضافة أمثلة
- ترجمة التوثيق

## 🔄 عملية إرسال التغييرات

### 1. إعداد Git
```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 2. إنشاء Branch
```bash
git checkout -b feature/your-feature-name
# أو
git checkout -b fix/your-bug-fix
```

### 3. إجراء التغييرات
- اكتب الكود
- اكتب الاختبارات
- احدث التوثيق

### 4. Commit التغييرات
```bash
git add .
git commit -m "feat: add new feature description"
```

### 5. إرسال Pull Request
- ادفع التغييرات إلى fork
- أنشئ Pull Request
- اكتب وصفاً واضحاً للتغييرات

## 📋 معايير Commit Messages

استخدم [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: fix a bug
docs: update documentation
style: format code
refactor: refactor code
test: add tests
chore: maintenance tasks
```

## 🧪 الاختبارات

### تشغيل الاختبارات
```bash
# جميع الاختبارات
python -m pytest

# اختبارات محددة
python -m pytest test_ai_system.py

# مع التغطية
python -m pytest --cov=. --cov-report=html
```

### كتابة اختبارات جديدة
```python
def test_new_feature():
    """Test the new feature"""
    # Arrange
    expected = "expected result"
    
    # Act
    result = new_feature()
    
    # Assert
    assert result == expected
```

## 📞 التواصل

- **Issues**: [GitHub Issues](https://github.com/your-repo/ai-deals-manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/ai-deals-manager/discussions)
- **Email**: support@aideals.com

## 🎉 الاعتراف

سيتم إضافة أسماء المساهمين إلى:
- ملف CONTRIBUTORS.md
- صفحة GitHub Contributors
- ملف README.md

## 📄 الترخيص

بالمساهمة في هذا المشروع، فإنك توافق على أن مساهماتك ستكون مرخصة تحت نفس ترخيص المشروع (MIT License).

---

شكراً لك على المساهمة في جعل AI Deals Manager أفضل! 🚀
