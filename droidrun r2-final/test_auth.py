from reddit_agent import RedditAutomation
import sys

try:
    agent = RedditAutomation()
    print("Successfully instantiated RedditAutomation. API Key loaded.")
except Exception as e:
    print(f"Failed to instantiate RedditAutomation: {e}")
    sys.exit(1)
