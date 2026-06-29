# modules/resume_parser.py
# PDF resume se text aur skills extract karta hai

import fitz  # PyMuPDF
import json
from groq import Groq
from config import GROQ_API_KEY, GPT_MODEL

# Groq client
client = Groq(api_key=GROQ_API_KEY)


def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF file se raw text extract karo"""
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        return full_text.strip()
    except Exception as e:
        raise Exception(f"PDF read karne mein error: {str(e)}")


def extract_skills_and_info(resume_text: str) -> dict:
    """Groq Llama se resume analyse karke structured info nikalo"""
    
    prompt = f"""
    Neeche ek resume diya gaya hai. Isko analyse karke JSON format mein return karo.
    
    Return ONLY valid JSON, koi extra text nahi:
    {{
        "name": "candidate ka naam",
        "email": "email address",
        "phone": "phone number",
        "total_experience": "X years",
        "current_role": "current ya latest job title",
        "technical_skills": ["skill1", "skill2", ...],
        "soft_skills": ["skill1", "skill2", ...],
        "programming_languages": ["lang1", "lang2", ...],
        "frameworks": ["framework1", ...],
        "databases": ["db1", ...],
        "tools": ["tool1", ...],
        "education": "highest degree",
        "companies": ["company1", "company2", ...],
        "key_projects": ["project description 1", ...],
        "certifications": ["cert1", ...]
    }}
    
    Resume:
    {resume_text}
    """
    
    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Tum ek expert HR analyst ho jo resumes ko analyse karta hai. Sirf valid JSON return karo."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    result_text = response.choices[0].message.content.strip()
    
    # JSON parse karo
    if "```" in result_text:
        parts = result_text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("{") or part.startswith("json"):
                result_text = part.replace("json", "", 1).strip()
                break
    
    candidate_info = json.loads(result_text)
    return candidate_info


def parse_resume(pdf_path: str) -> dict:
    """Main function - PDF path do, structured info lo"""
    print(f"[Resume Parser] PDF load ho raha hai: {pdf_path}")
    
    # Step 1: Text extract karo
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text:
        raise Exception("PDF mein koi text nahi mila!")
    
    print(f"[Resume Parser] Text extract hua: {len(raw_text)} characters")
    
    # Step 2: Groq se analyse karo
    print("[Resume Parser] Groq Llama se skills extract ho rahi hain...")
    candidate_info = extract_skills_and_info(raw_text)
    
    print(f"[Resume Parser] Done! {len(candidate_info.get('technical_skills', []))} technical skills mili")
    return candidate_info