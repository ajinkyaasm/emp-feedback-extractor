# Employee Feedback Extractor

A FastAPI application that uses the Groq LLM with function calling to convert unstructured employee reviews into structured feedback.

## Features

- Extracts employee strengths
- Identifies areas for improvement
- Classifies review sentiment (Positive, Neutral, Negative)
- Stores extracted feedback in a Parquet file
- Provides a feedback summary endpoint

## Tech Stack

- Python
- FastAPI
- Groq API
- Pandas
- PyArrow

## API Endpoints

### POST `/extract-feedback`

Extract structured feedback from an employee review.

**Sample Request**

```json
{
  "emp_id": "EMP001",
  "review_text": "Excellent Python developer with good SQL skills but needs to improve Azure."
}
```

**Sample Response**

```json
{
  "strengths": ["Python", "SQL"],
  "areas_for_improvement": ["Azure"],
  "overall_sentiment": "neutral"
}
```

---

### GET `/feedback-summary`

Returns the total number of reviews by sentiment.

Example Response

```json
{
  "positive": 5,
  "neutral": 2,
  "negative": 1
}
```

## Installation

```bash
git clone <repository-url>
cd structured-feedback-extractor

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file:

```text
GROQ_API_KEY=your_api_key
```

Run the application:

```bash
uvicorn main:app --reload
```

Open the Swagger UI:

```
http://127.0.0.1:8000/docs
```
