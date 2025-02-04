import React, { useState } from 'react'

const UrlInput = ({ onNavigate }) => {
    const [url, setUrl] = useState('https://www.google.com')

    const handleSubmit = (e) => {
        e.preventDefault()
        onNavigate(url)
    }

    return (
        <form onSubmit={handleSubmit} className="controls">
            <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Enter URL"
                className="url-input"
            />
            <button type="submit" className="nav-button">Go</button>
        </form>
    )
}

export default UrlInput