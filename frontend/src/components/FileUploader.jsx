import React, { useState } from 'react';

const FileUploader = ({ onUploadSuccess }) => {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState(null);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
        setError(null);
        setProgress(0);
    };

    const handleUpload = async () => {
        if (!file) {
            setError("Please select a file first.");
            return;
        }

        setUploading(true);
        setError(null);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const xhr = new XMLHttpRequest();
            xhr.open("POST", "https://localhost:8000/upload"); // Note: HTTPS

            xhr.upload.onprogress = (event) => {
                if (event.lengthComputable) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    setProgress(percentComplete);
                }
            };

            xhr.onload = () => {
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    onUploadSuccess(response.task_id);
                    setUploading(false);
                } else {
                    setError("Upload failed: " + xhr.statusText);
                    setUploading(false);
                }
            };

            xhr.onerror = () => {
                setError("Upload failed due to network error.");
                setUploading(false);
            };

            xhr.send(formData);

        } catch (err) {
            setError("An error occurred: " + err.message);
            setUploading(false);
        }
    };

    return (
        <div className="p-6 bg-white rounded-lg shadow-md">
            <h2 className="text-xl font-bold mb-4">Upload Video</h2>
            <input
                type="file"
                accept="video/*"
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-500
          file:mr-4 file:py-2 file:px-4
          file:rounded-full file:border-0
          file:text-sm file:font-semibold
          file:bg-blue-50 file:text-blue-700
          hover:file:bg-blue-100
        "
            />

            {uploading && (
                <div className="mt-4">
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                            className="bg-blue-600 h-2.5 rounded-full"
                            style={{ width: `${progress}%` }}
                        ></div>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{Math.round(progress)}% Uploaded</p>
                </div>
            )}

            {error && (
                <p className="text-red-500 mt-2 text-sm">{error}</p>
            )}

            <button
                onClick={handleUpload}
                disabled={uploading || !file}
                className={`mt-4 px-4 py-2 rounded text-white font-bold ${uploading || !file ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-500 hover:bg-blue-700'
                    }`}
            >
                {uploading ? 'Uploading...' : 'Start Processing'}
            </button>
        </div>
    );
};

export default FileUploader;
