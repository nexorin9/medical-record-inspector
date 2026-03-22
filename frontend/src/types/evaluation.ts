/**
 * 评估结果类型定义
 */

// 可用的模型列表
export interface LLMModel {
  name: string;
  provider: string;
  maxTokens: number;
  contextTokens: number;
  costPerMillionInput: number;
  costPerMillionOutput: number;
  description: string;
}

// 模型提供者
export type LLMProvider = 'openai' | 'dashscope' | 'ernie' | 'local';

// 模型配置
export const AVAILABLE_MODELS: LLMModel[] = [
  // OpenAI models
  {
    name: 'gpt-4',
    provider: 'openai',
    maxTokens: 4096,
    contextTokens: 8192,
    costPerMillionInput: 30.0,
    costPerMillionOutput: 30.0,
    description: 'GPT-4 最佳平衡性能和成本',
  },
  {
    name: 'gpt-4-turbo',
    provider: 'openai',
    maxTokens: 4096,
    contextTokens: 128000,
    costPerMillionInput: 30.0,
    costPerMillionOutput: 30.0,
    description: 'GPT-4 Turbo 支持长上下文',
  },
  {
    name: 'gpt-3.5-turbo',
    provider: 'openai',
    maxTokens: 16385,
    contextTokens: 16385,
    costPerMillionInput: 0.5,
    costPerMillionOutput: 0.5,
    description: 'GPT-3.5 Turbo 快速且经济',
  },
  // Dashscope models
  {
    name: 'qwen-plus',
    provider: 'dashscope',
    maxTokens: 8192,
    contextTokens: 32768,
    costPerMillionInput: 2.0,
    costPerMillionOutput: 2.0,
    description: '通义千问 Plus 平衡性能',
  },
  {
    name: 'qwen-max',
    provider: 'dashscope',
    maxTokens: 8192,
    contextTokens: 32768,
    costPerMillionInput: 2.0,
    costPerMillionOutput: 2.0,
    description: '通义千问 Max 最强性能',
  },
  {
    name: 'qwen-turbo',
    provider: 'dashscope',
    maxTokens: 8192,
    contextTokens: 32768,
    costPerMillionInput: 0.5,
    costPerMillionOutput: 0.5,
    description: '通义千问 Turbo 快速响应',
  },
  // Ernie Bot models
  {
    name: 'ERNIE-Bot-4',
    provider: 'ernie',
    maxTokens: 4096,
    contextTokens: 4096,
    costPerMillionInput: 0.3,
    costPerMillionOutput: 0.3,
    description: '文心一言 4.0 最强性能',
  },
  {
    name: 'ERNIE-Bot-3',
    provider: 'ernie',
    maxTokens: 4096,
    contextTokens: 4096,
    costPerMillionInput: 0.15,
    costPerMillionOutput: 0.15,
    description: '文心一言 3.0 快速响应',
  },
];

// 默认模型
export const DEFAULT_MODEL = 'gpt-4';

// 问题严重程度
export type Severity = 'critical' | 'high' | 'medium' | 'low';

// 评估维度分数
export interface DimensionScores {
  completeness: number;    // 完整性
  logicality: number;      // 逻辑性
  timeliness: number;      // 及时性
  normativity: number;     // 规范性
}

// 问题项
export interface Issue {
  dimension: string;       // 问题所属维度
  severity: Severity;      // 严重程度
  description: string;     // 问题描述
  recommendation?: string; // 改进建议
}

// 评估响应
export interface EvaluationResult {
  overall_score: number;           // 总体评分 (0-100)
  dimension_scores: DimensionScores; // 各维度分数
  issues: Issue[];                 // 问题列表
  recommendations: string[];       // 综合改进建议
}

// 评估请求参数
export interface EvaluationRequest {
  content: string;           // 病历文本
  template_id?: string;      // 模板ID (可选)
  evaluation_dims?: string[]; // 评估维度 (可选)
  model_name?: string;       // LLM模型名称 (可选)
  provider?: string;         // LLM提供者 (可选)
}
