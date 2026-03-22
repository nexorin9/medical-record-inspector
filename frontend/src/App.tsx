import { useState, useEffect } from 'react';
import InputSection from '@/components/InputSection';
import EvaluationResult from '@/components/EvaluationResult';
import { EvaluationRequest, EvaluationResult as EvaluationResultType } from '@/types/evaluation';
import type { Template } from '@/types/template';
import { fetchTemplates } from '@/hooks/useTemplates';

// 主应用组件
const App = () => {
  const [templates, setTemplates] = useState<Array<{ id: string; name: string; description: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<EvaluationResultType | null>(null);
  const [darkMode, setDarkMode] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 加载模板列表
  useEffect(() => {
    loadTemplates();
  }, []);

  // 加载模板
  const loadTemplates = async () => {
    try {
      const data = await fetchTemplates();
      setTemplates(data.map((t: Template) => ({
        id: t.id,
        name: t.name,
        description: t.description,
      })));
    } catch (err) {
      console.warn('Failed to load templates:', err);
      setTemplates([]);
    }
  };

  // 处理评估
  const handleEvaluate = async (data: EvaluationRequest) => {
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      // 调用后端 API
      const response = await fetch('http://localhost:8000/api/v1/evaluator', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`评估失败: ${response.status} ${response.statusText}`);
      }

      const resultData = await response.json();
      setResult(resultData);
    } catch (err: any) {
      setError(err.message || '评估过程中发生错误，请稍后重试');
      console.error('Evaluation error:', err);
    } finally {
      setLoading(false);
    }
  };

  // 处理复制报告
  const handleCopyReport = () => {
    alert('报告已复制到剪贴板');
  };

  // 切换主题
  const toggleTheme = () => {
    setDarkMode(prev => !prev);
  };

  // 获取容器类名
  const getContainerClass = () => {
    return darkMode
      ? 'min-h-screen bg-gray-900 text-gray-100'
      : 'min-h-screen bg-gray-50 text-gray-900';
  };

  // 获取卡片类名
  const getCardClass = () => {
    return darkMode
      ? 'bg-gray-800 border-gray-700'
      : 'bg-white border-gray-200';
  };

  return (
    <div className={getContainerClass()}>
      {/* 导航栏 */}
      <nav className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-b shadow-sm`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">
                MR
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight">
                  Medical Record Inspector
                </h1>
                <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  病历质量智能评估系统
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <a
                href="https://github.com/yourusername/medical-record-inspector"
                target="_blank"
                rel="noopener noreferrer"
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  darkMode
                    ? 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                }`}
              >
                GitHub
              </a>
              <button
                onClick={toggleTheme}
                className={`p-2 rounded-lg transition-colors ${
                  darkMode
                    ? 'bg-gray-700 hover:bg-gray-600 text-yellow-400'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
                }`}
                title={darkMode ? '切换到浅色模式' : '切换到深色模式'}
              >
                {darkMode ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* 主内容 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 输入区域 */}
        <div className={`rounded-2xl shadow-xl p-6 sm:p-8 mb-8 border ${getCardClass()}`}>
          <InputSection
            onEvaluate={handleEvaluate}
            templates={templates}
            loading={loading}
          />
        </div>

        {/* 错误消息 */}
        {error && (
          <div className="max-w-7xl mx-auto mb-8 bg-red-50 border border-red-200 rounded-xl p-6 flex items-start gap-4">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-red-900">评估失败</h3>
              <p className="text-red-700 mt-1">{error}</p>
              <button
                onClick={() => setError(null)}
                className="mt-3 text-sm text-red-600 hover:text-red-800 font-medium"
              >
                隐藏此消息
              </button>
            </div>
          </div>
        )}

        {/* 评估结果 */}
        {result && (
          <div className="max-w-7xl mx-auto animate-fade-in-up">
            <EvaluationResult result={result} onCopy={handleCopyReport} />
          </div>
        )}

        {/* 未开始评估时的提示 */}
        {!result && !loading && !error && (
          <div className="max-w-7xl mx-auto mt-12 text-center opacity-60">
            <div className="w-24 h-24 mx-auto mb-6 text-gray-300">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <p className="text-lg text-gray-500">病历已准备好，点击"开始评估"进行质控分析</p>
          </div>
        )}
      </main>

      {/* 页脚 */}
      <footer className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-t mt-12`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-center md:text-left">
              <p className={`font-semibold ${darkMode ? 'text-gray-200' : 'text-gray-900'}`}>
                Medical Record Inspector
              </p>
              <p className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                让病历自我审查的质控工具
              </p>
            </div>
            <div className="flex items-center gap-6">
              <a
                href="https://github.com/yourusername/medical-record-inspector"
                target="_blank"
                rel="noopener noreferrer"
                className={`text-sm font-medium transition-colors ${
                  darkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-900'
                }`}
              >
                GitHub 仓库
              </a>
              <a
                href="#"
                className={`text-sm font-medium transition-colors ${
                  darkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-900'
                }`}
              >
                使用文档
              </a>
              <a
                href="#"
                className={`text-sm font-medium transition-colors ${
                  darkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-500 hover:text-gray-900'
                }`}
              >
                关于我们
              </a>
            </div>
          </div>
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 text-center">
            <p className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
              &copy; 2024 Medical Record Inspector. All rights reserved.
            </p>
          </div>
        </div>
      </footer>

      {/* 全局样式 */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fadeIn 0.5s ease-out;
        }
        .animate-fade-in-up {
          animation: fadeInUp 0.5s ease-out;
        }
      `}</style>
    </div>
  );
};

export default App;
