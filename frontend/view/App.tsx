// frontend/view/App.tsx
import React, { useState } from 'react';
import { uploadConfig } from './api';

interface AppProps {
  onConfigSelected: (config: unknown) => void;
}

export function App({ onConfigSelected }: AppProps) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>('');
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setErrors([]);
    setStatus('Reading configuration...');

    try {
      const config: unknown = JSON.parse(await selectedFile.text());
      onConfigSelected(config);
      setStatus(`Loaded ${selectedFile.name} into the editor.`);
    } catch (error) {
      setStatus('Could not read configuration file.');
      setErrors([
        error instanceof Error ? error.message : 'Invalid JSON file.',
      ]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setErrors([]);
    setStatus('Uploading configuration...');

    try {
      const res = await uploadConfig(file);
      setStatus(res.message || 'Config loaded successfully!');
    } catch (err: any) {
      setStatus('Upload failed.');
      if (err.response?.data?.detail?.errors) {
        setErrors(err.response.data.detail.errors);
      } else {
        setErrors([err.response?.data?.detail || err.message]);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '40px auto', fontFamily: 'sans-serif', padding: '0 20px' }}>
      <h1>Configuration Editor</h1>

      <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
        <h2>Create New Config or Load Existing</h2>
        <div style={{ marginBottom: '10px' }}>
          <button
            type="button"
            onClick={() => {
              setFile(null);
              setStatus('New blank configuration started.');
              setErrors([]);
            }}
          >
            Create New Config
          </button>
        </div>
        <input type="file" accept=".json,application/json" onChange={handleFileChange} />
        <button onClick={handleUpload} disabled={!file || loading} style={{ marginLeft: '10px' }}>
          {loading ? 'Loading...' : 'Load Config'}
        </button>
      </div>

      {status && <p><strong>Status:</strong> {status}</p>}
      {errors.length > 0 && (
        <div style={{ background: '#ffe6e6', color: '#900', padding: '10px', borderRadius: '4px' }}>
          <h4>Diagnostics / Errors:</h4>
          <ul>
            {errors.map((err, idx) => (
              <li key={idx}>{err}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;