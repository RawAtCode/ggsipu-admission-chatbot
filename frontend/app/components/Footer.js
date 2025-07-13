import React from 'react';

function Footer() {
  return (
    <footer className="bg-[#041d54] text-white py-4 w-full">
      <div className="container mx-auto px-4 flex flex-col items-center text-center gap-2">
        <p className="text-sm italic">
          Disclaimer: This chatbot is unofficial and not affiliated with GGSIPU.
        </p>

        <div>
          <iframe
            src="https://ghbtns.com/github-btn.html?user=RawAtCode&repo=your-repo&type=star&count=true"
            frameBorder="0"
            scrolling="0"
            width="100"
            height="20"
            title="GitHub Star Button"
          ></iframe>
        </div>

        <p className="text-sm">
          Developed by{' '}
          <a
            href="https://github.com/RawAtCode"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-gray-300"
          >
            RawAtCode
          </a>
        </p>
      </div>
    </footer>
  );
}

export default Footer;
