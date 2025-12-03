from typing import Optional, List
import datetime as dt
from pydantic import BaseModel

#
# -------------------------------------------------------------------
# RAGE BREAKDOWN
# -------------------------------------------------------------------
#

class RageBreakdown(BaseModel):
    rage_score: float
    difficulty_rage: float
    technical_rage: float
    social_toxicity_rage: float
    ui_design_rage: float

    max_achievement_drop: Optional[float] = None
    max_drop_from: Optional[float] = None
    max_drop_to: Optional[float] = None
    max_drop_achievement: Optional[str] = None


#
# -------------------------------------------------------------------
# BASIC GAME MODELS
# -------------------------------------------------------------------
#

class GameSummary(BaseModel):
    id: int
    name: str
    slug: str
    rage_score: float

    class Config:
        orm_mode = True


class GameDetail(BaseModel):
    id: int
    name: str
    slug: str
    rage: RageBreakdown

    class Config:
        orm_mode = True


#
# -------------------------------------------------------------------
# STEAM REVIEWS
# -------------------------------------------------------------------
#

class SteamReviewOut(BaseModel):
    is_positive: bool
    language: Optional[str] = None
    review_text: str
    created_at_steam: Optional[dt.datetime] = None

    class Config:
        orm_mode = True


#
# -------------------------------------------------------------------
# REDDIT POSTS
# -------------------------------------------------------------------
#

class RedditPostOut(BaseModel):
    title: str
    body: str
    upvotes: Optional[int] = None
    num_comments: Optional[int] = None
    created_utc: Optional[dt.datetime] = None

    class Config:
        orm_mode = True


#
# -------------------------------------------------------------------
# RAGE WORD CLOUD
# -------------------------------------------------------------------
#

class RageWordOut(BaseModel):
    word: str
    score: float


#
# -------------------------------------------------------------------
# RAGE TIMELINE
# -------------------------------------------------------------------
#

class RageTimelinePoint(BaseModel):
    date: dt.date
    rage_score: float
    positive: int
    negative: int
    total: int

    class Config:
        orm_mode = True


#
# -------------------------------------------------------------------
# RAGE CLIPS (YouTube / Twitch)
# -------------------------------------------------------------------
#

class RageClipOut(BaseModel):
    id: int
    source: Optional[str] = None
    url: str
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None

    class Config:
        orm_mode = True


#
# -------------------------------------------------------------------
# COMPARISON (optional, already used)
# -------------------------------------------------------------------
#

class GameComparison(BaseModel):
    left: GameDetail
    right: GameDetail
