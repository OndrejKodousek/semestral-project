import React from "react";

interface ModelSelectProps {
  setModel: (model: string) => void;
}

const ModelSelect: React.FC<ModelSelectProps> = ({ setModel }) => {
  const items: string[] = [
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite-preview",
    "gemini-2.0-pro-exp",
    "gemini-2.0-flash-exp",

    "gemma2-9b-it",

    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "llama-3-8b-8192",
    "llama-3-70b-8192",

    "mixtral-8x7b-32768",
  ];

  return (
    <div className="inset-container p-3 h-100">
      <div className="d-flex flex-column h-100">
        <h3 className="no-select">Choose model</h3>
        <select
          className="form-select flex-grow-1 overflow-y-auto"
          size={5}
          aria-label="Select option"
          onChange={(e) => setModel(e.target.value)}
        >
          {items.map((item, index) => (
            <option key={index} value={item}>
              {item}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default ModelSelect;
