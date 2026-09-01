from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Post(BaseModel):
    id: str
    author_id: str
    author_handle: str
    text: str
    created_at: datetime
    likes: int = 0
    reposts: int = 0
    replies: int = 0
    is_reply: bool = False
    author_created_at: Optional[datetime] = None
    followers: int = 0


class Asset(BaseModel):
    cashtag: str
    name: str
    asset_class: str = "equity"  # equity | crypto | etf | other
    mega: bool = False
    illiquid: bool = False
    notes: str = ""


class Extracted(BaseModel):
    post: Post
    cashtags: list[str]


class Edge(BaseModel):
    source: str
    target: str
    weight: float
    unique_authors: int
    posts: int


class NodeStats(BaseModel):
    cashtag: str
    mentions: int
    unique_authors: int
    first_timers: int = 0
    first_timer_share: float = 0.0
    baseline_unique: float = 0.0
    unique_delta: float = 0.0
    mega: bool = False
    illiquid: bool = False


class PiggybackHit(BaseModel):
    host: str
    parasite: str
    co_posts: int
    unique_authors: int
    score: float
    reason: str


class Origin(BaseModel):
    cashtag: str
    post_id: str
    author_handle: str
    created_at: datetime
    likes: int
    text: str


class FarmCluster(BaseModel):
    kind: str  # template | burst
    template: str
    score: float
    unique_authors: int
    posts: int
    handles: list[str]
    post_ids: list[str]
    reason: str


class Snapshot(BaseModel):
    generated_at: datetime
    window_hours: int
    source: str = "fixture"
    nodes: list[NodeStats]
    edges: list[Edge]
    piggybacks: list[PiggybackHit]
    farms: list[FarmCluster] = Field(default_factory=list)
    origins: list[Origin] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
