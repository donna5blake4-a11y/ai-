import requests
import json
import asyncio
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from ai_price_analyzer import AIPriceAnalyzer
from enhanced_database import EnhancedDatabaseManager, Product

logger = logging.getLogger(__name__)

class EnhancedTelegramBot:
    """بوت تليجرام محسن مع دعم AI"""
    
    def __init__(self, config_file: str = "telegram_config.json"):
        self.config = self._load_config(config_file)
        self.bot_token = self.config.get("bot_token", "")
        self.users = self.config.get("users", [])
        self.ai_analyzer = AIPriceAnalyzer()
        self.db_manager = EnhancedDatabaseManager()
        self.sent_deals = set()  # لتجنب إرسال نفس العرض مرتين
        self.daily_limit = 15  # حد العروض اليومية
        self.sent_today = 0
        self.last_reset = datetime.now().date()
        
        # إعدادات AI
        self.ai_enabled = True
        self.min_ai_confidence = 0.7
        self.verified_only = True  # إرسال العروض المصدقة فقط
        
        logger.info("🤖 Enhanced Telegram Bot initialized with AI support")
    
    def _load_config(self, config_file: str) -> dict:
        """تحميل إعدادات البوت"""
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {"bot_token": "", "users": []}
    
    def _reset_daily_counter(self):
        """إعادة تعيين العداد اليومي"""
        today = datetime.now().date()
        if today > self.last_reset:
            self.sent_today = 0
            self.last_reset = today
            self.sent_deals.clear()
            logger.info("🔄 Daily counter reset")
    
    def send_ai_enhanced_alert(self, product: Product, analysis_data: dict) -> bool:
        """إرسال تنبيه محسن مع تحليل AI"""
        try:
            self._reset_daily_counter()
            
            # التحقق من الحد اليومي
            if self.sent_today >= self.daily_limit:
                logger.info(f"📊 Daily limit reached ({self.daily_limit})")
                return False
            
            # تجنب إرسال نفس العرض مرتين
            deal_key = f"{product.asin}_{product.current_price}"
            if deal_key in self.sent_deals:
                return False
            
            # إنشاء الرسالة المحسنة
            message = self._create_ai_enhanced_message(product, analysis_data)
            
            # إرسال الرسالة
            success = self._send_message_to_all_users(message, product.img)
            
            if success:
                self.sent_today += 1
                self.sent_deals.add(deal_key)
                logger.info(f"✅ AI Alert sent ({self.sent_today}/{self.daily_limit})")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending AI alert: {e}")
            return False
    
    def _create_ai_enhanced_message(self, product: Product, analysis_data: dict) -> str:
        """إنشاء رسالة محسنة مع تحليل AI"""
        
        # العنوان الرئيسي
        if analysis_data.get('is_good_deal', False):
            if analysis_data.get('confidence_score', 0) >= 0.9:
                headline = "🎯 <b>AI VERIFIED - EXCELLENT DEAL!</b> 🎯"
            else:
                headline = "✅ <b>AI VERIFIED - GOOD DEAL!</b> ✅"
        else:
            headline = "⚠️ <b>AI ANALYSIS - REGULAR OFFER</b> ⚠️"
        
        # معلومات المنتج الأساسية
        product_name = product.name[:100] + "..." if len(product.name) > 100 else product.name
        price_now = f"<b>{int(product.current_price):,} EGP</b>"
        
        # معلومات الخصم
        discount_info = ""
        if product.strike_price and product.strike_price > product.current_price:
            price_strike = f"<s>{int(product.strike_price):,} EGP</s>"
            discount_info = f"💰 {price_strike} → {price_now}\n⚡ <b>Discount:</b> <code>{product.discount_percent:.1f}%</code>"
        else:
            discount_info = f"💰 {price_now}"
        
        # تحليل AI
        ai_analysis = ""
        if analysis_data:
            confidence = analysis_data.get('confidence_score', 0)
            market_avg = analysis_data.get('market_average', 0)
            best_alt = analysis_data.get('best_alternative_price', 0)
            best_site = analysis_data.get('best_alternative_website', 'Unknown')
            price_diff = analysis_data.get('price_difference_percent', 0)
            
            ai_analysis = f"""
🤖 <b>AI Market Analysis:</b>

📊 <b>Market Average:</b> <code>{market_avg:,.0f} EGP</code>
🏪 <b>Best Alternative:</b> <code>{best_alt:,.0f} EGP</code> ({best_site})
💡 <b>Price Difference:</b> <code>{price_diff:+.1f}%</code>
🎯 <b>AI Confidence:</b> <code>{confidence:.1f}</code>
"""
            
            # التوصيات
            recommendations = analysis_data.get('recommendations', [])
            if recommendations:
                ai_analysis += "\n💡 <b>AI Recommendations:</b>\n"
                for rec in recommendations[:3]:  # أول 3 توصيات فقط
                    ai_analysis += f"• {rec}\n"
        
        # روابط مفيدة
        kanbkam_url = f"https://www.kanbkam.com/eg/ar/search/l?q={product.url}"
        
        # تجميع الرسالة
        message = f"""{headline}

<b>{product_name}</b>

🔗 <a href="{product.url}">Open on Amazon</a>
📦 <b>Section:</b> <code>{product.section}</code>

{discount_info}
{ai_analysis}
📊 <b>Price History:</b> <a href="{kanbkam_url}">View on Kanbkam</a>

🕒 <i>Analyzed at {datetime.now().strftime('%H:%M')}</i>
"""
        
        return message
    
    def _send_message_to_all_users(self, message: str, image_url: str = None) -> bool:
        """إرسال الرسالة لجميع المستخدمين"""
        success_count = 0
        
        for user_id in self.users:
            try:
                if image_url:
                    response = requests.post(
                        f"https://api.telegram.org/bot{self.bot_token}/sendPhoto",
                        data={
                            "chat_id": user_id,
                            "photo": image_url,
                            "caption": message,
                            "parse_mode": "HTML"
                        },
                        timeout=15
                    )
                else:
                    response = requests.post(
                        f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                        data={
                            "chat_id": user_id,
                            "text": message,
                            "parse_mode": "HTML"
                        },
                        timeout=15
                    )
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    logger.warning(f"Failed to send to user {user_id}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
        
        return success_count > 0
    
    def send_daily_summary(self) -> bool:
        """إرسال ملخص يومي للعروض"""
        try:
            # الحصول على أفضل العروض من اليوم
            today = datetime.now().date()
            deals = self.db_manager.get_deals(min_discount=25, limit=10, verified_only=True)
            
            if not deals:
                return False
            
            # إنشاء ملخص
            summary = self._create_daily_summary(deals)
            
            # إرسال الملخص
            return self._send_message_to_all_users(summary)
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return False
    
    def _create_daily_summary(self, deals: List[Product]) -> str:
        """إنشاء ملخص يومي"""
        
        summary = f"""📊 <b>Daily AI Deals Summary</b> 📊

📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}
🎯 <b>AI Verified Deals:</b> {len(deals)}

<b>Top Deals Today:</b>

"""
        
        for i, deal in enumerate(deals[:5], 1):
            discount_emoji = "🔥" if deal.discount_percent >= 50 else "✨" if deal.discount_percent >= 30 else "💸"
            ai_score = deal.ai_score or 0
            ai_emoji = "🎯" if ai_score >= 0.8 else "✅" if ai_score >= 0.6 else "⚠️"
            
            summary += f"""{i}. {discount_emoji} <b>{deal.name[:60]}...</b>
   💰 <code>{int(deal.current_price):,} EGP</code> (-{deal.discount_percent:.1f}%)
   {ai_emoji} AI Score: <code>{ai_score:.1f}</code>
   🔗 <a href="{deal.url}">View Deal</a>

"""
        
        summary += f"""
📈 <b>Today's Stats:</b>
• Deals Sent: {self.sent_today}/{self.daily_limit}
• AI Confidence: {sum(d.ai_score or 0 for d in deals) / len(deals):.1f}
• Average Discount: {sum(d.discount_percent for d in deals) / len(deals):.1f}%

🎯 <i>All deals verified by AI for market competitiveness</i>
"""
        
        return summary
    
    def analyze_and_send_deals(self, limit: int = 5) -> int:
        """تحليل وإرسال أفضل العروض"""
        try:
            # الحصول على العروض المخفضة
            deals = self.db_manager.get_deals(min_discount=25, limit=limit * 2, verified_only=False)
            
            sent_count = 0
            
            for deal in deals:
                # التحقق من الحد اليومي
                if self.sent_today >= self.daily_limit:
                    break
                
                # تحليل AI
                if self.ai_enabled:
                    product_data = {
                        'name': deal.name,
                        'price': deal.current_price,
                        'discount_percent': deal.discount_percent
                    }
                    
                    analysis = self.ai_analyzer.analyze_deal(product_data)
                    
                    # حفظ تحليل AI
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
                    
                    self.db_manager.save_ai_analysis(deal.asin, analysis_data)
                    
                    # إرسال فقط إذا كان العرض جيد ودرجة الثقة عالية
                    if (analysis.is_good_deal and 
                        analysis.confidence_score >= self.min_ai_confidence):
                        
                        if self.send_ai_enhanced_alert(deal, analysis_data):
                            sent_count += 1
                            logger.info(f"✅ Sent AI-verified deal: {deal.name[:50]}...")
                        
                        # إيقاف مؤقت لتجنب حظر IP
                        threading.Event().wait(2)
                
                else:
                    # إرسال بدون تحليل AI
                    if self.send_ai_enhanced_alert(deal, {}):
                        sent_count += 1
            
            logger.info(f"📤 Sent {sent_count} AI-verified deals")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error analyzing and sending deals: {e}")
            return 0
    
    def get_bot_stats(self) -> dict:
        """الحصول على إحصائيات البوت"""
        return {
            'sent_today': self.sent_today,
            'daily_limit': self.daily_limit,
            'ai_enabled': self.ai_enabled,
            'verified_only': self.verified_only,
            'min_ai_confidence': self.min_ai_confidence,
            'total_users': len(self.users),
            'last_reset': self.last_reset.isoformat()
        }
    
    def update_settings(self, **kwargs):
        """تحديث إعدادات البوت"""
        if 'daily_limit' in kwargs:
            self.daily_limit = kwargs['daily_limit']
        if 'ai_enabled' in kwargs:
            self.ai_enabled = kwargs['ai_enabled']
        if 'verified_only' in kwargs:
            self.verified_only = kwargs['verified_only']
        if 'min_ai_confidence' in kwargs:
            self.min_ai_confidence = kwargs['min_ai_confidence']
        
        logger.info(f"Bot settings updated: {kwargs}")

# دوال مساعدة للتوافق مع الكود القديم
def send_telegram_alert(item: dict, old_price: float, new_price: float, 
                       discount_percent: float, drop_detected: bool) -> bool:
    """دالة التوافق مع الكود القديم"""
    try:
        bot = EnhancedTelegramBot()
        
        # تحويل البيانات إلى نموذج Product
        product = Product(
            asin=item.get('asin', ''),
            name=item.get('name', ''),
            url=item.get('url', ''),
            img=item.get('img', ''),
            section=item.get('section', ''),
            current_price=new_price,
            strike_price=old_price,
            discount_percent=discount_percent,
            last_updated=datetime.now(),
            created_at=datetime.now()
        )
        
        # تحليل AI
        product_data = {
            'name': product.name,
            'price': product.current_price,
            'discount_percent': product.discount_percent
        }
        
        analysis = bot.ai_analyzer.analyze_deal(product_data)
        
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
        
        return bot.send_ai_enhanced_alert(product, analysis_data)
        
    except Exception as e:
        logger.error(f"Error in send_telegram_alert: {e}")
        return False

def send_summary_report() -> bool:
    """إرسال تقرير ملخص"""
    try:
        bot = EnhancedTelegramBot()
        return bot.send_daily_summary()
    except Exception as e:
        logger.error(f"Error in send_summary_report: {e}")
        return False

# مثال للاستخدام
if __name__ == "__main__":
    # إنشاء البوت
    bot = EnhancedTelegramBot()
    
    # عرض الإحصائيات
    stats = bot.get_bot_stats()
    print(f"Bot Stats: {stats}")
    
    # تحليل وإرسال العروض
    sent_count = bot.analyze_and_send_deals(limit=3)
    print(f"Sent {sent_count} deals")
    
    # إرسال ملخص يومي
    bot.send_daily_summary()