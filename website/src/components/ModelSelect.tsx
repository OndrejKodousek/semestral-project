/**
 * @file ModelSelect.tsx
 * @brief Component for selecting an AI model from a predefined list
 * @details Provides a scrollable select list of available AI models
 * that can be used for stock prediction analysis.
 */

import React from "react";
import { ModelSelectProps } from "../utils/interfaces";

/**
 * @brief Model selection dropdown component
 * @param setModel - Callback function to update the selected model
 */
const ModelSelect: React.FC<ModelSelectProps> = ({ setModel }) => {
  // List of available AI models (should match backend)
  const items: string[] = [
    // Google AI Studio
    "gemini-2.5-flash-preview-04-17",
    "gemini-2.5-pro-preview-03-25",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    // OpenRouter
    "deepseek/deepseek-chat:free",
    // Groq
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    // Groq preview
    "deepseek-r1-distill-llama-70b",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen-qwq-32b",
  ];

  return (
    <div className="h-100">
      <select
        className="w-100 h-100"
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
  );
};

export default ModelSelect;
