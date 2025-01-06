import React, { useState, useEffect } from 'react';

function App() {
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch('http://localhost:5001/api/hello')
      .then(response => response.json())
      .then(data => setMessage(data.message))
      .catch(error => {
        console.error('Error fetching data:', error);
        setMessage('Error: Could not fetch message');
      });
  }, []);

  return (
    <div className="App">
      <h1>Message from Flask API</h1>
      {message ? <p>{message}</p> : <p>Loading...</p>}
    </div>
  );
}

export default App;