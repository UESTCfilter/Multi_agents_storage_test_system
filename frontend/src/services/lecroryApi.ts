// LeCroy Script 相关 API 服务

import axios from 'axios';

export type GenerationMode = 'template' | 'llm' | 'hybrid';

export interface LeCroyScriptGenerateRequest {
  description: string;
  test_name?: string;
  mode?: GenerationMode;
}

export interface LeCroyScriptOptimizeRequest {
  script_id: number;
  feedback: string;
}

export interface LeCroyScriptGenerateResponse {
  success: boolean;
  id?: number;
  test_name?: string;
  protocol?: string;
  scenario?: string;
  peg_content?: string;
  pevs_content?: string;
  generation_mode?: string;
  reasoning?: string;
  optimized_from?: number;
  error?: string;
}

export interface LeCroyScriptInfo {
  id: number;
  test_name: string;
  protocol: string | null;
  scenario: string | null;
  generation_mode: string | null;
  peg_preview: string;
  created_at: string;
}

export interface LeCroyScriptDetail {
  id: number;
  test_name: string;
  protocol: string | null;
  scenario: string | null;
  description: string | null;
  peg_content: string;
  pevs_content: string;
  generation_mode: string | null;
  feedback_history: Array<{ feedback: string; timestamp: string; reasoning: string }>;
  optimized_from: number | null;
  created_at: string;
}

export const lecroyApi = {
  // 从自然语言描述生成脚本
  generateScript: async (projectId: string | number, request: LeCroyScriptGenerateRequest): Promise<LeCroyScriptGenerateResponse> => {
    const res = await axios.post(`/api/projects/${projectId}/generate-lecroy-script`, request);
    return res.data;
  },

  // 优化已有脚本
  optimizeScript: async (projectId: string | number, request: LeCroyScriptOptimizeRequest): Promise<LeCroyScriptGenerateResponse> => {
    const res = await axios.post(`/api/projects/${projectId}/optimize-lecroy-script`, request);
    return res.data;
  },

  // 获取脚本列表
  getScripts: async (projectId: string | number): Promise<{ scripts: LeCroyScriptInfo[]; total: number }> => {
    const res = await axios.get(`/api/projects/${projectId}/lecroy-scripts`);
    return res.data;
  },

  // 获取单个脚本内容
  getScript: async (projectId: string | number, scriptId: number): Promise<LeCroyScriptDetail> => {
    const res = await axios.get(`/api/projects/${projectId}/lecroy-scripts/${scriptId}`);
    return res.data;
  },

  // 删除脚本
  deleteScript: async (projectId: string | number, scriptId: number): Promise<{ message: string; script_id: number }> => {
    const res = await axios.delete(`/api/projects/${projectId}/lecroy-scripts/${scriptId}`);
    return res.data;
  }
};
