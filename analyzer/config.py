"""
@file config.py
@brief Configuration loader for API keys and system instructions.

This module handles loading of sensitive API keys and system instruction templates
from files in the project directory. It centralizes all configuration loading
to ensure secure and consistent access to these resources throughout the application.
"""

import os
from pathlib import Path
from utils import get_project_root

# Load Gemini API key from file
file_path = os.path.join(get_project_root(), "data", "API_KEY_GEMINI")
with open(file_path, "r") as f:
    API_KEY_GEMINI = f.readline().strip()

# Load Groq API key from file
file_path = os.path.join(get_project_root(), "data", "API_KEY_GROQ")
with open(file_path, "r") as f:
    API_KEY_GROQ = f.readline().strip()

# Load OpenRouter API key from file
file_path = os.path.join(get_project_root(), "data", "API_KEY_OPENROUTER")
with open(file_path, "r") as f:
    API_KEY_OPENROUTER = f.readline().strip()

# Load individual article analysis system instruction template
file_path = os.path.join(get_project_root(), "data", "system_instruction.txt")
with open(file_path, "r") as f:
    SYSTEM_INSTRUCTION_INDIVIDUAL = f.read().strip()

# Load aggregated analysis system instruction template
file_path = os.path.join(
    get_project_root(), "data", "system_instruction_sum_analysis.txt"
)
with open(file_path, "r") as f:
    SYSTEM_INSTRUCTION_AGGREGATED = f.read().strip()
