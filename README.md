# ExamForge AI

> **Portfolio edition:** a clean, generic assessment-authoring platform inspired by a real question-bank workflow, with no institutional data or inherited repository history.

ExamForge AI combines a structured item bank with human review, assessment assembly and optional AI-assisted drafting.

## Portfolio snapshot

This project demonstrates **assessment workflow design, Django domain modeling, AI integration, structured output validation, question approval, exam generation and LMS-ready export**.

**Stack:** Django · PostgreSQL/SQLite · Gemini REST API · Structured JSON · Tests · CI

## Core features

- authenticated item bank;
- courses / modules and academic terms;
- single-answer, multiple-statement and assertion–reason items;
- pedagogical metadata such as Bloom level, difficulty, primary area and competency;
- pending / approved / rejected workflow;
- AI-assisted question drafting from teacher parameters;
- AI-assisted item review;
- human editing before persistence;
- manual and automatic assessment assembly;
- answer-key view;
- printable exam view;
- Blackboard-compatible TXT export;
- synthetic demo data only.

## Human-in-the-loop AI

AI output is always treated as a **draft**. The application validates the returned JSON structure and never auto-approves generated items. A teacher/editor reviews and saves the content, and only approved items enter automatic assessments.

For local UI testing without API usage:

```dotenv
USE_FAKE_AI=1
```

For real AI calls:

```dotenv
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Demo credentials:

- `admin` / `Demo-Admin-12345`
- `editor.demo` / `Demo-Editor-12345`

## Origin and privacy

The operational assessment system that inspired this case remains separate. ExamForge AI contains no production question database, audit exports, institutional branding, faculty/student data, e-mail credentials or inherited Git history.
