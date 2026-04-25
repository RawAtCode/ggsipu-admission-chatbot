from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PDF_FOLDER = "./pdfs"
TOP_K = 10
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200

# ── Admission-specific synonym map ────────────────────────────────────────────
# Maps common user phrasings → terms likely to appear in official PDFs.
# This runs locally — no API call, never fails, instant.

SYNONYM_MAP = {
    # fees
    "fee": ["fee", "fees", "charges", "tuition", "amount", "payment", "cost"],
    "fees": ["fee", "fees", "charges", "tuition", "amount", "payment", "cost"],
    "charges": ["fee", "fees", "charges", "tuition", "amount", "payment"],
    "cost": ["fee", "fees", "charges", "tuition", "cost", "amount"],
    "tuition": ["tuition", "fee", "fees", "charges"],

    # programs
    "btech": ["b.tech", "btech", "b tech", "bachelor technology", "engineering"],
    "b.tech": ["b.tech", "btech", "b tech", "bachelor technology", "engineering"],
    "engineering": ["engineering", "b.tech", "btech", "technical"],
    "mba": ["mba", "m.b.a", "master business administration", "management"],
    "mca": ["mca", "m.c.a", "master computer applications"],
    "bca": ["bca", "b.c.a", "bachelor computer applications"],
    "mtech": ["m.tech", "mtech", "master technology"],
    "llb": ["llb", "ll.b", "bachelor law"],
    "bba": ["bba", "b.b.a", "bachelor business administration"],

    # admission terms
    "admission": ["admission", "admissions", "enrolment", "enrollment", "joining"],
    "cutoff": ["cutoff", "cut-off", "cut off", "merit", "minimum marks", "qualifying"],
    "eligibility": ["eligibility", "eligible", "criteria", "qualification", "required"],
    "counselling": ["counselling", "counseling", "allotment", "seat allotment"],
    "counseling": ["counselling", "counseling", "allotment", "seat allotment"],
    "document": ["document", "documents", "certificate", "certificates", "required documents"],
    "documents": ["document", "documents", "certificate", "certificates"],
    "seat": ["seat", "seats", "intake", "capacity", "vacancy"],
    "seats": ["seat", "seats", "intake", "capacity"],
    "rank": ["rank", "ranking", "merit list", "crl", "position"],
    "merit": ["merit", "merit list", "rank", "ranking", "crl"],
    "date": ["date", "dates", "schedule", "timeline", "last date", "deadline"],
    "last date": ["last date", "deadline", "closing date", "final date"],
    "deadline": ["deadline", "last date", "closing date", "final date"],
    "schedule": ["schedule", "dates", "timeline", "calendar", "timetable"],
    "hostel": ["hostel", "accommodation", "residence", "dormitory"],
    "scholarship": ["scholarship", "scholarships", "financial aid", "stipend", "waiver"],
    "reservation": ["reservation", "reserved", "category", "sc", "st", "obc", "ews"],
    "category": ["category", "reservation", "sc", "st", "obc", "ews", "general"],
    "cet": ["cet", "common entrance test", "entrance exam", "entrance test"],
    "entrance": ["entrance", "cet", "entrance exam", "entrance test", "common entrance"],
    "application": ["application", "registration", "apply", "form", "online form"],
    "registration": ["registration", "application", "apply", "form", "enroll"],
    "refund": ["refund", "refunds", "cancellation", "withdrawal", "return"],
}

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "what", "which", "who",
    "this", "that", "these", "those", "i", "me", "my", "we", "our",
    "you", "your", "he", "she", "it", "they", "them", "their",
    "for", "of", "in", "on", "at", "to", "from", "by", "with",
    "about", "as", "into", "and", "but", "or", "so", "if",
    "tell", "give", "please", "want", "know", "get",
    "how", "when", "where", "why", "any", "all", "some",
}

# ── In-memory state ───────────────────────────────────────────────────────────

_chunks: list[str] = []
_bm25: BM25Okapi | None = None


