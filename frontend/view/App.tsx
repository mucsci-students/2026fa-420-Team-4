// frontend/view/App.tsx
import { useRef, useState } from 'react';
import axios from 'axios';
import type { OpenedConfigFile } from './front_controllers/configFileController';
import { formatConfigErrors } from './configErrorMessages';

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
  const [status, setStatus] = useState<string>('');
  const [errors, setErrors] = useState<string[]>([]);

  const handleChooseFile = async (selectedFile: File | undefined) => {
    if (!selectedFile) return;
    setErrors([]);
    setStatus('Loading configuration file...');

    try {
      const selected = await onChooseFile(selectedFile);
      onConfigSelected(selected.config);
      setStatus(
        `Loaded ${selected.file.name} into the editor. "Save Changes" will download the edited configuration with the same filename.`,
      );
    } catch (error) {
      setStatus('Could not open configuration file.');
      if (
        axios.isAxiosError<{
          detail?: { errors?: string[] } | string;
        }>(error)
      ) {
        const detail = error.response?.data?.detail;
        setErrors(formatConfigErrors(
          typeof detail === 'string'
            ? [detail]
            : detail?.errors ?? [error.message],
        ));
      } else {
        setErrors(formatConfigErrors([
          error instanceof Error ? error.message : 'Invalid JSON file.',
        ]));
      }
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
        <div role="alert" style={{ background: '#fef2f2', color: '#991b1b', padding: '12px 16px', border: '1px solid #fecaca', borderRadius: '6px' }}>
          <h4 style={{ margin: '0 0 8px' }}>Please fix these configuration issues:</h4>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
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