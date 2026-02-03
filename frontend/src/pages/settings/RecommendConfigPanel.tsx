import type { RecommendConfig, UserProfileConfig, AlgorithmConfig } from '../../types';
import BasicConfig from './BasicConfig';
import TagWeights from './TagWeights';
import UserProfileConfigPanel from './UserProfileConfigPanel';
import AlgorithmConfigPanel from './AlgorithmConfigPanel';

interface RecommendConfigProps {
  recommendConfig: RecommendConfig;
  setRecommendConfig: (config: RecommendConfig) => void;
  userProfileConfig: UserProfileConfig;
  setUserProfileConfig: (config: UserProfileConfig) => void;
  algorithmConfig: AlgorithmConfig;
  setAlgorithmConfig: (config: AlgorithmConfig) => void;
}

export default function RecommendConfig({
  recommendConfig,
  setRecommendConfig,
  userProfileConfig,
  setUserProfileConfig,
  algorithmConfig,
  setAlgorithmConfig,
}: RecommendConfigProps) {
  return (
    <div className="space-y-6">
      <BasicConfig
        recommendConfig={recommendConfig}
        setRecommendConfig={setRecommendConfig}
      />
      <TagWeights
        recommendConfig={recommendConfig}
        setRecommendConfig={setRecommendConfig}
      />
      <UserProfileConfigPanel
        userProfileConfig={userProfileConfig}
        setUserProfileConfig={setUserProfileConfig}
      />
      <AlgorithmConfigPanel
        algorithmConfig={algorithmConfig}
        setAlgorithmConfig={setAlgorithmConfig}
      />
    </div>
  );
}
