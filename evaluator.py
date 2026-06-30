import json
import re
from groq import Groq
from config import GROQ_API_KEY, GPT_MODEL

# Groq client
client = Groq(api_key=GROQ_API_KEY)


def _extract_json(result_text: str) -> dict:
    """
    Groq response se safely JSON nikalo.
    Pehle ```json fences try karo, fir agar wo fail ho toh
    pehle '{' se last '}' tak ka portion try karo.
    """
    result_text = result_text.strip()

    # 1) ```json ... ``` fences ke andar se nikalo (agar hain)
    if "```" in result_text:
        parts = result_text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                try:
                    return json.loads(part)
                except json.JSONDecodeError:
                    pass  # next attempt try karo

    # 2) Direct parse try karo (agar pure JSON hi hai)
    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        pass

    # 3) First '{' se last '}' tak nikal ke try karo
    #    (jab model extra text pehle/baad mein jod deta hai)
    start = result_text.find("{")
    end = result_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = result_text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"AI response se valid JSON nahi nikal payi.\n"
                f"Error: {e}\n"
                f"Raw response (first 500 chars): {result_text[:500]}"
            )

    raise ValueError(
        f"AI response mein JSON nahi mila.\n"
        f"Raw response (first 500 chars): {result_text[:500]}"
    )


def _call_groq(messages, temperature=0.3, max_tokens=2000, retries=2):
    """
    Groq ko call karo with retry on JSON-parse failure / API error.
    max_tokens explicitly set kiya — warna lambe response truncate
    ho jaate the aur JSON incomplete aata tha (yehi report fail hone
    ki sabse badi wajah thi).
    """
    last_error = None
    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            result_text = response.choices[0].message.content.strip()
            return _extract_json(result_text)
        except Exception as e:
            last_error = e
            print(f"[Evaluator] Attempt {attempt + 1} failed: {e}")
    raise RuntimeError(f"Groq call {retries + 1} attempts ke baad bhi fail hui: {last_error}")


