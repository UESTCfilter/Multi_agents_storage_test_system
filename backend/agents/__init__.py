"""智能体基类 - 接入 LLM API（当前：Moonshot Kimi k2.6）"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import os
import httpx

# LLM API 配置（当前：Moonshot Kimi k2.6）
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("MOONSHOT_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.moonshot.cn/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "kimi-k2.6")


class LLMAPIError(Exception):
    """LLM API 调用异常"""
    pass


async def call_llm(messages: list, temperature: float = 1.0, max_tokens: int = 4000) -> str:
    """调用 LLM API（当前：Moonshot Kimi k2.6）"""
    if not LLM_API_KEY:
        raise LLMAPIError("未设置 LLM_API_KEY 环境变量")
    
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        msg = data["choices"][0]["message"]
        content = msg.get("content", "")
        # 某些模型可能返回空 content 但带 reasoning_content
        if not content or not content.strip():
            content = msg.get("reasoning_content", "") or ""
        return content


# 保留旧别名兼容已有导入
async def call_kimi(messages: list, temperature: float = 1.0, max_tokens: int = 4000) -> str:
    """兼容别名，实际调用当前配置的 LLM"""
    return await call_llm(messages, temperature, max_tokens)


KimiAPIError = LLMAPIError


class BaseAgent(ABC):
    """智能体基类"""
    
    def __init__(self, name: str, description: str, capabilities: list = None):
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        self.status = "idle"
        self.last_output = None
        self.last_error = None
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "status": self.status,
            "last_run": self.last_output is not None
        }


class TestingExpertAgent(BaseAgent):
    """测试专家智能体基类 - 接入 Kimi K2.5"""
    
    def __init__(self, name: str, expertise: str, description: str):
        super().__init__(
            name=name,
            description=description,
            capabilities=[expertise, "测试分析", "缺陷预测"]
        )
        self.expertise = expertise

    def _strip_thinking(self, text: str) -> str:
        """去除LLM输出中的思考过程，只保留从第一个Markdown标题或正文开始的内容。"""
        if not text:
            return text
        lines = text.split('\n')
        # 优先找到第一个 Markdown 标题行
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('# ') or stripped.startswith('## '):
                return '\n'.join(lines[i:]).strip()
        # 无标题时，查找策略正文关键词
        keywords = ['测试策略', '测试目标', '核心测试项', '测试范围', '测试设计',
                    '测试用例', '1. 测试', '## 1.', '# 1.', '测试环境', '用例ID']
        for i, line in enumerate(lines):
            stripped = line.strip()
            if any(kw in stripped for kw in keywords):
                return '\n'.join(lines[i:]).strip()
        return text.strip()

    def _build_strategy_prompt(self, context: Dict[str, Any]) -> list:
        """构建策略生成 Prompt"""
        device_type = context.get("device_type", "SSD")
        requirements = context.get("requirements", "无具体需求")
        device_name = context.get("device_name", f"{device_type}设备")
        
        system_msg = f"""你是{self.name}，专注于{self.expertise}。
你的任务是为存储设备生成专业的测试策略文档。

输出要求：
1. 使用 Markdown 格式
2. 包含具体的测试项、判定标准、推荐工具
3. 内容专业可执行，不要泛泛而谈
4. 针对 {device_type} 设备特点定制内容
5. 你的输出必须直接以 Markdown 标题（# 或 ##）开头，不要有任何前言、背景说明、自我对话、计划、分析过程或思考过程。"""

        user_msg = f"""请为以下设备生成测试策略：

设备类型: {device_type}
设备名称: {device_name}
测试需求: {requirements}

我的专业能力: {', '.join(self.capabilities)}

请生成包含以下内容的测试策略：
## 1. 测试目标
## 2. 核心测试项（带判定标准）
## 3. 测试工具推荐
## 4. 风险点与注意事项"""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
    
    def _build_design_prompt(self, context: Dict[str, Any]) -> list:
        """构建设计生成 Prompt"""
        device_type = context.get("device_type", "SSD")
        strategy = context.get("strategy", "")
        
        system_msg = f"""你是{self.name}，专注于{self.expertise}。
基于测试策略，生成详细的测试设计方案。

输出要求：
1. 使用 Markdown 格式
2. 测试步骤具体到可执行
3. 包含环境配置、测试数据准备
4. 每个测试项有明确的预期结果
5. 你的输出必须直接以 Markdown 标题（# 或 ##）开头，不要有任何前言、背景说明、自我对话、计划、分析过程或思考过程。"""

        user_msg = f"""请基于以下策略生成测试设计：

设备类型: {device_type}
已有策略: 
{strategy[:2000] if strategy else '（无策略文档）'}

请生成包含以下内容的测试设计：
## 1. 测试环境要求
## 2. 测试数据准备
## 3. 详细测试步骤
## 4. 预期结果与判定标准"""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
    
    def _build_case_prompt(self, context: Dict[str, Any]) -> list:
        """构建用例生成 Prompt"""
        device_type = context.get("device_type", "SSD")
        design = context.get("design", "")
        
        system_msg = f"""你是{self.name}，专注于{self.expertise}。
生成标准化的测试用例，便于执行和追溯。

输出要求：
1. 使用 Markdown 表格格式
2. 每条用例包含：ID、名称、前置条件、步骤、预期结果、优先级
3. 覆盖正常/异常/边界场景
4. 你的输出必须直接以 Markdown 标题（# 或 ##）或表格开头，不要有任何前言、背景说明、自我对话、计划、分析过程或思考过程。"""

        user_msg = f"""请基于以下设计生成测试用例：

设备类型: {device_type}
已有设计:
{design[:1500] if design else '（无设计文档）'}

请生成测试用例表格，格式如下：
| 用例ID | 用例名称 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|----------|--------|

至少生成 5-10 条用例，覆盖关键场景。"""

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行智能体任务 - 调用 Kimi K2.5"""
        task_type = context.get("task_type", "strategy")
        self.status = "running"
        
        try:
            # 根据任务类型构建不同 Prompt
            if task_type == "strategy":
                messages = self._build_strategy_prompt(context)
            elif task_type == "design":
                messages = self._build_design_prompt(context)
            elif task_type == "case":
                messages = self._build_case_prompt(context)
            else:
                messages = [
                    {"role": "system", "content": f"你是{self.name}，{self.description}"},
                    {"role": "user", "content": str(context)}
                ]
            
            # 调用 Kimi API
            output = await call_kimi(messages, temperature=1.0, max_tokens=2000)
            # 过滤思考过程
            output = self._strip_thinking(output)

            # 检查输出是否为空
            if not output or not output.strip():
                raise KimiAPIError("Kimi API 返回空内容")
            
            self.status = "completed"
            self.last_output = output
            
            return {
                "success": True,
                "agent": self.name,
                "expertise": self.expertise,
                "output": output,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.status = "error"
            err_msg = str(e) or f"{type(e).__name__}"
            self.last_error = err_msg
            return {
                "success": False,
                "agent": self.name,
                "error": err_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def analyze_requirements(self, requirements: str) -> str:
        """分析需求文档"""
        messages = [
            {"role": "system", "content": f"你是{self.name}，分析测试需求并提取关键点。输出必须直接以 Markdown 标题（# 或 ##）开头，不要有任何前言、背景说明、自我对话、计划、分析过程或思考过程。"},
            {"role": "user", "content": f"请分析以下需求文档，提取测试要点：\n\n{requirements}"}
        ]
        output = await call_kimi(messages)
        return self._strip_thinking(output)