import React from 'react';

function Footer() {
  return (
    <footer className="bg-[#041d54] text-white py-2 w-full">
      <div className="container mx-auto px-3 flex flex-col items-center text-center md:items-start md:text-left">
        {/* Contact Info */}
        <h2 className="text-lg font-semibold">Contact Us</h2>
        <p className="text-sm mt-1"><strong>Helpline:</strong> 011-25302167, 011-25302169</p>
        <p className="text-sm"><strong>Public Relation Officer:</strong> 011-25302171</p>
        <p className="text-sm"><strong>Email: </strong>
          <a href="mailto:pro@ipu.ac.in" className="">pro@ipu.ac.in</a>,  
          <a href="mailto:admissiongrievances@ipu.ac.in" className=" ml-1">admissiongrievances@ipu.ac.in</a>
        </p>
      </div>
    </footer>
  );
}

export default Footer;
