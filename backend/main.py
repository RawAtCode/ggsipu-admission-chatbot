from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import time
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ✅ Initialize FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Server is running!"}

# ✅ Define allowed origins (CORS Fix)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ✅ Define local PDF folder
PDF_FOLDER = "./pdfs"
FAISS_INDEX_PATH = "./faiss_index"

def load_pdfs():
    """ Load and process PDFs from the local folder """
    text = ""
    
    if not os.path.exists(PDF_FOLDER):
        print(f"⚠️ Warning: {PDF_FOLDER} does not exist. No PDFs loaded.")
        return ""

    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]

    if not pdf_files:
        print("⚠️ Warning: No PDF files found.")
        return ""

    for pdf_file in pdf_files:
        pdf_reader = PdfReader(os.path.join(PDF_FOLDER, pdf_file))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

    return text

def get_text_chunks(text):
    """ Split text into chunks for embedding """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    return text_splitter.split_text(text)

def create_vector_store():
    """ Create FAISS vector store """
    try:
        raw_text = load_pdfs()
        if not raw_text:
            print("⚠️ No text extracted from PDFs. Skipping FAISS creation.")
            return

        text_chunks = get_text_chunks(raw_text)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        # Ensure FAISS index directory exists
        os.makedirs(FAISS_INDEX_PATH, exist_ok=True)

        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
        vector_store.save_local(FAISS_INDEX_PATH)
        print(f"✅ FAISS index created successfully at {FAISS_INDEX_PATH}!")

    except Exception as e:
        print(f"❌ Error creating FAISS index: {e}")

# ✅ Run vector store creation before starting the API
print("⏳ Creating FAISS vector store...")
create_vector_store()
time.sleep(3)  # Ensure FAISS is created before the API starts

# ✅ Define request model
class QuestionRequest(BaseModel):
    question: str

def get_answer(user_question):
    """ Retrieve answer from FAISS index """
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        # ✅ Ensure FAISS index exists before loading
        if not os.path.exists(f"{FAISS_INDEX_PATH}/index.faiss"):
            print("❌ FAISS index file not found! Ensure it is created before querying.")
            return "Apologies! The system is still initializing. Please try again in a few minutes."

        new_db = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question)

        # ✅ Gemini Prompt Template
        prompt_template = """
        Answer the question as detailed as possible from the provided context. 

        - Use **bullet points** for lists.
        - Separate different sections into **clear paragraphs**.
        - Use *bold text* for important details.
        - If the answer is not in the context, say 'Apologies! There is no information available regarding your query.'
        - Do **not** provide incorrect answers.

        Context:
        {context}

        Question:
        {question}

        Answer:
        """

        model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
        
        response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        return response["output_text"]

    except Exception as e:
        return f"❌ Error retrieving answer: {e}"

@app.post("/ask")
def ask_question(request: QuestionRequest):
    """ API endpoint to get answers from the AI model """
    answer = get_answer(request.question)
    return {"answer": answer}

# ✅ Start FastAPI server
if __name__ == "__main__":
    print("🚀 Starting FastAPI server...")
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting FastAPI server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)