def tokenize(text: str) -> list[str]:
    """Lowercase, split, remove stopwords and short tokens."""
    return [
        w for w in text.lower().split()
        if w not in STOPWORDS and len(w) > 2
    ]


def expand_tokens(tokens: list[str]) -> list[str]:
    """
    Expand each token with domain synonyms.
    e.g. "fee" → ["fee", "fees", "charges", "tuition", "amount", "payment", "cost"]
    Deduplicates and returns flat list.
    """
    expanded = []
    seen = set()
    for token in tokens:
        variants = SYNONYM_MAP.get(token, [token])
        for v in variants:
            sub_tokens = v.lower().split()
            for st in sub_tokens:
                if st not in seen:
                    seen.add(st)
                    expanded.append(st)
    return expanded


def build_index():
    """Load PDFs → split → BM25 index. Runs once at startup."""
    global _chunks, _bm25

    if not os.path.exists(PDF_FOLDER):
        print(f"⚠️  {PDF_FOLDER} not found.")
        return

    pdf_files = sorted([f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")])
    if not pdf_files:
        print("⚠️  No PDFs found.")
        return

    raw_text = ""
    for pdf_file in pdf_files:
        reader = PdfReader(os.path.join(PDF_FOLDER, pdf_file))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                raw_text += page_text + "\n"

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "],
    )
    _chunks = splitter.split_text(raw_text)
    _bm25 = BM25Okapi([tokenize(chunk) for chunk in _chunks])
    print(f"✅ Indexed {len(pdf_files)} PDF(s) → {len(_chunks)} chunks.")


def retrieve(question: str) -> list[str]:
    """
    Retrieve top-K chunks using BM25 with local synonym expansion.
    Always returns results — never filters by score threshold.
    """
    if not _bm25 or not _chunks:
        return []

    base_tokens = tokenize(question)
    expanded_tokens = expand_tokens(base_tokens)

    # Score with expanded token set
    scores = _bm25.get_scores(expanded_tokens)

    # Always return top K — no score threshold
    top_indices = sorted(
        range(len(scores)), key=lambda i: scores[i], reverse=True
    )[:TOP_K]

    return [_chunks[i] for i in top_indices]


# Build index at startup
build_index()


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are the official AI assistant for GGSIPU (Guru Gobind Singh Indraprastha University) Admissions.
Your sole purpose is to give students accurate, complete answers about admissions using the provided context.

RULES:
1. Answer ONLY from the provided context. Never fabricate or assume data.
2. If the answer is present — give it in FULL. Do not summarize away numbers, dates, or conditions.
3. If context is partially relevant — extract what is useful and note what is missing.
4. If context has zero relevant info — say: "This specific information is not in the available documents. Please refer to the official brochure or contact pro@ipu.ac.in"
5. Never greet, apologize, or add filler. Start directly with the answer.

FORMATTING:
- Use `##` headers for each major section
- Use bullet points for lists, fees, dates, eligibility criteria
- **Bold** all numbers, amounts, dates, and deadlines
- Be dense with facts — no padding, no repetition
"""


# ── Core answer function ──────────────────────────────────────────────────────

def get_answer(user_question: str) -> str:
    try:
        if not _bm25:
            return "System error: documents not loaded. Please contact the administrator."

        chunks = retrieve(user_question)
        context = "\n\n---\n\n".join(chunks)

        user_message = f"""CONTEXT (from official GGSIPU admission documents):
{context}

STUDENT QUERY:
{user_question}"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=1024,
        )

        answer = response.choices[0].message.content.strip()
        print(f"✅ Answered: {user_question[:70]}")
        return answer

    except Exception as e:
        print(f"❌ Error: {e}")
        return f"❌ Error: {e}"


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://admission-chatbot.vercel.app",
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def read_root():
    return {"message": "Server is running!"}


@app.post("/ask")
def ask_question(request: QuestionRequest):
    answer = get_answer(request.question)
    return {"answer": answer}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting on port {port}…")
    uvicorn.run(app, host="0.0.0.0", port=port)