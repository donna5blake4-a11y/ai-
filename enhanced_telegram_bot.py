# enhanced_telegram_bot.py
import requests
import json
import sqlite3
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import threading
import time
from ai_price_analyzer import AIAnalyzer, DealQualityFilter

# إعداد الـ logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedTelegramBot:
    """بوت تليجرام محسن مع تقارير AI وتحليلات ذكية"""
    
    def __init__(self, config_file: str = "telegram_config.json", db_file: str = "amz_products.db"):
        self.config_file = config_file
        self.db_file = db_file
        self.config = self.load_config()
        self.bot_token = self.config.get("bot_token")
        self.users = self.config.get("users", [])
        self.ai_analyzer = None
        self.deal_filter = None
        
        # إعدادات التقارير
        self.daily_report_sent = False
        self.last_report_date = None
        
    def load_config(self) -> Dict:
        """تحميل إعدادات البوت"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {"bot_token": "", "users": []}
    
    def init_ai_system(self, api_key: str):
        """تهيئة نظام AI"""
        try:
            self.ai_analyzer = AIAnalyzer(api_key)
            self.deal_filter = DealQualityFilter(self.ai_analyzer, self.db_file)
            logger.info("AI system initialized successfully")
        except Exception as e:
            logger.error(f"AI system initialization error: {e}")
    
    def send_message(self, user_id: str, text: str, parse_mode: str = "HTML", 
                    reply_markup: Optional[Dict] = None) -> bool:
        """إرسال رسالة نصية"""
        try:
            data = {
                "chat_id": user_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                data=data,
                timeout=15
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def send_photo(self, user_id: str, photo_url: str, caption: str = "", 
                   reply_markup: Optional[Dict] = None) -> bool:
        """إرسال صورة مع تعليق"""
        try:
            data = {
                "chat_id": user_id,
                "photo": photo_url,
                "caption": caption,
                "parse_mode": "HTML"
            }
            
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendPhoto",
                data=data,
                timeout=15
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            return False
    
    def send_ai_verified_deal(self, deal: Dict) -> bool:
        """إرسال عرض تم التحقق منه بواسطة AI"""
        try:
            product_name = deal.get('name', 'Unknown Product')
            current_price = deal.get('current_price', 0)
            strike_price = deal.get('strike_price', 0)
            discount_percent = deal.get('discount_percent', 0)
            section = deal.get('section', 'Unknown')
            url = deal.get('url', '')
            img_url = deal.get('img', '')
            ai_score = deal.get('total_ai_score', 0)
            
            # تحليل AI
            ai_analysis = deal.get('ai_analysis', {})
            deal_type = ai_analysis.get('deal_type', 'غير محدد')
            recommendation = ai_analysis.get('recommendation', 'لا توجد توصية')
            
            # مقارنة الأسعار
            comparison_analysis = deal.get('comparison_analysis', {})
            comparison_verdict = comparison_analysis.get('verdict', 'غير متاح')\n            amazon_rank = comparison_analysis.get('amazon_rank', 'غير محدد')
            
            # تحديد أيقونة ولون العرض حسب النقاط
            if ai_score >= 9:
                headline = "🌟 <b>VERIFIED PREMIUM DEAL</b> 🌟"
                score_emoji = "🏆"
            elif ai_score >= 8:
                headline = "✨ <b>AI VERIFIED DEAL</b> ✨"
                score_emoji = "🥇"
            elif ai_score >= 7:
                headline = "🎯 <b>GOOD VERIFIED DEAL</b> 🎯"
                score_emoji = "🥈"
            else:
                headline = "📊 <b>ANALYZED DEAL</b> 📊"
                score_emoji = "📈"
            
            # تنسيق الأسعار
            price_strike = f"<s>{int(strike_price):,} EGP</s>" if strike_price else ""
            price_now = f"<b>{int(current_price):,} EGP</b>"
            price_row = f"💰 {price_strike} → {price_now}" if price_strike else f"💰 {price_now}"
            
            # مقارنة الأسعار
            price_comparison_text = ""
            if deal.get('price_comparison'):
                price_comparison_text = "\\n\\n🔍 <b>مقارنة الأسعار:</b>\\n"
                for comp in deal['price_comparison'][:3]:  # أول 3 مواقع
                    site_price = comp['price']
                    site_name = comp['site'].title()
                    if site_price > current_price:
                        savings = site_price - current_price
                        price_comparison_text += f"• {site_name}: {int(site_price):,} EGP (توفر {int(savings):,} جنيه)\\n"
                    else:
                        price_comparison_text += f"• {site_name}: {int(site_price):,} EGP\\n"
            
            # إنشاء الرسالة
            msg = f"""{headline}

<b>{product_name}</b>

🔗 <a href="{url}">عرض المنتج على أمازون</a>
📦 <b>القسم:</b> <code>{section}</code>

