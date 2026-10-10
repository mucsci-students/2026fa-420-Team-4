// frontend/view/App.tsx
import { useRef, useState } from 'react';
import { uploadConfig } from './api';
import type { OpenedConfigFile } from './configFileController';

interface AppProps {
  onConfigSelected: (config: unknown) => void;
  onChooseFile: (file: File) => Promise<OpenedConfigFile>;
  onCreateNew: () => void;
}

export function App({
  onConfigSelected,
  onChooseFile,
  onCreateNew,
}: AppProps) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>('');
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const handleChooseFile = async (selectedFile: File | undefined) => {
    if (!selectedFile) return;
    setErrors([]);
    setStatus('Loading configuration file...');

    try {
      const selected = await onChooseFile(selectedFile);
      setFile(selected.file);
      onConfigSelected(selected.config);
      setStatus(
        `Loaded ${selected.file.name} into the editor. Save Changes downloads the edited configuration with the same filename.`,
      );
    } catch (error) {
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
              setStatus('Success: New configuration created. Save Changes downloads it as new-config.json.');
              setErrors([]);
            }}
          >
            Create New Config
          </button>
        </div>
        <input
          ref={fileInput}
          type="file"
          accept=".json,application/json"
          onChange={(event) => {
            void handleChooseFile(event.target.files?.[0]);
            event.currentTarget.value = '';
          }}
          style={{ display: 'none' }}
        />
        <button type="button" onClick={() => fileInput.current?.click()}>
          Choose File
        </button>
        <button onClick={handleUpload} disabled={!file || loading} style={{ marginLeft: '10px' }}>
          {loading ? 'Loading...' : 'Load Config'}
        </button>
      </div>

      {status && (
        <p
          role="status"
          style={{
            color: status.startsWith('Success:') ? '#166534' : undefined,
            background: status.startsWith('Success:') ? '#dcfce7' : undefined,
            padding: status.startsWith('Success:') ? '10px' : undefined,
            borderRadius: status.startsWith('Success:') ? '4px' : undefined,
          }}
        >
          <strong>Status:</strong> {status}
        </p>
      )}
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