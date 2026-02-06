import { useTagging } from './tagging/useTagging';
import TaggingConfig from './tagging/TaggingConfig';
import BatchTagging from './tagging/BatchTagging';
import TagTest from './tagging/TagTest';
import TaggingTabs from './tagging/TaggingTabs';
import TaggingHeader from './tagging/TaggingHeader';

export default function Tagging() {
  const {
    activeTab,
    setActiveTab,
    config,
    setConfig,
    setIsConfigured,
    showConfig,
    setShowConfig,
    status,
    isGenerating,
    error,
    successMessage,
    history,
    historyTotal,
    historyLimit,
    historyOffset,
    setHistoryOffset,
    handleResetConfig,
    handleStartTagging,
    handleStopTagging,
    loadHistory,
    handleExportHistory,
    handleCleanup,
    highlightProcessed,
  } = useTagging();

  // 配置页面
  if (showConfig) {
    return (
      <TaggingConfig
        config={config}
        setConfig={setConfig}
        setIsConfigured={setIsConfigured}
        setShowConfig={setShowConfig}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <TaggingHeader onResetConfig={handleResetConfig} />

      {/* 标签页切换 */}
      <TaggingTabs activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* 批量生成标签页 */}
      {activeTab === 'batch' && (
        <BatchTagging
          status={status}
          isGenerating={isGenerating}
          config={config}
          history={history}
          historyTotal={historyTotal}
          historyLimit={historyLimit}
          historyOffset={historyOffset}
          error={error}
          successMessage={successMessage}
          onStartTagging={handleStartTagging}
          onStopTagging={handleStopTagging}
          onLoadHistory={loadHistory}
          onHistoryOffsetChange={setHistoryOffset}
          onCleanup={handleCleanup}
          highlightProcessed={highlightProcessed}
          onExportHistory={handleExportHistory}
        />
      )}

      {/* 标签测试标签页 */}
      {activeTab === 'test' && (
        <TagTest onTestSuccess={() => {}} />
      )}
    </div>
  );
}
