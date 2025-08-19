# CI/CD Pipeline - نظام إدارة العروض الذكي

هذا المجلد يحتوي على ملفات GitHub Actions للتحليل التلقائي والاختبارات والنشر.

## الملفات المتاحة

### 1. `workflows/tests.yml`
**الاختبارات الأساسية**
- تشغيل الاختبارات على Python 3.8, 3.9, 3.10, 3.11
- فحص جودة الكود (Black, Flake8, isort)
- فحص الأنواع (MyPy)
- فحص الأمان (Bandit, Safety)
- تقرير تغطية الكود
- اختبارات التكامل
- اختبارات Docker
- اختبارات النشر

### 2. `workflows/security.yml`
**التحليل الأمني**
- فحص Bandit للأمان
- فحص Safety للمكتبات
- فحص Semgrep للكود
- مراجعة التبعيات
- تعليقات تلقائية على Pull Requests

### 3. `workflows/static-analysis.yml`
**التحليل الثابت**
- فحص جودة الكود
- فحص التوثيق
- تحليل التبعيات
- تحليل الأداء
- فحص الذاكرة

### 4. `workflows/deploy.yml`
**النشر التلقائي**
- بناء Docker image
- رفع إلى Docker Hub
- إنشاء Releases
- رفع الملفات المرفقة

## تشغيل الـ Workflows

### تشغيل تلقائي
- **عند Push**: يتم تشغيل الاختبارات والتحليل الأمني والتحليل الثابت
- **عند Pull Request**: نفس الاختبارات + تعليقات تلقائية
- **عند إنشاء Tag**: يتم النشر التلقائي

### تشغيل يدوي
```bash
# تشغيل الاختبارات فقط
gh workflow run tests.yml

# تشغيل التحليل الأمني
gh workflow run security.yml

# تشغيل التحليل الثابت
gh workflow run static-analysis.yml

# تشغيل النشر
gh workflow run deploy.yml
```

## متطلبات الـ Secrets

### Docker Hub
```bash
DOCKER_USERNAME=your_docker_username
DOCKER_PASSWORD=your_docker_password
```

### GitHub
```bash
GITHUB_TOKEN=auto_generated
```

## إعدادات الـ Repository

### Branch Protection Rules
```yaml
# main branch
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Require pull request reviews before merging
- Require conversation resolution before merging
- Include administrators

# develop branch
- Require status checks to pass before merging
- Require branches to be up to date before merging
```

### Required Status Checks
- `test / test (3.8)`
- `test / test (3.9)`
- `test / test (3.10)`
- `test / test (3.11)`
- `security-scan`
- `code-quality`
- `documentation-check`

## مراقبة الـ Workflows

### GitHub Actions Dashboard
```
https://github.com/{username}/{repo}/actions
```

### Workflow Status
- ✅ **Success**: جميع الاختبارات نجحت
- ❌ **Failure**: فشل في واحد أو أكثر من الاختبارات
- ⏳ **Pending**: في انتظار التشغيل
- 🔄 **Running**: قيد التشغيل

### تقارير مفصلة
- **Coverage Report**: تقرير تغطية الكود
- **Security Reports**: تقارير الأمان
- **Performance Reports**: تقارير الأداء
- **Dependency Reports**: تقارير التبعيات

## استكشاف الأخطاء

### مشاكل شائعة

#### 1. فشل في الاختبارات
```bash
# تشغيل الاختبارات محلياً
pytest tests/ -v

# تشغيل اختبار محدد
pytest tests/test_database.py::TestEnhancedDatabaseManager::test_add_product -v
```

#### 2. فشل في فحص جودة الكود
```bash
# تنسيق الكود
black .
isort .

# فحص الأخطاء
flake8 .
mypy .
```

#### 3. فشل في فحص الأمان
```bash
# فحص Bandit
bandit -r . -f json -o bandit-report.json

# فحص Safety
safety check --json --output safety-report.json
```

#### 4. فشل في Docker
```bash
# بناء Docker image محلياً
docker build -t ai-deals-manager .

# تشغيل Docker container
docker run --rm ai-deals-manager python -m pytest tests/
```

### إعادة تشغيل Workflows
```bash
# إعادة تشغيل workflow محدد
gh run rerun {run_id}

# إعادة تشغيل workflow فاشل
gh run rerun --failed
```

## تحسين الأداء

### Cache Optimization
```yaml
# Cache pip dependencies
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### Parallel Jobs
```yaml
# تشغيل متوازي للاختبارات
strategy:
  matrix:
    python-version: [3.8, 3.9, 3.10, 3.11]
```

### Conditional Jobs
```yaml
# تشغيل فقط على main branch
if: github.ref == 'refs/heads/main'
```

## إحصائيات الـ CI/CD

### وقت التشغيل
- **الاختبارات الأساسية**: ~5-10 دقائق
- **التحليل الأمني**: ~3-5 دقائق
- **التحليل الثابت**: ~8-12 دقيقة
- **النشر**: ~5-8 دقائق

### التكلفة
- **GitHub Actions**: 2000 دقيقة/شهر مجاناً
- **Docker Hub**: 200 pull/شهر مجانياً
- **Codecov**: مجاني للمشاريع المفتوحة

## أفضل الممارسات

### 1. الاختبارات
- ✅ اختبارات سريعة ومحددة
- ✅ تغطية كود عالية (>80%)
- ✅ اختبارات التكامل
- ✅ اختبارات الأداء

### 2. الأمان
- ✅ فحص التبعيات بانتظام
- ✅ فحص الكود للأمان
- ✅ تحديث المكتبات
- ✅ مراجعة الأذونات

### 3. النشر
- ✅ اختبارات شاملة قبل النشر
- ✅ إصدارات محددة (Semantic Versioning)
- ✅ توثيق التغييرات
- ✅ Rollback plan

### 4. المراقبة
- ✅ تنبيهات للفشل
- ✅ تقارير دورية
- ✅ مقاييس الأداء
- ✅ تحليل الاتجاهات

## التطوير المستقبلي

### الميزات المخططة
- [ ] اختبارات متقدمة للأداء
- [ ] تحليل جودة الكود المتقدم
- [ ] نشر تلقائي للمستقبلات
- [ ] مراقبة التطبيق في الإنتاج
- [ ] تقارير تحليلية متقدمة

### التحسينات
- [ ] تحسين سرعة الاختبارات
- [ ] تقليل استخدام الموارد
- [ ] تحسين التقارير
- [ ] إضافة اختبارات جديدة

## الدعم والمساعدة

### الوثائق
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Pytest Documentation](https://docs.pytest.org/)

### التواصل
- إنشاء Issue للمشاكل
- إنشاء Discussion للأسئلة
- إنشاء Pull Request للتحسينات

### المساهمة
1. Fork المشروع
2. إنشاء branch جديد
3. إجراء التغييرات
4. إضافة الاختبارات
5. إنشاء Pull Request

---

**ملاحظة**: تأكد من تحديث هذه الوثائق عند إضافة workflows جديدة أو تعديل الموجودة.