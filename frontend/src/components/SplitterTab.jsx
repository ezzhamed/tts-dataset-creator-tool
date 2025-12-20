import React, { useState } from 'react';
import StatusViewer from './StatusViewer';

const SplitterTab = () => {
    const [taskId, setTaskId] = useState(null);
    const [error, setError] = useState(null);
    const [audioFolder, setAudioFolder] = useState('');
    const [splittingMethod, setSplittingMethod] = useState('vad'); // 'vad' or 'semantic'

    const handleSplit = async () => {
        if (!audioFolder) {
            setError("Please enter the audio folder path.");
            return;
        }

        const payload = {
            audio_folder: audioFolder,
            splitting_method: splittingMethod
        };
        setError(null);

        try {
            const apiUrl = import.meta.env.VITE_API_URL || "https://localhost:8000";
            const response = await fetch(`${apiUrl}/tasks/split`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
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
                    <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-4 mb-4 text-sm text-gray-400">
                        The tool will scan the provided folder for audio files (.wav, .mp3, etc.) and generate a new dataset CSV.
                    </div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Input Audio Folder Path</label>
                    <input
                        type="text"
                        value={audioFolder}
                        onChange={(e) => setAudioFolder(e.target.value)}
                        placeholder="e.g. storage/audios/my_channel OR C:\Path\To\Audios"
                        className="block w-full rounded-lg bg-black border-gray-800 text-white focus:border-white focus:ring-white sm:text-sm p-3 shadow-sm transition-colors"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-3">Splitting Method</label>
                    <div className="grid grid-cols-2 gap-4">
                        <button
                            onClick={() => setSplittingMethod('vad')}
                            className={`p-4 rounded-lg border transition-all ${splittingMethod === 'vad'
                                ? 'bg-white text-black border-white'
                                : 'bg-black text-gray-400 border-gray-800 hover:border-gray-600'
                                }`}
                        >
                            <div className="font-medium">Silero VAD</div>
                            <div className="text-xs mt-1 opacity-75">Fast, Silence-based</div>
                        </button>
                        <button
                            onClick={() => setSplittingMethod('semantic')}
                            className={`p-4 rounded-lg border transition-all ${splittingMethod === 'semantic'
                                ? 'bg-white text-black border-white'
                                : 'bg-black text-gray-400 border-gray-800 hover:border-gray-600'
                                }`}
                        >
                            <div className="font-medium">Semantic (Whisper)</div>
                            <div className="text-xs mt-1 opacity-75">Accurate, Sentence-based</div>
                        </button>
                    </div>
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
                    Start Splitting
                </button>
            </div>

            {taskId && <StatusViewer taskId={taskId} />}
        </div>
    );
};

export default SplitterTab;
