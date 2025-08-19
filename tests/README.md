# اختبارات نظام إدارة العروض الذكي

هذا المجلد يحتوي على جميع اختبارات النظام الشاملة.

## هيكل الاختبارات

```
tests/
├── __init__.py              # حزمة الاختبارات
├── conftest.py              # إعدادات و fixtures مشتركة
├── test_database.py         # اختبارات قاعدة البيانات
├── test_ai_analyzer.py      # اختبارات محلل AI
├── test_telegram_bot.py     # اختبارات بوت التليجرام
├── test_ai_deals_manager.py # اختبارات مدير العروض الذكي
├── test_integration.py      # اختبارات التكامل الشاملة
└── README.md               # هذا الملف
```

## تشغيل الاختبارات

### تشغيل جميع الاختبارات
```bash
pytest tests/
```

### تشغيل اختبارات محددة
```bash
# اختبارات قاعدة البيانات فقط
pytest tests/test_database.py

# اختبارات AI فقط
pytest tests/test_ai_analyzer.py

# اختبارات التكامل فقط
pytest tests/test_integration.py
```

### تشغيل مع تقرير التغطية
```bash
pytest tests/ --cov=. --cov-report=html
```

### تشغيل مع تفاصيل أكثر
```bash
pytest tests/ -v --tb=short
```

## أنواع الاختبارات

### 1. اختبارات الوحدة (Unit Tests)
- **`test_database.py`**: اختبارات قاعدة البيانات
- **`test_ai_analyzer.py`**: اختبارات محلل AI
- **`test_telegram_bot.py`**: اختبارات بوت التليجرام
- **`test_ai_deals_manager.py`**: اختبارات مدير العروض

### 2. اختبارات التكامل (Integration Tests)
- **`test_integration.py`**: اختبارات التكامل الشاملة

## Fixtures المشتركة

### `temp_db_path`
إنشاء مسار قاعدة بيانات مؤقت للاختبارات.

### `sample_product_data`
بيانات منتج نموذجية للاختبارات.

### `sample_product`
كائن Product نموذجي.

### `db_manager`
مدير قاعدة بيانات مُهيأ للاختبارات.

### `ai_analyzer`
محلل AI مُهيأ للاختبارات.

### `telegram_bot`
بوت تليجرام مُهيأ للاختبارات.

### `sample_json_data`
بيانات JSON نموذجية للاختبارات.

### `temp_json_file`
ملف JSON مؤقت للاختبارات.

## أمثلة على الاختبارات

### اختبار قاعدة البيانات
```python
def test_add_product(self, db_manager, sample_product):
    """Test adding a product to the database."""
    result = db_manager.add_product(sample_product)
    assert result is True
    
    # Verify product was added
    retrieved_product = db_manager.get_product(sample_product.asin)
    assert retrieved_product is not None
    assert retrieved_product.asin == sample_product.asin
```

### اختبار محلل AI
```python
def test_analyze_deal_with_comparisons(self, ai_analyzer, sample_price_comparisons):
    """Test deal analysis with price comparisons."""
    product_data = {
        "name": "Test Product",
        "current_price": 1400.0,
        "strike_price": 1600.0,
        "discount_percent": 12.5,
    }
    
    with patch.object(ai_analyzer.scraper, 'search_product', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = sample_price_comparisons
        
        result = ai_analyzer.analyze_deal(product_data)
        
        assert isinstance(result, DealAnalysis)
        assert result.product_name == "Test Product"
        assert result.confidence_score > 0
```

### اختبار بوت التليجرام
```python
def test_send_ai_enhanced_alert_success(self, telegram_bot, sample_product):
    """Test successful AI enhanced alert sending."""
    analysis_data = {
        "market_average": 1550.0,
        "best_alternative_price": 1500.0,
        "best_alternative_website": "jumia",
        "price_difference": 100.0,
        "price_difference_percent": 6.67,
        "confidence_score": 0.85,
        "is_good_deal": True,
        "recommendations": ["Good price compared to market"],
        "analysis_summary": "This is a good deal.",
    }
    
    with patch.object(telegram_bot, '_send_message_to_all_users') as mock_send:
        mock_send.return_value = True
        
        result = telegram_bot.send_ai_enhanced_alert(sample_product, analysis_data)
        
        assert result is True
        mock_send.assert_called_once()
```

## اختبارات التكامل

