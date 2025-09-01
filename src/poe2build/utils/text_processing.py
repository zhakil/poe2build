"""PoE2专用文本处理工具"""

import re
import unicodedata
from typing import List, Dict, Optional, Set
from difflib import SequenceMatcher

class PoE2TextProcessor:
    """PoE2专用文本处理工具"""
    
    # PoE2物品名称清理正则
    ITEM_NAME_PATTERNS = {
        'rarity_prefix': re.compile(r'^(Normal|Magic|Rare|Unique|Currency)\s+'),
        'socket_info': re.compile(r'\s+\(\d+[RGBW]-\d+[RGBW].*?\)$'),
        'quality_info': re.compile(r'\s+\(Quality:\s*\+?\d+%\)$'),
        'level_req': re.compile(r'\s+\(Level\s+\d+\)$'),
        'corrupted': re.compile(r'\s+\(Corrupted\)$')
    }
    
    # PoE2技能名称模式
    SKILL_PATTERNS = {
        'support_gem': re.compile(r'\s+Support$'),
        'aura_skill': re.compile(r'^(Grace|Hatred|Anger|Wrath|Discipline|Clarity)\b'),
        'curse_skill': re.compile(r'(Curse|Hex|Mark)$')
    }
    
    @classmethod
    def clean_item_name(cls, item_name: str) -> str:
        """清理物品名称，移除多余信息"""
        if not item_name:
            return ""
            
        cleaned = item_name.strip()
        
        # 应用清理模式
        for pattern_name, pattern in cls.ITEM_NAME_PATTERNS.items():
            cleaned = pattern.sub('', cleaned)
            
        return cleaned.strip()
        
    @classmethod
    def normalize_skill_name(cls, skill_name: str) -> str:
        """标准化技能名称"""
        if not skill_name:
            return ""
            
        normalized = skill_name.strip()
        
        # 移除常见后缀
        normalized = cls.SKILL_PATTERNS['support_gem'].sub('', normalized)
        
        # 标准化大小写
        normalized = ' '.join(word.capitalize() for word in normalized.split())
        
        return normalized
        
    @classmethod
    def extract_numeric_values(cls, text: str) -> Dict[str, List[float]]:
        """从文本中提取数值"""
        # 常见的数值模式
        patterns = {
            'percentage': re.compile(r'(\d+(?:\.\d+)?)\s*%'),
            'flat_value': re.compile(r'(\d+(?:\.\d+)?)\s+to\s+(\d+(?:\.\d+)?)'),
            'single_number': re.compile(r'\b(\d+(?:\.\d+)?)\b'),
            'range': re.compile(r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)')
        }
        
        results = {}
        
        for pattern_name, pattern in patterns.items():
            matches = pattern.findall(text)
            if matches:
                if pattern_name == 'flat_value':
                    # 返回范围的平均值
                    results[pattern_name] = [
                        (float(match[0]) + float(match[1])) / 2 
                        for match in matches
                    ]
                elif pattern_name == 'range':
                    results[pattern_name] = [
                        (float(match[0]) + float(match[1])) / 2
                        for match in matches  
                    ]
                else:
                    results[pattern_name] = [float(match) for match in matches]
                    
        return results
        
    @classmethod
    def calculate_text_similarity(cls, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        if not text1 or not text2:
            return 0.0
            
        # 标准化文本
        norm_text1 = cls._normalize_text(text1)
        norm_text2 = cls._normalize_text(text2)
        
        # 使用序列匹配计算相似度
        return SequenceMatcher(None, norm_text1, norm_text2).ratio()
        
    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """标准化文本用于比较"""
        # 转为小写
        normalized = text.lower()
        
        # 移除Unicode组合字符
        normalized = unicodedata.normalize('NFKD', normalized)
        
        # 移除标点符号和多余空格
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
        
    @classmethod
    def fuzzy_search(cls, query: str, candidates: List[str], 
                    threshold: float = 0.6) -> List[tuple]:
        """模糊搜索"""
        if not query or not candidates:
            return []
            
        results = []
        for candidate in candidates:
            similarity = cls.calculate_text_similarity(query, candidate)
            if similarity >= threshold:
                results.append((candidate, similarity))
                
        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results
        
    @classmethod
    def extract_build_tags(cls, build_description: str) -> Set[str]:
        """从构筑描述中提取标签"""
        if not build_description:
            return set()
            
        # 预定义的标签模式
        tag_patterns = {
            'damage_type': re.compile(r'\b(physical|fire|cold|lightning|chaos)\b', re.I),
            'build_style': re.compile(r'\b(bow|spell|melee|minion|totem)\b', re.I),
            'defense': re.compile(r'\b(life|es|hybrid|armor|evasion)\b', re.I),
            'budget': re.compile(r'\b(budget|cheap|expensive|mirror)\b', re.I),
            'difficulty': re.compile(r'\b(beginner|easy|medium|hard|expert)\b', re.I)
        }
        
        tags = set()
        for category, pattern in tag_patterns.items():
            matches = pattern.findall(build_description)
            for match in matches:
                tags.add(f"{category}:{match.lower()}")
                
        return tags
        
    @classmethod
    def extract_currency_mentions(cls, text: str) -> Dict[str, List[float]]:
        """提取文本中的货币提及"""
        currency_patterns = {
            'divine': re.compile(r'(\d+(?:\.\d+)?)\s*(?:divine|div)', re.I),
            'chaos': re.compile(r'(\d+(?:\.\d+)?)\s*(?:chaos|c)', re.I),
            'exalted': re.compile(r'(\d+(?:\.\d+)?)\s*(?:exalted|ex)', re.I),
            'ancient': re.compile(r'(\d+(?:\.\d+)?)\s*(?:ancient|anc)', re.I)
        }
        
        results = {}
        for currency, pattern in currency_patterns.items():
            matches = pattern.findall(text)
            if matches:
                results[currency] = [float(match) for match in matches]
                
        return results
        
    @classmethod
    def format_build_summary(cls, build_data: Dict) -> str:
        """格式化构筑摘要"""
        template = "{class_name} {ascendancy} - {main_skill}\n"
        template += "预估DPS: {estimated_dps:,}\n"
        template += "生命: {total_life:,}"
        
        if build_data.get('energy_shield', 0) > 0:
            template += " | 能量护盾: {energy_shield:,}"
            
        template += "\n预算: {total_cost} {currency}"
        
        try:
            return template.format(**build_data)
        except KeyError as e:
            return f"构筑摘要格式错误: 缺少字段 {e}"

class TextTemplate:
    """文本模板处理器"""
    
    def __init__(self, template: str):
        self.template = template
        self.variables = self._extract_variables()
        
    def _extract_variables(self) -> Set[str]:
        """提取模板变量"""
        return set(re.findall(r'\{(\w+)\}', self.template))
        
    def render(self, **kwargs) -> str:
        """渲染模板"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
            
    def validate_variables(self, **kwargs) -> List[str]:
        """验证模板变量"""
        missing = []
        for var in self.variables:
            if var not in kwargs:
                missing.append(var)
        return missing
        
    def get_required_variables(self) -> Set[str]:
        """获取必需的模板变量"""
        return self.variables.copy()

# 预定义的PoE2文本模板
class PoE2Templates:
    """预定义的PoE2文本模板"""
    
    BUILD_SUMMARY = TextTemplate(
        "{class_name} {ascendancy} - {main_skill}\n"
        "预估DPS: {estimated_dps:,}\n"
        "生命: {total_life:,} | 能量护盾: {energy_shield:,}\n"
        "预算: {total_cost} {currency}"
    )
    
    ITEM_DESCRIPTION = TextTemplate(
        "{item_name} ({item_type})\n"
        "价格: {price} {currency}\n"
        "品质: {quality}%\n"
        "{modifiers}"
    )
    
    ERROR_MESSAGE = TextTemplate(
        "错误: {error_type}\n"
        "详细信息: {error_details}\n"
        "建议: {suggestion}"
    )
    
    MARKET_LISTING = TextTemplate(
        "[{timestamp}] {item_name}\n"
        "价格: {price} {currency}\n"
        "卖家: {seller_name}\n"
        "备注: {note}"
    )
    
    BUILD_COMPARISON = TextTemplate(
        "构筑对比:\n"
        "A: {build_a_name} - DPS: {build_a_dps:,}\n"
        "B: {build_b_name} - DPS: {build_b_dps:,}\n"
        "差异: {dps_difference:+,} DPS ({percentage_difference:+.1f}%)"
    )

class PoE2TextUtils:
    """PoE2文本处理实用函数"""
    
    @staticmethod
    def format_large_number(number: float, precision: int = 1) -> str:
        """格式化大数字"""
        if number >= 1_000_000:
            return f"{number/1_000_000:.{precision}f}M"
        elif number >= 1_000:
            return f"{number/1_000:.{precision}f}K"
        else:
            return f"{number:,.{precision}f}".rstrip('0').rstrip('.')
            
    @staticmethod
    def format_currency(amount: float, currency: str) -> str:
        """格式化货币显示"""
        formatted_amount = PoE2TextUtils.format_large_number(amount)
        currency_symbols = {
            'divine': 'div',
            'chaos': 'c', 
            'exalted': 'ex',
            'ancient': 'anc'
        }
        
        symbol = currency_symbols.get(currency.lower(), currency)
        return f"{formatted_amount} {symbol}"
        
    @staticmethod
    def format_percentage(value: float, show_plus: bool = True) -> str:
        """格式化百分比"""
        if show_plus and value > 0:
            return f"+{value:.1f}%"
        return f"{value:.1f}%"
        
    @staticmethod
    def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
        """截断文本"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
        
    @staticmethod
    def capitalize_words(text: str, exceptions: List[str] = None) -> str:
        """单词首字母大写，支持例外词"""
        if not text:
            return ""
            
        exceptions = exceptions or ['of', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for']
        words = text.split()
        
        result = []
        for i, word in enumerate(words):
            # 第一个单词总是大写
            if i == 0 or word.lower() not in exceptions:
                result.append(word.capitalize())
            else:
                result.append(word.lower())
                
        return ' '.join(result)

# 便利函数
def clean_poe2_item_name(item_name: str) -> str:
    """快速清理PoE2物品名称"""
    return PoE2TextProcessor.clean_item_name(item_name)

def search_poe2_items(query: str, item_list: List[str], threshold: float = 0.6) -> List[tuple]:
    """快速搜索PoE2物品"""
    return PoE2TextProcessor.fuzzy_search(query, item_list, threshold)

def format_poe2_currency(amount: float, currency: str) -> str:
    """快速格式化PoE2货币"""
    return PoE2TextUtils.format_currency(amount, currency)

def extract_poe2_numbers(text: str) -> Dict[str, List[float]]:
    """快速提取PoE2文本中的数值"""
    return PoE2TextProcessor.extract_numeric_values(text)