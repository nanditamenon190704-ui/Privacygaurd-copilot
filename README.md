# TAKE OFF

**Take off your private information before AI sees it.**

**[Try the live demo (lite version)](https://nanditamenon190704-ui.github.io/Privacygaurd-copilot/)**

TAKE OFF is a privacy gateway for AI. It lets teams use LLMs on documents full of personal data
(support tickets, emails, call notes) without the model ever seeing that data.

![TAKE OFF demo](screenshots/demo.png)

## The problem
Companies want AI help with real documents, but those are full of names, phone numbers and
Aadhaar numbers. Sending them to an outside model risks breaking privacy rules such as India's
DPDP Act and GDPR.

## How it works
1. **Redact:** personal data is detected and replaced with numbered labels such as `<PERSON_1>`.
2. **AI task:** the model works only on the redacted text and is told exactly which labels exist.
3. **Restore:** real values are swapped back into the answer on the user's side. The
   label-to-value map is never sent to the model.
4. **Transparency:** every result shows the original, what the AI saw, what the AI wrote, and the
   final answer side by side.

## Two versions

| | Live demo (lite) | Full version |
|---|---|---|
| Where it runs | GitHub Pages + Cloudflare Worker | On your own machine |
| Redaction | JavaScript rules in the browser | Microsoft Presidio + spaCy, with custom Indian rules |
| AI orchestration | Direct call through the Worker | Semantic Kernel agent with plugins |
| API | One Worker endpoint | FastAPI REST API (`/redact`, `/ask`, `/audit`) |
| Audit log | None, nothing is stored | Counts and timestamps only |

The lite version exists so anyone can try the idea with one click, without a server. The full
version is the stronger implementation. Its detection is more accurate, especially for names.

## Features
- Detects names, emails, phone numbers, locations, IP addresses and card numbers
- Aadhaar and +91 phone number support
- Numbered labels so the AI can still tell people apart
- Real values restored in the final answer
- Fail-safe rule that hides any long digit run, even when it is not a valid number
- Side-by-side view of original, redacted text, AI output and final answer
- Sample documents, file upload, copy and download of answers
- Interactive UI with a mouse-reactive background and a built-in mini game

## Tech stack
- **Full version:** Python, FastAPI, Semantic Kernel, Microsoft Presidio, spaCy
- **Live demo:** vanilla JavaScript redaction, a Cloudflare Worker (holds the API key), GitHub Pages
- **UI (both):** React, served as a single page
- **Model:** Groq-hosted LLM through an OpenAI-compatible endpoint

## Design decisions
- **Redact before the LLM:** the model never receives raw personal data.
- **Numbered labels plus restore:** answers stay useful ("Dear Arjun") without exposing real values
  to the model.
- **Fail toward redaction:** testing showed my phone validator skipped a malformed 11-digit number,
  so I added a safety-net rule that hides any long digit run.
- **Constrain the model:** the model first invented its own placeholders, which broke restoration.
  I now pass it the exact allowed labels and convert any invented ones into plain [blanks].
- **Keep the key off the page:** the live demo calls the model through a Cloudflare Worker, so the
  API key never appears in the website's code. The Worker accepts only requests from this site and
  caps input length.
- **Swappable model:** Semantic Kernel keeps the model separate from the app logic, so the same
  code can target Azure AI Foundry through configuration.

## Limitations
- Detection is not perfect. The lite version uses simple rules and can miss unusual names. The full
  version is more accurate but still not flawless.
- AI drafts can contain invented details and need human review.
- Demo only. Please use synthetic data.

## Run the full version locally
1. `cd backend`
2. `python -m venv .venv` then `.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `python -m spacy download en_core_web_sm`
5. Create `backend/.env` containing:
   ```
   GROQ_API_KEY=your-key
   GROQ_MODEL=openai/gpt-oss-20b
   GROQ_URL=https://api.groq.com/openai/v1
   ```
6. `uvicorn main:app --reload`, then open http://127.0.0.1:8000

## Project structure
```
backend/   Full version: FastAPI + Semantic Kernel + Presidio, plus its web page
docs/      Live demo (lite version) served by GitHub Pages
screenshots/
```

## Next steps
- Sensitivity classifier (scikit-learn) to block highly sensitive documents
- Redaction precision and recall evaluation on a labeled sample
- Permanent hosting for the full version

## Author
Built by Nandita Menon. [LinkedIn](https://www.linkedin.com/in/nandita-menon-8197a5355/) | nanditamenon190704@gmail.com