def evaluate_answer(question: dict, answer_text: str, candidate_info: dict) -> dict:
    """
    Ek answer evaluate karo
    Returns: evaluation dict with score and feedback
    """

    if not answer_text or len(answer_text.strip()) < 10:
        return {
            "score": 0,
            "rating": "No Answer",
            "strengths": [],
            "improvements": ["Candidate does not give any answer"],
            "keywords_matched": [],
            "keywords_missed": question.get("expected_keywords", []),
            "detailed_feedback": "Candidate did not provide an answer."
        }

    question_text = question.get("question", "")
    category = question.get("category", "Technical")
    skill_tested = question.get("skill_tested", "")
    difficulty = question.get("difficulty", "Medium")
    expected_keywords = question.get("expected_keywords", [])
    experience = candidate_info.get("total_experience", "fresher")

    prompt = f"""
Evaluate the following interview answer.

Question: "{question_text}"
Category: {category}
Skill Being Tested: {skill_tested}
Difficulty: {difficulty}
Candidate Experience: {experience}
Expected Keywords: {', '.join(expected_keywords)}

Candidate Answer:
"{answer_text}"

Evaluate the answer and return ONLY valid JSON in English. Do not include any
text before or after the JSON object. Do not use markdown code fences.

{{
    "score": <integer between 0 and 10>,
    "rating": "<Excellent/Good/Average/Poor/No Answer>",
    "strengths": ["strength1", "strength2"],
    "improvements": ["improvement1", "improvement2"],
    "keywords_matched": ["keyword1"],
    "keywords_missed": ["keyword2"],
    "detailed_feedback": "Provide detailed feedback in 2-3 sentences, strictly in English.",
    "communication_score": <integer between 0 and 10>,
    "technical_accuracy": <integer between 0 and 10>,
    "confidence_level": "<High/Medium/Low>"
}}
"""

    try:
        evaluation = _call_groq(
            messages=[
                {
                    "role": "system",
                    "content": "You are a fair and expert technical interviewer. Evaluate answers objectively. Return only valid JSON. All feedback, strengths, weaknesses, ratings, recommendations, and summaries must be in English."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        print(f"[Evaluator] Q scored: {evaluation.get('score')}/10 - {evaluation.get('rating')}")
        return evaluation
    except Exception as e:
        # Agar AI evaluation hi fail ho jaye, toh poori report crash karne
        # ke bajaye ek fallback evaluation do — taaki interview/report
        # aage chal sake.
        print(f"[Evaluator] evaluate_answer failed, using fallback: {e}")
        return {
            "score": 0,
            "rating": "Evaluation Error",
            "strengths": [],
            "improvements": ["Could not evaluate this answer due to a technical error"],
            "keywords_matched": [],
            "keywords_missed": expected_keywords,
            "detailed_feedback": f"Automatic evaluation failed: {e}",
            "communication_score": 0,
            "technical_accuracy": 0,
            "confidence_level": "Low",
        }


def generate_final_report_data(candidate_info: dict, qa_pairs: list) -> dict:
    """
    Generate the final analysis of interview
    qa_pairs = [{"question": {...}, "answer": "...", "evaluation": {...}}, ...]
    """

    # Scores calculate karo
    scores = [qa["evaluation"].get("score", 0) for qa in qa_pairs if qa.get("evaluation")]
    avg_score = sum(scores) / len(scores) if scores else 0

    # Strengths aur weaknesses compile karo
    all_strengths = []
    all_improvements = []
    for qa in qa_pairs:
        eval_data = qa.get("evaluation", {})
        all_strengths.extend(eval_data.get("strengths", []))
        all_improvements.extend(eval_data.get("improvements", []))

    # Category-wise performance
    category_scores = {}
    for qa in qa_pairs:
        cat = qa["question"].get("category", "General")
        score = qa["evaluation"].get("score", 0)
        if cat not in category_scores:
            category_scores[cat] = []
        category_scores[cat].append(score)

    category_avg = {
        cat: round(sum(scores_list) / len(scores_list), 1)
        for cat, scores_list in category_scores.items()
    }

    # Overall recommendation Groq se
    prompt = f"""
    final interview assesment:
    - Candidate: {candidate_info.get('name', 'Candidate')}
    - Experience: {candidate_info.get('total_experience', 'N/A')}
    - Role: {candidate_info.get('current_role', 'N/A')}
    - Average Score: {avg_score:.1f}/10
    - Category Performance: {json.dumps(category_avg)}
    - Top Strengths: {all_strengths[:5]}
    - Areas to Improve: {all_improvements[:5]}

    Return ONLY valid JSON. Do not include any text before or after the JSON
    object. Do not use markdown code fences.
    {{
        "overall_verdict": "<Highly Recommended/Recommended/Consider/Not Recommended>",
        "verdict_reason": "2-3 line explanation",
        "top_strengths": ["strength1", "strength2", "strength3"],
        "key_improvements": ["improvement1", "improvement2", "improvement3"],
        "hiring_recommendation": "detailed 3-4 sentence recommendation",
        "suggested_role_level": "<Junior/Mid/Senior/Lead>",
        "interview_performance_summary": "overall performance ka brief summary"
    }}
    """

    try:
        final_analysis = _call_groq(
            messages=[
                {"role": "system", "content": "Tum HR expert ho. Sirf valid JSON return karo, koi extra text nahi."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1500,
        )
    except Exception as e:
        # Final analysis fail ho bhi jaye toh report ko crash mat hone do —
        # fallback analysis bana ke aage badho, taaki PDF phir bhi ban jaye.
        print(f"[Evaluator] generate_final_report_data failed, using fallback: {e}")
        verdict = (
            "Highly Recommended" if avg_score >= 8 else
            "Recommended" if avg_score >= 6 else
            "Consider" if avg_score >= 4 else
            "Not Recommended"
        )
        final_analysis = {
            "overall_verdict": verdict,
            "verdict_reason": "Auto-generated summary due to a technical error in AI analysis.",
            "top_strengths": all_strengths[:3] or ["N/A"],
            "key_improvements": all_improvements[:3] or ["N/A"],
            "hiring_recommendation": f"Candidate scored an average of {avg_score:.1f}/10 across {len(qa_pairs)} questions.",
            "suggested_role_level": "Mid",
            "interview_performance_summary": f"Average score: {avg_score:.1f}/10.",
        }

    # Sab combine karo
    report_data = {
        "candidate_info": candidate_info,
        "qa_pairs": qa_pairs,
        "summary": {
            "average_score": round(avg_score, 1),
            "total_questions": len(qa_pairs),
            "category_performance": category_avg,
            "scores_list": scores
        },
        "final_analysis": final_analysis
    }

    return report_data