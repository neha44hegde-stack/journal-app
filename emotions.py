"""
Multi-emotion detection: identifies specific emotions present in an entry,
across a much wider emotional range than typical positive/negative/neutral
scoring.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

_EMOTION_LEXICON: dict[str, set[str]] = {
    "joy": {
        "happy", "joy", "joyful", "excited", "great", "wonderful", "love",
        "fun", "glad", "delighted", "cheerful", "elated", "thrilled",
        "amazing", "yay", "ecstatic",
    },
    "sadness": {
        "sad", "sadd", "saddd", "down", "blue", "unhappy", "heartbroken",
        "miserable", "hopeless", "depressed", "empty", "grief", "crying",
        "cried", "hurt", "disappointed", "gloomy", "sorrow",
    },
    "anger": {
        "angry", "furious", "mad", "irritated", "annoyed", "frustrated",
        "resentful", "hate", "rage", "pissed", "fuming", "outraged",
        "bitter",
    },
    "anxiety": {
        "anxious", "worried", "nervous", "stressed", "overwhelmed",
        "panicking", "uneasy", "tense", "dread", "restless", "on edge",
        "apprehensive",
    },
    "fear": {
        "afraid", "scared", "terrified", "frightened", "fear", "panicked",
        "horrified", "spooked", "petrified",
    },
    "calm": {
        "calm", "peaceful", "relaxed", "content", "serene", "grounded",
        "steady", "at ease", "rested", "balanced", "tranquil",
    },
    "love": {
        "love", "loved", "loving", "adore", "cherish", "affection",
        "devoted", "fond", "romantic", "warmth",
    },
    "surprise": {
        "surprised", "shocked", "astonished", "stunned", "amazed",
        "unexpected", "startled", "wow", "whoa",
    },
    "disgust": {
        "disgusted", "gross", "revolting", "repulsed", "nauseated",
        "sickened", "yuck", "ew",
    },
    "shame": {
        "ashamed", "embarrassed", "humiliated", "mortified", "self-conscious",
        "exposed",
    },
    "guilt": {
        "guilty", "guilt", "remorseful", "regret", "regretful", "sorry",
        "blame",
    },
    "pride": {
        "proud", "accomplished", "achievement", "confident", "successful",
        "capable", "empowered",
    },
    "hope": {
        "hopeful", "optimistic", "looking forward", "excited for", "hope",
        "encouraged", "motivated",
    },
    "boredom": {
        "bored", "boring", "dull", "monotonous", "tedious", "uninspired",
    },
    "gratitude": {
        "grateful", "thankful", "appreciate", "appreciative", "blessed",
        "fortunate",
    },
    "loneliness": {
        "lonely", "alone", "isolated", "disconnected", "abandoned",
        "unseen",
    },
}


@dataclass
class EmotionProfile:
    scores: dict[str, float] = field(default_factory=dict)

    @property
    def dominant(self) -> str:
        if not self.scores or max(self.scores.values()) == 0.0:
            return "neutral"
        return max(self.scores, key=self.scores.get)

    @property
    def present(self) -> list[str]:
        return [e for e, s in sorted(self.scores.items(), key=lambda kv: -kv[1]) if s > 0]

    def to_dict(self) -> dict[str, float]:
        return dict(self.scores)

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "EmotionProfile":
        return cls(scores=data)


def detect_emotions(text: str) -> EmotionProfile:
    words = [w.strip(".,!?;:\"'()").lower() for w in text.split()]
    hits: Counter[str] = Counter()

    for word in words:
        for emotion, lexicon in _EMOTION_LEXICON.items():
            if word in lexicon:
                hits[emotion] += 1

    total = sum(hits.values())
    if total == 0:
        return EmotionProfile(scores={e: 0.0 for e in _EMOTION_LEXICON})

    scores = {e: round(hits.get(e, 0) / total, 3) for e in _EMOTION_LEXICON}
    return EmotionProfile(scores=scores)


def all_emotions() -> list[str]:
    return list(_EMOTION_LEXICON.keys())


def emotion_color(emotion: str) -> str:
    palette = {
        "joy": "#f4c542",
        "sadness": "#4c6ef5",
        "anger": "#e03131",
        "anxiety": "#f76707",
        "fear": "#862e9c",
        "calm": "#2f9e44",
        "love": "#f06595",
        "surprise": "#22b8cf",
        "disgust": "#5c940d",
        "shame": "#9c6644",
        "guilt": "#7048e8",
        "pride": "#f59f00",
        "hope": "#12b886",
        "boredom": "#868e96",
        "gratitude": "#d9480f",
        "loneliness": "#364fc7",
        "neutral": "#495057",
    }
    return palette.get(emotion, "#adb5bd")