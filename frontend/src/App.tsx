// frontend/src/App.tsx
import React, { useState } from 'react';
import { uploadConfig, runGenerator } from './api';
import type { GeneratedSchedule } from './api';

/** Render configuration upload, schedule generation, and their results. */
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
      <h1>Scheduler Control Dashboard</h1>

      {/* Upload Section */}
      <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
        <h2>1. Upload Configuration JSON</h2>
        <input type="file" accept=".json" onChange={handleFileChange} />
        <button onClick={handleUpload} disabled={!file || loading} style={{ marginLeft: '10px' }}>
          Upload Config
        </button>
      </div>

      {/* Generator Section */}
      <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
        <h2>2. Run Scheduler Engine</h2>
        <button onClick={handleGenerate} disabled={loading}>
          {loading ? 'Processing...' : 'Generate Schedules'}
        </button>
      </div>

      {/* Status & Diagnostics */}
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

      {/* Results Rendering */}
      {schedules.length > 0 && (
        <div>
          <h2>Generated Output ({schedules.length})</h2>
          {schedules.map((sched) => (
            <div key={sched.schedule_id} style={{ border: '1px solid #eee', margin: '10px 0', padding: '10px' }}>
              <h3>Schedule #{sched.schedule_id}</h3>
              <ul>
                {sched.courses.map((courseCsv, idx) => (
                  <li key={idx}><code>{courseCsv}</code></li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;