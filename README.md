# TAKE OFF

**Take off your private information before AI sees it.**

TAKE OFF is a privacy gateway for AI. It lets teams use LLMs on documents full of
personal data (support tickets, emails, notes) without the model ever seeing that data.

![TAKE OFF demo](ss1.png,s2.png,s3.png)

## The problem
Companies want AI help with real documents, but those are full of names, phone numbers
and Aadhaar numbers. Sending them to an outside model risks breaking privacy rules such
as India's DPDP Act and GDPR.

## How it works
1. **Redact:** Microsoft Presidio detects personal data, with custom rules for Indian
   mobile numbers and Aadhaar, and replaces each value with a numbered label such as
   `<PERSON_1>`.
2. **AI task:** A Semantic Kernel agent works only on the redacted text, using plugin
   functions (`get_document`, `get_redaction_report`).
3. **Restore:** Real values are swapped back into the answer on the user's side only.
   The label-to-value map is never sent to the model or logged.
4. **Audit:** `/audit` stores only counts and timestamps, never raw text.

## Features
- Automatic detection of names, emails, phones, locations, IPs and card numbers
- Aadhaar and +91 phone number support
- Numbered labels so the AI can still tell people apart
- Real values restored in the final answer
- Fail-safe rule that hides any long digit run, even if it is not a valid number
- Side-by-side view of original, redacted text, AI output and final answer
- Privacy-safe audit log
- Interactive UI with a mouse-reactive background and a built-in mini game

## Tech stack
Python, FastAPI (REST API), Semantic Kernel, Microsoft Presidio, spaCy, React (single
page UI), Groq-hosted LLM through an OpenAI-compatible endpoint.
## Design decisions
- **Redact before the LLM:** the model never receives raw personal data.
- **Numbered labels plus restore:** answers stay useful ("Dear Arjun") without exposing
  real values to the model.
- **Fail toward redaction:** testing showed my phone validator skipped a malformed
  11-digit number, so I added a safety-net rule for long digit runs.
- **Constrain the model:** the model first invented its own placeholders, which broke
  restoration. I now pass it the exact allowed labels and convert any invented ones into
  plain [blanks].
- **Swappable model:** Semantic Kernel keeps the model separate from the app logic, so the
  same code can target Azure AI Foundry through configuration.

## Limitations
- Detection is not perfect, and unusual name formats can be missed.
- AI drafts can contain invented details and need human review.
- Demo only. Please use synthetic data.

## Run it locally
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

## Next steps
- Sensitivity classifier (scikit-learn) to block highly sensitive documents
- Redaction precision and recall evaluation on a labeled sample
- Permanent cloud deployment

## Author
Built by Nandita Menon. [LinkedIn](https://www.linkedin.com/in/nandita-menon-8197a5355/) | nanditamenon190704@gmail.com
