import { useEffect, useId, useRef } from "react";

interface RetroConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
}

/** Render an app-styled confirmation dialog and handle keyboard dismissal. */
export default function RetroConfirmDialog({
  title,
  message,
  confirmLabel,
  onConfirm,
  onCancel,
}: RetroConfirmDialogProps) {
  const cancelButton = useRef<HTMLButtonElement>(null);
  const dialogId = useId();

  useEffect(() => {
    cancelButton.current?.focus();
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onCancel]);

  return (
    <div className="retro-dialog-backdrop">
      <section
        aria-labelledby={`${dialogId}-title`}
        aria-describedby={`${dialogId}-message`}
        aria-modal="true"
        className="retro-dialog"
        role="alertdialog"
      >
        <header className="retro-dialog-titlebar">{title}</header>
        <div className="retro-dialog-content">
          <p id={`${dialogId}-message`}>{message}</p>
          <div className="retro-dialog-actions">
            <button
              ref={cancelButton}
              type="button"
              onClick={onCancel}
            >
              Cancel
            </button>
            <button type="button" onClick={onConfirm}>
              {confirmLabel}
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
