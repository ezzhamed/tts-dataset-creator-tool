import React, { useEffect, useState, useRef } from 'react';

const ProgressBar = ({ percent }) => (
    <div className="w-full">
        <div className="flex justify-between mb-1">
            <span className="text-sm font-medium text-white">Progress</span>
            <span className="text-sm font-medium text-white">{percent}%</span>
        </div>
        <div className="w-full bg-gray-900 rounded-full h-2.5">
            <div
                className="bg-white h-2.5 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${percent}%` }}
            ></div>
        </div>
    </div>
);

const StatusViewer = ({ taskId }) => {
    const [status, setStatus] = useState('connecting');
    const [logs, setLogs] = useState([]);
    const [result, setResult] = useState(null);
    const [percent, setPercent] = useState(0);
    const ws = useRef(null);
    const logsEndRef = useRef(null);

    const scrollToBottom = () => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [logs]);

    useEffect(() => {
        if (!taskId) return;

        // Connect to WebSocket
        ws.current = new WebSocket(`wss://localhost:8000/ws/${taskId}`);

        ws.current.onopen = () => {
            setStatus('connected');
            setLogs(prev => [...prev, "Connected to server..."]);
        };

        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.status === 'completed') {
                setStatus('completed');
                setResult(data.result);
                setPercent(100);
                setLogs(prev => [...prev, "Processing Completed!"]);
                ws.current.close();
            } else if (data.status === 'error') {
                setStatus('error');
                setLogs(prev => [...prev, `Error: ${data.message}`]);
            } else {
                // Processing or other status
                setStatus(data.status);

                if (data.detail) {
                    if (data.detail.percent !== undefined) {
                        setPercent(data.detail.percent);
                    }

                    setLogs(prev => {
                        const lastLog = prev[prev.length - 1];
                        // Only add if different to avoid spamming
                        if (lastLog !== data.detail.message) {
                            return [...prev, data.detail.message];
                        }
                        return prev;
                    });
                } else {
                    setLogs(prev => {
                        const msg = `Status update: ${data.status}`;
                        if (prev[prev.length - 1] !== msg) {
                            return [...prev, msg];
                        }
                        return prev;
                    });
                }
            }
        };

        ws.current.onclose = () => {
            if (status !== 'completed') {
                setLogs(prev => [...prev, "Connection closed."]);
            }
        };

        return () => {
            if (ws.current) ws.current.close();
        };
    }, [taskId]);

    return (
        <div className="p-6 bg-black border border-gray-800 rounded-xl shadow-lg mt-8">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-white">Processing Status</h2>
                <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${status === 'completed' ? 'bg-green-900 text-green-300 border border-green-800' :
                    status === 'error' ? 'bg-red-900 text-red-300 border border-red-800' :
                        'bg-yellow-900 text-yellow-300 border border-yellow-800'
                    }`}>
                    {status}
                </span>
            </div>

            {status === 'processing' && (
                <div className="mb-6">
                    <ProgressBar percent={percent} />
                </div>
            )}

            <div className="bg-gray-900 text-green-400 p-4 rounded-lg border border-gray-800 h-64 overflow-y-auto font-mono text-sm shadow-inner">
                {logs.map((log, index) => (
                    <div key={index} className="mb-1 border-b border-gray-800 pb-1 last:border-0 last:pb-0">
                        <span className="text-gray-500 mr-2">&gt;</span>
                        {log}
                    </div>
                ))}
                {status === 'processing' && (
                    <div className="animate-pulse text-white mt-2">
                        <span className="mr-2">&gt;</span> ...
                    </div>
                )}
                <div ref={logsEndRef} />
            </div>

            {result && (
                <div className="mt-8 animate-fade-in">
                    <h3 className="text-lg font-bold text-white mb-4">
                        Result
                    </h3>

                    <div className="p-5 bg-gray-900 border border-gray-800 rounded-lg space-y-3 text-gray-200">
                        {result.filename && <p><strong className="text-white">File:</strong> {result.filename}</p>}
                        {result.output_path && <p><strong className="text-white">Output:</strong> {result.output_path}</p>}

                        {/* Scraper Results */}
                        {result.csv_filename && <p><strong className="text-white">CSV File:</strong> {result.csv_filename}</p>}
                        {result.csv_path && <p><strong className="text-white">CSV Path:</strong> {result.csv_path}</p>}

                        {/* Splitter Results */}
                        {result.output_csv && <p><strong className="text-white">Output CSV:</strong> {result.output_csv}</p>}
                        {result.audio_dir && <p><strong className="text-white">Audio Directory:</strong> {result.audio_dir}</p>}

                        {/* General Message */}
                        {result.message && <p><strong className="text-white">Message:</strong> {result.message}</p>}
                    </div>
                </div>
            )}
        </div>
    );
};

export default StatusViewer;
