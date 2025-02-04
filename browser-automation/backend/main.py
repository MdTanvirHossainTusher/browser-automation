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

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active browser sessions
browser_sessions: Dict[str, dict] = {}

async def capture_browser_frames(driver, websocket: WebSocket):
    """Continuously capture and stream browser frames"""
    while True:
        try:
            # Capture screenshot as PNG
            screenshot = driver.get_screenshot_as_png()
            
            # Optimize image size using PIL
            image = Image.open(io.BytesIO(screenshot))
            optimized = io.BytesIO()
            image.save(optimized, format='JPEG', quality=70)
            base64_image = base64.b64encode(optimized.getvalue()).decode('utf-8')
            
            # Send frame to client
            await websocket.send_json({
                "type": "frame",
                "data": base64_image
            })
            
            # Small delay to control frame rate
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
                # Map common keys to Selenium Keys
                key_mapping = {
                    "Enter": Keys.ENTER,
                    "Backspace": Keys.BACKSPACE,
                    "Tab": Keys.TAB,
                    "Escape": Keys.ESCAPE,
                    # Add more key mappings as needed
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
        
        # Configure Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Store session info
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
    
    # Start frame capture and user action handling tasks
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













# # from fastapi import FastAPI, WebSocket, HTTPException
# # from fastapi.middleware.cors import CORSMiddleware
# # from playwright.async_api import async_playwright
# # import asyncio
# # import base64
# # import json
# # from typing import Dict, Optional
# # import uuid

# # app = FastAPI()

# # # Enable CORS
# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )

# # # Store active browser sessions
# # browser_sessions: Dict[str, dict] = {}

# from fastapi import FastAPI, WebSocket, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from playwright.async_api import async_playwright
# import asyncio
# import base64
# import json
# from typing import Dict, Optional
# import uuid
# import logging

# # Set up logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# app = FastAPI()

# # Enable CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Store active browser sessions
# browser_sessions: Dict[str, dict] = {}

# async def capture_browser_frames(page, websocket: WebSocket):
#     """Continuously capture and stream browser frames"""
#     while True:
#         try:
#             # Capture screenshot as base64
#             screenshot = await page.screenshot(type='jpeg', quality=70)
#             base64_image = base64.b64encode(screenshot).decode('utf-8')
            
#             # Send frame to client
#             await websocket.send_json({
#                 "type": "frame",
#                 "data": base64_image
#             })
            
#             # Small delay to control frame rate
#             await asyncio.sleep(0.1)
#         except Exception as e:
#             print(f"Error capturing frame: {e}")
#             break

# async def handle_user_actions(page, websocket: WebSocket):
#     """Handle incoming user actions"""
#     try:
#         while True:
#             message = await websocket.receive_json()
            
#             if message["type"] == "click":
#                 x, y = message["x"], message["y"]
#                 await page.mouse.click(x, y)
            
#             elif message["type"] == "type":
#                 text = message["text"]
#                 await page.keyboard.type(text)
            
#             elif message["type"] == "navigate":
#                 url = message["url"]
#                 await page.goto(url)
            
#             elif message["type"] == "keypress":
#                 key = message["key"]
#                 await page.keyboard.press(key)
#     except Exception as e:
#         print(f"Error handling user action: {e}")

# # @app.post("/api/browser/start")
# # async def start_browser_session():
# #     """Start a new browser session"""
# #     session_id = str(uuid.uuid4())
    
# #     try:
# #         playwright = await async_playwright().start()
# #         browser = await playwright.chromium.launch()
# #         context = await browser.new_context()
# #         page = await context.new_page()
        
# #         # Store session info
# #         browser_sessions[session_id] = {
# #             "playwright": playwright,
# #             "browser": browser,
# #             "context": context,
# #             "page": page
# #         }
        
# #         return {"session_id": session_id}
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))


# @app.post("/api/browser/start")
# async def start_browser_session():
#     """Start a new browser session"""
#     session_id = str(uuid.uuid4())
    
#     try:
#         logger.debug("Starting new browser session...")
#         playwright = await async_playwright().start()
#         logger.debug("Playwright started successfully")
        
#         # Launch browser with specific arguments for better compatibility
#         browser = await playwright.chromium.launch(
#             headless=True,  # Make sure browser runs in headless mode
#             args=['--no-sandbox', '--disable-setuid-sandbox']
#         )
#         logger.debug("Browser launched successfully")
        
#         context = await browser.new_context()
#         page = await context.new_page()
        
#         # Store session info
#         browser_sessions[session_id] = {
#             "playwright": playwright,
#             "browser": browser,
#             "context": context,
#             "page": page
#         }
        
#         logger.debug(f"Browser session created successfully with ID: {session_id}")
#         return {
#             "status": "success",
#             "session_id": session_id,
#             "message": "Browser session started successfully"
#         }
        
#     except Exception as e:
#         logger.error(f"Failed to start browser session: {str(e)}", exc_info=True)
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to start browser session: {str(e)}"
#         )


# @app.websocket("/ws/{session_id}")
# async def websocket_endpoint(websocket: WebSocket, session_id: str):
#     """Handle WebSocket connection for browser streaming"""
#     if session_id not in browser_sessions:
#         await websocket.close(code=4000)
#         return
    
#     session = browser_sessions[session_id]
#     page = session["page"]
    
#     await websocket.accept()
    
#     # Start frame capture and user action handling tasks
#     frame_task = asyncio.create_task(capture_browser_frames(page, websocket))
#     action_task = asyncio.create_task(handle_user_actions(page, websocket))
    
#     try:
#         await asyncio.gather(frame_task, action_task)
#     except Exception as e:
#         print(f"WebSocket error: {e}")
#     finally:
#         frame_task.cancel()
#         action_task.cancel()

# @app.on_event("shutdown")
# async def shutdown_event():
#     """Cleanup browser sessions on shutdown"""
#     for session in browser_sessions.values():
#         await session["browser"].close()
#         await session["playwright"].stop()
#     browser_sessions.clear()

# @app.get("/")
# async def root():
#     return {"message": "Browser Automation API is running"}