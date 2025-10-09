#!/usr/bin/env python3
"""Quick test to verify .env loading."""

import os
from dotenv import load_dotenv

# Force reload
load_dotenv(override=True)

print("Environment variable test:")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT SET')[:20]}...")
print(f"ANTHROPIC_API_KEY: {os.getenv('ANTHROPIC_API_KEY', 'NOT SET')[:20]}...")
