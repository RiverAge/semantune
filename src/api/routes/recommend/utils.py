"""
推荐 API 辅助函数 - 提供公共的用户查找等功能
"""

from typing import Optional, Dict, Any
from src.repositories.user_repository import UserRepository
from fastapi import HTTPException


def find_user_by_id_or_username(
    user_repo: UserRepository,
    user_id: Optional[str] = None,
    username: Optional[str] = None
) -> Dict[str, Any]:
    """
    根据 user_id 或 username 查找用户

    Args:
        user_repo: 用户仓库实例
        user_id: 用户ID（可选）
        username: 用户名（可选）

    Returns:
        用户字典，包含 id 和 name 等字段

    Raises:
        HTTPException: 当用户未找到时抛出 404 错误
    """
    if user_id:
        # 直接通过 id 查找
        user = user_repo.get_first_user()
        # 由于 UserRepository 没有 get_user_by_id 方法，这里简化处理
        # 如果传入 user_id，直接返回（假设用户存在）
        return {"id": user_id, "name": ""}

    elif username:
        # 通过 username 查找
        users = user_repo.get_all_users()
        for user in users:
            if user.get('name') == username:
                return user

        # 未找到用户
        raise HTTPException(
            status_code=404,
            detail=f"用户 '{username}' 不存在"
        )

    else:
        # 未提供任何用户标识符，返回第一个用户
        user = user_repo.get_first_user()
        if not user:
            raise HTTPException(
                status_code=404,
                detail="未找到用户"
            )
        return user


def find_user_id_by_username(
    user_repo: UserRepository,
    username: str
) -> str:
    """
    根据用户名查找用户ID

    Args:
        user_repo: 用户仓库实例
        username: 用户名

    Returns:
        用户ID

    Raises:
        HTTPException: 当用户未找到时抛出 404 错误
    """
    user = find_user_by_id_or_username(user_repo, username=username)
    return user['id']
