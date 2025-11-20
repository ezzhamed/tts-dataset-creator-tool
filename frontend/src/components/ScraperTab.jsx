import React, { useState } from 'react';
import StatusViewer from './StatusViewer';

const ScraperTab = () => {
    const [url, setUrl] = useState('');
    const [taskId, setTaskId] = useState(null);
    const [error, setError] = useState(null);

    const handleScrape = async () => {
        if (!url) {
            setError("Please provide a YouTube URL (video or playlist).");
            return;
        }
        setError(null);

        try {
            const response = await fetch("https://localhost:8000/tasks/scrape", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ playlist_url: url })
            });
            const data = await response.json();
            setTaskId(data.task_id);
        } catch (err) {
            setError("Failed to start scraping: " + err.message);
        }
    };

    return (
        <div className="animate-fade-in">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">1. YouTube Scraper</h2>
                <span className="text-sm text-gray-400 bg-black px-3 py-1 rounded-full border border-gray-800">Step 1 of 3</span>
            </div>

            <div className="space-y-6">
                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">YouTube URL (Video or Playlist)</label>
                    <input
                        type="text"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="https://www.youtube.com/watch?v=... or https://www.youtube.com/playlist?list=..."
                        className="block w-full rounded-lg bg-black border border-gray-800 text-white placeholder-gray-500 focus:border-white focus:ring-white sm:text-sm p-3 shadow-sm transition-colors"
                    />
                    <p className="mt-2 text-xs text-gray-500">
                        Supports individual videos, playlists, and channels.
                    </p>
                </div>

                {error && (
                    <div className="bg-red-900/50 border border-red-800 text-red-200 px-4 py-3 rounded-lg">
                        {error}
                    </div>
                )}

                <button
                    onClick={handleScrape}
                    className="w-full sm:w-auto bg-white text-black px-6 py-3 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-white transition-all duration-200 font-medium shadow-lg"
                >
                    Start Scraping
                </button>
            </div>

            {taskId && <StatusViewer taskId={taskId} />}
        </div>
    );
};

export default ScraperTab;
