import sys
with open("test_result.txt", "w") as f:
    try:
        from reddit_agent import RedditAutomation
        agent = RedditAutomation()
        f.write("Filesuccess: API Key loaded.")
    except Exception as e:
        f.write(f"Filefail: {e}")
