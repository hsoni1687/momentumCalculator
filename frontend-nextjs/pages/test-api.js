import { useState, useEffect } from 'react';

export default function TestAPI() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const testAPI = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      console.log('Testing API call...');
      console.log('API Base URL:', process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:80');
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:80'}/health`);
      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Response data:', data);
      setResult(data);
    } catch (err) {
      console.error('API call failed:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    testAPI();
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>API Test Page</h1>
      <p><strong>API Base URL:</strong> {process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:80'}</p>
      
      <button onClick={testAPI} disabled={loading} style={{ margin: '10px 0', padding: '10px' }}>
        {loading ? 'Testing...' : 'Test API'}
      </button>

      {error && (
        <div style={{ color: 'red', margin: '10px 0', padding: '10px', border: '1px solid red' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={{ color: 'green', margin: '10px 0', padding: '10px', border: '1px solid green' }}>
          <strong>Success:</strong>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}

      <div style={{ margin: '20px 0' }}>
        <h3>Environment Variables:</h3>
        <pre>{JSON.stringify({
          NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL
        }, null, 2)}</pre>
      </div>
    </div>
  );
}
