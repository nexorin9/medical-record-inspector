import { Issue } from '@/types/evaluation';

// 类型导入
import type { EvaluationResult as EvaluationResultType } from '@/types/evaluation';

interface EvaluationResultProps {
  result: EvaluationResultType;
  onCopy?: () => void;
}

// 根据严重程度获取样式类名和图标
const getSeverityStyle = (severity: Issue['severity']) => {
  const styles = {
    critical: { class: 'severity-critical', icon: '🔴', label: '严重' },
    high: { class: 'severity-high', icon: '🟠', label: '较高' },
    medium: { class: 'severity-medium', icon: '🟡', label: '一般' },
    low: { class: 'severity-low', icon: '🟢', label: '轻微' },
  };
  return styles[severity];
};

// 根据分数获取颜色
const getScoreColor = (score: number): string => {
  if (score >= 90) return '#4caf50';
  if (score >= 80) return '#8bc34a';
  if (score >= 70) return '#cddc39';
  if (score >= 60) return '#ffeb3b';
  if (score >= 50) return '#ffc107';
  if (score >= 40) return '#ff9800';
  return '#f44336';
};

// 进度条组件
const ProgressBar = ({ score, size = 'medium' }: { score: number; size?: 'small' | 'medium' | 'large' }) => {
  const radius = size === 'small' ? 12 : size === 'medium' ? 20 : 35;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = getScoreColor(score);

  const sizeClasses = {
    small: 'w-12 h-12',
    medium: 'w-24 h-24',
    large: 'w-32 h-32',
  };

  return (
    <div className={`relative flex items-center justify-center ${sizeClasses[size]}`}>
      <svg className="transform -rotate-90 w-full h-full">
        <circle
          cx="50%"
          cy="50%"
          r={radius}
          stroke="#e0e0e0"
          strokeWidth="4"
          fill="transparent"
        />
        <circle
          cx="50%"
          cy="50%"
          r={radius}
          stroke={color}
          strokeWidth="4"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-stroke-dashoffset duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className={`font-bold ${size === 'large' ? 'text-3xl' : size === 'medium' ? 'text-2xl' : 'text-xl'}`}
              style={{ color }}>
          {score.toFixed(0)}
        </span>
        <span className="text-xs text-gray-500">分</span>
      </div>
    </div>
  );
};

// 维度分数卡片
const DimensionScoreCard = ({
  label,
  score,
  maxScore = 100
}: {
  label: string;
  score: number;
  maxScore?: number
}) => {
  const percentage = (score / maxScore) * 100;
  const color = getScoreColor(score);
  const heights = {
    critical: 'h-1',
    high: 'h-1.5',
    medium: 'h-2',
    low: 'h-2.5',
  };

  return (
    <div className="flex flex-col gap-1.5 p-3 bg-gray-50 rounded-lg">
      <div className="flex justify-between items-end">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-lg font-bold" style={{ color }}>{score.toFixed(1)}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full overflow-hidden h-2">
        <div
          className={`rounded-full transition-all duration-500 ${heights[score >= 90 ? 'critical' : score >= 80 ? 'high' : score >= 70 ? 'medium' : 'low']}`}
          style={{
            width: `${percentage}%`,
            backgroundColor: color
          }}
        />
      </div>
    </div>
  );
};

