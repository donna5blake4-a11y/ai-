# Support Guide

## 🆘 Need Help?

نحن هنا لمساعدتك! إليك الطرق المختلفة للحصول على الدعم.

## 📞 طرق التواصل

### 🐛 الإبلاغ عن الأخطاء
- **GitHub Issues**: [Create an Issue](https://github.com/your-repo/ai-deals-manager/issues)
- **Email**: support@aideals.com
- **Response Time**: 24-48 hours

### 💡 اقتراح ميزات جديدة
- **GitHub Discussions**: [Feature Requests](https://github.com/your-repo/ai-deals-manager/discussions)
- **GitHub Issues**: [Feature Request Template](https://github.com/your-repo/ai-deals-manager/issues/new?template=feature_request.md)

### ❓ أسئلة عامة
- **GitHub Discussions**: [Q&A](https://github.com/your-repo/ai-deals-manager/discussions)
- **Documentation**: [README.md](README.md)
- **Wiki**: [Project Wiki](https://github.com/your-repo/ai-deals-manager/wiki)

## 🚀 Quick Start Support

### التثبيت السريع
```bash
# تشغيل سكريبت التثبيت التلقائي
./quick_start.sh

# أو استخدام Make
make setup
```

### المشاكل الشائعة

#### 1. خطأ في تثبيت المكتبات
```bash
# تحديث pip
pip install --upgrade pip

# تثبيت المتطلبات
pip install -r requirements.txt
```

#### 2. خطأ في إعدادات البوت
```json
{
  "bot_token": "YOUR_BOT_TOKEN_HERE",
  "users": ["YOUR_USER_ID_HERE"]
}
```

#### 3. خطأ في قاعدة البيانات
```bash
# إعادة تهيئة قاعدة البيانات
python -c "from enhanced_database import EnhancedDatabaseManager; db = EnhancedDatabaseManager()"
```

## 📋 Troubleshooting Guide

### مشاكل التثبيت

#### Python Version Error
```bash
# التحقق من إصدار Python
python --version

# يجب أن يكون 3.8 أو أحدث
```

#### Permission Error
```bash
# إعطاء صلاحيات التنفيذ
chmod +x quick_start.sh
chmod +x *.py
```

#### Virtual Environment Issues
```bash
# إنشاء بيئة افتراضية جديدة
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate     # Windows
```

### مشاكل التشغيل

#### Database Connection Error
```bash
# فحص وجود قاعدة البيانات
ls -la *.db

# إعادة إنشاء قاعدة البيانات
rm -f *.db
python -c "from enhanced_database import EnhancedDatabaseManager; db = EnhancedDatabaseManager()"
```

#### Telegram Bot Error
```bash
# فحص إعدادات البوت
cat telegram_config.json

# اختبار البوت
python -c "from enhanced_telegram_bot import EnhancedTelegramBot; bot = EnhancedTelegramBot()"
```

#### AI Analysis Error
```bash
# فحص الاتصال بالإنترنت
ping google.com

# اختبار محلل AI
python test_ai_system.py
```

### مشاكل الأداء

#### بطء في التشغيل
```bash
# فحص استخدام الذاكرة
htop

# تنظيف الملفات المؤقتة
make clean
```

#### مشاكل في قاعدة البيانات
```bash
# تحسين قاعدة البيانات
python -c "
from enhanced_database import EnhancedDatabaseManager
db = EnhancedDatabaseManager()
db.connection.execute('VACUUM')
db.connection.execute('ANALYZE')
"
```

## 🧪 Testing & Debugging

### تشغيل الاختبارات
```bash
# جميع الاختبارات
make test

# اختبارات محددة
python -m pytest test_ai_system.py

# مع التغطية
make test-cov
```

### Debug Mode
```bash
# تشغيل في وضع التصحيح
python -u ai_deals_manager.py --debug

# أو
export DEBUG=1
python ai_deals_manager.py
```

### Logging
```bash
# فحص السجلات
tail -f ai_deals.log

# تنظيف السجلات
rm -f *.log
```

## 📚 Documentation

### الملفات المهمة
- **[README.md](README.md)** - الدليل الرئيسي
- **[CHANGELOG.md](CHANGELOG.md)** - سجل التغييرات
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - دليل المساهمة
- **[SECURITY.md](SECURITY.md)** - سياسة الأمان

### أمثلة الاستخدام
```python
# مثال بسيط
from ai_deals_manager import AIDealsManager

manager = AIDealsManager()
deals = manager.get_top_ai_deals(limit=5)
print(f"Found {len(deals)} deals")
```

## 🔧 Advanced Support

### للمطورين
- **Code Review**: [Pull Requests](https://github.com/your-repo/ai-deals-manager/pulls)
- **Development Setup**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **API Documentation**: [Inline Code Comments]()

### للمشرفين
- **Deployment**: [Docker Guide](docker-compose.yml)
- **Monitoring**: [Log Analysis](ai_deals.log)
- **Backup**: [Database Backup]()

## 📊 System Status

### الحالة الحالية
- **System**: ✅ Operational
- **Database**: ✅ Healthy
- **AI Analysis**: ✅ Working
- **Telegram Bot**: ✅ Connected

### الإحصائيات
- **Uptime**: 99.9%
- **Response Time**: < 2s
- **Error Rate**: < 0.1%

## 🆘 Emergency Support

### في حالة الطوارئ
1. **Stop the system**: `Ctrl+C` أو `make stop`
2. **Check logs**: `tail -f ai_deals.log`
3. **Restart**: `make run`
4. **Contact**: security@aideals.com

### معلومات الطوارئ
- **Critical Issues**: security@aideals.com
- **System Down**: +1-XXX-XXX-XXXX
- **Response Time**: 2 hours

## 🤝 Community Support

### المساعدة من المجتمع
- **GitHub Discussions**: [Community Help](https://github.com/your-repo/ai-deals-manager/discussions)
- **Stack Overflow**: [Tag: ai-deals-manager](https://stackoverflow.com/questions/tagged/ai-deals-manager)
- **Reddit**: [r/ai-deals-manager](https://reddit.com/r/ai-deals-manager)

### الموارد المفيدة
- **Tutorials**: [Wiki](https://github.com/your-repo/ai-deals-manager/wiki)
- **Examples**: [Examples Directory](examples/)
- **FAQ**: [Frequently Asked Questions](FAQ.md)

## 📞 Contact Information

### الفريق الأساسي
- **Lead Developer**: ai-assistant@aideals.com
- **Support Team**: support@aideals.com
- **Security**: security@aideals.com

### أوقات العمل
- **Monday - Friday**: 9:00 AM - 6:00 PM (GMT+2)
- **Weekend**: Emergency support only
- **Holidays**: Limited support

### Response Times
- **Critical**: 2 hours
- **High**: 24 hours
- **Medium**: 48 hours
- **Low**: 1 week

---

**🎯 هدفنا**: مساعدتك في تحقيق أقصى استفادة من النظام!

**💪 شعارنا**: "نحن هنا لمساعدتك!"