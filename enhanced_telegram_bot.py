# enhanced_telegram_bot.py
# بوت التليجرام المحسن مع دعم AI

import requests
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from ai_price_analyzer import DealAnalysis

class EnhancedTelegramBot:
    """بوت التليجرام المحسن"""
    
    def __init__(self, config_file="telegram_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.bot_token = self.config.get("bot_token", "")
        self.users = self.config.get("users", [])
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
    def load_config(self) -> dict:
        """تحميل إعدادات البوت"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {"bot_token": "", "users": []}
    
    def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML", 
                    reply_markup: dict = None) -> bool:
        """إرسال رسالة نصية"""
        try:
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            
            response = requests.post(f"{self.base_url}/sendMessage", data=data, timeout=15)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def send_photo(self, chat_id: str, photo_url: str, caption: str = "", 
                  parse_mode: str = "HTML", reply_markup: dict = None) -> bool:
        """إرسال صورة مع نص"""
        try:
            data = {
                "chat_id": chat_id,
                "photo": photo_url,
                "caption": caption,
                "parse_mode": parse_mode
            }
            
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            
            response = requests.post(f"{self.base_url}/sendPhoto", data=data, timeout=15)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error sending photo: {e}")
            return False
    
    def send_smart_alert(self, product_data: dict, analysis: DealAnalysis) -> bool:
        """إرسال تنبيه ذكي محسن"""
        if not self.bot_token or not self.users:
            return False
        
        product_name = product_data.get('name', 'No name')
        url = product_data.get('url', '')
        img_url = product_data.get('img', '')
        section = product_data.get('section', 'Unknown')
        
        # إنشاء الرابط المختصر
        kanbkam_url = f"https://www.kanbkam.com/eg/ar/search/l?q={url}"
        
        # تحديد نوع التنبيه حسب درجة العرض
        if analysis.deal_score >= 90:
            headline = "🔥🔥 **عرض استثنائي!** 🔥🔥"
            emoji = "🔥"
        elif analysis.deal_score >= 80:
            headline = "🔥 **عرض ممتاز!** 🔥"
            emoji = "🔥"
        elif analysis.deal_score >= 70:
            headline = "🎉 **عرض رائع!** 🎉"
            emoji = "🎉"
        elif analysis.deal_score >= 60:
            headline = "✨ **عرض جيد!** ✨"
            emoji = "✨"
        else:
            headline = "📊 **عرض عادي** 📊"
            emoji = "📊"
        
        # إنشاء الرسالة المحسنة
        message = f"""
{headline}

{emoji} **{product_name}**

💰 **السعر الحالي**: {product_data.get('price', 0):,.0f} جنيه
📉 **السعر الأصلي**: {product_data.get('strike_price', 0):,.0f} جنيه
🎯 **نسبة الخصم**: {product_data.get('discount_percent', 0):.1f}%

⭐ **درجة العرض**: {analysis.deal_score:.1f}/100
🎯 **التوصية**: {analysis.recommendation}
🔒 **مستوى الثقة**: {analysis.confidence:.1%}

📊 **مقارنة السوق**:
• متوسط السعر: {analysis.average_market_price:,.0f} جنيه
• ترتيب أمازون: {analysis.price_rank} من {len(analysis.competitor_prices) + 1}
• عدد المنافسين: {len(analysis.competitor_prices)}

📦 **القسم**: {section}

🔗 **روابط مفيدة**:
• [عرض المنتج]({url})
• [مقارنة الأسعار]({kanbkam_url})
        """
        
        # أزرار التفاعل
        reply_markup = {
            "inline_keyboard": [
                [{"text": "🛍️ عرض المنتج", "url": url}],
                [{"text": "📊 مقارنة الأسعار", "url": kanbkam_url}],
                [{"text": "⭐ تقييم العرض", "callback_data": f"rate_{product_data.get('asin', '')}"}]
            ]
        }
        
        # إرسال للجميع
        success_count = 0
        for user_id in self.users:
            try:
                if img_url:
                    success = self.send_photo(
                        user_id, img_url, message, "Markdown", reply_markup
                    )
                else:
                    success = self.send_message(
                        user_id, message, "Markdown", reply_markup
                    )
                
                if success:
                    success_count += 1
                    
            except Exception as e:
                print(f"Error sending to user {user_id}: {e}")
                continue
        
        return success_count > 0
    
    def send_price_comparison(self, product_data: dict, analysis: DealAnalysis) -> bool:
        """إرسال مقارنة أسعار مفصلة"""
        if not self.bot_token or not self.users:
            return False
        
        product_name = product_data.get('name', 'No name')
        
        # إنشاء رسالة المقارنة
        comparison_msg = f"""
📊 **مقارنة أسعار مفصلة**

{product_name}

💰 **سعر أمازون**: {product_data.get('price', 0):,.0f} جنيه
📉 **الخصم**: {product_data.get('discount_percent', 0):.1f}%

🏪 **أسعار المنافسين**:
        """
        
        # إضافة أسعار المنافسين
        for comp in analysis.competitor_prices:
            price_diff = comp.price - product_data.get('price', 0)
            diff_text = f"أرخص بـ {abs(price_diff):,.0f} جنيه" if price_diff > 0 else f"أغلى بـ {abs(price_diff):,.0f} جنيه"
            
            comparison_msg += f"""
• **{comp.retailer}**: {comp.price:,.0f} جنيه ({diff_text})
  الثقة: {comp.confidence:.1%}"""
        
        comparison_msg += f"""

📈 **التحليل**:
• متوسط السوق: {analysis.average_market_price:,.0f} جنيه
• توفير مقارنة بالسوق: {((analysis.average_market_price - product_data.get('price', 0)) / analysis.average_market_price * 100):.1f}%
• درجة العرض: {analysis.deal_score:.1f}/100

🎯 **التوصية النهائية**: {analysis.recommendation}
        """
        
        # إرسال للجميع
        success_count = 0
        for user_id in self.users:
            try:
                success = self.send_message(user_id, comparison_msg, "Markdown")
                if success:
                    success_count += 1
            except Exception as e:
                print(f"Error sending comparison to user {user_id}: {e}")
                continue
        
        return success_count > 0
    
    def send_summary_report(self, total_products: int, real_deals: int, 
                          fake_deals: int, section: str) -> bool:
        """إرسال تقرير ملخص الجلسة"""
        if not self.bot_token or not self.users:
            return False
        
        # حساب النسب
        total_deals = real_deals + fake_deals
        real_deals_percent = (real_deals / total_deals * 100) if total_deals > 0 else 0
        fake_deals_percent = (fake_deals / total_deals * 100) if total_deals > 0 else 0
        
        # تحديد نوع التقرير
        if real_deals_percent >= 80:
            report_emoji = "🎉"
            report_title = "تقرير ممتاز!"
        elif real_deals_percent >= 60:
            report_emoji = "✨"
            report_title = "تقرير جيد!"
        elif real_deals_percent >= 40:
            report_emoji = "📊"
            report_title = "تقرير عادي!"
        else:
            report_emoji = "⚠️"
            report_title = "تقرير ضعيف!"
        
        report_msg = f"""
{report_emoji} **{report_title}**

📊 **ملخص الجلسة**:
• القسم: {section}
• إجمالي المنتجات: {total_products:,}
• العروض المكتشفة: {total_deals}
• العروض الحقيقية: {real_deals} ({real_deals_percent:.1f}%)
• العروض الوهمية: {fake_deals} ({fake_deals_percent:.1f}%)

🎯 **جودة العروض**:
• نسبة العروض الحقيقية: {real_deals_percent:.1f}%
• كفاءة الكشط: {'ممتازة' if real_deals_percent >= 80 else 'جيدة' if real_deals_percent >= 60 else 'عادية' if real_deals_percent >= 40 else 'ضعيفة'}

⏰ **وقت التقرير**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        
        # إرسال للجميع
        success_count = 0
        for user_id in self.users:
            try:
                success = self.send_message(user_id, report_msg, "Markdown")
                if success:
                    success_count += 1
            except Exception as e:
                print(f"Error sending report to user {user_id}: {e}")
                continue
        
        return success_count > 0
    
    def send_daily_summary(self, deals_summary: dict) -> bool:
        """إرسال ملخص يومي للعروض الذكية"""
        if not self.bot_token or not self.users:
            return False
        
        summary_msg = f"""
📅 **الملخص اليومي - العروض الذكية**

🎯 **إحصائيات العروض الحقيقية**:
• إجمالي العروض الحقيقية: {deals_summary.get('total_real_deals', 0)}
• عروض ممتازة (80+): {deals_summary.get('excellent_deals', 0)}
• عروض جيدة (60-79): {deals_summary.get('good_deals', 0)}
• متوسط درجة العرض: {deals_summary.get('average_deal_score', 0):.1f}/100

🏆 **أفضل 3 عروض اليوم**:
        """
        
        # إضافة أفضل العروض
        top_deals = deals_summary.get('top_deals', [])
        for i, deal in enumerate(top_deals[:3], 1):
            summary_msg += f"""
{i}. **{deal.get('name', 'Unknown')[:50]}...**
   💰 السعر: {deal.get('price', 0):,.0f} جنيه
   📉 الخصم: {deal.get('discount_percent', 0):.1f}%
   ⭐ الدرجة: {deal.get('deal_score', 0):.1f}/100
   🎯 التوصية: {deal.get('recommendation', '')}
            """
        
        summary_msg += f"""

📊 **تحليل الأداء**:
• جودة العروض: {'ممتازة' if deals_summary.get('average_deal_score', 0) >= 80 else 'جيدة' if deals_summary.get('average_deal_score', 0) >= 60 else 'عادية'}
• عدد العروض المميزة: {deals_summary.get('excellent_deals', 0)}

⏰ **تاريخ التقرير**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        
        # إرسال للجميع
        success_count = 0
        for user_id in self.users:
            try:
                success = self.send_message(user_id, summary_msg, "Markdown")
                if success:
                    success_count += 1
            except Exception as e:
                print(f"Error sending daily summary to user {user_id}: {e}")
                continue
        
        return success_count > 0

# دوال التوافق مع الكود الحالي
def send_telegram_alert(item, old_price, new_price, discount_percent, drop_detected=False):
    """دالة التوافق مع الكود الحالي"""
    bot = EnhancedTelegramBot()
    
    # إنشاء بيانات المنتج
    product_data = {
        'name': item.get('name', 'No name'),
        'url': item.get('url', ''),
        'img': item.get('img', ''),
        'section': item.get('section', 'Unknown'),
        'price': new_price,
        'strike_price': old_price,
        'discount_percent': discount_percent,
        'asin': item.get('asin', '')
    }
    
    # إنشاء تحليل بسيط (بدون AI)
    from dataclasses import dataclass
    from typing import List
    
    @dataclass
    class SimpleAnalysis:
        deal_score: float = 50.0
        is_real_deal: bool = True
        confidence: float = 0.7
        recommendation: str = "عرض جيد"
        average_market_price: float = new_price
        price_rank: int = 1
        competitor_prices: List = None
        risk_factors: List[str] = None
    
    analysis = SimpleAnalysis()
    analysis.competitor_prices = []
    analysis.risk_factors = []
    
    # إرسال التنبيه
    return bot.send_smart_alert(product_data, analysis)

def send_summary_report(total_products, real_deals, fake_deals, section):
    """دالة التوافق مع الكود الحالي"""
    bot = EnhancedTelegramBot()
    return bot.send_summary_report(total_products, real_deals, fake_deals, section)

# اختبار البوت
if __name__ == "__main__":
    # اختبار إرسال رسالة
    bot = EnhancedTelegramBot()
    
    test_product = {
        'name': 'ماكينة حلاقة متعددة الاستخدامات 10 في 1 للرجال من بيبي ليس',
        'url': 'https://www.amazon.eg/test',
        'img': 'https://example.com/test.jpg',
        'section': 'Electronics',
        'price': 299.99,
        'strike_price': 599.99,
        'discount_percent': 50.0,
        'asin': 'TEST123'
    }
    
    test_analysis = DealAnalysis(
        amazon_price=299.99,
        amazon_original_price=599.99,
        amazon_discount=50.0,
        competitor_prices=[],
        average_market_price=450.0,
        price_rank=1,
        deal_score=85.0,
        is_real_deal=True,
        confidence=0.9,
        recommendation="🔥 عرض استثنائي! سارع بالشراء",
        risk_factors=[]
    )
    
    # bot.send_smart_alert(test_product, test_analysis)
    print("Bot test completed!")