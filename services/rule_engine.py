"""规则引擎服务"""
import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import ahocorasick


@dataclass
class RuleResult:
    """规则检测结果"""
    is_violated: bool
    violation_types: List[str]
    matched_keywords: List[str]
    matched_positions: List[tuple]
    severity: str
    evidence: str


class RuleEngine:
    """规则引擎"""

    def __init__(self, rules_path: str = "config/rules.yaml"):
        """初始化规则引擎
        
        Args:
            rules_path: 规则配置文件路径
        """
        self.rules_path = Path(rules_path)
        self.blacklist_rules: Dict = {}
        self.whitelist: List[str] = []
        self.automaton = None
        self.regex_patterns: Dict = {}
        self.last_reload_time: Optional[datetime] = None
        
        self.load_rules()

    def load_rules(self) -> None:
        """从YAML文件加载规则"""
        if not self.rules_path.exists():
            raise FileNotFoundError(f"规则文件不存在: {self.rules_path}")

        with open(self.rules_path, "r", encoding="utf-8") as f:
            rules_data = yaml.safe_load(f)

        self.blacklist_rules = rules_data.get("blacklist", {})
        self.whitelist = rules_data.get("whitelist", [])
        
        # 构建AC自动机（用于精确匹配）
        self._build_automaton()
        
        # 编译正则表达式
        self._compile_regex_patterns()
        
        self.last_reload_time = datetime.now()

    def _build_automaton(self) -> None:
        """构建AC自动机用于快速多模式匹配"""
        self.automaton = ahocorasick.Automaton()
        
        # 添加所有需要精确匹配的关键词
        has_words = False
        for category, rules in self.blacklist_rules.items():
            for rule in rules:
                pattern = rule.get("pattern", "")
                # 如果不是正则表达式（不包含特殊字符），添加到AC自动机
                if not any(char in pattern for char in r"()[]{}.*+?|^\\$\\\\"):
                    self.automaton.add_word(
                        pattern,
                        (category, rule.get("type"), rule.get("severity"))
                    )
                    has_words = True
        
        # 只有添加了词后才调用 make_automaton
        if has_words:
            self.automaton.make_automaton()

    def _compile_regex_patterns(self) -> None:
        """编译正则表达式模式"""
        self.regex_patterns = {}
        
        for category, rules in self.blacklist_rules.items():
            self.regex_patterns[category] = []
            for rule in rules:
                pattern = rule.get("pattern", "")
                try:
                    compiled = re.compile(pattern)
                    self.regex_patterns[category].append({
                        "pattern": compiled,
                        "type": rule.get("type"),
                        "severity": rule.get("severity"),
                        "original": pattern
                    })
                except re.error as e:
                    print(f"正则表达式编译失败: {pattern}, 错误: {e}")

    def check_text(self, text: str) -> RuleResult:
        """检查文本是否违规
        
        Args:
            text: 待检测文本
            
        Returns:
            RuleResult: 检测结果
        """
        if not text:
            return RuleResult(
                is_violated=False,
                violation_types=[],
                matched_keywords=[],
                matched_positions=[],
                severity="none",
                evidence=""
            )

        # 检查白名单
        for whitelist_item in self.whitelist:
            if whitelist_item in text:
                text = text.replace(whitelist_item, "")

        violation_types = []
        matched_keywords = []
        matched_positions = []
        max_severity = "none"
        
        severity_order = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

        # 使用AC自动机进行快速匹配（只有在自动机已构建时）
        if self.automaton:
            try:
                for end_index, (category, vtype, severity) in self.automaton.iter(text):
                    violation_types.append(vtype)
                    matched_positions.append((end_index - len(text) + 1, end_index))
                    if severity_order.get(severity, 0) > severity_order.get(max_severity, 0):
                        max_severity = severity
            except AttributeError:
                # 如果自动机未构建，跳过
                pass

        # 使用正则表达式匹配
        for category, patterns in self.regex_patterns.items():
            for pattern_info in patterns:
                matches = pattern_info["pattern"].finditer(text)
                for match in matches:
                    keyword = match.group()
                    matched_keywords.append(keyword)
                    violation_types.append(pattern_info["type"])
                    matched_positions.append((match.start(), match.end()))
                    
                    severity = pattern_info["severity"]
                    if severity_order.get(severity, 0) > severity_order.get(max_severity, 0):
                        max_severity = severity

        # 去重
        violation_types = list(set(violation_types))
        matched_keywords = list(set(matched_keywords))

        is_violated = len(violation_types) > 0
        evidence = f"检测到违规关键词: {', '.join(matched_keywords[:5])}" if matched_keywords else ""

        return RuleResult(
            is_violated=is_violated,
            violation_types=violation_types,
            matched_keywords=matched_keywords,
            matched_positions=matched_positions,
            severity=max_severity,
            evidence=evidence
        )

    def hot_reload(self) -> bool:
        """热更新规则（不重启服务）
        
        Returns:
            bool: 是否更新成功
        """
        try:
            self.load_rules()
            return True
        except Exception as e:
            print(f"规则热更新失败: {e}")
            return False

    def get_statistics(self) -> Dict:
        """获取规则统计信息
        
        Returns:
            Dict: 统计信息
        """
        total_rules = sum(len(rules) for rules in self.blacklist_rules.values())
        
        return {
            "total_rules": total_rules,
            "categories": list(self.blacklist_rules.keys()),
            "whitelist_count": len(self.whitelist),
            "last_reload_time": self.last_reload_time.isoformat() if self.last_reload_time else None
        }
