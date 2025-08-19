# historical_data_analyzer.py
# محلل البيانات التاريخية من ملف JSON الضخم

import json
import gzip
import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from collections import defaultdict
from ai_price_analyzer import AIPriceAnalyzer

class HistoricalDataAnalyzer:
    """محلل البيانات التاريخية"""
    
    def __init__(self, json_file_path: str, db_path: str = "historical_analysis.db"):
        self.json_file_path = json_file_path
        self.db_path = db_path
        self.connection = None
        self.init_database()
    
    def init_database(self):
        """تهيئة قاعدة البيانات للتحليل التاريخي"""
        self.connection = sqlite3.connect(self.db_path)
        cursor = self.connection.cursor()
        
        # جدول المنتجات التاريخية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_products (
                asin TEXT PRIMARY KEY,
                name TEXT,
                url TEXT,
                img TEXT,
                section TEXT,
                current_price REAL,
                strike_price REAL,
                discount_percent REAL,
                first_seen_date TEXT,
                last_updated_date TEXT,
                price_change_count INTEGER DEFAULT 0,
                total_price_changes REAL DEFAULT 0,
                volatility_score REAL DEFAULT 0,
                trend_direction TEXT DEFAULT 'stable'
            )
        ''')
        
        # جدول تاريخ الأسعار المفصل
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detailed_price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT,
                price REAL,
                date TEXT,
                time TEXT,
                price_change REAL DEFAULT 0,
                change_percent REAL DEFAULT 0,
                FOREIGN KEY (asin) REFERENCES historical_products (asin)
            )
        ''')
        
        # جدول تحليل الاتجاهات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT,
                trend_period TEXT,
                start_price REAL,
                end_price REAL,
                trend_direction TEXT,
                trend_strength REAL,
                volatility REAL,
                analysis_date TEXT,
                FOREIGN KEY (asin) REFERENCES historical_products (asin)
            )
        ''')
        
        # جدول العروض التاريخية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT,
                deal_date TEXT,
                original_price REAL,
                deal_price REAL,
                discount_percent REAL,
                deal_duration_days INTEGER,
                deal_score REAL,
                is_real_deal BOOLEAN,
                FOREIGN KEY (asin) REFERENCES historical_products (asin)
            )
        ''')
        
        # إنشاء الفهارس
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_historical_asin ON historical_products(asin)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_historical_section ON historical_products(section)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_historical_volatility ON historical_products(volatility_score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_asin ON detailed_price_history(asin)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_date ON detailed_price_history(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trends_asin ON price_trends(asin)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_deals_asin ON historical_deals(asin)')
        
        self.connection.commit()
    
    def load_json_data(self, chunk_size: int = 1000) -> Dict:
        """تحميل البيانات من ملف JSON"""
        print(f"📂 جاري تحميل البيانات من {self.json_file_path}...")
        
        try:
            # محاولة فتح الملف المضغوط أولاً
            if self.json_file_path.endswith('.gz'):
                with gzip.open(self.json_file_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(self.json_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            print(f"✅ تم تحميل {len(data):,} منتج")
            return data
            
        except Exception as e:
            print(f"❌ خطأ في تحميل الملف: {e}")
            return {}
    
    def analyze_price_history(self, price_history: List[Dict]) -> Dict:
        """تحليل تاريخ الأسعار لمنتج واحد"""
        if not price_history:
            return {}
        
        # تحويل إلى DataFrame للتحليل
        df = pd.DataFrame(price_history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # حساب التغييرات
        df['price_change'] = df['price'].diff()
        df['change_percent'] = (df['price_change'] / df['price'].shift(1)) * 100
        
        # إحصائيات أساسية
        analysis = {
            'price_changes': len(df[df['price_change'] != 0]),
            'total_price_change': df['price'].iloc[-1] - df['price'].iloc[0],
            'price_change_percent': ((df['price'].iloc[-1] - df['price'].iloc[0]) / df['price'].iloc[0]) * 100,
            'volatility': df['price'].std(),
            'volatility_percent': (df['price'].std() / df['price'].mean()) * 100,
            'min_price': df['price'].min(),
            'max_price': df['price'].max(),
            'avg_price': df['price'].mean(),
            'first_date': df['date'].min().strftime('%Y-%m-%d'),
            'last_date': df['date'].max().strftime('%Y-%m-%d'),
            'days_tracked': (df['date'].max() - df['date'].min()).days
        }
        
        # تحديد اتجاه الاتجاه
        if analysis['price_change_percent'] > 5:
            analysis['trend_direction'] = 'increasing'
        elif analysis['price_change_percent'] < -5:
            analysis['trend_direction'] = 'decreasing'
        else:
            analysis['trend_direction'] = 'stable'
        
        # حساب قوة الاتجاه
        analysis['trend_strength'] = abs(analysis['price_change_percent'])
        
        # حساب درجة التقلب
        analysis['volatility_score'] = analysis['volatility_percent']
        
        return analysis
    
    def detect_historical_deals(self, price_history: List[Dict], asin: str) -> List[Dict]:
        """كشف العروض التاريخية"""
        if not price_history:
            return []
        
        df = pd.DataFrame(price_history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        deals = []
        window_size = 30  # نافذة 30 يوم للكشف عن العروض
        
        for i in range(window_size, len(df)):
            window = df.iloc[i-window_size:i]
            current_price = df.iloc[i]['price']
            
            # حساب متوسط السعر في النافذة
            avg_price = window['price'].mean()
            
            # كشف الخصم
            if current_price < avg_price * 0.9:  # خصم 10% أو أكثر
                discount_percent = ((avg_price - current_price) / avg_price) * 100
                
                # حساب مدة العرض
                deal_start = i - window_size
                deal_end = i
                deal_duration = (df.iloc[deal_end]['date'] - df.iloc[deal_start]['date']).days
                
                # حساب درجة العرض
                deal_score = self.calculate_historical_deal_score(
                    current_price, avg_price, discount_percent, deal_duration
                )
                
                deals.append({
                    'asin': asin,
                    'deal_date': df.iloc[i]['date'].strftime('%Y-%m-%d'),
                    'original_price': avg_price,
                    'deal_price': current_price,
                    'discount_percent': discount_percent,
                    'deal_duration_days': deal_duration,
                    'deal_score': deal_score,
                    'is_real_deal': deal_score >= 60
                })
        
        return deals
    
    def calculate_historical_deal_score(self, deal_price: float, original_price: float, 
                                      discount_percent: float, duration: int) -> float:
        """حساب درجة العرض التاريخي"""
        score = 0.0
        
        # عامل الخصم (50%)
        score += min(discount_percent * 0.5, 50)
        
        # عامل السعر (30%)
        if deal_price > 50:  # سعر معقول
            score += 30
        
        # عامل المدة (20%)
        if duration <= 7:  # عرض قصير الأمد
            score += 20
        elif duration <= 14:
            score += 15
        elif duration <= 30:
            score += 10
        
        return min(score, 100)
    
    def save_product_analysis(self, asin: str, product_data: Dict, analysis: Dict):
        """حفظ تحليل المنتج"""
        cursor = self.connection.cursor()
        
        # حفظ المنتج الرئيسي
        cursor.execute('''
            INSERT OR REPLACE INTO historical_products 
            (asin, name, url, img, section, current_price, strike_price, discount_percent,
             first_seen_date, last_updated_date, price_change_count, total_price_changes,
             volatility_score, trend_direction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            asin,
            product_data.get('name', ''),
            product_data.get('url', ''),
            product_data.get('img', ''),
            product_data.get('section', ''),
            product_data.get('price', 0),
            product_data.get('strike_price'),
            product_data.get('discount_percent'),
            analysis.get('first_date', ''),
            analysis.get('last_date', ''),
            analysis.get('price_changes', 0),
            analysis.get('total_price_change', 0),
            analysis.get('volatility_score', 0),
            analysis.get('trend_direction', 'stable')
        ))
        
        # حفظ تاريخ الأسعار المفصل
        price_history = product_data.get('price_history', [])
        for entry in price_history:
            cursor.execute('''
                INSERT INTO detailed_price_history 
                (asin, price, date, time, price_change, change_percent)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                asin,
                entry.get('price', 0),
                entry.get('date', ''),
                entry.get('time', '00:00'),
                0, 0  # سيتم حسابها لاحقاً
            ))
        
        # حفظ العروض التاريخية
        deals = self.detect_historical_deals(price_history, asin)
        for deal in deals:
            cursor.execute('''
                INSERT INTO historical_deals 
                (asin, deal_date, original_price, deal_price, discount_percent,
                 deal_duration_days, deal_score, is_real_deal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                deal['asin'],
                deal['deal_date'],
                deal['original_price'],
                deal['deal_price'],
                deal['discount_percent'],
                deal['deal_duration_days'],
                deal['deal_score'],
                deal['is_real_deal']
            ))
        
        self.connection.commit()
    
    def process_all_products(self, limit: int = None):
        """معالجة جميع المنتجات"""
        data = self.load_json_data()
        if not data:
            return
        
        total_products = len(data)
        if limit:
            total_products = min(total_products, limit)
        
        print(f"🔄 جاري معالجة {total_products:,} منتج...")
        
        processed = 0
        for asin, product_data in list(data.items())[:limit]:
            try:
                # تحليل تاريخ الأسعار
                price_history = product_data.get('price_history', [])
                analysis = self.analyze_price_history(price_history)
                
                # حفظ التحليل
                self.save_product_analysis(asin, product_data, analysis)
                
                processed += 1
                if processed % 1000 == 0:
                    print(f"✅ تم معالجة {processed:,} منتج...")
                
            except Exception as e:
                print(f"❌ خطأ في معالجة {asin}: {e}")
                continue
        
        print(f"🎉 تم الانتهاء من معالجة {processed:,} منتج")
    
    def get_volatile_products(self, min_volatility: float = 10.0, limit: int = 50) -> List[Dict]:
        """جلب المنتجات المتقلبة"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT asin, name, section, current_price, volatility_score, trend_direction
            FROM historical_products 
            WHERE volatility_score >= ?
            ORDER BY volatility_score DESC
            LIMIT ?
        ''', (min_volatility, limit))
        
        return [
            {
                'asin': row[0],
                'name': row[1],
                'section': row[2],
                'current_price': row[3],
                'volatility_score': row[4],
                'trend_direction': row[5]
            }
            for row in cursor.fetchall()
        ]
    
    def get_best_historical_deals(self, min_score: float = 70, limit: int = 50) -> List[Dict]:
        """جلب أفضل العروض التاريخية"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT hd.asin, hp.name, hp.section, hd.deal_price, hd.original_price,
                   hd.discount_percent, hd.deal_score, hd.deal_date
            FROM historical_deals hd
            JOIN historical_products hp ON hd.asin = hp.asin
            WHERE hd.deal_score >= ? AND hd.is_real_deal = TRUE
            ORDER BY hd.deal_score DESC
            LIMIT ?
        ''', (min_score, limit))
        
        return [
            {
                'asin': row[0],
                'name': row[1],
                'section': row[2],
                'deal_price': row[3],
                'original_price': row[4],
                'discount_percent': row[5],
                'deal_score': row[6],
                'deal_date': row[7]
            }
            for row in cursor.fetchall()
        ]
    
    def get_section_analysis(self) -> Dict:
        """تحليل الأقسام"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT section,
                   COUNT(*) as total_products,
                   AVG(volatility_score) as avg_volatility,
                   AVG(current_price) as avg_price,
                   COUNT(CASE WHEN trend_direction = 'increasing' THEN 1 END) as increasing,
                   COUNT(CASE WHEN trend_direction = 'decreasing' THEN 1 END) as decreasing,
                   COUNT(CASE WHEN trend_direction = 'stable' THEN 1 END) as stable
            FROM historical_products
            GROUP BY section
            ORDER BY total_products DESC
        ''')
        
        sections = {}
        for row in cursor.fetchall():
            sections[row[0]] = {
                'total_products': row[1],
                'avg_volatility': row[2],
                'avg_price': row[3],
                'increasing_trend': row[4],
                'decreasing_trend': row[5],
                'stable_trend': row[6]
            }
        
        return sections
    
    def generate_insights_report(self) -> str:
        """توليد تقرير الرؤى"""
        cursor = self.connection.cursor()
        
        # إحصائيات عامة
        cursor.execute("SELECT COUNT(*) FROM historical_products")
        total_products = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(volatility_score) FROM historical_products")
        avg_volatility = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM historical_deals WHERE is_real_deal = TRUE")
        total_real_deals = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(deal_score) FROM historical_deals WHERE is_real_deal = TRUE")
        avg_deal_score = cursor.fetchone()[0] or 0
        
        # أفضل الأقسام
        sections = self.get_section_analysis()
        top_sections = sorted(sections.items(), key=lambda x: x[1]['total_products'], reverse=True)[:5]
        
        # أفضل العروض
        best_deals = self.get_best_historical_deals(min_score=80, limit=5)
        
        # المنتجات الأكثر تقلباً
        volatile_products = self.get_volatile_products(min_volatility=20, limit=5)
        
        report = f"""
📊 **تقرير تحليل البيانات التاريخية**

📈 **إحصائيات عامة**:
• إجمالي المنتجات: {total_products:,}
• متوسط التقلب: {avg_volatility:.1f}%
• العروض الحقيقية المكتشفة: {total_real_deals:,}
• متوسط درجة العرض: {avg_deal_score:.1f}/100

🏆 **أفضل 5 أقسام**:
"""
        
        for section, stats in top_sections:
            report += f"""
• **{section}**:
  - المنتجات: {stats['total_products']:,}
  - متوسط التقلب: {stats['avg_volatility']:.1f}%
  - متوسط السعر: {stats['avg_price']:,.0f} جنيه
  - الاتجاهات: ↗️ {stats['increasing_trend']} | ↘️ {stats['decreasing_trend']} | ➡️ {stats['stable_trend']}
"""
        
        report += "\n🔥 **أفضل العروض التاريخية**:\n"
        for deal in best_deals:
            report += f"""
• **{deal['name'][:50]}...**
  - الخصم: {deal['discount_percent']:.1f}%
  - السعر: {deal['deal_price']:,.0f} → {deal['original_price']:,.0f} جنيه
  - الدرجة: {deal['deal_score']:.1f}/100
  - التاريخ: {deal['deal_date']}
"""
        
        report += "\n📈 **المنتجات الأكثر تقلباً**:\n"
        for product in volatile_products:
            report += f"""
• **{product['name'][:50]}...**
  - التقلب: {product['volatility_score']:.1f}%
  - الاتجاه: {product['trend_direction']}
  - السعر الحالي: {product['current_price']:,.0f} جنيه
"""
        
        return report
    
    def close(self):
        """إغلاق الاتصال"""
        if self.connection:
            self.connection.close()

# دالة مساعدة لمعالجة الملف الكبير
def process_large_json_file(json_file_path: str, output_db: str = "historical_analysis.db", 
                          limit: int = None):
    """معالجة ملف JSON كبير"""
    print(f"🚀 بدء معالجة الملف الكبير: {json_file_path}")
    
    analyzer = HistoricalDataAnalyzer(json_file_path, output_db)
    
    try:
        # معالجة المنتجات
        analyzer.process_all_products(limit=limit)
        
        # توليد التقرير
        report = analyzer.generate_insights_report()
        print(report)
        
        # حفظ التقرير
        with open("historical_analysis_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        
        print("✅ تم حفظ التقرير في historical_analysis_report.txt")
        
    finally:
        analyzer.close()

if __name__ == "__main__":
    # مثال على الاستخدام
    # process_large_json_file("amz_products.json", limit=10000)  # معالجة أول 10,000 منتج للاختبار
    print("📋 جاهز لمعالجة البيانات التاريخية!")
    print("💡 استخدم: process_large_json_file('your_file.json')")