from enum import Enum

class TopicName(str, Enum):
    POLITICS = "Politics"
    HEALTH = "Health"
    SPORT = "Sport"
    TECH = "Tech"

class ReactionName(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"

class Status(str, Enum):
    LIVE = "Live"
    EXPIRED = "Expired"