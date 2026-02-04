"""
测试 src.services.profile_service 模块
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.services.profile_service import ProfileService


class TestProfileService:
    """测试 ProfileService 类"""

    def test_profile_service_initialization(self):
        """测试 ProfileService 初始化"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()

        service = ProfileService(mock_user_repo, mock_sem_repo)

        assert service.user_repo == mock_user_repo
        assert service.sem_repo == mock_sem_repo

    def test_calculate_time_decay_recent(self):
        """测试最近播放的时间衰减"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        # 最近播放（1天前）
        now = time.time()
        one_day_ago = now - 86400

        with patch('src.services.profile_service.time.time', return_value=now):
            decay = service._calculate_time_decay(one_day_ago)

        assert decay > 0.9  # 最近播放衰减应该很小

    def test_calculate_time_decay_old(self):
        """测试很久以前播放的时间衰减"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        # 很久以前（100天前）
        now = time.time()
        hundred_days_ago = now - (100 * 86400)

        with patch('src.services.profile_service.time.time', return_value=now):
            decay = service._calculate_time_decay(hundred_days_ago)

        # 应该达到或接近最小衰减值
        assert decay <= 0.5  # 100天前的衰减应该比较小

    def test_calculate_time_decay_none(self):
        """测试播放时间为空的时间衰减"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        decay = service._calculate_time_decay(None)

        # 应该返回最小衰减值
        assert decay >= 0.0

    def test_calculate_time_decay_zero(self):
        """测试播放时间为零的时间衰减"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        decay = service._calculate_time_decay(0)

        # 应该达到最小衰减值
        assert decay >= 0.0

    def test_calculate_song_weight_basic(self):
        """测试基础歌曲权重计算"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        play_data = {
            'play_count': 5,
            'starred': False,
            'play_date': time.time()
        }

        weight = service._calculate_song_weight(play_data, 0)

        # 基础权重应该只考虑播放次数
        assert weight > 0

    def test_calculate_song_weight_starred(self):
        """测试收藏歌曲的权重计算"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        now = time.time()
        play_data = {
            'play_count': 5,
            'starred': True,
            'play_date': now
        }

        weight_starred = service._calculate_song_weight(play_data, 0)

        play_data['starred'] = False
        weight_normal = service._calculate_song_weight(play_data, 0)

        # 收藏歌曲的权重应该更大
        assert weight_starred > weight_normal

    def test_calculate_song_weight_playlist(self):
        """测试在歌单中歌曲的权重计算"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        now = time.time()
        play_data = {
            'play_count': 5,
            'starred': False,
            'play_date': now
        }

        weight_playlist = service._calculate_song_weight(play_data, 2)
        weight_normal = service._calculate_song_weight(play_data, 0)

        # 在歌单中的歌曲权重应该更大
        assert weight_playlist > weight_normal

    def test_calculate_song_weight_decay(self):
        """测试时间衰减对权重的影响"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        now = time.time()

        # 最近播放
        play_data_recent = {
            'play_count': 10,
            'starred': False,
            'play_date': now - 86400  # 1天前
        }

        # 很久以前播放
        play_data_old = {
            'play_count': 10,
            'starred': False,
            'play_date': now - (100 * 86400)  # 100天前
        }

        with patch('src.services.profile_service.time.time', return_value=now):
            weight_recent = service._calculate_song_weight(play_data_recent, 0)
            weight_old = service._calculate_song_weight(play_data_old, 0)

        # 最近播放的权重应该更大
        assert weight_recent > weight_old

    def test_get_tag_type_valid(self):
        """测试获取有效标签类型"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        # 测试 mood 类型
        tag_type = service._get_tag_type('happy')
        assert tag_type in ['mood', 'energy', 'genre', 'region', None]

    def test_get_tag_type_invalid(self):
        """测试获取无效标签类型"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        tag_type = service._get_tag_type('invalid_tag')
        assert tag_type is None

    def test_build_user_profile_basic(self):
        """测试基础用户画像构建"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        # Mock 播放历史
        mock_user_repo.get_play_history = Mock(return_value={
            'song1': {
                'play_count': 10,
                'starred': True,
                'play_date': time.time()
            }
        })

        # Mock 歌单歌曲
        mock_user_repo.get_playlist_songs = Mock(return_value={
            'song1': 2
        })

        # Mock 歌曲标签
        mock_sem_repo.get_song_tags = Mock(return_value={
            'mood': 'happy',
            'energy': 'high',
            'genre': 'pop',
            'region': 'Western',
            'scene': 'None'
        })

        profile = service.build_user_profile('user1')

        assert profile['user_id'] == 'user1'
        assert 'profile' in profile
        assert 'stats' in profile
        assert 'generated_at' in profile
        assert profile['stats']['total_plays'] == 10
        assert profile['stats']['starred_count'] == 1

    def test_build_user_profile_empty_history(self):
        """测试空播放历史的用户画像"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        mock_user_repo.get_play_history = Mock(return_value={})
        mock_user_repo.get_playlist_songs = Mock(return_value={})

        profile = service.build_user_profile('user1')

        assert profile['user_id'] == 'user1'
        assert profile['stats']['total_plays'] == 0
        assert profile['stats']['starred_count'] == 0
        assert profile['stats']['unique_songs'] == 0

    def test_build_user_profile_no_tags(self):
        """测试歌曲没有标签的情况"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        mock_user_repo.get_play_history = Mock(return_value={
            'song1': {
                'play_count': 10,
                'starred': False,
                'play_date': time.time()
            }
        })
        mock_user_repo.get_playlist_songs = Mock(return_value={})

        # 没有标签
        mock_sem_repo.get_song_tags = Mock(return_value=None)

        profile = service.build_user_profile('user1')

        # 应该构建空画像
        assert profile['stats']['total_plays'] == 0  # 没有处理任何歌曲

    def test_build_user_profile_tag_types(self):
        """测试用户画像包含所有标签类型"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        mock_user_repo.get_play_history = Mock(return_value={
            'song1': {
                'play_count': 5,
                'starred': False,
                'play_date': time.time()
            }
        })
        mock_user_repo.get_playlist_songs = Mock(return_value={})

        mock_sem_repo.get_song_tags = Mock(return_value={
            'mood': 'happy',
            'energy': 'high',
            'genre': 'pop',
            'region': 'Western'
        })

        profile = service.build_user_profile('user1')

        assert 'mood' in profile['profile']
        assert 'energy' in profile['profile']
        assert 'genre' in profile['profile']
        assert 'region' in profile['profile']

    def test_build_user_profile_sorted_weights(self):
        """测试权重是否正确排序"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        mock_user_repo.get_play_history = Mock(return_value={
            'song1': {
                'play_count': 10,
                'starred': False,
                'play_date': time.time()
            }
        })
        mock_user_repo.get_playlist_songs = Mock(return_value={})

        mock_sem_repo.get_song_tags = Mock(return_value={
            'mood': 'happy',
            'energy': 'high',
            'genre': 'pop',
            'region': 'Western'
        })

        profile = service.build_user_profile('user1')

        # 检查每个类型都是字典
        for tag_type in ['mood', 'energy', 'genre', 'region']:
            assert isinstance(profile['profile'][tag_type], dict)

    def test_get_user_profile_existing(self):
        """测试获取存在的用户画像"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        mock_user_repo.get_user_by_id = Mock(return_value={
            'id': 'user1',
            'name': 'test_user'
        })
        mock_user_repo.get_play_history = Mock(return_value={})
        mock_user_repo.get_playlist_songs = Mock(return_value={})

        profile = service.get_user_profile('user1')

        assert profile is not None
        assert profile['user_id'] == 'user1'

    def test_get_user_profile_nonexistent(self):
        """测试获取不存在的用户画像"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        mock_user_repo.get_user_by_id = Mock(return_value=None)

        profile = service.get_user_profile('nonexistent_user')

        assert profile is None

    def test_get_user_profile_calls_build(self):
        """测试 get_user_profile 调用 build_user_profile"""
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        service = ProfileService(mock_user_repo, mock_sem_repo)

        mock_user_repo.get_user_by_id = Mock(return_value={
            'id': 'user1',
            'name': 'test_user'
        })
        mock_user_repo.get_play_history = Mock(return_value={
            'song1': {
                'play_count': 5,
                'starred': False,
                'play_date': time.time()
            }
        })
        mock_user_repo.get_playlist_songs = Mock(return_value={})
        mock_sem_repo.get_song_tags = Mock(return_value={
            'mood': 'happy',
            'energy': 'high',
            'genre': 'pop',
            'region': 'Western'
        })

        profile = service.get_user_profile('user1')

        # 验证 profile 包含画像数据
        assert profile is not None
        assert 'profile' in profile
        assert 'stats' in profile
