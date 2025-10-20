from datetime import datetime, timedelta
from typing import List
from src.core.data.political_source import PoliticalEvent, PoliticalDataSource
from src.core.data.database import DatabaseManager
import asyncio

class PolicyService:
    """处理政治事件数据的服务类"""
    
    def __init__(self):
        self.data_source = PoliticalDataSource()
        self.db = DatabaseManager()
        self.cache_duration = timedelta(minutes=5)
        
    def get_recent_events(self) -> List[PoliticalEvent]:
        """获取最近的政治事件"""
        try:
            # 尝试从数据库获取缓存数据
            cached_events = self.db.query(
                "SELECT * FROM political_events "
                "WHERE event_date > ? "
                "ORDER BY event_date DESC LIMIT 20",
                (datetime.now() - self.cache_duration,)
            )
            
            if cached_events:
                return [
                    PoliticalEvent(
                        event_date=row["event_date"],
                        country=row["country"],
                        policy_type=row["policy_type"],
                        impact_score=row["impact_score"],
                        raw_content=row["raw_content"]
                    ) for row in cached_events
                ]
                
            # 没有缓存则从数据源获取
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            new_events = loop.run_until_complete(self.data_source.fetch_real_time())
            loop.close()
            
            # 存储新事件到数据库
            for event in new_events:
                self.db.execute(
                    "INSERT INTO political_events "
                    "(event_date, country, policy_type, impact_score, raw_content) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (event.event_date, event.country, event.policy_type, 
                     event.impact_score, event.raw_content)
                )
            
            return new_events
            
        except Exception as e:
            print(f"Error getting political events: {str(e)}")
            return []
            
    def close(self):
        """清理资源"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.data_source.close())
        loop.close()
