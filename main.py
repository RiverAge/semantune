"""
Navidrome 语义音乐推荐系统 - 主入口
"""

import sys
import argparse
import logging

from src.utils.logger import setup_logger

logger = setup_logger("main", console_level=logging.INFO)


def show_banner() -> None:
    """显示欢迎横幅"""
    logger.info("=" * 60)
    logger.info("🎵 Navidrome 语义音乐推荐系统")
    logger.info("=" * 60)


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Navidrome 语义音乐推荐系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
# 生成语义标签
python main.py tag

# 生成推荐（用户画像即时生成）
python main.py recommend

# 查询歌曲
python main.py query

# 分析数据
python main.py analyze

# 导出数据
python main.py export

# 预览标签生成
python main.py tag-preview
        """
    )

    parser.add_argument(
        'command',
        choices=['tag', 'recommend', 'query', 'analyze', 'export', 'tag-preview', 'api'],
        help='要执行的命令'
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='API 服务监听地址（仅用于 api 命令）'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='API 服务监听端口（仅用于 api 命令）'
    )

    args = parser.parse_args()

    show_banner()

    if args.command == 'tag':
        logger.info("🏷️  生成语义标签...")
        from src.tagging.worker import main as tag_main
        tag_main()

    elif args.command == 'recommend':
        logger.info("🎯 生成个性化推荐...")
        from src.recommend.engine import main as recommend_main
        recommend_main()

    elif args.command == 'query':
        logger.info("🔍 查询歌曲...")
        from src.query.search import main as query_main
        query_main()

    elif args.command == 'analyze':
        logger.info("📊 分析数据...")
        from src.utils.analyze import main as analyze_main
        analyze_main()

    elif args.command == 'export':
        logger.info("📦 导出数据...")
        from src.utils.export import main as export_main
        export_main()

    elif args.command == 'tag-preview':
        logger.info("👁️  预览标签生成...")
        from src.tagging.preview import main as preview_main
        preview_main()
    
    elif args.command == 'api':
        logger.info("🚀 启动 API 服务...")
        import uvicorn
        logger.info(f"API 服务地址: http://{args.host}:{args.port}")
        logger.info(f"API 文档: http://{args.host}:{args.port}/docs")
        uvicorn.run("src.api.app:app", host=args.host, port=args.port, reload=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("已退出")
        sys.exit(0)
    except Exception as e:
        logger.error(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
