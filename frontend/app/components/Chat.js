"use client";

import { useState } from "react";
import axios from "axios";
import { marked } from "marked"; // Import Markdown Parser
import { link } from './../../node_modules/mdast-util-to-hast/lib/handlers/link';

export default function Chat() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const askQuestion = async () => {
    if (!question) return;
    setLoading(true);
    setResponse("");

    try {
      const res = await axios.post("http://127.0.0.1:8000/ask", { question });
      setResponse(res.data.answer || "No response received.");
    } catch (error) {
      console.error("Error fetching response:", error);
      setResponse("Failed to get a response. Try again!");
    }

    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      askQuestion();
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white p-4">

      <h1 className="text-3xl font-bold mb-6">Admission Chatbot</h1>
      <div className="w-full max-w-2xl bg-gray-800 p-6 rounded-lg shadow-md">
        <input
          type="text"
          className="w-full p-3 text-black rounded-md"
          placeholder="How may I help you?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          onClick={askQuestion}
          className="w-full mt-4 bg-[rgba(2,72,88,0.6)] hover:bg-[rgba(2,90,110,0.8)] active:scale-95 text-white py-2 px-4 rounded-md transition-transform"

          disabled={loading}
        >
          {loading ? "Retrieving Info..." : "Ask"}
        </button>
      </div>

      {response && (
        <div
          className="mt-6 p-4 bg-gray-700 rounded-lg w-full max-w-2xl max-h-80 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800"
        >
          <div className="mt-2 text-white"
            dangerouslySetInnerHTML={{ __html: marked(response) }}
          />
        </div>
      )}

      <footer className="absolute bottom-4 w-full flex justify-center">
        <p className="text-gray-400">
          Developed by{" "}
          <a
            href="https://github.com/RawAtCode"
            target="_blank"
            rel="noopener noreferrer"
            className="text-cyan-400 hover:text-cyan-300 transition"
          >
            RawAtCode
          </a>
        </p>
      </footer>
    </div>
  );
}
