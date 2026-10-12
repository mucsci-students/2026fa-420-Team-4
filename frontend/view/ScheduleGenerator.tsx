import { useRef, useState } from "react";
import axios from "axios";
import {
  getGeneratorProgress,
  runGenerator,
  uploadConfig,
  type ScheduleExportFormat,
} from "./api";
import {
  createGenerationSettingsController,
  DEFAULT_GENERATION_LIMIT,
} from "./front_controllers/generationSettingsController";
import { formatConfigErrors } from "./configErrorMessages";
import { exportScheduleFile } from "./front_controllers/scheduleExportController";
import RetroConfirmDialog from "./RetroConfirmDialog";

const optimizerFlagOptions = [
  { value: "faculty_course", label: "Faculty → Course Preference" },
  { value: "faculty_room", label: "Faculty → Room Preference" },
  { value: "faculty_lab", label: "Faculty → Lab Preference" },
  { value: "same_room", label: "Same Room" },
  { value: "same_lab", label: "Same Lab" },
  { value: "pack_rooms", label: "Pack Rooms" },
  { value: "pack_labs", label: "Pack Labs" },
];

/** Render configuration loading, generation settings, and schedule export controls. */
export default function ScheduleGenerator({
  onStatusChange,
}: {
  onStatusChange: (message: string) => void;
}) {
  const generationConfigInput = useRef<HTMLInputElement>(null);
  const [generationLimit, setGenerationLimit] = useState(
    DEFAULT_GENERATION_LIMIT,
  );
  const [generationLimitInput, setGenerationLimitInput] = useState(
    String(DEFAULT_GENERATION_LIMIT),
  );
  const [generationLimitError, setGenerationLimitError] = useState("");
  const [confirmClearSchedules, setConfirmClearSchedules] = useState(false);
  const [optimizerFlags, setOptimizerFlags] = useState<string[]>([]);
  const [generatedScheduleCount, setGeneratedScheduleCount] = useState(0);
  const [generationStatus, setGenerationStatus] = useState(
    "Ready to generate a schedule.",
  );
  const [generationError, setGenerationError] = useState("");
  const [generatingSchedules, setGeneratingSchedules] = useState(false);
  const [exportingSchedule, setExportingSchedule] = useState(false);
  const [exportFormat, setExportFormat] =
    useState<ScheduleExportFormat>("json");
  const [configFile, setConfigFile] = useState<File | null>(null);
  const [configLoading, setConfigLoading] = useState(false);
  const [configStatus, setConfigStatus] = useState("");
  const [configErrors, setConfigErrors] = useState<string[]>([]);
  const [generationSettingsController] = useState(
    createGenerationSettingsController,
  );
  const genProgress = generationLimit > 0
    ? Math.min(100, (generatedScheduleCount / generationLimit) * 100)
    : 0;

  const toggleOptimizerFlag = (flag: string) => {
    const updatedFlags = optimizerFlags.includes(flag)
      ? optimizerFlags.filter((currentFlag) => currentFlag !== flag)
      : [...optimizerFlags, flag];
    setOptimizerFlags(updatedFlags);
    if (configFile) {
      generationSettingsController.setOptimizerFlags(updatedFlags);
    }
  };

  /** Load the selected configuration into the controller and backend, reporting any errors. */
  const handleGenerationConfigSelected = async (file: File | undefined) => {
    if (!file) return;
    setConfigLoading(true);
    setGenerationLimitError("");
    setConfigErrors([]);
    setConfigStatus("Reading and loading configuration...");
    onStatusChange("Reading and loading configuration...");
    try {
      const settings = await generationSettingsController.open(file);
      await uploadConfig(generationSettingsController.toFile());
      setConfigFile(file);
      setGenerationLimit(settings.limit);
      setGenerationLimitInput(String(settings.limit));
      setOptimizerFlags(settings.optimizer_flags);
      setConfigStatus(`${file.name} loaded successfully.`);
      onStatusChange(`${file.name} loaded successfully.`);
    } catch (error) {
      generationSettingsController.clear();
      setConfigFile(null);
      setConfigStatus("Could not load configuration.");
      onStatusChange("Could not load configuration.");
      if (
        axios.isAxiosError<{
          detail?: { errors?: string[] } | string;
        }>(error)
      ) {
        const detail = error.response?.data?.detail;
        setConfigErrors(formatConfigErrors(
          typeof detail === "string"
            ? [detail]
            : detail?.errors ?? [error.message],
        ));
      } else {
        setConfigErrors(formatConfigErrors([
          error instanceof Error ? error.message : "Invalid JSON configuration.",
        ]));
      }
    } finally {
      setConfigLoading(false);
    }
  };

  /** Generate with the current overrides while polling for schedule-count progress. */
  const generateSchedules = async () => {
    setGeneratingSchedules(true);
    setGenerationError("");
    setGenerationStatus("Generating schedules...");
    onStatusChange("Generating schedules...");
    let finished = false;

    try {
      if (configFile && generationLimit > 0) {
        await uploadConfig(generationSettingsController.toFile());
      }
      const generationPromise = runGenerator(generationLimit);
      generationPromise.then(
        () => { finished = true; },
        () => { finished = true; },
      );

      while (!finished) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        if (finished) break;

        const progress = await getGeneratorProgress();
        const message = `Generated ${progress.count} schedule(s) so far...`;
        setGeneratedScheduleCount(progress.count);
        setGenerationStatus(message);
        onStatusChange(message);
      }

      const result = await generationPromise;
      setGeneratedScheduleCount(result.count);
      const message = generationLimit === 0
        ? "Schedules cleared."
        : `Generated ${result.count} schedule(s).`;
      setGenerationStatus(message);
      onStatusChange(message);
    } catch (error) {
      setGeneratedScheduleCount(0);
      const message = error instanceof Error
        ? `Schedule generation failed: ${error.message}`
        : "Schedule generation failed.";
      setGenerationStatus("Schedule generation failed.");
      setGenerationError(message);
      onStatusChange(message);
    } finally {
      setGeneratingSchedules(false);
    }
  };

  const handleGenerateSchedule = () => {
    if (configLoading || configFile === null || generationLimitError !== "") return;
    if (generationLimit === 0) {
      setConfirmClearSchedules(true);
      return;
    }
    void generateSchedules();
  };

  /** Download generated schedules in the selected format and report progress or errors. */
  const handleExportSchedule = async () => {
    setExportingSchedule(true);
    setGenerationError("");
    onStatusChange("Exporting schedules...");
    try {
      await exportScheduleFile(exportFormat);
      onStatusChange(
        `Schedule export downloaded as ${exportFormat.toUpperCase()}.`,
      );
    } catch (error) {
      const message = error instanceof Error
        ? `Could not export schedules: ${error.message}`
        : "Could not export schedules.";
      setGenerationError(message);
      onStatusChange(message);
    } finally {
      setExportingSchedule(false);
    }
  };

  return (
    <section
      style={{
        minHeight: "100%",
        background: "white",
        border: "1px solid #cbd5e1",
        borderRadius: 8,
        padding: 24,
        boxSizing: "border-box",
      }}
    >
      <h1 style={{ marginTop: 0, fontSize: 28 }}>Schedule Generator</h1>
      <div
        style={{
          marginBottom: 20,
          padding: 16,
          border: "1px solid #cbd5e1",
          borderRadius: 8,
          background: "#f8fafc",
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: 12, fontSize: 18 }}>
          Load Config to Generate Schedules
        </h2>
        <input
          ref={generationConfigInput}
          type="file"
          accept=".json,application/json"
          disabled={configLoading || generatingSchedules}
          onChange={(event) => {
            void handleGenerationConfigSelected(event.target.files?.[0]);
            event.currentTarget.value = "";
          }}
          style={{ display: "none" }}
        />
        <button
          type="button"
          onClick={() => generationConfigInput.current?.click()}
          disabled={configLoading || generatingSchedules}
        >
          {configLoading ? "Loading..." : "Choose File"}
        </button>
        {configStatus && (
          <p role="status" style={{ marginTop: 8 }}>
            {configStatus}
          </p>
        )}
        {configErrors.length > 0 && (
          <div
            className="retro-validation-errors"
            role="alert"
            style={{
              marginTop: 10,
              padding: "10px 14px",
              color: "#991b1b",
              background: "#fef2f2",
              border: "1px solid #fecaca",
              borderRadius: 6,
            }}
          >
            <strong>Please fix these configuration issues:</strong>
            <ul style={{ margin: "8px 0 0", paddingLeft: 20 }}>
              {configErrors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div
        style={{
          padding: 20,
          border: "1px solid #cbd5e1",
          borderRadius: 8,
          background: "#f8fafc",
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: 16, fontSize: 18 }}>
          Generation Limit
        </h2>
        <label
          htmlFor="generation-limit"
          style={{
            display: "block",
            marginBottom: 8,
            fontSize: 14,
            fontWeight: "bold",
          }}
        >
          Maximum schedules to generate
        </label>
        <input
          id="generation-limit"
          disabled={configFile === null || generatingSchedules}
          type="number"
          min={0}
          step={1}
          value={generationLimitInput}
          aria-invalid={generationLimitError !== ""}
          aria-describedby={
            generationLimitError ? "generation-limit-error" : undefined
          }
          onChange={(event) => {
            const input = event.target.value;
            setGenerationLimitInput(input);
            if (!/^\d+$/.test(input)) {
              setGenerationLimitError(
                "Enter a non-negative whole number of schedules.",
              );
              return;
            }
            const value = Number(input);
            if (!Number.isSafeInteger(value)) {
              setGenerationLimitError(
                "Enter a whole number within the supported range.",
              );
              return;
            }
            setGenerationLimitError("");
            setGenerationLimit(value);
            if (configFile) {
              generationSettingsController.setLimit(value);
            }
          }}
          style={{
            width: 200,
            padding: "8px 10px",
            border: "1px solid #94a3b8",
            borderRadius: 6,
            fontSize: 14,
            boxSizing: "border-box",
          }}
        />
        <p style={{ marginBottom: 0, color: "#64748b", fontSize: 12 }}>
          Number of schedules the generator should produce. Enter 0 to clear
          generated schedules without generating any.
        </p>
        {generationLimitError && (
          <p
            id="generation-limit-error"
            role="alert"
            style={{ marginBottom: 0, color: "#b91c1c" }}
          >
            {generationLimitError}
          </p>
        )}
      </div>

      <div
        style={{
          marginTop: 20,
          padding: 20,
          border: "1px solid #cbd5e1",
          borderRadius: 8,
          background: "#f8fafc",
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: 18 }}>
          Optimizer Flags
        </h2>
        <p
          style={{
            marginTop: 0,
            marginBottom: 18,
            color: "#64748b",
            fontSize: 13,
          }}
        >
          Select optimization preferences for schedule generation.
        </p>
        {optimizerFlagOptions.map((option) => (
          <label
            key={option.value}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              marginBottom: 12,
              cursor: "pointer",
              fontSize: 14,
            }}
          >
            <input
              type="checkbox"
              disabled={configFile === null || generatingSchedules}
              checked={optimizerFlags.includes(option.value)}
              onChange={() => toggleOptimizerFlag(option.value)}
            />
            {option.label}
          </label>
        ))}
      </div>

      <button
        type="button"
        onClick={() => void handleGenerateSchedule()}
        disabled={
          generatingSchedules ||
          configLoading ||
          configFile === null ||
          generationLimitError !== ""
        }
        style={{
          marginTop: 24,
          padding: "11px 20px",
          border: 0,
          borderRadius: 6,
          background: "#334155",
          color: "#f8fafc",
          fontSize: 14,
          fontWeight: "bold",
          cursor: generatingSchedules ? "not-allowed" : "pointer",
        }}
      >
        {generatingSchedules ? "Generating..." : "Generate Schedules"}
      </button>

      <div
        style={{
          marginTop: 24,
          padding: 20,
          border: "1px solid #cbd5e1",
          borderRadius: 8,
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: 18 }}>
          Generation Status
        </h2>
        {generatingSchedules && (
          <progress
            aria-label="Generating schedules"
            max={100}
            value={genProgress}
            style={{
              display: "block",
              width: "100%",
              height: 12,
              marginBottom: 12,
            }}
          />
        )}
        <p style={{ margin: 0, color: "#64748b" }}>{generationStatus}</p>
        {generationError && (
          <p role="alert" style={{ marginBottom: 0, color: "#b91c1c" }}>
            {generationError}
          </p>
        )}
      </div>

      <label
        htmlFor="schedule-export-format"
        style={{ display: "inline-block", marginTop: 20, marginRight: 8 }}
      >
        Export format
      </label>
      <select
        id="schedule-export-format"
        value={exportFormat}
        onChange={(event) =>
          setExportFormat(event.target.value as ScheduleExportFormat)
        }
        disabled={generatedScheduleCount === 0 || exportingSchedule}
        style={{
          padding: "9px 10px",
          border: "1px solid #94a3b8",
          borderRadius: 6,
          fontSize: 14,
        }}
      >
        <option value="json">JSON</option>
        <option value="csv">CSV</option>
      </select>
      <button
        type="button"
        onClick={() => void handleExportSchedule()}
        disabled={
          generatedScheduleCount === 0 ||
          exportingSchedule ||
          generatingSchedules
        }
        style={{
          marginTop: 20,
          marginLeft: 8,
          padding: "11px 20px",
          border: 0,
          borderRadius: 6,
          background: "#334155",
          color: "#f8fafc",
          fontSize: 14,
          fontWeight: "bold",
          cursor:
            generatedScheduleCount > 0 &&
              !exportingSchedule &&
              !generatingSchedules
              ? "pointer"
              : "not-allowed",
        }}
      >
        {exportingSchedule ? "Exporting..." : "Export Generated Schedules"}
      </button>
      {confirmClearSchedules && (
        <RetroConfirmDialog
          title="Clear Available Schedules"
          message="A generation limit of 0 clears all available schedules. Continue?"
          confirmLabel="Clear Schedules"
          onCancel={() => setConfirmClearSchedules(false)}
          onConfirm={() => {
            setConfirmClearSchedules(false);
            void generateSchedules();
          }}
        />
      )}
    </section>
  );
}