{price_row}
⚡ <b>الخصم:</b> <code>{discount_percent:.1f}%</code>

{score_emoji} <b>نقاط AI:</b> <code>{ai_score:.1f}/10</code>
🎯 <b>نوع العرض:</b> <code>{deal_type}</code>
🏅 <b>ترتيب أمازون:</b> <code>{amazon_rank}</code>

🤖 <b>تحليل AI:</b>
<i>{recommendation}</i>

🔍 <b>حكم المقارنة:</b>
<i>{comparison_verdict}</i>{price_comparison_text}

⏰ <b>تم التحقق:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
            
            # أزرار التفاعل
            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": "🛍️ شراء من أمازون", "url": url},
                        {"text": "📊 مقارنة الأسعار", "callback_data": f"compare_{deal['asin']}"}
                    ],
                    [
                        {"text": "❤️ حفظ العرض", "callback_data": f"save_{deal['asin']}"},
                        {"text": "🔔 تنبيه عند انخفاض السعر", "callback_data": f"alert_{deal['asin']}"}
                    ]
                ]
            }
            
            # إرسال للجميع
            success_count = 0
            for user_id in self.users:
                if img_url:
                    if self.send_photo(user_id, img_url, msg, reply_markup):
                        success_count += 1
                else:
                    if self.send_message(user_id, msg, reply_markup=reply_markup):
                        success_count += 1
                
                # تأخير بين الإرسالات
                time.sleep(0.5)
            
            logger.info(f"AI verified deal sent to {success_count}/{len(self.users)} users: {product_name[:50]}...")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending AI verified deal: {e}")
            return False
    
    def send_daily_summary_report(self) -> bool:
        """إرسال تقرير يومي مفصل"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # إحصائيات اليوم
            today = datetime.now().strftime('%Y-%m-%d')
            
            # إجمالي المنتجات
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]
            
            # المنتجات التي تم تحليلها بـ AI اليوم
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE ai_verified = TRUE 
                AND date(last_updated) = ?
            """, (today,))
            ai_analyzed_today = cursor.fetchone()[0]
            
            # أفضل العروض (AI Score >= 7)
            cursor.execute("""
                SELECT name, current_price, discount_percent, ai_score, section
                FROM products 
                WHERE ai_score >= 7 
                ORDER BY ai_score DESC, discount_percent DESC 
                LIMIT 10
            """)
            top_deals = cursor.fetchall()
            
            # إحصائيات الأقسام
            cursor.execute("""
                SELECT section, COUNT(*), AVG(ai_score)
                FROM products 
                WHERE ai_verified = TRUE AND ai_score > 0
                GROUP BY section 
                ORDER BY AVG(ai_score) DESC 
                LIMIT 5
            """)
            section_stats = cursor.fetchall()
            
            # متوسط النقاط
            cursor.execute("SELECT AVG(ai_score) FROM products WHERE ai_score > 0")
            avg_score = cursor.fetchone()[0] or 0
            
            conn.close()
            
            # إنشاء التقرير
            report = f"""📊 <b>التقرير اليومي - {today}</b> 📊

🔍 <b>إحصائيات عامة:</b>
• إجمالي المنتجات: {total_products:,}
• تم تحليلها بـ AI اليوم: {ai_analyzed_today:,}
• متوسط نقاط AI: {avg_score:.1f}/10

🏆 <b>أفضل العروض المتاحة:</b>
"""
            
            for i, (name, price, discount, score, section) in enumerate(top_deals[:5], 1):
                report += f"{i}. {name[:40]}...\n"
                report += f"   💰 {int(price):,} EGP | ⚡ {discount:.1f}% | 🎯 {score:.1f}/10\n"
                report += f"   📦 {section}\n\n"
            
            report += "📈 <b>أفضل الأقسام (حسب جودة العروض):</b>\n"
            for section, count, avg_score_section in section_stats:
                report += f"• {section}: {count} منتج | متوسط النقاط: {avg_score_section:.1f}\n"
            
            report += f"\n⏰ <b>تم إنشاء التقرير:</b> {datetime.now().strftime('%H:%M')}"
            report += "\n\n🤖 <i>تم إنشاء هذا التقرير تلقائياً بواسطة نظام AI</i>"
            
            # إرسال التقرير
            success_count = 0
            for user_id in self.users:
                if self.send_message(user_id, report):
                    success_count += 1
                time.sleep(0.5)
            
            logger.info(f"Daily report sent to {success_count}/{len(self.users)} users")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
            return False
    
    def send_price_alert(self, product: Dict, old_price: float, new_price: float) -> bool:
        """إرسال تنبيه انخفاض السعر"""
        try:
            product_name = product.get('name', 'Unknown Product')
            url = product.get('url', '')
            img_url = product.get('img', '')
            
            price_drop = old_price - new_price
            drop_percent = (price_drop / old_price) * 100 if old_price > 0 else 0
            
            msg = f"""🚨 <b>تنبيه انخفاض السعر!</b> 🚨

<b>{product_name}</b>

💰 السعر السابق: <s>{int(old_price):,} EGP</s>
💰 السعر الجديد: <b>{int(new_price):,} EGP</b>
📉 الانخفاض: <b>{int(price_drop):,} EGP ({drop_percent:.1f}%)</b>

🔗 <a href="{url}">اشتري الآن</a>

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
            
            reply_markup = {
                "inline_keyboard": [
                    [{"text": "🛍️ شراء فوراً", "url": url}]
                ]
            }
            
            success_count = 0
            for user_id in self.users:
                if img_url:
                    if self.send_photo(user_id, img_url, msg, reply_markup):
                        success_count += 1
                else:
                    if self.send_message(user_id, msg, reply_markup=reply_markup):
                        success_count += 1
                time.sleep(0.5)
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending price alert: {e}")
            return False
    
    def process_ai_deals(self, max_deals: int = 10, min_score: float = 7.0):
        """معالجة وإرسال العروض المحللة بـ AI"""
        try:
            if not self.deal_filter:
                logger.error("AI system not initialized")
                return
            
            # الحصول على العروض عالية الجودة
            high_quality_deals = self.deal_filter.filter_high_quality_deals(
                min_score=min_score, 
                max_deals=max_deals
            )
            
            logger.info(f"Found {len(high_quality_deals)} high quality deals")
            
            # إرسال العروض
            sent_count = 0
            for deal in high_quality_deals:
                if self.send_ai_verified_deal(deal):
                    sent_count += 1
                    # تأخير بين العروض
                    time.sleep(2)
            
            logger.info(f"Sent {sent_count} AI verified deals")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error processing AI deals: {e}")
            return 0
    
    def start_daily_routine(self):
        """بدء الروتين اليومي للبوت"""
        def daily_routine():
            while True:
                try:
                    current_time = datetime.now()
                    current_date = current_time.strftime('%Y-%m-%d')
                    
                    # إرسال التقرير اليومي (مرة واحدة في اليوم في الساعة 9 صباحاً)
                    if (current_time.hour == 9 and 
                        current_time.minute == 0 and 
                        self.last_report_date != current_date):
                        
                        self.send_daily_summary_report()
                        self.last_report_date = current_date
                    
                    # معالجة العروض كل 30 دقيقة
                    if current_time.minute % 30 == 0:
                        self.process_ai_deals(max_deals=5, min_score=7.0)
                    
                    # انتظار دقيقة واحدة
                    time.sleep(60)
                    
                except Exception as e:
                    logger.error(f"Daily routine error: {e}")
                    time.sleep(60)
        
        # تشغيل الروتين في thread منفصل
        routine_thread = threading.Thread(target=daily_routine, daemon=True)
        routine_thread.start()
        logger.info("Daily routine started")

# دالة للتوافق مع الكود القديم
def send_telegram_alert(item, old_price, new_price, discount_percent, drop_detected):
    """دالة للتوافق مع النظام القديم"""
    try:
        bot = EnhancedTelegramBot()
        
        if drop_detected:
            return bot.send_price_alert(item, old_price, new_price)
        else:
            # تحويل للتنسيق الجديد
            deal_data = {
                'name': item.get('name', ''),
                'current_price': new_price,
                'strike_price': old_price if old_price > new_price else None,
                'discount_percent': discount_percent,
                'section': item.get('section', ''),
                'url': item.get('url', ''),
                'img': item.get('img', ''),
                'asin': item.get('asin', ''),
                'total_ai_score': min(discount_percent / 10, 10),  # تقدير بسيط
                'ai_analysis': {
                    'deal_type': 'تقليدي',
                    'recommendation': 'عرض عادي'
                },
                'comparison_analysis': {
                    'verdict': 'غير متاح',
                    'amazon_rank': 'غير محدد'
                }
            }
            return bot.send_ai_verified_deal(deal_data)
            
    except Exception as e:
        logger.error(f"Legacy alert error: {e}")
        return False

def send_summary_report():
    """دالة للتوافق مع النظام القديم"""
    try:
        bot = EnhancedTelegramBot()
        return bot.send_daily_summary_report()
    except Exception as e:
        logger.error(f"Legacy summary report error: {e}")
        return False

if __name__ == "__main__":
    # اختبار البوت
    bot = EnhancedTelegramBot()
    
    # تهيئة نظام AI (ضع مفتاح API الحقيقي)
    API_KEY = "YOUR_GEMINI_API_KEY_HERE"
    bot.init_ai_system(API_KEY)
    
    # بدء الروتين اليومي
    bot.start_daily_routine()
    
    # اختبار إرسال تقرير
    bot.send_daily_summary_report()
    
    print("Enhanced Telegram Bot is running...")
    
    # إبقاء البرنامج يعمل
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Bot stopped.")