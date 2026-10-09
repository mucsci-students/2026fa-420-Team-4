// frontend/view/App.tsx
import React, { useState } from 'react';
import { uploadConfig } from './api';

export function App() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>('');
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
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
    <div style={{ maxWidth: '800px', margin: '40px auto', fontFamily: '"MS Sans Serif", "Segoe UI", sans-serif', padding: '0 20px', color: '#000' }}>
      <h1 style={{ marginBottom: '16px', fontSize: '28px' }}>Configuration Editor</h1>

      <div style={{ border: '2px solid', borderColor: '#fff #808080 #808080 #fff', background: '#d4d0c8', padding: '20px', marginBottom: '20px', boxShadow: 'inset 1px 1px #fff, inset -1px -1px #808080' }}>
        <h2 style={{ marginTop: 0, marginBottom: '12px' }}>Create New Config or Load Existing</h2>
        <div style={{ marginBottom: '10px' }}>
          <button
            type="button"
            onClick={() => {
              setFile(null);
              setStatus('New blank configuration started.');
              setErrors([]);
            }}
            style={{
              background: '#d4d0c8',
              border: '2px solid',
              borderColor: '#fff #808080 #808080 #fff',
              padding: '6px 12px',
              fontFamily: '"MS Sans Serif", "Segoe UI", sans-serif',
              cursor: 'pointer',
            }}
          >
            Create New Config
          </button>
        </div>
        <input type="file" accept=".json" onChange={handleFileChange} style={{ marginRight: '10px', background: '#fff', border: '1px solid #000' }} />
        <button onClick={handleUpload} disabled={!file || loading} style={{
          background: '#d4d0c8',
          border: '2px solid',
          borderColor: '#fff #808080 #808080 #fff',
          padding: '6px 12px',
          marginLeft: '10px',
          fontFamily: '"MS Sans Serif", "Segoe UI", sans-serif',
          cursor: !file || loading ? 'not-allowed' : 'pointer',
        }}>
          {loading ? 'Loading...' : 'Load Config'}
        </button>
      </div>

      {status && <p style={{ marginTop: '12px', fontWeight: 700 }}><strong>Status:</strong> {status}</p>}
      {errors.length > 0 && (
        <div style={{ background: '#f4f4f4', color: '#900', padding: '10px', border: '2px solid', borderColor: '#fff #808080 #808080 #fff' }}>
          <h4 style={{ marginTop: 0 }}>Diagnostics / Errors:</h4>
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