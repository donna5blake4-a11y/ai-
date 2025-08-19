# egyptian_retailers.py
# قائمة المواقع المصرية الرئيسية للمقارنة

EGYPTIAN_RETAILERS = {
    "Jumia": {
        "base_url": "https://www.jumia.com.eg",
        "search_url": "https://www.jumia.com.eg/catalog/?q={query}",
        "price_selector": ".prc",
        "name_selector": "h3.name",
        "image_selector": "img.img",
        "link_selector": "a.core",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    },
    
    "Noon": {
        "base_url": "https://www.noon.com",
        "search_url": "https://www.noon.com/egypt-en/search?q={query}",
        "price_selector": "[data-qa='product-price']",
        "name_selector": "[data-qa='product-name']",
        "image_selector": "img.product-image",
        "link_selector": "a.product-link",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    },
    
    "Souq": {
        "base_url": "https://egypt.souq.com",
        "search_url": "https://egypt.souq.com/eg-en/search?q={query}",
        "price_selector": ".price-value",
        "name_selector": ".item-name",
        "image_selector": ".item-image img",
        "link_selector": ".item-link",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    },
    
    "B.Tech": {
        "base_url": "https://www.btech.com",
        "search_url": "https://www.btech.com/search?q={query}",
        "price_selector": ".product-price",
        "name_selector": ".product-name",
        "image_selector": ".product-image img",
        "link_selector": ".product-link",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    },
    
    "Carrefour": {
        "base_url": "https://www.carrefouregypt.com",
        "search_url": "https://www.carrefouregypt.com/search?q={query}",
        "price_selector": ".product-price",
        "name_selector": ".product-title",
        "image_selector": ".product-image img",
        "link_selector": ".product-link",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    },
    
    "Ounass": {
        "base_url": "https://www.ounass.ae",
        "search_url": "https://www.ounass.ae/search?q={query}",
        "price_selector": ".product-price",
        "name_selector": ".product-name",
        "image_selector": ".product-image img",
        "link_selector": ".product-link",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    },
    
    "Kanbkam": {
        "base_url": "https://www.kanbkam.com",
        "search_url": "https://www.kanbkam.com/eg/ar/search/l?q={query}",
        "price_selector": ".price",
        "name_selector": ".product-name",
        "image_selector": ".product-image img",
        "link_selector": ".product-link",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    }
}

# مواقع إضافية للتحقق من الأسعار
ADDITIONAL_RETAILERS = {
    "ElAraby": "https://www.elarabygroup.com",
    "SharafDG": "https://www.sharafdg.com",
    "Extra": "https://www.extra.com",
    "HyperOne": "https://www.hyperone.com.eg",
    "Spinneys": "https://www.spinneys-egypt.com",
    "Metro": "https://www.metro-egypt.com"
}

# كلمات مفتاحية للبحث الذكي
SEARCH_KEYWORDS = {
    "electronics": ["إلكترونيات", "كهربائيات", "تكنولوجيا"],
    "beauty": ["تجميل", "عناية", "مكياج", "عطور"],
    "fashion": ["ملابس", "أزياء", "أحذية", "حقائب"],
    "home": ["منزل", "مطبخ", "أثاث", "ديكور"],
    "health": ["صحة", "رياضة", "تغذية", "فيتامينات"]
}

def get_search_query(product_name, category=None):
    """تحويل اسم المنتج إلى كلمات بحث مناسبة"""
    # إزالة الكلمات الزائدة
    stop_words = ["من", "في", "على", "إلى", "مع", "و", "أو", "هذا", "هذه", "ذلك", "تلك"]
    
    # استخراج الكلمات المهمة
    words = product_name.split()
    important_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # إضافة كلمات مفتاحية حسب الفئة
    if category and category in SEARCH_KEYWORDS:
        important_words.extend(SEARCH_KEYWORDS[category][:2])
    
    return " ".join(important_words[:5])  # أخذ أول 5 كلمات مهمة