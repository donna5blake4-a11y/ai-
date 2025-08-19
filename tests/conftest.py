"""
Pytest configuration and fixtures for AI Deals Manager tests.
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any

from enhanced_database import EnhancedDatabaseManager, Product
from ai_price_analyzer import AIPriceAnalyzer
from enhanced_telegram_bot import EnhancedTelegramBot


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_product_data():
    """Sample product data for testing."""
    return {
        "asin": "B0C7CQT9ZS",
        "name": "Anker Soundcore VI R50i True Wireless Earbuds",
        "url": "https://www.amazon.eg/-/en/Anker-Soundcore-Wireless-Bluetooth-Resistant/dp/B0C7CQT9ZS/",
        "img": "https://m.media-amazon.com/images/I/51Sc5zOZGzL._AC_UL320_.jpg",
        "section": "Electronics",
        "current_price": 847.92,
        "strike_price": 899.0,
        "discount_percent": 5.68,
    }


@pytest.fixture
def sample_product(sample_product_data):
    """Create a sample Product instance."""
    return Product(**sample_product_data)


@pytest.fixture
def db_manager(temp_db_path):
    """Create a database manager instance for testing."""
    manager = EnhancedDatabaseManager(temp_db_path)
    manager.initialize_database()
    yield manager
    manager.close()


@pytest.fixture
def ai_analyzer(temp_db_path):
    """Create an AI analyzer instance for testing."""
    return AIPriceAnalyzer(temp_db_path)


@pytest.fixture
def telegram_bot():
    """Create a mock Telegram bot instance for testing."""
    with patch("enhanced_telegram_bot.EnhancedTelegramBot._load_config") as mock_config:
        mock_config.return_value = {
            "bot_token": "test_token",
            "user_ids": ["123456789"],
            "daily_limit": 15,
            "min_discount": 20,
        }
        bot = EnhancedTelegramBot()
        yield bot


@pytest.fixture
def sample_json_data():
    """Sample JSON data for migration testing."""
    return {
        "B0C7CQT9ZS": {
            "name": "Anker Soundcore VI R50i True Wireless Earbuds",
            "url": "https://www.amazon.eg/-/en/Anker-Soundcore-Wireless-Bluetooth-Resistant/dp/B0C7CQT9ZS/",
            "img": "https://m.media-amazon.com/images/I/51Sc5zOZGzL._AC_UL320_.jpg",
            "section": "Electronics",
            "price": 847.92,
            "price_history": [
                {"date": "2025-01-01", "price": 899.0},
                {"date": "2025-01-02", "price": 847.92},
            ],
            "strike_price": 899.0,
            "discount_percent": 5.68,
        },
        "B0C7CQT9ZS2": {
            "name": "Test Product 2",
            "url": "https://www.amazon.eg/test2",
            "img": "https://test.com/img2.jpg",
            "section": "Electronics",
            "price": 100.0,
            "price_history": [
                {"date": "2025-01-01", "price": 120.0},
                {"date": "2025-01-02", "price": 100.0},
            ],
            "strike_price": 120.0,
            "discount_percent": 16.67,
        },
    }


@pytest.fixture
def temp_json_file(sample_json_data):
    """Create a temporary JSON file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump(sample_json_data, tmp)
        json_path = tmp.name
    yield json_path
    # Cleanup
    if os.path.exists(json_path):
        os.unlink(json_path)


@pytest.fixture
def mock_requests_response():
    """Mock requests response for testing."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = """
    <html>
        <body>
            <div class="product-price">1500 EGP</div>
            <div class="product-title">Test Product</div>
        </body>
    </html>
    """
    return mock_response


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for testing."""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = asyncio.coroutine(lambda: """
        <html>
            <body>
                <div class="product-price">1500 EGP</div>
                <div class="product-title">Test Product</div>
            </body>
        </html>
        """)
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        yield mock_session


@pytest.fixture
def sample_price_comparisons():
    """Sample price comparisons for testing."""
    from ai_price_analyzer import PriceComparison
    
    return [
        PriceComparison(
            website="jumia",
            product_name="Test Product",
            price=1500.0,
            url="https://jumia.com/test",
            confidence=0.8,
        ),
        PriceComparison(
            website="noon",
            product_name="Test Product",
            price=1600.0,
            url="https://noon.com/test",
            confidence=0.7,
        ),
    ]


@pytest.fixture
def sample_deal_analysis():
    """Sample deal analysis for testing."""
    from ai_price_analyzer import DealAnalysis
    
    return DealAnalysis(
        product_name="Test Product",
        amazon_price=1400.0,
        market_average=1550.0,
        best_alternative_price=1500.0,
        best_alternative_website="jumia",
        price_difference=100.0,
        price_difference_percent=6.67,
        confidence_score=0.85,
        is_good_deal=True,
        recommendations=["Good price compared to market", "Consider buying"],
        analysis_summary="This is a good deal with 6.67% savings compared to the best alternative.",
    )


# Async test utilities
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test data utilities
def create_test_product(asin: str = "TEST123", **kwargs) -> Product:
    """Helper function to create test products."""
    default_data = {
        "asin": asin,
        "name": f"Test Product {asin}",
        "url": f"https://amazon.eg/test/{asin}",
        "img": f"https://test.com/img/{asin}.jpg",
        "section": "Electronics",
        "current_price": 100.0,
        "strike_price": 120.0,
        "discount_percent": 16.67,
    }
    default_data.update(kwargs)
    return Product(**default_data)


def create_test_price_history(asin: str, days: int = 7) -> list:
    """Helper function to create test price history."""
    from datetime import datetime, timedelta
    
    history = []
    base_date = datetime.now() - timedelta(days=days)
    
    for i in range(days):
        date = base_date + timedelta(days=i)
        history.append({
            "date": date.strftime("%Y-%m-%d"),
            "price": 100.0 + i,
            "time": "12:00",
        })
    
    return history