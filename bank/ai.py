import json,re
import requests
from django.conf import settings

MAX_PROMPT_CHARS=6000

def _extract_json(text):
    text=(text or "").strip()
    match=re.search(r"\{.*\}",text,re.DOTALL)
    if not match: raise ValueError("AI response did not contain JSON.")
    data=json.loads(match.group(0))
    required={"context","stem","options","rationale"}
    if not required.issubset(data): raise ValueError("AI response is missing required fields.")
    if not isinstance(data["options"],list) or not 2<=len(data["options"])<=5: raise ValueError("AI response has invalid options.")
    correct=sum(1 for o in data["options"] if bool(o.get("is_correct")))
    if correct!=1: raise ValueError("AI draft must contain exactly one correct option.")
    for option in data["options"]:
        if not str(option.get("text","")).strip(): raise ValueError("AI response has an empty option.")
    return data

def _fake(topic,params):
    from .demo_content import synthetic_draft
    return synthetic_draft(topic,params)

def generate_question(topic,course_name,params):
    topic=(topic or "").strip()
    if not topic or len(topic)>MAX_PROMPT_CHARS: raise ValueError("Prompt is empty or too long.")
    if settings.PORTFOLIO_DEMO or settings.USE_FAKE_AI: return _fake(topic,params)
    if not settings.GEMINI_API_KEY: raise RuntimeError("GEMINI_API_KEY is not configured.")
    prompt=f"""You are an assessment-design assistant. Draft ONE multiple-choice item for {course_name}.
Topic/instructions: {topic}
Bloom level: {params.get('bloom','APPLY')}
Difficulty: {params.get('difficulty','MEDIUM')}
Primary area: {params.get('primary_area','')}
Competency: {params.get('competency','')}
Return only JSON with context, stem, proposition_two, options (array of text/is_correct), rationale, bloom and difficulty.
Exactly one option must be correct. Avoid trick wording and absolute clues. The output is a draft and will undergo human review."""
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
    response=requests.post(url,params={"key":settings.GEMINI_API_KEY},json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"responseMimeType":"application/json","temperature":0.3}},timeout=45)
    response.raise_for_status()
    payload=response.json()
    text=payload["candidates"][0]["content"]["parts"][0]["text"]
    return _extract_json(text)

def review_question(question):
    if settings.PORTFOLIO_DEMO or settings.USE_FAKE_AI:
        return ("REVISÃO SIMULADA — sem API de IA\n\n"
                + f"Estrutura: {question.options.count()} alternativas; "
                + f"{question.options.filter(is_correct=True).count()} gabarito(s).\n"
                + f"Demanda cognitiva: {question.get_bloom_display()}.\n"
                + "Clareza: conferir se o comando solicita uma ação inequívoca.\n"
                + "Distratores: revisar plausibilidade e ausência de pistas.\n"
                + "Alinhamento: comparar o item à competência declarada.\n\n"
                + "Este relatório demonstra o fluxo; não constitui validação por um modelo. A decisão permanece humana.")
    if not settings.GEMINI_API_KEY: raise RuntimeError("GEMINI_API_KEY is not configured.")
    options="\n".join(f"- {o.text} [{'correct' if o.is_correct else 'distractor'}]" for o in question.options.all())
    prompt=f"""Review this assessment item for clarity, alignment, plausibility of distractors, cueing, ambiguity and cognitive demand.
Do not change its approval status. Produce a concise professional report.
Context: {question.context}
Stem: {question.stem}
Options:
{options}
Rationale: {question.rationale}
Bloom: {question.bloom}
Difficulty: {question.difficulty}"""
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
    response=requests.post(url,params={"key":settings.GEMINI_API_KEY},json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.2}},timeout=45)
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
