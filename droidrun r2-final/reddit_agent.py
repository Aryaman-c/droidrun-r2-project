import os
import asyncio
from dotenv import load_dotenv
load_dotenv()
from droidrun import DroidAgent, DroidrunConfig, AgentConfig, AdbTools
# from llama_index.llms.google_genai import GoogleGenAI
# from llama_index.llms.openai import OpenAI
from llama_index.llms.openai_like import OpenAILike

class RedditAutomation:
    def __init__(self):
        # Using OpenRouter as requested
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        self.api_base = "https://openrouter.ai/api/v1"
        self.model = "google/gemini-2.0-flash-001" 
        
        self.llm = OpenAILike(
            model=self.model,
            api_key=self.api_key,
            api_base=self.api_base,
            is_chat_model=True,
            temperature=0.0
        )
        self.tools = AdbTools()
        self.is_monitoring = False
        self.logs = []

    def log(self, message):
        print(f"[RedditAuto] {message}")
        self.logs.append(message)
        if len(self.logs) > 50:
            self.logs.pop(0)

    async def post_message(self, title: str, body: str, subreddit: str):
        self.log(f"Starting post task: {title} in {subreddit}")
        prompt = (
            f"Goal: Post a new message to '{subreddit}'.\n"
            f"1. Open Reddit App: Ensure the Reddit app is open.\n"
            f"2. Search: \n"
            f"   - Tap the search icon/bar.\n"
            f"   - Type '{subreddit}'.\n"
            f"   - IMPORTANT: Wait a moment for search suggestions.\n"
            f"   - Tap the 'r/{subreddit}' community result. If not seen, press Enter on keyboard and look for the community tab/result.\n"
            f"3. Verify: Check that you are actually in 'r/{subreddit}'.\n"
            f"4. Create Post:\n"
            f"   - Tap the '+' (Create) button.\n"
            f"   - Input Title: '{title}'.\n"
            f"   - **AUTO-FLAIR (CONDITIONAL)**:\n"
            f"     1. LOOK for a button labeled 'Add tags and flair' or 'Add flair' under the title.\n"
            f"     2. IF NOT VISIBLE: Skip this step and proceed to Body.\n"
            f"     3. IF VISIBLE:\n"
            f"        a. TAP exactly on the button to open the menu.\n"
            f"        b. WAIT for the list.\n"
            f"        c. SCAN for the best matching flair based on Title: '{title}'.\n"
            f"        d. IMPORTANT: You MUST choose a specific flair if available. DO NOT leave as 'None'.\n"
            f"        e. TAP 'Apply'.\n"
            f"   - Input Body: '{body}'.\n"
            f"   - Tap 'Next' (if shown) -> 'Post'.\n"
            f"5. Confirm: Wait for post confirmation."
        )
        
        agent = DroidAgent(
            prompt,
            config=DroidrunConfig(agent=AgentConfig(max_steps=30)), # Increased steps for navigation
            llms=self.llm,
            tools=self.tools
        )
        
        try:
            await agent.run()
            self.log(f"Posting to {subreddit} completed.")
            return True
        except Exception as e:
            self.log(f"Posting to {subreddit} failed: {e}")
            return False

    async def post_multiple(self, title: str, body: str, subreddits: list[str]):
        results = {}
        for sub in subreddits:
            self.log(f"Broadcasting: Posting to {sub}...")
            success = await self.post_message(title, body, sub)
            results[sub] = "Success" if success else "Failed"
            # Optional: Wait a bit between posts?
            await asyncio.sleep(2) 
        self.log(f"Broadcast complete: {results}")
        return results

    async def reply_to_comments(self):
        self.log("Checking for new comments...")
        prompt = (
            "Open the Reddit app. "
            "Navigate to my profile and open the most recent post. "
            "Scroll through the comments to find new ones I haven't replied to. "
            "For each unreplied comment from another user: "
            "1. Read the text. IF it asks to 'DM', 'message me', or 'private message': "
            f"   a. Tap the username to view their profile (verify it's the right person). \n"
            f"   b. Tap 'Start Chat' or 'Chat' icon. \n"
            f"   c. Send the message: 'Hi! I saw your comment asking to DM. How can I help?'. \n"
            f"   d. Go BACK to the comment thread. \n"
            f"   e. LOCATE the specific comment you just replied to. \n"
            f"   f. Tap the 'Reply' button **directly underneath that specific comment**. DO NOT tap the main 'Add a comment' bar at the bottom. \n"
            f"   g. Write: 'Sent you a DM!', then send. \n"
            "2. IF it does NOT ask for a DM: "
            "   a. Understand the context of their comment. "
            "   b. Tap 'Reply'. "
            "   c. Type a friendly, relevant response addressing their specific point. "
            "   d. Send the reply. "
            "Repeat this for visible unreplied comments. "
            "Refresh the page when done."
        )

        agent = DroidAgent(
            prompt,
            config=DroidrunConfig(agent=AgentConfig(max_steps=30)),
            llms=self.llm,
            tools=self.tools
        )

        try:
            await agent.run()
            self.log("Comment check completed.")
        except Exception as e:
            self.log(f"Comment check failed: {e}")

    async def start_monitoring_loop(self):
        self.is_monitoring = True
        self.log("Monitoring started.")
        while self.is_monitoring:
            await self.reply_to_comments()
            # Wait for 1 minute before next check
            for _ in range(60):
                if not self.is_monitoring:
                    break
                await asyncio.sleep(1)
        self.log("Monitoring stopped.")

    def stop_monitoring(self):
        self.is_monitoring = False
