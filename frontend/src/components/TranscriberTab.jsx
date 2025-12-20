import React, { useState } from 'react';
import StatusViewer from './StatusViewer';

const TranscriberTab = () => {
    const [outputName, setOutputName] = useState('transcription.csv');
    const [method, setMethod] = useState('local'); // 'local' or 'elevenlabs'
    const [apiKey, setApiKey] = useState('');
    const [taskId, setTaskId] = useState(null);
    const [error, setError] = useState(null);

    const handleTranscribe = async () => {
        setError(null);

        // Validate inputs
        if (method === 'elevenlabs' && !apiKey.trim()) {
            setError("Please provide an ElevenLabs API key.");
            return;
        }

        try {
            const payload = {
                output_csv_name: outputName,
                method: method
            };

            if (method === 'elevenlabs') {
                payload.api_key = apiKey;
            }

            const apiUrl = import.meta.env.VITE_API_URL || "https://localhost:8000";
            const response = await fetch(`${apiUrl}/tasks/transcribe`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            setTaskId(data.task_id);
        } catch (err) {
            setError("Failed to start transcription: " + err.message);
        }
    };

    return (
        <div className="animate-fade-in">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">3. Audio Transcriber</h2>
                <span className="text-sm text-gray-400 bg-black px-3 py-1 rounded-full border border-gray-800">Step 3 of 3</span>
            </div>

            <div className="space-y-6">
                <div className="bg-blue-900/20 border border-blue-900 rounded-lg p-4">
                    <p className="text-sm text-blue-200">
                        This will transcribe all audio files currently in the <code className="bg-black px-1 py-0.5 rounded text-blue-100">storage/audios/splitted_audios</code> folder.
                    </p>
                </div>

                {/* Transcription Method Selection */}
                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-3">Transcription Method</label>
                    <div className="grid grid-cols-2 gap-4">
                        <button
                            onClick={() => setMethod('local')}
                            className={`p-4 rounded-lg border transition-all ${method === 'local'
                                ? 'bg-white text-black border-white'
                                : 'bg-black text-gray-400 border-gray-800 hover:border-gray-600'
                                }`}
                        >
                            <div className="font-medium">Local STT Model</div>
                            <div className="text-xs mt-1 opacity-75">Seamless M4T</div>
                        </button>
                        <button
                            onClick={() => setMethod('elevenlabs')}
                            className={`p-4 rounded-lg border transition-all ${method === 'elevenlabs'
                                ? 'bg-white text-black border-white'
                                : 'bg-black text-gray-400 border-gray-800 hover:border-gray-600'
                                }`}
                        >
                            <div className="font-medium">ElevenLabs API</div>
                            <div className="text-xs mt-1 opacity-75">Cloud-based</div>
                        </button>
                    </div>
                </div>

                {/* ElevenLabs API Key Input */}
                {method === 'elevenlabs' && (
                    <div className="animate-fade-in">
                        <label className="block text-sm font-medium text-gray-300 mb-2">ElevenLabs API Key</label>
                        <input
                            type="password"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            placeholder="Enter your ElevenLabs API key"
                            className="block w-full rounded-lg bg-black border border-gray-800 text-white placeholder-gray-500 focus:border-white focus:ring-white sm:text-sm p-3 shadow-sm transition-colors"
                        />
                        <p className="mt-2 text-xs text-gray-500">
                            Get your API key from <a href="https://elevenlabs.io" target="_blank" rel="noopener noreferrer" className="text-white hover:underline">elevenlabs.io</a>
                        </p>
                    </div>
                )}

                {/* Output CSV Name */}
                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Output CSV Name</label>
                    <input
                        type="text"
                        value={outputName}
                        onChange={(e) => setOutputName(e.target.value)}
                        className="block w-full rounded-lg bg-black border border-gray-800 text-white placeholder-gray-500 focus:border-white focus:ring-white sm:text-sm p-3 shadow-sm transition-colors"
                    />
                </div>

                {error && (
                    <div className="bg-red-900/50 border border-red-800 text-red-200 px-4 py-3 rounded-lg">
                        {error}
                    </div>
                )}

                <button
                    onClick={handleTranscribe}
                    className="w-full sm:w-auto bg-white text-black px-6 py-3 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-white transition-all duration-200 font-medium shadow-lg"
                >
                    Start Transcription
                </button>
            </div>

            {taskId && <StatusViewer taskId={taskId} />}
        </div>
    );
};

export default TranscriberTab;
