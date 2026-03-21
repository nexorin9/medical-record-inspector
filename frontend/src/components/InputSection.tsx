import { useState } from 'react';
import { EvaluationRequest, AVAILABLE_MODELS, DEFAULT_MODEL } from '@/types/evaluation';

// 支持的文件类型
const SUPPORTED_FILE_TYPES = ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/pdf'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

// 评估维度选项
const DIMENSION_OPTIONS = [
  { value: 'completeness', label: '完整性' },
  { value: 'logicality', label: '逻辑性' },
  { value: 'timeliness', label: '及时性' },
  { value: 'normativity', label: '规范性' },
];

// 模型选项
const MODEL_OPTIONS = AVAILABLE_MODELS.map(model => ({
  value: model.name,
  label: `${model.name} (${model.provider})`,
  description: model.description,
  provider: model.provider,
}));

interface InputSectionProps {
  onEvaluate: (data: EvaluationRequest) => void;
  templates: Array<{ id: string; name: string; description: string }>;
  loading: boolean;
}

const InputSection = ({ onEvaluate, templates, loading }: InputSectionProps) => {
  const [content, setContent] = useState('');
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');
  const [selectedDims, setSelectedDims] = useState<string[]>(['completeness', 'logicality', 'timeliness', 'normativity']);
  const [selectedModel, setSelectedModel] = useState<string>(DEFAULT_MODEL);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplateId(templateId);
    // 自动填充模板内容（可选）
    if (templateId && templates.length > 0) {
      // 这里可以加载模板内容到输入框
      // setContent(template.content);
    }
  };

  const toggleDimension = (dim: string) => {
    setSelectedDims(prev =>
      prev.includes(dim)
        ? prev.filter(d => d !== dim)
        : [...prev, dim]
    );
  };

  const handleClear = () => {
    setContent('');
    setSelectedTemplateId('');
    setSelectedDims(['completeness', 'logicality', 'timeliness', 'normativity']);
    setSelectedModel(DEFAULT_MODEL);
    setError(null);
    setSelectedFile(null);
    setFileError(null);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 清空文本输入
    setContent('');

    // 验证文件类型
    if (!SUPPORTED_FILE_TYPES.includes(file.type)) {
      const ext = file.name.split('.').pop()?.toLowerCase();
      if (ext === 'docx' || ext === 'pdf') {
        // 文件扩展名正确但 MIME 类型不对（可能是某些浏览器的奇怪行为）
        // 继续处理
      } else {
        setFileError(`不支持的文件类型: ${file.type}`);
        setSelectedFile(null);
        return;
      }
    }

    // 验证文件大小
    if (file.size > MAX_FILE_SIZE) {
      setFileError(`文件过大。最大支持 10MB，当前: ${(file.size / 1024 / 1024).toFixed(2)}MB`);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setFileError(null);

    // 如果有内容，自动触发评估
    if (content.trim()) {
      handleSubmit(e as React.FormEvent);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // 验证输入
    if (!content.trim()) {
      setError('请输入病历文本或上传文件');
      return;
    }

    if (content.length < 10) {
      setError('病历文本太短，请输入更详细的内容');
      return;
    }

    const data: EvaluationRequest = {
      content: content.trim(),
      template_id: selectedTemplateId || undefined,
      evaluation_dims: selectedDims.length > 0 ? selectedDims : undefined,
      model_name: selectedModel || undefined,
    };

    onEvaluate(data);
  };

  return (
    <div className="input-section space-y-4">
      {/* 标题 */}
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">病历质量评估</h2>
        <p className="text-gray-600">
          上传或粘贴病历文本，系统将自动评估其完整性、逻辑性、及时性和规范性
        </p>
      </div>

      {/* 错误消息 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <span>❌</span>
          {error}
        </div>
      )}

      {/* 表单 */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* 病历文本输入 */}
        <div className="space-y-2">
          <label htmlFor="病历文本" className="flex items-center justify-between">
            <span className="font-medium text-gray-700">病历文本 *</span>
            <span className="text-sm text-gray-500">{content.length} 字符</span>
          </label>
          <textarea
            id="病历文本"
            className="w-full h-64 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm leading-relaxed bg-white"
            placeholder="粘贴或输入病历文本...
示例：
主诉：...
现病史：...
既往史：...
体格检查：...
辅助检查：...
诊断：...
治疗经过：...
]"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            disabled={loading}
            spellCheck={false}
          />
        </div>

        {/* 模板选择 */}
        {templates.length > 0 && (
          <div className="space-y-2">
            <label className="block font-medium text-gray-700">参考模板（可选）</label>
            <div className="relative">
              <select
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                value={selectedTemplateId}
                onChange={(e) => handleTemplateSelect(e.target.value)}
                disabled={loading}
              >
                <option value="">请选择参考模板...</option>
                {templates.map(template => (
                  <option key={template.id} value={template.id}>
                    {template.name} - {template.description}
                  </option>
                ))}
              </select>
              <div className="absolute right-3 top-3.5 pointer-events-none text-gray-500">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>
        )}

        {/* 评估维度选择 */}
        <div className="space-y-2">
          <label className="block font-medium text-gray-700">评估维度 *</label>
          <div className="flex flex-wrap gap-2">
            {DIMENSION_OPTIONS.map(dim => (
              <button
                key={dim.value}
                type="button"
                onClick={() => toggleDimension(dim.value)}
                disabled={loading}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedDims.includes(dim.value)
                    ? 'bg-blue-600 text-white shadow-md hover:bg-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {dim.label}
              </button>
            ))}
          </div>
        </div>

        {/* 模型选择 */}
        <div className="space-y-2">
          <label className="block font-medium text-gray-700">LLM 模型 (可选)</label>
          <div className="relative">
            <select
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={loading}
            >
              <option value="">使用默认模型 ({DEFAULT_MODEL})</option>
              {MODEL_OPTIONS.map(model => (
                <option key={model.value} value={model.value}>
                  {model.label} - {model.description}
                </option>
              ))}
            </select>
            <div className="absolute right-3 top-3.5 pointer-events-none text-gray-500">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
          <p className="text-xs text-gray-500">
            选择不同的 LLM 模型进行评估，不同模型质量和成本不同
          </p>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={loading || !content.trim()}
            className={`flex-1 py-3 px-6 rounded-lg font-bold text-white shadow-lg transition-all flex items-center justify-center gap-2 ${
              loading || !content.trim()
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 hover:shadow-xl transform hover:-translate-y-0.5'
            }`}
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>评估中...</span>
              </>
            ) : (
              <>
                <span>开始评估</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleClear}
            disabled={loading && !content}
            className="px-6 py-3 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <span>🗑️</span>
            <span>清空</span>
          </button>
        </div>

        {/* 文件上传 */}
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">或上传文件</label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 hover:bg-blue-50 transition-colors cursor-pointer">
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".docx,.pdf"
              onChange={handleFileSelect}
              disabled={loading}
            />
            <label htmlFor="file-upload" className="cursor-pointer block">
              <div className="flex flex-col items-center gap-2">
                {selectedFile ? (
                  <>
                    <div className="flex items-center gap-2 text-green-600">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className="text-sm font-medium">{selectedFile.name}</span>
                      <span className="text-xs text-gray-500">
                        {(selectedFile.size / 1024).toFixed(1)} KB
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        setSelectedFile(null);
                        setFileError(null);
                      }}
                      className="text-xs text-red-500 hover:text-red-700 mt-2"
                    >
                      取消选择
                    </button>
                  </>
                ) : (
                  <>
                    <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <span className="text-gray-600">点击选择文件 (DOCX/PDF)</span>
                    <span className="text-xs text-gray-400">支持 DOCX、PDF 格式，最大 10MB</span>
                  </>
                )}
              </div>
            </label>
          </div>
          {fileError && (
            <div className="text-red-500 text-sm mt-2 flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {fileError}
            </div>
          )}
        </div>
      </form>
    </div>
  );
};

export default InputSection;
