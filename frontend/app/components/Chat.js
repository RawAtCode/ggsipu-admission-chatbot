"use client";

import { useState } from "react";
import axios from "axios";
import { marked } from "marked";
import DOMPurify from "dompurify";
import Header from "./Header";
import Footer from "./Footer";

export default function Chat() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  const askQuestion = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setResponse("");

    try {
      const res = await axios.post(`${BACKEND_URL}/ask`, { question });
      setResponse(res.data.answer || "No response received.");
    } catch (error) {
      console.error("Error fetching response:", error);
      setResponse("Failed to get a response. Try again!");
    }

    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && question.trim()) {
      askQuestion();
    }
  };

  return (
    <div className='app-body'>
      <Header/>

      <div className="container">
        <div className="container-heading">
            <h1>GGSIPU Admission Chatbot</h1>
        </div>

        <div className="input-container">
          <input
            type="text"
            id="query-field"
            className="input-field"
            placeholder="How may I help you?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={askQuestion}
            className="ask-button"
            disabled={loading}
          >
            {loading ? "Retrieving Info..." : "Ask"}
          </button>
        </div>

        {response && (
          <div className="response-container">
            <div
              className="response-content"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(marked(response)) }}
            />
          </div>
        )}

      </div>

      <Footer/>
    </div>
   
  );
}