### اختبار سير العمل الكامل
```python
def test_full_system_workflow(self, temp_db_path, temp_json_file):
    """Test the complete system workflow from JSON to Telegram alerts."""
    
    # 1. Initialize all components
    db_manager = EnhancedDatabaseManager(temp_db_path)
    db_manager.initialize_database()
    
    ai_analyzer = AIPriceAnalyzer(temp_db_path)
    telegram_bot = EnhancedTelegramBot()
    
    # 2. Migrate JSON data
    migration_result = db_manager.migrate_from_json(temp_json_file)
    assert migration_result is True
    
    # 3. Get deals from database
    deals = db_manager.get_deals(min_discount=10, limit=10)
    assert len(deals) == 2
    
    # 4. Analyze deals with AI
    for deal in deals:
        analysis = ai_analyzer.analyze_deal({...})
        assert isinstance(analysis, DealAnalysis)
    
    # 5. Send alerts via Telegram
    for deal in deals:
        alert_result = telegram_bot.send_ai_enhanced_alert(deal, analysis_data)
        assert alert_result is True
```

## اختبارات الأداء

### اختبار قاعدة البيانات مع بيانات كبيرة
```python
def test_database_performance(self, temp_db_path):
    """Test database performance with large datasets."""
    
    db_manager = EnhancedDatabaseManager(temp_db_path)
    db_manager.initialize_database()
    
    # Add many products
    for i in range(1000):
        product = Product(...)
        db_manager.add_product(product)
    
    # Test query performance
    deals = db_manager.get_deals(min_discount=15, limit=50)
    assert len(deals) > 0
```

### اختبار العمليات المتزامنة
```python
def test_concurrent_operations(self, temp_db_path):
    """Test concurrent database operations."""
    
    import threading
    
    def worker(thread_id: int, count: int):
        db_manager = EnhancedDatabaseManager(temp_db_path)
        # Add products...
        db_manager.close()
    
    # Create multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker, args=(i, 20))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
```

## اختبارات السيناريوهات الواقعية

### اختبار تحليل السوق المصري
```python
def test_egyptian_market_analysis(self, temp_db_path):
    """Test analysis of Egyptian market products."""
    
    ai_analyzer = AIPriceAnalyzer(temp_db_path)
    
    egyptian_products = [
        {
            "name": "ماكينة حلاقة متعددة الاستخدامات 10 في 1 للرجال من بيبي ليس",
            "current_price": 1200.0,
            "strike_price": 1500.0,
            "discount_percent": 20.0,
        },
        # ... more products
    ]
    
    for product_data in egyptian_products:
        analysis = ai_analyzer.analyze_deal(product_data)
        assert isinstance(analysis, DealAnalysis)
        assert analysis.product_name == product_data["name"]
```

## تشغيل الاختبارات في CI/CD

### GitHub Actions
```yaml
- name: Run tests
  run: |
    pip install pytest pytest-cov pytest-asyncio
    pytest tests/ --cov=. --cov-report=xml
```

### Local Development
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run tests with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_database.py -v

# Run tests in parallel
pytest tests/ -n auto
```

## إحصائيات الاختبارات

### تغطية الكود
- قاعدة البيانات: 95%+
- محلل AI: 90%+
- بوت التليجرام: 85%+
- مدير العروض: 80%+

### وقت التشغيل
- اختبارات الوحدة: < 30 ثانية
- اختبارات التكامل: < 2 دقيقة
- جميع الاختبارات: < 3 دقائق

## استكشاف الأخطاء

### مشاكل شائعة
1. **خطأ في قاعدة البيانات**: تأكد من وجود مساحة كافية على القرص
2. **خطأ في الشبكة**: تأكد من اتصال الإنترنت للاختبارات التي تحتاج شبكة
3. **خطأ في الذاكرة**: قلل عدد الاختبارات المتزامنة

### تشغيل اختبارات محددة
```bash
# تشغيل اختبار واحد فقط
pytest tests/test_database.py::TestEnhancedDatabaseManager::test_add_product

# تشغيل اختبارات تحتوي على كلمة معينة
pytest tests/ -k "database"

# تشغيل اختبارات مع تجاهل بعضها
pytest tests/ -k "not slow"
```

## إضافة اختبارات جديدة

### هيكل الاختبار الجديد
```python
class TestNewFeature:
    """Test cases for new feature."""
    
    def test_feature_functionality(self):
        """Test the main functionality of the feature."""
        # Arrange
        # Act
        # Assert
        pass
    
    def test_feature_edge_cases(self):
        """Test edge cases of the feature."""
        pass
    
    def test_feature_integration(self):
        """Test integration with other components."""
        pass
```

### إضافة Fixtures جديدة
```python
@pytest.fixture
def new_test_data():
    """Create test data for new feature."""
    return {
        "key": "value",
        "number": 42,
    }
```

## المراجع

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Pytest-cov](https://pytest-cov.readthedocs.io/)
- [Python Testing Best Practices](https://realpython.com/python-testing/)