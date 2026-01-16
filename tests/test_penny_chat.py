#!/usr/bin/env python3
from research_first_pipeline import ResearchFirstPipeline

print("=" * 60)
print("🎉 PENNY - NOW 100% LOCAL WITH NEMOTRON!")
print("=" * 60)
print("\nType 'quit' to exit\n")

pipeline = ResearchFirstPipeline()

while True:
    user_input = input("You: ")
    if user_input.lower() in ['quit', 'exit', 'bye']:
        print("\n👋 Goodbye!\n")
        break
    
    print("\nPenny: ", end="", flush=True)
    response = pipeline.think(user_input)
    print(f"{response}\n")
