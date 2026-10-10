// frontend/view/App.tsx
import { useState } from 'react';
import { uploadConfig } from './api';
import type { OpenedConfigFile } from './configFileController';

interface AppProps {
  onConfigSelected: (config: unknown) => void;
  onChooseFile: () => Promise<OpenedConfigFile | null>;
  onCreateNew: () => void;
}

export function App({ onConfigSelected, onChooseFile, onCreateNew }: AppProps) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>('');
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const handleChooseFile = async () => {
    setErrors([]);
    setStatus('Choose a configuration file...');

    try {
      const selected = await onChooseFile();
      if (!selected) return;
      setFile(selected.file);
      onConfigSelected(selected.config);
      setStatus(`Loaded ${selected.file.name} into the editor. Save Changes writes edits back to this file.`);
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return;
      setStatus('Could not open configuration file.');
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
              onCreateNew();
              setStatus('New blank configuration started.');
              setErrors([]);
            }}
          >
            Create New Config
          </button>
        </div>
        <button type="button" onClick={() => void handleChooseFile()}>
          Choose File
        </button>
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