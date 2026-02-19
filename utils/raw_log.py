from typing import List, TypedDict, Literal

class RawLog(TypedDict):
    user_id: int
    feature: str
    timestamp: str
    action: Literal["start", "end"]
    line_number: int