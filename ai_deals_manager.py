#!/usr/bin/env python3
"""
AI Deals Manager - نظام إدارة العروض الذكي
دمج AI مع نظام تتبع العروض لتحسين جودة التنبيهات
"""

import asyncio
import threading
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import schedule

from ai_price_analyzer import AIPriceAnalyzer
from enhanced_database import EnhancedDatabaseManager, Product
from enhanced_telegram_bot import EnhancedTelegramBot

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_deals.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIDealsManager:
    """مدير العروض الذكي مع دعم AI"""
    
    def __init__(self, config_file: str = "ai_config.json"):
        self.config = self._load_config(config_file)
        self.db_manager = EnhancedDatabaseManager()
        self.ai_analyzer = AIPriceAnalyzer()
        self.telegram_bot = EnhancedTelegramBot()
        
        # إعدادات النظام
        self.analysis_interval = self.config.get('analysis_interval', 30)  # دقائق
        self.daily_limit = self.config.get('daily_limit', 15)
        self.min_discount = self.config.get('min_discount', 25)
        self.min_ai_confidence = self.config.get('min_ai_confidence', 0.7)
        self.verified_only = self.config.get('verified_only', True)
        
        # حالة النظام
        self.is_running = False
        self.last_analysis = None
        self.stats = {
            'total_analyzed': 0,
            'good_deals_found': 0,
            'deals_sent': 0,
            'ai_errors': 0,
            'start_time': datetime.now()
        }
        
        logger.info("🚀 AI Deals Manager initialized")
    
    def _load_config(self, config_file: str) -> dict:
        """تحميل الإعدادات"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # إعدادات افتراضية
            default_config = {
                'analysis_interval': 30,
                'daily_limit': 15,
                'min_discount': 25,
                'min_ai_confidence': 0.7,
                'verified_only': True,
                'sites_to_check': ['jumia', 'noon', 'amazon_eg'],
                'auto_migrate_json': True
            }
            
            # حفظ الإعدادات الافتراضية
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created default config: {config_file}")
            return default_config
    
    def migrate_json_data(self, json_file: str = "amz_products.json") -> bool:
        """نقل البيانات من JSON إلى قاعدة البيانات"""
        try:
            logger.info(f"🔄 Starting JSON migration from {json_file}")
            
            success = self.db_manager.migrate_from_json(json_file)
            
            if success:
                stats = self.db_manager.get_database_stats()
                logger.info(f"✅ Migration completed: {stats['total_products']} products imported")
                return True
            else:
                logger.error("❌ Migration failed")
                return False
                
        except Exception as e:
            logger.error(f"Migration error: {e}")
            return False
    
    def analyze_product_with_ai(self, product: Product) -> Optional[Dict]:
        """تحليل منتج واحد باستخدام AI"""
        try:
            product_data = {
                'name': product.name,
                'price': product.current_price,
                'discount_percent': product.discount_percent
            }
            
            analysis = self.ai_analyzer.analyze_deal(product_data)
            
            # تحويل التحليل إلى dict
            analysis_data = {
                'market_average': analysis.market_average,
                'best_alternative_price': analysis.best_alternative_price,
                'best_alternative_website': analysis.best_alternative_website,
                'price_difference': analysis.price_difference,
                'price_difference_percent': analysis.price_difference_percent,
                'confidence_score': analysis.confidence_score,
                'is_good_deal': analysis.is_good_deal,
                'recommendations': analysis.recommendations,
                'analysis_summary': analysis.analysis_summary
            }
            
            # حفظ التحليل في قاعدة البيانات
            self.db_manager.save_ai_analysis(product.asin, analysis_data)
            
            self.stats['total_analyzed'] += 1
            
            if analysis.is_good_deal:
                self.stats['good_deals_found'] += 1
                logger.info(f"🎯 Good deal found: {product.name[:50]}... (AI Score: {analysis.confidence_score:.2f})")
            
            return analysis_data
            
        except Exception as e:
            self.stats['ai_errors'] += 1
            logger.error(f"AI analysis error for {product.asin}: {e}")
            return None
    
    def process_deals_batch(self, limit: int = 10) -> int:
        """معالجة دفعة من العروض"""
        try:
            # الحصول على العروض المخفضة
            deals = self.db_manager.get_deals(
                min_discount=self.min_discount,
                limit=limit * 2,  # جلب ضعف العدد للتحليل
                verified_only=False
            )
            
            if not deals:
                logger.info("No deals to process")
                return 0
            
            logger.info(f"📊 Processing {len(deals)} deals...")
            
            sent_count = 0
            
            for deal in deals:
                # التحقق من حد البوت اليومي
                if self.telegram_bot.sent_today >= self.daily_limit:
                    logger.info(f"📊 Daily limit reached ({self.daily_limit})")
                    break
                
                # تحليل AI
                analysis_data = self.analyze_product_with_ai(deal)
                
                if analysis_data:
                    # إرسال فقط إذا كان العرض جيد ودرجة الثقة عالية
                    if (analysis_data['is_good_deal'] and 
                        analysis_data['confidence_score'] >= self.min_ai_confidence):
                        
                        if self.telegram_bot.send_ai_enhanced_alert(deal, analysis_data):
                            sent_count += 1
                            self.stats['deals_sent'] += 1
                            logger.info(f"✅ Sent AI-verified deal: {deal.name[:50]}...")
                        
                        # إيقاف مؤقت لتجنب حظر IP
                        time.sleep(2)
                
                else:
                    # إذا فشل تحليل AI، إرسال بدون تحليل
                    if not self.verified_only:
                        if self.telegram_bot.send_ai_enhanced_alert(deal, {}):
                            sent_count += 1
                            self.stats['deals_sent'] += 1
            
            logger.info(f"📤 Processed batch: {sent_count} deals sent")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error processing deals batch: {e}")
            return 0
    
    def run_continuous_analysis(self):
        """تشغيل التحليل المستمر"""
        self.is_running = True
        logger.info("🔄 Starting continuous AI analysis...")
        
        while self.is_running:
            try:
                # معالجة دفعة من العروض
                sent_count = self.process_deals_batch(limit=5)
                
                # تحديث آخر تحليل
                self.last_analysis = datetime.now()
                
                # عرض الإحصائيات
                self.print_stats()
                
                # انتظار حتى التحليل التالي
                logger.info(f"⏰ Waiting {self.analysis_interval} minutes until next analysis...")
                time.sleep(self.analysis_interval * 60)
                
            except KeyboardInterrupt:
                logger.info("🛑 Stopping continuous analysis...")
                break
            except Exception as e:
                logger.error(f"Error in continuous analysis: {e}")
                time.sleep(60)  # انتظار دقيقة قبل المحاولة مرة أخرى
        
        self.is_running = False
    
    def run_single_analysis(self, limit: int = 10) -> int:
        """تشغيل تحليل واحد"""
        try:
            logger.info(f"🔍 Running single AI analysis (limit: {limit})")
            
            sent_count = self.process_deals_batch(limit=limit)
            
            self.last_analysis = datetime.now()
            self.print_stats()
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Error in single analysis: {e}")
            return 0
    
    def print_stats(self):
        """عرض الإحصائيات"""
        runtime = datetime.now() - self.stats['start_time']
        
        print("\n" + "="*60)
        print("📊 AI DEALS MANAGER STATS")
        print("="*60)
        print(f"🕒 Runtime: {runtime}")
        print(f"📈 Total Analyzed: {self.stats['total_analyzed']}")
        print(f"🎯 Good Deals Found: {self.stats['good_deals_found']}")
        print(f"📤 Deals Sent: {self.stats['deals_sent']}")
        print(f"❌ AI Errors: {self.stats['ai_errors']}")
        
        if self.stats['total_analyzed'] > 0:
            success_rate = (self.stats['good_deals_found'] / self.stats['total_analyzed']) * 100
            print(f"📊 Success Rate: {success_rate:.1f}%")
        
        # إحصائيات قاعدة البيانات
        db_stats = self.db_manager.get_database_stats()
        print(f"\n🗄️ Database Stats:")
        print(f"   Total Products: {db_stats.get('total_products', 0):,}")
        print(f"   Discounted: {db_stats.get('discounted_products', 0):,}")
        print(f"   Verified Deals: {db_stats.get('verified_deals', 0):,}")
        
        # إحصائيات البوت
        bot_stats = self.telegram_bot.get_bot_stats()
        print(f"\n🤖 Bot Stats:")
        print(f"   Sent Today: {bot_stats['sent_today']}/{bot_stats['daily_limit']}")
        print(f"   AI Enabled: {bot_stats['ai_enabled']}")
        print(f"   Min Confidence: {bot_stats['min_ai_confidence']}")
        
        if self.last_analysis:
            print(f"   Last Analysis: {self.last_analysis.strftime('%H:%M:%S')}")
        
        print("="*60 + "\n")
    
    def schedule_daily_summary(self):
        """جدولة الملخص اليومي"""
        schedule.every().day.at("20:00").do(self.send_daily_summary)
        logger.info("📅 Daily summary scheduled at 20:00")
    
    def send_daily_summary(self):
        """إرسال الملخص اليومي"""
        try:
            logger.info("📊 Sending daily summary...")
            success = self.telegram_bot.send_daily_summary()
            
            if success:
                logger.info("✅ Daily summary sent successfully")
            else:
                logger.warning("⚠️ Failed to send daily summary")
                
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
    
    def get_top_ai_deals(self, limit: int = 10) -> List[Dict]:
        """الحصول على أفضل العروض المصدقة من AI"""
        try:
            deals = self.db_manager.get_deals(
                min_discount=self.min_discount,
                limit=limit,
                verified_only=True
            )
            
            result = []
            for deal in deals:
                result.append({
                    'asin': deal.asin,
                    'name': deal.name,
                    'price': deal.current_price,
                    'discount': deal.discount_percent,
                    'ai_score': deal.ai_score,
                    'url': deal.url,
                    'analysis': deal.market_comparison
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting top AI deals: {e}")
            return []
    
    def update_settings(self, **kwargs):
        """تحديث إعدادات النظام"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"Updated setting: {key} = {value}")
        
        # تحديث إعدادات البوت
        self.telegram_bot.update_settings(**kwargs)
    
    def stop(self):
        """إيقاف النظام"""
        self.is_running = False
        logger.info("🛑 AI Deals Manager stopped")

def main():
    """الدالة الرئيسية"""
    print("🚀 AI Deals Manager - Starting...")
    
    # إنشاء مدير العروض
    manager = AIDealsManager()
    
    # التحقق من وجود بيانات JSON للنقل
    if manager.config.get('auto_migrate_json', True):
        if manager.migrate_json_data():
            print("✅ JSON data migrated successfully")
        else:
            print("⚠️ JSON migration failed or no JSON file found")
    
    # عرض الإحصائيات الأولية
    manager.print_stats()
    
    # جدولة الملخص اليومي
    manager.schedule_daily_summary()
    
    # تشغيل التحليل المستمر
    try:
        manager.run_continuous_analysis()
    except KeyboardInterrupt:
        print("\n🛑 Stopping AI Deals Manager...")
    finally:
        manager.stop()
        print("👋 AI Deals Manager stopped")

if __name__ == "__main__":
    main()