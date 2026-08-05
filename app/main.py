from fastapi import FastAPI, HTTPException
from schema import FeedbackIn, FeedbackOut
from dotenv import load_dotenv
import os
import json
import requests
import pandas as pd

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

INSTRUCTIONS = """
    Extract structured employee review.

    Rules:

    - strengths should contain ONLY skill names.
    - areas_for_improvement should contain ONLY skill names.
    - Do not include descriptive phrases.

    Sentiment Rules:

    - positive:
    Employee has only strengths or overwhelmingly positive feedback.
    Minor suggestions do not change the sentiment.

    - neutral:
    Balanced mix of strengths and improvement areas.

    - negative:
    Mostly criticism with few or no strengths.

    Examples:

    Review:
    "Excellent Python developer with great SQL skills."

    Return:
    {
    "strengths": ["Python", "SQL"],
    "areas_for_improvement": [],
    "overall_sentiment": "positive"
    }

    Review:
    "Good Python skills but needs to improve Azure."

    Return:
    {
    "strengths": ["Python"],
    "areas_for_improvement": ["Azure"],
    "overall_sentiment": "neutral"
    }

    Review:
    "Poor SQL knowledge and weak communication."

    Return:
    {
    "strengths": [],
    "areas_for_improvement": ["SQL", "Communication"],
    "overall_sentiment": "negative"
    }
    """

FILEPATH = "employee_feedback.parquet"

tools = [
    {
        "type": "function",
        "function": {
            "name": "extract_review",
            "description": "Extract employee review information",
            "parameters": {
                "type": "object",
                "properties": {
                    "strengths": {"type": "array", "items": {"type": "string"}},
                    "areas_for_improvement": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "overall_sentiment": {
                        "type": "string",
                        "enum": ["positive", "neutral", "negative"],
                    },
                },
                "required": [
                    "strengths",
                    "areas_for_improvement",
                    "overall_sentiment",
                ],
            },
        },
    }
]


app = FastAPI(title="structured-feedback-extractor")


@app.post("/extract-feedback", response_model=FeedbackOut)
def extract_review(payload: FeedbackIn):
    if not payload.emp_id.strip():
        raise HTTPException(status_code=422, detail="Employee id Missing.")

    if not payload.review_text.strip():
        raise HTTPException(status_code=422, detail="review text missing")

    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not set.")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": INSTRUCTIONS,
            },
            {"role": "user", "content": payload.review_text},
        ],
        "tools": tools,
        "tool_choice": {"type": "function", "function": {"name": "extract_review"}},
    }

    response = requests.post(GROQ_URL, headers=headers, json=body)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=data)

    data = response.json()
    print(data)

    try:
        call = data["choices"][0]["message"]["tool_calls"][0]
        # print(call)
        feedback = json.loads(call["function"]["arguments"])
        print(feedback)
        new_df = pd.DataFrame(
            [
                {
                    "Employee_id": payload.emp_id,
                    "strenghts": feedback["strengths"],
                    "areas_For_improvement": feedback["areas_for_improvement"],
                    "overall_sentiment": feedback["overall_sentiment"],
                }
            ]
        )
        if os.path.exists(FILEPATH):
            existing_df = pd.read_parquet(FILEPATH)
            df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            df = new_df
        df.to_parquet(FILEPATH, engine="pyarrow", index=False)
        return FeedbackOut(**feedback)
    except (KeyError, IndexError):
        raise HTTPException(
            status_code=502, detail=f"Unexpected Groq response format: {data}"
        )


@app.get("/feedback-summary")
def feedback_summary():
    if not os.path.exists(FILEPATH):
        raise HTTPException(status_code=404, detail="No feedback has submitted yet.")

    df = pd.read_parquet(FILEPATH)
    summary = df["overall_sentiment"].value_counts().to_dict()
    return summary


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
