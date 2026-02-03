import { useState, useEffect } from 'react';
import { Save, RefreshCw, Settings as SettingsIcon } from 'lucide-react';
import { configApi } from '../api/client';
import type {
  RecommendConfig,
  UserProfileConfig,
  AlgorithmConfig,
  AllowedLabels,
  TaggingApiConfig,
} from '../types';
import RecommendConfigPanel from './settings/RecommendConfigPanel';
import TaggingConfigPanel from './settings/TaggingConfigPanel';

export default function Settings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'recommend' | 'tagging'>('recommend');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // 推荐配置
  const [recommendConfig, setRecommendConfig] = useState<RecommendConfig>({
    default_limit: 30,
    recent_filter_count: 100,
    diversity_max_per_artist: 1,
    diversity_max_per_album: 1,
    exploration_ratio: 0.25,
    tag_weights: { mood: 2.0, energy: 1.5, genre: 1.2, region: 0.8 },
  });

  const [userProfileConfig, setUserProfileConfig] = useState<UserProfileConfig>({
    play_count: 1.0,
    starred: 10.0,
    in_playlist: 8.0,
    time_decay_days: 90,
    min_decay: 0.3,
  });

  const [algorithmConfig, setAlgorithmConfig] = useState<AlgorithmConfig>({
    exploitation_pool_multiplier: 3,
    exploration_pool_start: 0.25,
    exploration_pool_end: 0.5,
    randomness: 0.0,
  });

  // 标签配置
  const [allowedLabels, setAllowedLabels] = useState<AllowedLabels>({
    mood: [],
    energy: [],
    scene: [],
    region: [],
    subculture: [],
    genre: [],
  });

  const [taggingApiConfig, setTaggingApiConfig] = useState<TaggingApiConfig>({
    timeout: 60,
    max_tokens: 1024,
    temperature: 0.1,
    retry_delay: 1,
    max_retries: 3,
    retry_backoff: 2,
  });

  useEffect(() => {
    loadConfig();
  }, [activeTab]);

  const loadConfig = async () => {
    setLoading(true);
    try {
      if (activeTab === 'recommend') {
        const response = await configApi.getRecommendConfig() as any;
        if (response.success && response.data) {
          setRecommendConfig(response.data.recommend);
          setUserProfileConfig(response.data.user_profile);
          setAlgorithmConfig(response.data.algorithm);
        }
      } else {
        const response = await configApi.getTaggingConfig() as any;
        if (response.success && response.data) {
          setAllowedLabels(response.data.allowed_labels);
          setTaggingApiConfig(response.data.api_config);
        }
      }
    } catch (error: any) {
      showMessage('error', `加载配置失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const saveRecommendConfig = async () => {
    setSaving(true);
    try {
      await configApi.updateRecommendConfig({
        recommend: recommendConfig,
        user_profile: userProfileConfig,
        algorithm: algorithmConfig,
      });
      showMessage('success', '推荐配置已保存');
    } catch (error: any) {
      showMessage('error', `保存失败: ${error.message}`);
    } finally {
      setSaving(false);
    }
  };

  const saveTaggingConfig = async () => {
    setSaving(true);
    try {
      await configApi.updateTaggingConfig({
        allowed_labels: allowedLabels,
        api_config: taggingApiConfig,
      });
      showMessage('success', '标签配置已保存');
    } catch (error: any) {
      showMessage('error', `保存失败: ${error.message}`);
    } finally {
      setSaving(false);
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center">
          <SettingsIcon className="h-6 w-6 mr-2" />
          系统配置
        </h1>
        <div className="flex items-center space-x-2">
          <button
            onClick={loadConfig}
            disabled={loading}
            className="flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </button>
          <button
            onClick={activeTab === 'recommend' ? saveRecommendConfig : saveTaggingConfig}
            disabled={saving || loading}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
          >
            <Save className="h-4 w-4 mr-2" />
            {saving ? '保存中...' : '保存配置'}
          </button>
        </div>
      </div>

      {message && (
        <div className={`p-4 rounded-md ${message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
          {message.text}
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              onClick={() => setActiveTab('recommend')}
              className={`px-6 py-4 text-sm font-medium border-b-2 ${
                activeTab === 'recommend'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              推荐配置
            </button>
            <button
              onClick={() => setActiveTab('tagging')}
              className={`px-6 py-4 text-sm font-medium border-b-2 ${
                activeTab === 'tagging'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              标签配置
            </button>
          </nav>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-primary-600" />
            </div>
          ) : activeTab === 'recommend' ? (
            <RecommendConfigPanel
              recommendConfig={recommendConfig}
              setRecommendConfig={setRecommendConfig}
              userProfileConfig={userProfileConfig}
              setUserProfileConfig={setUserProfileConfig}
              algorithmConfig={algorithmConfig}
              setAlgorithmConfig={setAlgorithmConfig}
            />
          ) : (
            <TaggingConfigPanel
              allowedLabels={allowedLabels}
              setAllowedLabels={setAllowedLabels}
              taggingApiConfig={taggingApiConfig}
              setTaggingApiConfig={setTaggingApiConfig}
            />
          )}
        </div>
      </div>
    </div>
  );
}
