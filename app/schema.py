from pydantic import BaseModel


class FeedbackIn(BaseModel):
    emp_id: str
    review_text: str


class FeedbackOut(BaseModel):
    strengths: list[str]
    areas_for_improvement: list[str]
    overall_sentiment: str
