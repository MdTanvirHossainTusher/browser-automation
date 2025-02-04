import React, { useRef, useEffect } from 'react'

const BrowserView = ({ websocket, onInteract }) => {
    const canvasRef = useRef(null)

    useEffect(() => {
        if (!websocket) return

        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data)
            if (data.type === 'frame') {
                const canvas = canvasRef.current
                const ctx = canvas.getContext('2d')
                const image = new Image()
                image.onload = () => {
                    canvas.width = image.width
                    canvas.height = image.height
                    ctx.drawImage(image, 0, 0)
                }
                image.src = `data:image/jpeg;base64,${data.data}`
            }
        }
    }, [websocket])

    const handleCanvasClick = (event) => {
        const canvas = canvasRef.current
        const rect = canvas.getBoundingClientRect()
        const scaleX = canvas.width / rect.width
        const scaleY = canvas.height / rect.height

        const x = Math.round((event.clientX - rect.left) * scaleX)
        const y = Math.round((event.clientY - rect.top) * scaleY)

        onInteract({ type: 'click', x, y })
    }

    const handleKeyDown = (event) => {
        onInteract({
            type: 'keypress', 
            key: event.key
        })
    }

    return (
        <div className="browser-container">
            <canvas 
                ref={canvasRef} 
                className="browser-canvas"
                onClick={handleCanvasClick}
                tabIndex={0}
                onKeyDown={handleKeyDown}
            />
        </div>
    )
}

export default BrowserView