# modules/question_gen.py
import json
from groq import Groq
from config import GROQ_API_KEY, GPT_MODEL, MAX_QUESTIONS

client = Groq(api_key=GROQ_API_KEY)


def generate_interview_questions(candidate_info: dict) -> list:
    name = candidate_info.get("name", "Candidate")
    experience = candidate_info.get("total_experience", "fresher")
    current_role = candidate_info.get("current_role", "Software Developer")
    tech_skills = candidate_info.get("technical_skills", [])
    languages = candidate_info.get("programming_languages", [])
    frameworks = candidate_info.get("frameworks", [])
    projects = candidate_info.get("key_projects", [])

    prompt = f"""
    Candidate profile:
    - Name: {name}
    - Experience: {experience}
    - Current Role: {current_role}
    - Technical Skills: {', '.join(tech_skills[:10])}
    - Programming Languages: {', '.join(languages)}
    - Frameworks: {', '.join(frameworks[:5])}
    - Key Projects: {'; '.join(projects[:3])}

    Generate exactly {MAX_QUESTIONS} interview questions that:
    1. Are based on the candidate's skills (mix of technical + behavioral)
    2. Gradually increase in difficulty (easy to medium to hard)
    3. Feel like a real interview

    IMPORTANT: ALL questions MUST be written in ENGLISH only. No Hindi. No other language.

    Return ONLY a valid JSON array, no extra text:
    [
        {{
            "id": 1,
            "question": "question text here in English",
            "category": "Technical/Behavioral/Situational",
            "skill_tested": "which skill is being tested",
            "difficulty": "Easy/Medium/Hard",
            "expected_keywords": ["keyword1", "keyword2", "keyword3"]
        }}
    ]
    """

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a senior technical interviewer. Generate professional interview questions. STRICT RULE: ALL output including questions must be in ENGLISH only. Never use Hindi or any other language. Return only valid JSON."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    result_text = response.choices[0].message.content.strip()

    if "```" in result_text:
        parts = result_text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("[") or part.startswith("json"):
                result_text = part.replace("json", "", 1).strip()
                break

    questions = json.loads(result_text)
    print(f"[Question Gen] {len(questions)} questions generate hue!")
    return questions