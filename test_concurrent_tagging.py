"""
测试并发标签生成功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.tagging_service import TaggingService
from src.services.llm_client import LLMClient
from src.repositories.navidrome_repository import NavidromeRepository
from src.repositories.semantic_repository import SemanticRepository
from src.core.database import nav_db_context, sem_db_context
from config.settings import get_model
import time

# 测试歌曲数据
TEST_SONGS = [
    {
        "title": "夜曲",
        "artist": "周杰伦",
        "album": "十一月的萧邦"
    },
    {
        "title": "青花瓷",
        "artist": "周杰伦",
        "album": "我很忙"
    },
    {
        "title": "稻香",
        "artist": "周杰伦",
        "album": "魔杰座"
    },
    {
        "title": "告白气球",
        "artist": "周杰伦",
        "album": "周杰伦的床边故事"
    },
    {
        "title": "Mojito",
        "artist": "周杰伦",
        "album": "最伟大的作品"
    }
]

def test_concurrent_tagging():
    """测试并发标签生成"""
    print("=" * 60)
    print("测试并发标签生成功能")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        with nav_db_context() as nav_conn, sem_db_context() as sem_conn:
            nav_repo = NavidromeRepository(nav_conn)
            sem_repo = SemanticRepository(sem_conn)
            tagging_service = TaggingService(nav_repo, sem_repo)
            
            # 处理歌曲
            result = tagging_service.process_all_songs()
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            print(f"\n处理结果:")
            print(f"  总数: {result['total']}")
            print(f"  已处理: {result['processed']}")
            print(f"  验证失败: {result['validation_failed']}")
            print(f"  失败: {result['failed']}")
            print(f"  耗时: {elapsed_time:.2f} 秒")
            
            return result
            
    except Exception as e:
        print(f"测试失败: {e}")
        return None

if __name__ == "__main__":
    result = test_concurrent_tagging()
    sys.exit(0 if result else 1)