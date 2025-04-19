import os

from pathlib import Path

from utils import get_project_root


file_path = os.path.join(get_project_root(), "data", "API_KEY_GEMINI")
with open(file_path, "r") as f:
    API_KEY_GEMINI = f.readline().strip()

file_path = os.path.join(get_project_root(), "data", "API_KEY_GROQ")
with open(file_path, "r") as f:
    API_KEY_GROQ = f.readline().strip()

file_path = os.path.join(get_project_root(), "data", "API_KEY_OPENROUTER")
with open(file_path, "r") as f:
    API_KEY_OPENROUTER = f.readline().strip()

file_path = os.path.join(get_project_root(), "analyzer", "system_instruction.txt")
with open(file_path, "r") as f:
    SYSTEM_INSTRUCTION_INDIVIDUAL = f.read().strip()

file_path = os.path.join(
    get_project_root(), "analyzer", "system_instruction_sum_analysis.txt"
)
with open(file_path, "r") as f:
    SYSTEM_INSTRUCTION_AGGREGATED = f.read().strip()
