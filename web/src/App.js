import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ViewEpub from './ViewEpub'; 

function App() {
  const [file, setFile] = useState(null);
  const [model, setModel] = useState('openai');
  const [selectedModel, setSelectedModel] = useState('gpt-4o');
  const [language, setLanguage] = useState('en');
  const [apiKey, setApiKey] = useState('');
  const [message, setMessage] = useState('');
  const [singleTranslate, setSingleTranslate] = useState("True");
  const [textOnly, setTextOnly] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [translatedFilePath, setTranslatedFilePath] = useState("");

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model', model);
    formData.append('selectedModel', selectedModel);
    formData.append('apiKey', apiKey);
    formData.append('language', language);
    formData.append('single_translate', singleTranslate);
    formData.append('textOnly', textOnly);

    try {
      const response = await fetch('http://localhost:5001/api/process', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setMessage(data.message);
        setTranslatedFilePath(data.translated_file_path.replace('temp_uploads/', '')); 
        setIsSuccess(true);        
      } else {
        setMessage('Error: Could not process request');
        setIsSuccess(false);
      }
    } catch (error) {
      console.error('Error:', error);
      setMessage('Error: Could not process request');
      setIsSuccess(false);
    }
  };

  return (
    <Router>
      <div className="App">
        <h1>AI Model Processor</h1>
        <form onSubmit={handleSubmit}>
          <div>
            <label htmlFor="file">Select File: </label>
            <input type="file" id="file" onChange={handleFileChange} />
          </div>
          <div>
            <label htmlFor="model">Model: </label>
            <input 
              type="text" 
              id="model" 
              value={model} 
              onChange={(e) => setModel(e.target.value)} 
            />
          </div>
          <div>
            <label htmlFor="modelList">Model List: </label>
            <select 
              id="modelList" 
              value={selectedModel} 
              onChange={(e) => setSelectedModel(e.target.value)}
            >
              <option value="gpt-4o-mini">gpt-4o-mini</option>
            </select>
          </div>
          <div>
            <label htmlFor="language">Target Language: </label>
            <select
              id="language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="en">English</option>
              <option value="zh">Chinese</option>
              <option value="ja">Japanese</option>
              <option value="vi">Vietnamese</option>
            </select>
          </div>
          <div>
            <label htmlFor="single_translate">Bilingual: </label>
            <select
              id="single_translate"
              value={singleTranslate}
              onChange={(e) => setSingleTranslate(e.target.value)}
            >
              <option value="True">No</option>
              <option value="False">Yes</option>
            </select>
          </div>
          <div>
            <label htmlFor="apiKey">API Key: </label>
            <input 
              type="text" 
              id="apiKey" 
              value={apiKey} 
              onChange={(e) => setApiKey(e.target.value)} 
            />
          </div>
          <div>
            <label htmlFor="textOnly">Translate Text Only: </label>
            <select
              id="textOnly"
              value={textOnly}
              onChange={(e) => setTextOnly(e.target.value)}
            >
              <option value="false">No</option>
              <option value="true">Yes</option>
            </select>
          </div>
          <button type="submit">Start</button>
        </form>
        {message && <p>{message}</p>}
        
        {isSuccess && (
          <Link to="/view-epub">
            <button>View Translated EPUB</button>
          </Link>
        )}
      </div>
      <Routes>
        <Route 
          path="/view-epub" 
          element={<ViewEpub translatedFilePath={translatedFilePath} />} 
        />
      </Routes>
    </Router>
  );
}

export default App;
