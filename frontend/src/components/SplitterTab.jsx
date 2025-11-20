import React, { useState, useEffect } from 'react';
import StatusViewer from './StatusViewer';

const SplitterTab = () => {
    const [csvs, setCsvs] = useState([]);
    const [selectedCsv, setSelectedCsv] = useState('');
    const [taskId, setTaskId] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch("https://localhost:8000/files/csvs")
            .then(res => res.json())
            .then(data => setCsvs(data))
            .catch(err => console.error("Failed to load CSVs", err));
    }, []);

    const handleSplit = async () => {
        if (!selectedCsv) {
            setError("Please select a CSV file.");
            return;
        }
        setError(null);

        try {
            const response = await fetch("https://localhost:8000/tasks/split", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ csv_filename: selectedCsv })
            });
            const data = await response.json();
            setTaskId(data.task_id);
        } catch (err) {
            setError("Failed to start splitting: " + err.message);
        }
    };

    return (
        <div className="animate-fade-in">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">2. Audio Splitter</h2>
                <span className="text-sm text-gray-400 bg-black px-3 py-1 rounded-full border border-gray-800">Step 2 of 3</span>
            </div>

            <div className="space-y-6">
                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Select Scraped Metadata CSV</label>
                    <select
                        value={selectedCsv}
                        onChange={(e) => setSelectedCsv(e.target.value)}
                        className="block w-full rounded-lg bg-black border-gray-800 text-white focus:border-white focus:ring-white sm:text-sm p-3 shadow-sm transition-colors"
                    >
                        <option value="">-- Select CSV --</option>
                        {csvs.map(csv => (
                            <option key={csv} value={csv}>{csv}</option>
                        ))}
                    </select>
                </div>

                {error && (
                    <div className="bg-red-900/50 border border-red-800 text-red-200 px-4 py-3 rounded-lg">
                        {error}
                    </div>
                )}

                <button
                    onClick={handleSplit}
                    className="w-full sm:w-auto bg-white text-black px-6 py-3 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-white transition-all duration-200 font-medium shadow-lg"
                >
                    Start Downloading & Splitting
                </button>
            </div>

            {taskId && <StatusViewer taskId={taskId} />}
        </div>
    );
};

export default SplitterTab;
