// "use client";

// import { useState } from "react";
// import axios from "axios";
// import { marked } from "marked";
// import DOMPurify from "dompurify";
// import Header from "./Header";
// import Footer from "./Footer";

// export default function Chat() {
//   const [question, setQuestion] = useState("");
//   const [response, setResponse] = useState("");
//   const [loading, setLoading] = useState(false);

//   const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

//   const askQuestion = async (query) => {
//     if (!query.trim()) return;
//     setLoading(true);
//     setResponse("");

//     try {
//       const res = await axios.post(`${BACKEND_URL}/ask`, { question: query });
//       setResponse(res.data.answer || "No response received.");
//     } catch (error) {
//       console.error("Error fetching response:", error);
//       setResponse("Failed to get a response. Try again!");
//     }

//     setLoading(false);
//   };

//   const handleKeyDown = (e) => {
//     if (e.key === "Enter" && question.trim()) {
//       askQuestion(question);
//     }
//   };

//   const handleFAQClick = (faq) => {
//     setQuestion(faq);
//     askQuestion(faq);
//   };

//   return (
//     <div className="app-body">
//       <Header />

//       <div className="container">
//         <div className="container-heading">
//           <h1>GGSIPU Admission Chatbot</h1>
//           <p className="text-gray-700 text-center mt-2 max-w-2xl">
//             Ask me anything about admission queries. I'm here to assist you!
//           </p>
//         </div>

//         {/* Input Section */}
//         <div className="input-container">
//           <input
//             type="text"
//             id="query-field"
//             className="input-field"
//             placeholder="How may I help you?"
//             value={question}
//             onChange={(e) => setQuestion(e.target.value)}
//             onKeyDown={handleKeyDown}
//           />
//           <button
//             onClick={() => askQuestion(question)}
//             className="ask-button"
//             disabled={loading}
//           >
//             {loading ? "Retrieving Info..." : "Ask"}
//           </button>
//         </div>

//         {/* Response Section */}
//         {response && (
//           <div className="response-container">
//             <div
//               className="response-content"
//               dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(marked(response)) }}
//             />
//           </div>
//         )}

//         {/* FAQ Section */}
//         <div className="response-container">
//           <h2 className="text-xl font-bold text-gray-800 mb-3 text-center">
//             Frequently Asked Questions
//           </h2>
//           <ul className="space-y-3 text-gray-700">
//             {[
//               "What are the CET dates?",
//               "What is the fee for MCA?",
//               "Is CET mandatory for all courses?",
//               "What is the fee structure for B.Tech?",
//               "What documents are required for admission?",
//             ].map((faq, index) => (
//               <li
//                 key={index}
//                 className="p-3 bg-white rounded-lg shadow-sm border border-gray-300 cursor-pointer hover:bg-gray-100 transition"
//                 onClick={() => handleFAQClick(faq)}
//               >
//                 <strong>‣ {faq}</strong>
//               </li>
//             ))}
//           </ul>
//         </div>
//       </div>

//       <Footer />
//     </div>
//   );
// }



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

  const askQuestion = async (query) => {
    if (!query.trim()) return;
    setLoading(true);
    setResponse("");

    try {
      const res = await axios.post(`${BACKEND_URL}/ask`, { question: query });
      setResponse(res.data.answer || "No response received.");
    } catch (error) {
      console.error("Error fetching response:", error);
      setResponse("Failed to get a response. Try again!");
    }

    setLoading(false);
  };

  const handleFAQClick = (faq) => {
    setQuestion(faq);
    window.scrollTo({ top: 0, behavior: "smooth" }); // Scrolls to the top
    askQuestion(faq);
  };

  return (
    <div className="app-body">
      <Header />

      <div className="container">
        <div className="container-heading">
          <h1>GGSIPU Admission Chatbot</h1>
          <p className="text-gray-700 text-center mt-2 max-w-2xl">
            Ask me anything about admission queries. I'm here to assist you!
          </p>
        </div>

        {/* Input Section */}
        <div className="input-container">
          <input
            type="text"
            id="query-field"
            className="input-field"
            placeholder="How may I help you?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && askQuestion(question)}
          />
          <button
            onClick={() => askQuestion(question)}
            className="ask-button"
            disabled={loading}
          >
            {loading ? "Retrieving Info..." : "Ask"}
          </button>
        </div>

        {/* Response Section */}
        {response && (
          <div className="response-container">
            <div
              className="response-content"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(marked(response)) }}
            />
          </div>
        )}

        {/* FAQ Section */}
        <div className="response-container">
          <h2 className="text-xl font-bold text-gray-800 mb-3 text-center">
            Frequently Asked Questions
          </h2>
          <ul className="space-y-3 text-gray-700">
            {[
              "What are the CET dates?",
              "What is the fee for MCA?",
              "Is CET mandatory for all courses?",
              "What is the fee structure for B.Tech?",
              "What are the counselling dates for MBA?",
            ].map((faq, index) => (
              <li
                key={index}
                className="p-3 bg-white rounded-lg shadow-sm border border-gray-300 cursor-pointer hover:bg-gray-100 transition"
                onClick={() => handleFAQClick(faq)}
              >
                <strong>‣ {faq}</strong>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <Footer />
    </div>
  );
}
