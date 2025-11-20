import React, { useState } from 'react';
import ScraperTab from './components/ScraperTab';
import SplitterTab from './components/SplitterTab';
import TranscriberTab from './components/TranscriberTab';

function App() {
  const [activeTab, setActiveTab] = useState('scraper');

  const tabs = [
    { id: 'scraper', label: '1. Scraper' },
    { id: 'splitter', label: '2. Splitter' },
    { id: 'transcriber', label: '3. Transcriber' },
  ];

  return (
    <div className="min-h-screen bg-black text-white font-sans selection:bg-blue-500 selection:text-white">
      {/* Header */}
      <header className="bg-black border-b border-gray-800 shadow-lg">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">
              TTS Dataset Creator
            </h1>
            <p className="mt-1 text-sm text-gray-400">
              Build Arabic Audio Datasets for TTS Training
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <a
              href="https://github.com/ezzhamed"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-white transition-colors"
              title="GitHub Profile"
            >
              <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
              </svg>
            </a>
            <div className="text-xs text-gray-500 bg-gray-900 px-3 py-1 rounded-full border border-gray-800">
              v1.0.0
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Navigation Tabs */}
        <div className="flex space-x-4 mb-8 overflow-x-auto pb-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                px-6 py-3 rounded-lg text-sm font-medium transition-all duration-200 ease-in-out
                ${activeTab === tab.id
                  ? 'bg-white text-black shadow-lg'
                  : 'bg-gray-900 text-gray-400 hover:bg-gray-800 hover:text-white border border-gray-800'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="bg-gray-900 rounded-xl shadow-2xl border border-gray-800 overflow-hidden min-h-[500px]">
          <div className="p-6 sm:p-8">
            {activeTab === 'scraper' && <ScraperTab />}
            {activeTab === 'splitter' && <SplitterTab />}
            {activeTab === 'transcriber' && <TranscriberTab />}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