// 问题列表组件
const IssueList = ({ issues }: { issues: Issue[] }) => {
  if (issues.length === 0) {
    return (
      <div className="text-center py-8 bg-green-50 rounded-lg border border-green-100">
        <span className="text-green-600 text-lg">🎉</span>
        <p className="text-green-700 mt-2">未发现明显问题</p>
      </div>
    );
  }

  // 按严重程度排序
  const severityOrder: Record<Issue['severity'], number> = {
    critical: 0,
    high: 1,
    medium: 2,
    low: 3,
  };

  const sortedIssues = [...issues].sort(
    (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
  );

  return (
    <div className="space-y-3">
      {sortedIssues.map((issue, index) => {
        const style = getSeverityStyle(issue.severity);
        return (
          <div
            key={index}
            className={`p-4 rounded-lg border-l-4 bg-white shadow-sm ${style.class}`}
            style={{ borderColor: getScoreColor(issue.severity === 'critical' ? 30 : issue.severity === 'high' ? 50 : 70) }}
          >
            <div className="flex items-start gap-3">
              <span className="text-xl">{style.icon}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-semibold lowercase text-gray-700">{style.label}优先</span>
                  <span className="text-xs text-gray-500 uppercase">{issue.dimension}</span>
                </div>
                <p className="text-gray-800 mb-2">{issue.description}</p>
                {issue.recommendation && (
                  <div className="bg-blue-50 p-2 rounded text-sm">
                    <span className="font-medium text-blue-700">💡 建议:</span>
                    <span className="text-blue-800 ml-1">{issue.recommendation}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// 综合建议列表
const RecommendationsList = ({ recommendations }: { recommendations: string[] }) => {
  if (recommendations.length === 0) {
    return null;
  }

  return (
    <div className="mt-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
        <span>📋</span> 综合改进建议
      </h3>
      <div className="space-y-2">
        {recommendations.map((rec, index) => (
          <div key={index} className="flex gap-3 items-start p-3 bg-amber-50 rounded-lg">
            <span className="text-amber-500 font-bold shrink-0">Tip {index + 1}:</span>
            <p className="text-gray-700 text-sm">{rec}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

// 评估结果展示组件
const EvaluationResult = ({ result, onCopy }: EvaluationResultProps) => {
  const overallScore = result.overall_score;
  const scoreColor = getScoreColor(overallScore);

  // 复制功能
  const handleCopy = () => {
    const report = generateReportText();
    navigator.clipboard.writeText(report);
    onCopy?.();
  };

  // 生成报告文本
  const generateReportText = () => {
    const lines = [
      '=============== 病历质量评估报告 ===============',
      '',
      `总体评分: ${overallScore.toFixed(1)} / 100`,
      '',
      '维度评分:',
      `  - 完整性: ${result.dimension_scores.completeness.toFixed(1)}`,
      `  - 逻辑性: ${result.dimension_scores.logicality.toFixed(1)}`,
      `  - 及时性: ${result.dimension_scores.timeliness.toFixed(1)}`,
      `  - 规范性: ${result.dimension_scores.normativity.toFixed(1)}`,
      '',
      `问题数量: ${result.issues.length}`,
      '',
    ];

    if (result.issues.length > 0) {
      lines.push('主要问题:');
      result.issues.forEach((issue, index) => {
        lines.push(`  ${index + 1}. [${issue.severity.toUpperCase()}] ${issue.description}`);
      });
      lines.push('');
    }

    if (result.recommendations.length > 0) {
      lines.push('改进建议:');
      result.recommendations.forEach((rec, index) => {
        lines.push(`  ${index + 1}. ${rec}`);
      });
    }

    lines.push('');
    lines.push('=============================================');

    return lines.join('\n');
  };

  return (
    <div className="evaluation-result space-y-6 animate-fade-in">
      {/* 总体评分 */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
          <span>📊</span> 总体评分
        </h2>
        <div className="flex items-center justify-center gap-8">
          <ProgressBar score={overallScore} size="large" />
          <div className="flex-1 space-y-4">
            <div className="text-center">
              <span className="text-sm text-gray-500 block mb-1">评估得分</span>
              <span className={`text-4xl font-bold ${scoreColor}`}>{overallScore.toFixed(1)}</span>
              <span className="text-gray-400 ml-1">/ 100</span>
            </div>
            <div className="text-center">
              <span className={`inline-block px-4 py-1 rounded-full text-sm font-medium ${
                overallScore >= 90 ? 'bg-green-100 text-green-800' :
                overallScore >= 80 ? 'bg-green-50 text-green-700' :
                overallScore >= 70 ? 'bg-yellow-50 text-yellow-700' :
                overallScore >= 60 ? 'bg-orange-50 text-orange-700' :
                'bg-red-50 text-red-700'
              }`}>
                {overallScore >= 90 ? '优秀' :
                 overallScore >= 80 ? '良好' :
                 overallScore >= 70 ? '合格' :
                 overallScore >= 60 ? '需改进' : '较差'}
              </span>
            </div>
            <div className="flex justify-center gap-2">
              <button
                onClick={handleCopy}
                className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
              >
                <span>📋</span> 拷贝报告
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 维度评分 */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <span>📈</span> 维度评分
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <DimensionScoreCard
            label="完整性"
            score={result.dimension_scores.completeness}
          />
          <DimensionScoreCard
            label="逻辑性"
            score={result.dimension_scores.logicality}
          />
          <DimensionScoreCard
            label="及时性"
            score={result.dimension_scores.timeliness}
          />
          <DimensionScoreCard
            label="规范性"
            score={result.dimension_scores.normativity}
          />
        </div>
      </div>

      {/* 问题列表 */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <span>🔍</span> 发现问题
            <span className="px-2 py-1 bg-gray-100 rounded-full text-sm font-medium">
              {result.issues.length}
            </span>
          </h2>
        </div>
        <IssueList issues={result.issues} />
      </div>

      {/* 综合建议 */}
      <RecommendationsList recommendations={result.recommendations} />
    </div>
  );
};

export default EvaluationResult;
