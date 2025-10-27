"""LLM服务"""
import json
import yaml
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
from openai import OpenAI
import time


@dataclass
class LLMResult:
    """LLM审核结果"""
    is_compliant: bool
    violation_types: List[str]
    evidence: str
    confidence: float
    reasoning: str
    tokens_used: int
    api_cost: float


class LLMService:
    """LLM服务包装类"""

    def __init__(
        self,
        deepseek_api_key: str = "",
        openai_api_key: Optional[str] = None,
        prompts_path: str = "config/prompts.yaml"
    ):
        """初始化LLM服务
        
        Args:
            deepseek_api_key: DeepSeek API密钥
            openai_api_key: OpenAI API密钥
            prompts_path: Prompt模板文件路径
        """
        self.deepseek_api_key = deepseek_api_key
        self.openai_api_key = openai_api_key
        self.prompts_path = Path(prompts_path)
        
        # 初始化客户端
        self.deepseek_client = None
        if deepseek_api_key:
            self.deepseek_client = OpenAI(
                api_key=deepseek_api_key,
                base_url="https://api.deepseek.com"
            )
        
        self.openai_client = None
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
        
        # 加载Prompt模板
        self.prompts = self._load_prompts()
        
        # Token统计
        self.total_tokens_used = 0
        self.total_api_cost = 0.0

    def _load_prompts(self) -> Dict:
        """加载Prompt模板"""
        if not self.prompts_path.exists():
            raise FileNotFoundError(f"Prompt文件不存在: {self.prompts_path}")
        
        with open(self.prompts_path, "r", encoding="utf-8") as f:
            prompts_data = yaml.safe_load(f)
        
        active_version = prompts_data.get("active_version", "v1")
        return prompts_data["prompts"][active_version]

    def _select_model(self, model_type: str = "light") -> tuple:
        """选择模型
        
        Args:
            model_type: 模型类型 (light/strong)
            
        Returns:
            tuple: (client, model_name, cost_per_1k_tokens)
        """
        if model_type == "strong":
            if self.openai_client:
                return self.openai_client, "gpt-4", 0.03
            elif self.deepseek_client:
                return self.deepseek_client, "deepseek-chat", 0.00014
        else:  # light
            if self.deepseek_client:
                return self.deepseek_client, "deepseek-chat", 0.00014
            elif self.openai_client:
                return self.openai_client, "gpt-3.5-turbo", 0.001
        
        raise ValueError("没有可用的LLM客户端")

    def review_content(
        self,
        content: str,
        regulations: str = "",
        model_type: str = "light",
        max_retries: int = 3
    ) -> LLMResult:
        """审核内容
        
        Args:
            content: 待审核内容
            regulations: 参考法规
            model_type: 模型类型 (light/strong)
            max_retries: 最大重试次数
            
        Returns:
            LLMResult: 审核结果
        """
        client, model_name, cost_per_1k = self._select_model(model_type)
        
        # 构建Prompt
        system_prompt = self.prompts["system"]
        task_prompt = self.prompts["task"].format(
            content=content,
            regulations=regulations if regulations else "无特定法规参考"
        )
        
        # 重试机制
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": task_prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                
                # 解析结果
                result_text = response.choices[0].message.content
                result_json = json.loads(result_text)
                
                # 统计Token
                tokens_used = response.usage.total_tokens
                api_cost = (tokens_used / 1000) * cost_per_1k
                
                self.total_tokens_used += tokens_used
                self.total_api_cost += api_cost
                
                return LLMResult(
                    is_compliant=result_json.get("is_compliant", True),
                    violation_types=result_json.get("violation_types", []),
                    evidence=result_json.get("evidence", ""),
                    confidence=result_json.get("confidence", 0.5),
                    reasoning=result_json.get("reasoning", ""),
                    tokens_used=tokens_used,
                    api_cost=api_cost
                )
                
            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    # 返回低置信度结果
                    return LLMResult(
                        is_compliant=True,
                        violation_types=[],
                        evidence="",
                        confidence=0.3,
                        reasoning=f"JSON解析失败: {str(e)}",
                        tokens_used=0,
                        api_cost=0.0
                    )
            
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise Exception(f"LLM调用失败: {str(e)}")

    def get_statistics(self) -> Dict:
        """获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "total_tokens_used": self.total_tokens_used,
            "total_api_cost": round(self.total_api_cost, 4),
            "deepseek_available": self.deepseek_client is not None,
            "openai_available": self.openai_client is not None
        }
