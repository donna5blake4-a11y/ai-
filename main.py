# main.py - نقطة الدخول الرئيسية للنظام
import sys
import os
import argparse
import logging
from datetime import datetime

# إعداد المسار للاستيراد
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# الاستيرادات الرئيسية
from ai_enhanced_gui import AIEnhancedGUI
from ai_price_analyzer import AIAnalyzer, DealQualityFilter
from enhanced_telegram_bot import EnhancedTelegramBot
from egyptian_sites_scraper import EgyptianSitesScraper
from migrate_json_to_sqlite import JSONToSQLiteMigrator
from enhanced_amz_scraper import DatabaseManager

# إعداد الـ logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_deal_analyzer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AIDealsAnalyzerApp:
    """التطبيق الرئيسي لنظام تحليل العروض بالذكاء الاصطناعي"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.app_name = "AI-Enhanced Amazon Deal Analyzer"
        logger.info(f"Starting {self.app_name} v{self.version}")
    
    def print_banner(self):
        """طباعة شعار التطبيق"""
        banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🤖 AI-Enhanced Amazon Deal Analyzer v{self.version}           ║
║                                                              ║
║    نظام ذكي لتحليل العروض ومقارنة الأسعار                     ║
║    باستخدام الذكاء الاصطناعي والتعلم الآلي                   ║
║                                                              ║
║    المميزات:                                                 ║
║    • تحليل AI للعروض الحقيقية vs الوهمية                     ║
║    • مقارنة الأسعار عبر المواقع المصرية                      ║
║    • بوت تليجرام ذكي مع تقارير يومية                        ║
║    • واجهة مستخدم احترافية مع لوحة تحكم                      ║
║    • قاعدة بيانات محسنة مع 300K+ منتج                       ║
║                                                              ║
║    تم التطوير بـ ❤️ للسوق المصري                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def check_requirements(self):
        """فحص المتطلبات الأساسية"""
        requirements = {
            'google.generativeai': 'Gemini AI',
            'customtkinter': 'GUI Framework',
            'requests': 'HTTP Requests',
            'beautifulsoup4': 'Web Scraping',
            'sqlite3': 'Database',
            'pandas': 'Data Analysis',
            'matplotlib': 'Visualization'
        }
        
        missing = []
        for module, description in requirements.items():
            try:
                __import__(module)
                logger.info(f"✅ {description}: OK")
            except ImportError:
                missing.append((module, description))
                logger.error(f"❌ {description}: Missing")
        
        if missing:
            print("\\n⚠️  Missing Dependencies:")
            for module, desc in missing:
                print(f"   • {desc} ({module})")
            print("\\n📦 Install with: pip install -r requirements.txt\\n")
            return False
        
        logger.info("✅ All requirements satisfied")
        return True
    
    def run_gui_mode(self):
        """تشغيل الواجهة الرسومية"""
        try:
            logger.info("Starting GUI mode...")
            app = AIEnhancedGUI()
            app.run()
        except Exception as e:
            logger.error(f"GUI mode error: {e}")
            return False
        return True
    
    def run_cli_analysis(self, api_key: str, max_deals: int = 10, min_score: float = 7.0):
        """تشغيل تحليل AI من سطر الأوامر"""
        try:
            logger.info("Starting CLI analysis mode...")
            
            # تهيئة نظام AI
            ai_analyzer = AIAnalyzer(api_key)
            deal_filter = DealQualityFilter(ai_analyzer)
            
            # تحليل العروض
            logger.info(f"Analyzing up to {max_deals} deals with minimum score {min_score}")
            deals = deal_filter.filter_high_quality_deals(min_score, max_deals)
            
            # عرض النتائج
            print(f"\\n🎯 Found {len(deals)} high quality deals:\\n")
            
            for i, deal in enumerate(deals, 1):
                print(f"{i}. {deal['name'][:60]}...")
                print(f"   💰 Price: {int(deal['current_price']):,} EGP")
                print(f"   ⚡ Discount: {deal['discount_percent']:.1f}%")
                print(f"   🤖 AI Score: {deal.get('total_ai_score', 0):.1f}/10")
                print(f"   🔗 URL: {deal.get('url', 'N/A')}")
                print()
            
            return True
            
        except Exception as e:
            logger.error(f"CLI analysis error: {e}")
            return False
    
    def run_telegram_bot(self, api_key: str = None):
        """تشغيل بوت التليجرام"""
        try:
            logger.info("Starting Telegram bot...")
            
            bot = EnhancedTelegramBot()
            
            if api_key:
                bot.init_ai_system(api_key)
            
            # بدء الروتين اليومي
            bot.start_daily_routine()
            
            print("🤖 Telegram bot is running...")
            print("Press Ctrl+C to stop")
            
            # إبقاء البوت يعمل
            import time
            while True:
                time.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("Telegram bot stopped by user")
            return True
        except Exception as e:
            logger.error(f"Telegram bot error: {e}")
            return False
    
    def run_price_search(self, product_name: str):
        """البحث عن أسعار منتج معين"""
        try:
            logger.info(f"Searching prices for: {product_name}")
            
            scraper = EgyptianSitesScraper()
            results = scraper.get_best_prices(product_name)
            
            print(f"\\n🔍 Search Results for: {product_name}\\n")
            print(f"📊 Total Results: {results.get('total_results', 0)}")
            
            if results.get('best_price'):
                best = results['best_price']
                print(f"🏆 Best Price: {int(best['current_price']):,} EGP from {best['site'].title()}")
            
            if results.get('average_price'):
                print(f"📈 Average Price: {int(results['average_price']):,} EGP")
            
            print("\\n🌐 Results by Site:")
            for site, products in results.get('results_by_site', {}).items():
                if products:
                    print(f"\\n{site.upper()}:")
                    for product in products[:3]:
                        print(f"  • {product['name'][:50]}... - {int(product['current_price']):,} EGP")
            
            scraper.cleanup()
            return True
            
        except Exception as e:
            logger.error(f"Price search error: {e}")
            return False
    
    def run_data_migration(self, json_file: str, db_file: str = "amz_products.db", batch_size: int = 1000):
        """تحويل البيانات من JSON إلى SQLite"""
        try:
            logger.info(f"Starting data migration from {json_file} to {db_file}")
            
            migrator = JSONToSQLiteMigrator(json_file, db_file)
            stats = migrator.migrate(batch_size=batch_size)
            
            print("\\n🎉 Migration Completed Successfully!")
            print("="*50)
            print(f"📊 Total Products: {stats.get('total_products', 0):,}")
            print(f"💰 Products with Discount: {stats.get('products_with_discount', 0):,}")
            print(f"📈 Average Discount: {stats.get('average_discount', 0)}%")
            print(f"🏆 Max Discount: {stats.get('max_discount', 0)}%")
            print(f"📜 Price History Records: {stats.get('price_history_records', 0):,}")
            
            print(f"\\n📂 Top Sections:")
            for section, count in stats.get('sections', [])[:5]:
                print(f"   • {section}: {count:,} products")
            
            print(f"\\n💾 Database saved to: {db_file}")
            print("="*50)
            
            return True
            
        except Exception as e:
            logger.error(f"Data migration error: {e}")
            return False
    
    def show_help(self):
        """عرض مساعدة الاستخدام"""
        help_text = f"""
{self.app_name} v{self.version}

