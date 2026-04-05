from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()

# ✅ FIX 1: Middleware MUST be registered before any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://admission-chatbot.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PDF_FOLDER = "./pdfs"
FAISS_INDEX_PATH = "./faiss_index"

# ✅ FIX 2: Cache FAISS in memory — load once, reuse on every /ask request
_faiss_db = None

def load_pdfs():
    text = ""
    if not os.path.exists(PDF_FOLDER):
        print(f"⚠️ {PDF_FOLDER} does not exist.")
        return ""
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]
    if not pdf_files:
        print("⚠️ No PDF files found.")
        return ""
    for pdf_file in pdf_files:
        pdf_reader = PdfReader(os.path.join(PDF_FOLDER, pdf_file))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    return text_splitter.split_text(text)

def create_vector_store():
    raw_text = load_pdfs()
    if not raw_text:
        print("⚠️ No text extracted from PDFs. Skipping FAISS creation.")
        return
    text_chunks = get_text_chunks(raw_text)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local(FAISS_INDEX_PATH)
    print(f"✅ FAISS index created at {FAISS_INDEX_PATH}!")

def get_faiss_db():
    """Load FAISS once and cache it in memory for all subsequent requests."""
    global _faiss_db
    if _faiss_db is not None:
        return _faiss_db

    index_file = f"{FAISS_INDEX_PATH}/index.faiss"

    # ✅ FIX 3: Build index if it doesn't exist yet (e.g. first cold start)
    if not os.path.exists(index_file):
        print("⏳ FAISS index not found. Building now...")
        create_vector_store()

    if not os.path.exists(index_file):
        print("❌ FAISS index still missing after build attempt.")
        return None

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    _faiss_db = FAISS.load_local(
        FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True
    )
    print("✅ FAISS index loaded and cached in memory.")
    return _faiss_db

PROMPT_TEMPLATE = """
You are an AI assistant specialized in answering queries about **GGSIPU Admissions**. Your responses must be **highly structured, well-formatted, and in clean Markdown** based strictly on the provided PDF documents.

# 🛑 **STRICT RULES:**
- **ONLY use information from the given PDFs**. Do NOT generate responses based on assumptions.
- **DO NOT** add greetings, disclaimers, or extra text.
- **DO NOT** start with anything except the direct answer.
- **FORMAT the response in clear, structured Markdown** as per the guidelines below.

# ✅ **MARKDOWN FORMAT GUIDELINES:**
- `#` → **Main Topics**
- `##` → **Subtopics**
- `###` → **Detailed Sections**
- `-` → **Bullet Points for clarity**
- **Bold** → **For highlighting key terms**
- Ensure **at least ONE blank line** between major sections for readability.

# 🚨 **MISSING INFORMATION HANDLING:**
If the answer is **not available in the PDFs**, respond with:
- **"Refer to the official admission brochure for accurate details."**
- **Official contact email:** `pro@ipu.ac.in`
- **DO NOT** guess, assume, or fabricate any information.

---

# 📌 **CONTEXT (Extracted from PDFs):**
{context}

# 📌 **USER QUERY:**
{question}

# 📌 **STRUCTURED ANSWER:**
"""

class QuestionRequest(BaseModel):
    question: str

def get_answer(user_question):
    try:
        db = get_faiss_db()
        if db is None:
            return "Apologies! The system is still initializing. Please try again in a few minutes."

        docs = db.similarity_search(user_question)
        print(f"✅ Retrieved {len(docs)} similar docs")

        if not docs:
            return "Apologies! No relevant information found."

        model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
        prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["context", "question"])
        chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
        response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        print("✅ AI Response Generated!")
        return response["output_text"]

    except Exception as e:
        print(f"❌ Error: {e}")
        return f"❌ Error: {e}"

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
    print(f"🚀 Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)