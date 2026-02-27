import os


def is_openai_available():
    return bool(os.environ.get("OPENAI_API_KEY"))


def generate_reading_feedback(student_summary, book_title="", grade_level=""):
    """Generate reading feedback using OpenAI if available."""
    if not is_openai_available():
        return None
    try:
        from openai import OpenAI
        client = OpenAI()
        prompt = (
            f"A student (grade {grade_level or 'unknown'}) wrote this summary about '{book_title}':\n\n"
            f"{student_summary}\n\n"
            "Please provide brief, encouraging teacher feedback and a suggested rubric score (1-5). "
            "Keep it under 100 words."
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        return response.choices[0].message.content
    except Exception:
        return None
