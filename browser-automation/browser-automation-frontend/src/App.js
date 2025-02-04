import React, { useState, useEffect, useRef } from 'react'
import BrowserView from './components/BrowserView'
import UrlInput from './components/UrlInput'

const App = () => {
    const [sessionId, setSessionId] = useState(null)
    const [isConnected, setIsConnected] = useState(false)
    const websocketRef = useRef(null)

    const startBrowserSession = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/browser/start', {
                method: 'POST'
            })
            const data = await response.json()
            setSessionId(data.session_id)
        } catch (error) {
            console.error('Failed to start browser session:', error)
        }
    }

    const connectWebSocket = () => {
        if (!sessionId) return

        const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`)
        
        ws.onopen = () => {
            console.log('WebSocket Connected')
            setIsConnected(true)
        }

        ws.onclose = () => {
            console.log('WebSocket Disconnected')
            setIsConnected(false)
        }

        websocketRef.current = ws
    }

    useEffect(() => {
        startBrowserSession()
    }, [])

    useEffect(() => {
        if (sessionId) {
            connectWebSocket()
        }
        
        return () => {
            if (websocketRef.current) {
                websocketRef.current.close()
            }
        }
    }, [sessionId])

    const sendWebSocketMessage = (message) => {
        if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
            websocketRef.current.send(JSON.stringify(message))
        }
    }

    return (
        <div className="app-container">
            <h1>Browser Automation</h1>
            {sessionId && (
                <>
                    <UrlInput 
                        onNavigate={(url) => sendWebSocketMessage({ type: 'navigate', url })} 
                    />
                    <BrowserView 
                        websocket={websocketRef.current}
                        onInteract={sendWebSocketMessage}
                    />
                </>
            )}
            {!sessionId && <p>Starting browser session...</p>}
        </div>
    )
}

export default App