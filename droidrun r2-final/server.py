from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from reddit_agent import RedditAutomation
from datetime import datetime
import time

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize automation agent lazily
reddit_bot = None

def get_reddit_bot():
    global reddit_bot
    if reddit_bot is None:
        try: 
            reddit_bot = RedditAutomation()
        except Exception as e:
            print(f"Failed to initialize RedditAutomation: {e}")
            return None
    return reddit_bot

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/post")
async def post_message(request: Request):
    bot = get_reddit_bot()
    if not bot:
        return JSONResponse({"status": "error", "message": "Backend not initialized. Check GOOGLE_API_KEY."}, status_code=500)

    data = await request.json()
    title = data.get("title")
    body = data.get("body", "") # Optional
    
    # Check for list of subreddits OR single subreddit
    subreddits = data.get("subreddits") # Expecting list of strings
    single_subreddit = data.get("subreddit") # Legacy/Single support

    if not title:
        return JSONResponse({"status": "error", "message": "Title is required"}, status_code=400)
    
    if not subreddits and not single_subreddit:
         return JSONResponse({"status": "error", "message": "Either 'subreddits' (list) or 'subreddit' (string) is required"}, status_code=400)

    # Check for scheduling
    scheduled_time_str = data.get("scheduled_time")
    
    async def delayed_post(target_subreddits, delay_seconds):
        print(f"Waiting {delay_seconds} seconds before posting...")
        await asyncio.sleep(delay_seconds)
        await bot.post_multiple(title, body, target_subreddits)

    # Prepare target list (single or multiple)
    targets = []
    if subreddits:
        if isinstance(subreddits, str):
             targets = [s.strip() for s in subreddits.split(',')]
        else:
             targets = subreddits
    else:
        targets = [single_subreddit or "u/me"]

    if scheduled_time_str:
        try:
             # Browser sends: YYYY-MM-DDTHH:mm
             scheduled_dt = datetime.fromisoformat(scheduled_time_str)
             now = datetime.now()
             delay = (scheduled_dt - now).total_seconds()
             
             if delay > 0:
                 asyncio.create_task(delayed_post(targets, delay))
                 return {"status": "success", "message": f"Post scheduled for {scheduled_time_str} ({int(delay)}s delay)"}
             else:
                 print("Scheduled time is in the past, posting immediately.")
        except ValueError as e:
            return JSONResponse({"status": "error", "message": f"Invalid date format: {e}"}, status_code=400)

    # Immediate execution
    asyncio.create_task(bot.post_multiple(title, body, targets))
    return {"status": "success", "message": f"Broadcast started for {targets}"}

@app.post("/start_monitor")
async def start_monitor():
    bot = get_reddit_bot()
    if not bot:
         return JSONResponse({"status": "error", "message": "Backend not initialized."}, status_code=500)

    if bot.is_monitoring:
        return {"status": "info", "message": "Already monitoring"}
    
    asyncio.create_task(bot.start_monitoring_loop())
    return {"status": "success", "message": "Monitoring started"}

@app.post("/stop_monitor")
async def stop_monitor():
    bot = get_reddit_bot()
    if bot:
        bot.stop_monitoring()
    return {"status": "success", "message": "Monitoring stopping..."}

@app.get("/logs")
async def get_logs():
    bot = get_reddit_bot()
    if not bot:
        return {"logs": ["System: Waiting for initialization... Check API Key."], "is_monitoring": False}
    return {"logs": bot.logs, "is_monitoring": bot.is_monitoring}

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"\nServer error: {e}")
