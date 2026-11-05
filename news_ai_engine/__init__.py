from .news_fetcher import NewsAggregator
from .editorial_generator import EditorialEngine
from .recommendation_engine import RecommendationEngine
from .database import (
    init_db,
    register_or_update_user,
    get_user_language,
    log_search_interest,
    get_top_interests,
    get_active_subscribers
)

__all__ = [
    "NewsAggregator",
    "EditorialEngine",
    "RecommendationEngine",
    "init_db",
    "register_or_update_user",
    "get_user_language",
    "log_search_interest",
    "get_top_interests",
    "get_active_subscribers"
]
__version__ = "1.0.0"
