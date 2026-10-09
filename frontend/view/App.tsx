// frontend/view/App.tsx
import React, { useState } from 'react';
import { runGenerator, uploadConfig } from './api';
import type { GeneratedSchedule } from './api';

export function App() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>('');
  const [errors, setErrors] = useState<string[]>([]);
  const [schedules, setSchedules] = useState<GeneratedSchedule[]>([]);
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
    setSchedules([]);
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

  const handleGenerate = async () => {
    setLoading(true);
    setErrors([]);
    setStatus('Generating schedules...');

    try {
      const res = await runGenerator();
      setSchedules(res.schedules || []);
      setStatus(`Generated ${res.count} schedule(s) successfully!`);
    } catch (err: any) {
      setStatus('Schedule generation failed.');
      setErrors([err.response?.data?.detail || err.message]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '40px auto', fontFamily: 'sans-serif', padding: '0 20px' }}>
      <h1>Configuration Editor</h1>

      <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
        <h2>Load Config</h2>
        <input type="file" accept=".json" onChange={handleFileChange} />
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
      {schedules.length > 0 && (
        <div>
          <h2>Generated Output ({schedules.length})</h2>
          {schedules.map((schedule) => (
            <div key={schedule.schedule_id} style={{ border: '1px solid #eee', margin: '10px 0', padding: '10px' }}>
              <h3>Schedule #{schedule.schedule_id}</h3>
              <ul>
                {schedule.courses.map((course, index) => (
                  <li key={index}><code>{course}</code></li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
      <button
        onClick={handleGenerate}
        disabled={loading}
        style={{ marginTop: '24px', padding: '10px 16px' }}
      >
        {loading ? 'Processing...' : 'Generate Schedule'}
      </button>
    </div>
  );
}

export default App;