from dataclasses import dataclass

@dataclass(slots=True)
class QuestionHandlerDto:
    user_id: str|int
    question: str
    correlation_id: str