import React from 'react';
import ReactMarkdown from 'react-markdown';

const Md = ({ children }) => (
  <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-li:my-0 prose-headings:my-2 prose-strong:text-white">
    <ReactMarkdown>{children || ''}</ReactMarkdown>
  </div>
);

export default Md;
