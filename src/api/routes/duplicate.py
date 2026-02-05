"""
重复检测接口路由
"""
import logging
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List

from src.core.database import nav_db_context
from src.core.response import ApiResponse
from src.services.service_factory import ServiceFactory
from src.utils.logger import setup_logger

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, LOG_LEVEL, logging.INFO)
logger = setup_logger("api", level=log_level, console_level=log_level)

router = APIRouter()


class DuplicateSongInfo(BaseModel):
    """重复歌曲信息"""
    id: str
    path: str
    title: str
    artist: str
    album: str


class DuplicateSongGroup(BaseModel):
    """重复歌曲组"""
    size: int
    count: int
    songs: List[DuplicateSongInfo]


class DuplicateSongsResponse(BaseModel):
    """重复歌曲响应"""
    type: str
    total_groups: int
    duplicates: List[DuplicateSongGroup]


class DuplicateAlbumInfo(BaseModel):
    """重复专辑信息"""
    id: str
    name: str
    album_artist: str
    min_year: int
    max_year: int
    song_count: int
    date: str


class DuplicateAlbumGroup(BaseModel):
    """重复专辑组"""
    album: str
    album_artist: str
    count: int
    total_songs: int
    albums: List[DuplicateAlbumInfo]


class DuplicateAlbumsResponse(BaseModel):
    """重复专辑响应"""
    type: str
    total_groups: int
    duplicates: List[DuplicateAlbumGroup]


class DuplicateSongInAlbumInfo(BaseModel):
    """专辑内重复歌曲信息"""
    id: str
    album_id: str
    album: str
    album_artist: str
    title: str


class DuplicateSongInAlbumGroup(BaseModel):
    """专辑内重复歌曲组"""
    path: str
    count: int
    songs: List[DuplicateSongInAlbumInfo]


class DuplicateSongsInAlbumResponse(BaseModel):
    """专辑内重复歌曲响应"""
    type: str
    total_groups: int
    duplicates: List[DuplicateSongInAlbumGroup]


class DuplicateSummary(BaseModel):
    """重复检测汇总"""
    duplicate_song_groups: int
    duplicate_album_groups: int
    duplicate_songs_in_album_groups: int
    total_issues: int


class AllDuplicatesResponse(BaseModel):
    """所有重复检测响应"""
    duplicate_songs: DuplicateSongsResponse
    duplicate_albums: DuplicateAlbumsResponse
    duplicate_songs_in_album: DuplicateSongsInAlbumResponse
    summary: DuplicateSummary


@router.get("/songs", response_model=ApiResponse)
async def get_duplicate_songs():
    """
    检测重复歌曲
    
    基于（标题, 艺术家, 专辑）的组合判断重复
    """
    try:
        with nav_db_context() as conn:
            service = ServiceFactory.create_duplicate_detection_service(conn)
            result = service.detect_duplicate_songs()

            logger.info(f"检测到 {result['total_groups']} 组重复歌曲")

            return ApiResponse.success_response(
                data=DuplicateSongsResponse(
                    type=result['type'],
                    total_groups=result['total_groups'],
                    duplicates=result['duplicates']
                )
            )

    except Exception as e:
        logger.error(f"检测重复歌曲失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/albums", response_model=ApiResponse)
async def get_duplicate_albums():
    """
    检测重复专辑
    
    基于同一艺术家的相同专辑名称判断重复
    专辑可能因为发行时间不同而被拆分成多个专辑
    """
    try:
        with nav_db_context() as conn:
            service = ServiceFactory.create_duplicate_detection_service(conn)
            result = service.detect_duplicate_albums()

            logger.info(f"检测到 {result['total_groups']} 组重复专辑")

            return ApiResponse.success_response(
                data=DuplicateAlbumsResponse(
                    type=result['type'],
                    total_groups=result['total_groups'],
                    duplicates=result['duplicates']
                )
            )

    except Exception as e:
        logger.error(f"检测重复专辑失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/songs-in-album", response_model=ApiResponse)
async def get_duplicate_songs_in_album():
    """
    检测同一专辑中的重复歌曲
    
    基于同一专辑中相同标题的歌曲判断重复
    可能由于文件夹移动导致重复
    """
    try:
        with nav_db_context() as conn:
            service = ServiceFactory.create_duplicate_detection_service(conn)
            result = service.detect_duplicate_songs_in_album()

            logger.info(f"检测到 {result['total_groups']} 组专辑内重复歌曲")

            return ApiResponse.success_response(
                data=DuplicateSongsInAlbumResponse(
                    type=result['type'],
                    total_groups=result['total_groups'],
                    duplicates=result['duplicates']
                )
            )

    except Exception as e:
        logger.error(f"检测专辑内重复歌曲失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all", response_model=ApiResponse)
async def get_all_duplicates():
    """
    检测所有类型的重复项
    
    包括重复歌曲、重复专辑和专辑内重复歌曲
    """
    try:
        with nav_db_context() as conn:
            service = ServiceFactory.create_duplicate_detection_service(conn)
            result = service.detect_all_duplicates()

            logger.info(f"检测汇总: {result['summary']['total_issues']} 个问题")

            return ApiResponse.success_response(
                data=AllDuplicatesResponse(
                    duplicate_songs=DuplicateSongsResponse(
                        type=result['duplicate_songs']['type'],
                        total_groups=result['duplicate_songs']['total_groups'],
                        duplicates=result['duplicate_songs']['duplicates']
                    ),
                    duplicate_albums=DuplicateAlbumsResponse(
                        type=result['duplicate_albums']['type'],
                        total_groups=result['duplicate_albums']['total_groups'],
                        duplicates=result['duplicate_albums']['duplicates']
                    ),
                    duplicate_songs_in_album=DuplicateSongsInAlbumResponse(
                        type=result['duplicate_songs_in_album']['type'],
                        total_groups=result['duplicate_songs_in_album']['total_groups'],
                        duplicates=result['duplicate_songs_in_album']['duplicates']
                    ),
                    summary=DuplicateSummary(
                        duplicate_song_groups=result['summary']['duplicate_song_groups'],
                        duplicate_album_groups=result['summary']['duplicate_album_groups'],
                        duplicate_songs_in_album_groups=result['summary']['duplicate_songs_in_album_groups'],
                        total_issues=result['summary']['total_issues']
                    )
                )
            )

    except Exception as e:
        logger.error(f"检测所有重复项失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