الاستخدام:
  python main.py [MODE] [OPTIONS]

الأوضاع المتاحة:
  gui                     تشغيل الواجهة الرسومية (افتراضي)
  analyze                 تحليل AI من سطر الأوامر
  telegram               تشغيل بوت التليجرام
  search                 البحث عن أسعار منتج
  migrate                تحويل JSON إلى SQLite
  help                   عرض هذه المساعدة

خيارات التحليل:
  --api-key KEY          مفتاح Gemini AI API
  --max-deals N          عدد العروض القصوى (افتراضي: 10)
  --min-score SCORE      الحد الأدنى للنقاط (افتراضي: 7.0)

خيارات البحث:
  --product NAME         اسم المنتج للبحث عنه

خيارات التحويل:
  --json-file FILE       ملف JSON المصدر
  --db-file FILE         ملف قاعدة البيانات الهدف
  --batch-size N         حجم الدفعة (افتراضي: 1000)

أمثلة:
  python main.py                                    # واجهة رسومية
  python main.py analyze --api-key YOUR_KEY        # تحليل AI
  python main.py search --product "ماكينة حلاقة"    # البحث عن أسعار
  python main.py migrate --json-file products.json # تحويل البيانات
  python main.py telegram --api-key YOUR_KEY       # بوت تليجرام

للمزيد من المعلومات، راجع README.md
        """
        print(help_text)

def main():
    """الدالة الرئيسية"""
    app = AIDealsAnalyzerApp()
    
    # إعداد معالج الوسائط
    parser = argparse.ArgumentParser(
        description=app.app_name,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'mode', 
        nargs='?', 
        default='gui',
        choices=['gui', 'analyze', 'telegram', 'search', 'migrate', 'help'],
        help='Operation mode'
    )
    
    parser.add_argument('--api-key', help='Gemini AI API key')
    parser.add_argument('--max-deals', type=int, default=10, help='Maximum deals to analyze')
    parser.add_argument('--min-score', type=float, default=7.0, help='Minimum AI score')
    parser.add_argument('--product', help='Product name to search')
    parser.add_argument('--json-file', help='JSON file to migrate')
    parser.add_argument('--db-file', default='amz_products.db', help='Database file')
    parser.add_argument('--batch-size', type=int, default=1000, help='Migration batch size')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # تعديل مستوى الـ logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # طباعة الشعار
    app.print_banner()
    
    # فحص المتطلبات
    if not app.check_requirements():
        sys.exit(1)
    
    # تنفيذ الوضع المطلوب
    success = True
    
    try:
        if args.mode == 'help':
            app.show_help()
        
        elif args.mode == 'gui':
            success = app.run_gui_mode()
        
        elif args.mode == 'analyze':
            if not args.api_key:
                logger.error("API key required for analysis mode")
                success = False
            else:
                success = app.run_cli_analysis(args.api_key, args.max_deals, args.min_score)
        
        elif args.mode == 'telegram':
            success = app.run_telegram_bot(args.api_key)
        
        elif args.mode == 'search':
            if not args.product:
                logger.error("Product name required for search mode")
                success = False
            else:
                success = app.run_price_search(args.product)
        
        elif args.mode == 'migrate':
            if not args.json_file:
                logger.error("JSON file required for migration mode")
                success = False
            else:
                success = app.run_data_migration(args.json_file, args.db_file, args.batch_size)
    
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        success = True
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        success = False
    
    # الخروج
    if success:
        logger.info("Application completed successfully")
        sys.exit(0)
    else:
        logger.error("Application completed with errors")
        sys.exit(1)

if __name__ == "__main__":
    main()