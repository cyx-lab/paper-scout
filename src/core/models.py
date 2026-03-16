from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# -------------------------
# 基础信号：规则 / embedding 等
# -------------------------
class Signals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    keyword_hits: List[str] = Field(default_factory=list)
    author_match: bool = False

    # 规则阶段的分数（Day 1 用）
    rule_score: int = 0

    # embedding 阶段（Day 2 用）
    embedding_score: Optional[float] = None


# -------------------------
# LLM 相关输出（Day 2 起用）
# -------------------------
class LLMRelevance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relevant: bool
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class LLMOutline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    one_liner: str
    method: List[str] = Field(default_factory=list)
    results: List[str] = Field(default_factory=list)
    contribution: List[str] = Field(default_factory=list)
    limitation: List[str] = Field(default_factory=list)


class LLMBlock(BaseModel):
    """
    所有 LLM 产物统一放这里，避免字段散落
    """
    model_config = ConfigDict(extra="forbid")

    relevance: Optional[LLMRelevance] = None
    outline: Optional[LLMOutline] = None
    # Day 3+ 可加：quality / deep_read 等


# -------------------------
# 资源与文件
# -------------------------
class Assets(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pdf_url: Optional[str] = None
    pdf_path: Optional[str] = None   # 本地路径（仅本地脚本会填）


# -------------------------
# 决策 / 策略结果
# -------------------------
class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    final_score: Optional[float] = None
    action: str = "skip"   # skip | download | deep_read
    reason: Optional[str] = None


# -------------------------
# 核心：PaperRecord
# -------------------------
class PaperRecord(BaseModel):
    """
    系统中“一篇论文”的统一表示
    """
    model_config = ConfigDict(extra="forbid")

    # ---- 基本元数据（Fetch 阶段就有）----
    id: str = Field(description="arXiv id, e.g. 2401.01234")
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]

    published: datetime
    updated: Optional[datetime] = None

    # ---- 运行上下文 ----
    source: str = "arxiv"
    mode: str = "daily"   # daily | backfill_10y | ...

    # ---- 各阶段产物 ----
    signals: Signals = Field(default_factory=Signals)
    llm: LLMBlock = Field(default_factory=LLMBlock)
    assets: Assets = Field(default_factory=Assets)
    decision: Decision = Field(default_factory=Decision)

    # ---- 调试 / 追踪 ----
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
