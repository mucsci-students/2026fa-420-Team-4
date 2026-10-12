// frontend/view/App.tsx
import { useRef, useState } from 'react';
import axios from 'axios';
import type { OpenedConfigFile } from './front_controllers/configFileController';
import type { ConfigDraft } from './front_controllers/configDraftController';
import { formatConfigErrors } from './configErrorMessages';
import RetroConfirmDialog from './RetroConfirmDialog';

interface AppProps {
  onConfigSelected: (config: unknown) => void;
  onChooseFile: (file: File) => Promise<OpenedConfigFile>;
  onCreateNew: () => void;
<<<<<<< HEAD
  recoverableDrafts: ConfigDraft[];
  onRestoreDraft: (draft: ConfigDraft) => void;
=======
  hasUnsavedChanges: boolean;
>>>>>>> develop
  onStatusChange: (message: string) => void;
}

/** Render configuration creation and file loading controls with status and error feedback. */
export function App({
  onConfigSelected,
  onChooseFile,
  onCreateNew,
<<<<<<< HEAD
  recoverableDrafts,
  onRestoreDraft,
=======
  hasUnsavedChanges,
>>>>>>> develop
  onStatusChange,
}: AppProps) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<string>('');
  const [errors, setErrors] = useState<string[]>([]);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [confirmCreate, setConfirmCreate] = useState(false);

  /** Open a selected configuration and report loading results; ignore an empty selection. */
  const openConfigFile = async (selectedFile: File) => {
    setErrors([]);
    setStatus('Loading configuration file...');
    onStatusChange('Loading configuration file...');

    try {
      const selected = await onChooseFile(selectedFile);
      onConfigSelected(selected.config);
      setStatus(
        `Loaded ${selected.file.name} into the editor. "Save Changes" will download the edited configuration with the same filename.`,
      );
      onStatusChange(`${selected.file.name} loaded successfully.`);
    } catch (error) {
      setStatus('Could not open configuration file.');
      onStatusChange('Could not open configuration file.');
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

  const handleChooseFile = (selectedFile: File | undefined) => {
    if (!selectedFile) return;
    if (hasUnsavedChanges) {
      setPendingFile(selectedFile);
      return;
    }
    void openConfigFile(selectedFile);
  };

  const createNewConfig = () => {
    onCreateNew();
    setStatus('Success: New configuration created. Save Changes downloads it as new-config.json.');
    onStatusChange('New configuration created.');
    setErrors([]);
  };

  return (
    <div className="config-start-screen">
      <h1>Configuration Editor</h1>

      <div className="config-start-card">
        <h2>Create New Config or Load Existing</h2>
        <div className="config-start-actions">
          <button
            type="button"
            onClick={() => {
              if (hasUnsavedChanges) {
                setConfirmCreate(true);
              } else {
                createNewConfig();
              }
            }}
          >
            Create New Config
          </button>
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
          {recoverableDrafts.map((draft) => (
            <button
              key={draft.id}
              type="button"
              onClick={() => {
                onRestoreDraft(draft);
                setStatus(`Restored unsaved changes to ${draft.fileName}.`);
                onStatusChange(`Restored unsaved changes to ${draft.fileName}.`);
                setErrors([]);
              }}
            >
              Restore {draft.fileName}
            </button>
          ))}
        </div>
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
        <div className="retro-validation-errors" role="alert" style={{ background: '#fef2f2', color: '#991b1b', padding: '12px 16px', border: '1px solid #fecaca', borderRadius: '6px' }}>
          <h4 style={{ margin: '0 0 8px' }}>Please fix these configuration issues:</h4>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {errors.map((err, idx) => (
              <li key={idx}>{err}</li>
            ))}
          </ul>
        </div>
      )}
      {pendingFile && (
        <RetroConfirmDialog
          title="Discard Unsaved Changes"
          message="Discard unsaved configuration changes and load another file?"
          confirmLabel="Discard and Load"
          onCancel={() => setPendingFile(null)}
          onConfirm={() => {
            const fileToLoad = pendingFile;
            setPendingFile(null);
            void openConfigFile(fileToLoad);
          }}
        />
      )}
      {confirmCreate && (
        <RetroConfirmDialog
          title="Discard Unsaved Changes"
          message="Discard unsaved configuration changes and create a new configuration?"
          confirmLabel="Discard and Create"
          onCancel={() => setConfirmCreate(false)}
          onConfirm={() => {
            setConfirmCreate(false);
            createNewConfig();
          }}
        />
      )}
    </div>
  );
}

export default App;