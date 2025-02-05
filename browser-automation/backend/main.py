from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import asyncio
import base64
from typing import Dict
import uuid
import logging
import io
from PIL import Image

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

browser_sessions: Dict[str, dict] = {}

async def capture_browser_frames(driver, websocket: WebSocket):
    """Continuously capture and stream browser frames"""
    while True:
        try:
            screenshot = driver.get_screenshot_as_png()
            
            image = Image.open(io.BytesIO(screenshot))
            optimized = io.BytesIO()
            image.save(optimized, format='JPEG', quality=70)
            base64_image = base64.b64encode(optimized.getvalue()).decode('utf-8')
            
            await websocket.send_json({
                "type": "frame",
                "data": base64_image
            })
            
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            break

async def handle_user_actions(driver, websocket: WebSocket):
    """Handle incoming user actions"""
    try:
        action_chains = ActionChains(driver)
        while True:
            message = await websocket.receive_json()
            
            if message["type"] == "click":
                x, y = message["x"], message["y"]
                action_chains.move_by_offset(x, y).click().perform()
                action_chains.reset_actions()
            
            elif message["type"] == "type":
                text = message["text"]
                action_chains.send_keys(text).perform()
                action_chains.reset_actions()
            
            elif message["type"] == "navigate":
                url = message["url"]
                driver.get(url)
            
            elif message["type"] == "keypress":
                key = message["key"]

                key_mapping = {
                    "Enter": Keys.ENTER,
                    "Backspace": Keys.BACKSPACE,
                    "Tab": Keys.TAB,
                    "Escape": Keys.ESCAPE,
                }
                selenium_key = key_mapping.get(key, key)
                action_chains.send_keys(selenium_key).perform()
                action_chains.reset_actions()
                
    except Exception as e:
        logger.error(f"Error handling user action: {e}")

@app.post("/api/browser/start")
async def start_browser_session():
    """Start a new browser session"""
    session_id = str(uuid.uuid4())
    
    try:
        logger.debug("Starting new browser session...")
        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        driver = webdriver.Chrome(options=chrome_options)
        
        browser_sessions[session_id] = {
            "driver": driver
        }
        
        logger.debug(f"Browser session created successfully with ID: {session_id}")
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Browser session started successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to start browser session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start browser session: {str(e)}"
        )

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Handle WebSocket connection for browser streaming"""
    if session_id not in browser_sessions:
        await websocket.close(code=4000)
        return
    
    session = browser_sessions[session_id]
    driver = session["driver"]
    
    await websocket.accept()
    
    frame_task = asyncio.create_task(capture_browser_frames(driver, websocket))
    action_task = asyncio.create_task(handle_user_actions(driver, websocket))
    
    try:
        await asyncio.gather(frame_task, action_task)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        frame_task.cancel()
        action_task.cancel()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup browser sessions on shutdown"""
    for session in browser_sessions.values():
        session["driver"].quit()
    browser_sessions.clear()

@app.get("/")
async def root():
    return {"message": "Browser Automation API is running"}