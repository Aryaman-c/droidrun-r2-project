try:
    import fastapi
    import uvicorn
    import droidrun
    print("All dependencies found.")
except ImportError as e:
    print(f"Missing dependency: {e}")
