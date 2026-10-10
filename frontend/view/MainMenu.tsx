import { useState } from "react";
import App from "./App";
import { runGenerator, uploadConfig } from "./api";
import {
  applyConfigTableRows,
  asObject,
  configTableColumns,
  getConfigTableRows,
  type ConfigTableRow,
} from "./configEditorModel";
import {
  createConfigFileController,
  type OpenedConfigFile,
} from "./configFileController";
import { exportScheduleCsvFile } from "./scheduleExportController";
const configMenus = [
  "Rooms",
  "Labs",
  "Courses",
  "Faculty",
  "Timeslots",
  "Class Patterns",
];
function formatTableValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map(formatTableValue).filter(Boolean).join(", ");
  }
  if (value !== null && typeof value === "object") {
    return Object.entries(value)
      .map(([key, item]) => {
        const label = key.replaceAll("_", " ");
        const formattedValue = formatTableValue(item);
        return formattedValue ? `${label}: ${formattedValue}` : label;
      })
      .join("; ");
  }
  return value === null || value === undefined ? "" : String(value);
}

function formatCellDisplay(value: string | undefined): string {
  if (!value) return "";
  const trimmed = value.trim();
  if (trimmed.startsWith("[") || trimmed.startsWith("{")) {
    try {
      return formatTableValue(JSON.parse(trimmed));
    } catch {
      return value;
    }
  }
  return value;
}

function formatTimeBlocks(value: unknown): string {
  const days = asObject(value);
  return Object.entries(days)
    .map(([day, blocks]) => {
      const summaries = Array.isArray(blocks)
        ? blocks.map((blockValue) => {
            const block = asObject(blockValue);
            const range = `${String(block.start ?? "")}–${String(block.end ?? "")}`;
            return block.spacing
              ? `${range} (every ${String(block.spacing)} min)`
              : range;
          })
        : [];
      return `${day}: ${summaries.join(", ") || "unavailable"}`;
    })
    .join(" · ");
}

function formatMeetings(value: unknown): string {
  if (!Array.isArray(value)) return "";
  return value
    .map((meetingValue) => {
      const meeting = asObject(meetingValue);
      const start = meeting.start_time ? ` ${String(meeting.start_time)}` : "";
      const duration = meeting.duration
        ? `, ${String(meeting.duration)} min`
        : "";
      const lab = meeting.lab ? ", lab" : "";
      const delivery = meeting.delivery ? `, ${String(meeting.delivery)}` : "";
      return `${String(meeting.day ?? "")}${start}${duration}${lab}${delivery}`;
    })
    .join("; ");
}

function formatConfigCell(
  menu: string,
  column: string,
  value: string | undefined,
): string {
  if (!value) return "";
  if (menu === "Timeslots" && column === "Times") {
    try {
      return formatTimeBlocks(JSON.parse(value));
    } catch {
      return formatCellDisplay(value);
    }
  }
  if (
    menu === "Class Patterns" &&
    column === "Meetings"
  ) {
    try {
      return formatMeetings(JSON.parse(value));
    } catch {
      return formatCellDisplay(value);
    }
  }
  if (menu === "Class Patterns" && column === "Disabled") {
    return value === "true" ? "Disabled" : "Enabled";
  }
  return formatCellDisplay(value);
}

function parseEditorJson(value: string, fallback: unknown): unknown {
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

const editorDays = ["MON", "TUE", "WED", "THU", "FRI"];
const listFields: Record<string, string[]> = {
  Rooms: ["Features"],
  Labs: ["Features"],
  Courses: [
    "Room",
    "Lab",
    "Conflicts",
    "Faculty",
    "Alternate Faculty",
    "Required Room Features",
    "Required Lab Features",
  ],
};

const structuredEditorStyle = {
  display: "grid",
  gap: 12,
  width: "100%",
  minWidth: 280,
  maxHeight: "32vh",
  overflowY: "auto" as const,
  marginTop: 4,
  padding: 12,
  border: "1px solid #cbd5e1",
  borderRadius: 4,
  boxSizing: "border-box" as const,
  background: "#f8fafc",
};

function ConfigFieldEditor({
  menu,
  column,
  value,
  onChange,
  autoFocus = false,
}: {
  menu: string;
  column: string;
  value: string;
  onChange: (value: string) => void;
  autoFocus?: boolean;
}) {
  if (
    menu === "Faculty" &&
    ["Course Preferences", "Room Preferences", "Lab Preferences"].includes(column)
  ) {
    const preferencesValue = parseEditorJson(value, {});
    const preferences = asObject(preferencesValue);
    const entries = Object.entries(preferences);
    const updateEntries = (nextEntries: Array<[string, unknown]>) => {
      onChange(JSON.stringify(Object.fromEntries(
        nextEntries.filter(([key]) => key.trim() !== ""),
      )));
    };

    return (
      <div style={{ ...structuredEditorStyle, maxHeight: "24vh" }}>
        {entries.map(([name, score], index) => (
          <div
            key={`${name}-${index}`}
            style={{ display: "flex", alignItems: "end", gap: 8 }}
          >
            <label style={{ flex: "1 1 180px", fontSize: 12 }}>
              {column.replace(" Preferences", "")}
              <input
                value={name}
                onChange={(event) => {
                  const nextEntries = [...entries] as Array<[string, unknown]>;
                  nextEntries[index] = [event.target.value, score];
                  updateEntries(nextEntries);
                }}
                style={{ display: "block", width: "100%", marginTop: 4, padding: 7, boxSizing: "border-box" }}
              />
            </label>
            <label style={{ flex: "0 1 110px", fontSize: 12 }}>
              Score (0–10)
              <input
                type="number"
                min={0}
                max={10}
                value={String(score)}
                onChange={(event) => {
                  const nextEntries = [...entries] as Array<[string, unknown]>;
                  nextEntries[index] = [name, event.target.value === "" ? "" : Number(event.target.value)];
                  updateEntries(nextEntries);
                }}
                style={{ display: "block", width: "100%", marginTop: 4, padding: 7, boxSizing: "border-box" }}
              />
            </label>
            <button
              type="button"
              onClick={() => updateEntries(entries.filter((_, entryIndex) => entryIndex !== index))}
              style={{ padding: 7, flexShrink: 0 }}
            >
              Remove
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={() => {
            let index = 1;
            let name = "new";
            while (Object.prototype.hasOwnProperty.call(preferences, name)) {
              index += 1;
              name = `new ${index}`;
            }
            updateEntries([...entries, [name, 0]]);
          }}
          style={{ justifySelf: "start", padding: "6px 9px" }}
        >
          + Add preference
        </button>
      </div>
    );
  }

  if (menu === "Faculty" && column === "Mandatory Days") {
    const selectedDaysValue = parseEditorJson(value, []);
    const selectedDays = Array.isArray(selectedDaysValue)
      ? selectedDaysValue.map(String)
      : [];
    return (
      <div
        role="group"
        aria-label="Mandatory Days"
        style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 8 }}
      >
        {editorDays.map((day) => (
          <label
            key={day}
            style={{ display: "inline-flex", alignItems: "center", gap: 4 }}
          >
            <input
              type="checkbox"
              checked={selectedDays.includes(day)}
              onChange={(event) => {
                const nextDays = event.target.checked
                  ? [...selectedDays, day]
                  : selectedDays.filter((selectedDay) => selectedDay !== day);
                onChange(JSON.stringify(nextDays));
              }}
            />
            {day}
          </label>
        ))}
      </div>
    );
  }

  if (listFields[menu]?.includes(column)) {
    const listValue = parseEditorJson(value, []);
    const textValue = Array.isArray(listValue)
      ? listValue.map(String).join(", ")
      : value;
    return (
      <input
        autoFocus={autoFocus}
        aria-label={column}
        type="text"
        placeholder="Separate values with commas"
        value={textValue}
        onChange={(event) =>
          onChange(JSON.stringify(
            event.target.value
              .split(",")
              .map((item) => item.trim())
              .filter(Boolean),
          ))
        }
        style={{
          display: "block",
          width: "100%",
          marginTop: 4,
          padding: 8,
          border: "1px solid #cbd5e1",
          borderRadius: 4,
          boxSizing: "border-box",
        }}
      />
    );
  }

  if (
    ["Rooms", "Labs", "Faculty"].includes(menu) &&
    column === "Times"
  ) {
    const times = asObject(parseEditorJson(value, {}));
    return (
      <div style={structuredEditorStyle}>
        {editorDays.map((day) => {
          const ranges = Array.isArray(times[day]) ? times[day] : [];
          return (
            <fieldset
              key={day}
              style={{ margin: 0, padding: 10, border: "1px solid #cbd5e1", borderRadius: 4 }}
            >
              <legend style={{ padding: "0 4px", fontWeight: "bold" }}>{day}</legend>
              {ranges.map((rangeValue, index) => {
                const range = asObject(rangeValue);
                return (
                  <div
                    key={`${day}-${index}`}
                    style={{ display: "flex", flexWrap: "wrap", alignItems: "end", gap: 8, marginBottom: 8 }}
                  >
                    {([
                      ["start", "Start"],
                      ["end", "End"],
                    ] as const).map(([key, label]) => (
                      <label key={key} style={{ flex: "1 1 120px", fontSize: 12 }}>
                        {label}
                        <input
                          autoFocus={autoFocus && day === editorDays[0] && index === 0 && key === "start"}
                          aria-label={`${day} ${label}`}
                          type="time"
                          value={String(range[key] ?? "")}
                          onChange={(event) => {
                            const updatedRanges = ranges.map((entry, rangeIndex) =>
                              rangeIndex === index
                                ? { ...asObject(entry), [key]: event.target.value }
                                : entry,
                            );
                            onChange(JSON.stringify({ ...times, [day]: updatedRanges }));
                          }}
                          style={{ display: "block", width: "100%", marginTop: 4, padding: 7, boxSizing: "border-box" }}
                        />
                      </label>
                    ))}
                    <button
                      type="button"
                      onClick={() => onChange(JSON.stringify({
                        ...times,
                        [day]: ranges.filter((_, rangeIndex) => rangeIndex !== index),
                      }))}
                      style={{ padding: 7, flexShrink: 0 }}
                    >
                      Remove
                    </button>
                  </div>
                );
              })}
              <button
                type="button"
                onClick={() => onChange(JSON.stringify({
                  ...times,
                  [day]: [...ranges, { start: "", end: "" }],
                }))}
                style={{ padding: "6px 9px" }}
              >
                + Add time range
              </button>
            </fieldset>
          );
        })}
      </div>
    );
  }

  if (menu === "Timeslots" && column === "Times") {
    const times = asObject(
      parseEditorJson(value, Object.fromEntries(editorDays.map((day) => [day, []]))),
    );
    return (
      <div style={structuredEditorStyle}>
        {editorDays.map((day) => {
          const blocks = Array.isArray(times[day]) ? times[day] : [];
          return (
            <fieldset
              key={day}
              style={{ margin: 0, padding: 10, border: "1px solid #cbd5e1", borderRadius: 4 }}
            >
              <legend style={{ padding: "0 4px", fontWeight: "bold" }}>{day}</legend>
              {blocks.map((blockValue, index) => {
                const block = asObject(blockValue);
                return (
                  <div
                    key={`${day}-${index}`}
                    style={{ display: "flex", flexWrap: "wrap", alignItems: "end", gap: 8, marginBottom: 8 }}
                  >
                    {([
                      ["start", "Start", "time"],
                      ["spacing", "Spacing (min)", "number"],
                      ["end", "End", "time"],
                    ] as const).map(([key, label, type]) => (
                      <label key={key} style={{ flex: "1 1 100px", fontSize: 12 }}>
                        {label}
                        <input
                          autoFocus={autoFocus && day === editorDays[0] && index === 0 && key === "start"}
                          aria-label={`${day} ${label}`}
                          type={type}
                          value={String(block[key] ?? "")}
                          onChange={(event) => {
                            const updatedBlocks = blocks.map((entry, blockIndex) =>
                              blockIndex === index
                                ? { ...asObject(entry), [key]: type === "number" ? Number(event.target.value) : event.target.value }
                                : entry,
                            );
                            onChange(JSON.stringify({ ...times, [day]: updatedBlocks }));
                          }}
                          style={{ display: "block", width: "100%", marginTop: 4, padding: 7, boxSizing: "border-box" }}
                        />
                      </label>
                    ))}
                    <button
                      type="button"
                      onClick={() => onChange(JSON.stringify({
                        ...times,
                        [day]: blocks.filter((_, blockIndex) => blockIndex !== index),
                      }))}
                      style={{ padding: 7, flexShrink: 0 }}
                    >
                      Remove
                    </button>
                  </div>
                );
              })}
              <button
                type="button"
                onClick={() => onChange(JSON.stringify({
                  ...times,
                  [day]: [...blocks, { start: "", spacing: 60, end: "" }],
                }))}
                style={{ padding: "6px 9px" }}
              >
                + Add time block
              </button>
            </fieldset>
          );
        })}
      </div>
    );
  }

  if (menu === "Class Patterns" && column === "Meetings") {
    const meetingsValue = parseEditorJson(value, []);
    const meetings = Array.isArray(meetingsValue) ? meetingsValue : [];
    return (
      <div style={structuredEditorStyle}>
        {meetings.map((meetingValue, index) => {
          const meeting = asObject(meetingValue);
          const updateMeeting = (key: string, nextValue: unknown) => {
            onChange(JSON.stringify(
              meetings.map((item, meetingIndex) =>
                meetingIndex === index
                  ? { ...asObject(item), [key]: nextValue }
                  : item,
              ),
            ));
          };
          return (
            <fieldset
              key={`meeting-${index}`}
              style={{ margin: 0, padding: 10, border: "1px solid #cbd5e1", borderRadius: 4 }}
            >
              <legend style={{ padding: "0 4px", fontWeight: "bold" }}>Meeting {index + 1}</legend>
              <div style={{ display: "flex", flexWrap: "wrap", alignItems: "end", gap: 8 }}>
                <label style={{ flex: "1 1 100px", fontSize: 12 }}>
                  Day
                  <select
                    value={String(meeting.day ?? "MON")}
                    onChange={(event) => updateMeeting("day", event.target.value)}
                    style={{ display: "block", width: "100%", marginTop: 4, padding: 7 }}
                  >
                    {editorDays.map((day) => <option key={day} value={day}>{day}</option>)}
                  </select>
                </label>
                <label style={{ flex: "1 1 125px", fontSize: 12 }}>
                  Start time
                  <input
                    type="time"
                    value={String(meeting.start_time ?? "")}
                    onChange={(event) => updateMeeting("start_time", event.target.value || null)}
                    style={{ display: "block", width: "100%", marginTop: 4, padding: 7, boxSizing: "border-box" }}
                  />
                </label>
                <label style={{ flex: "1 1 100px", fontSize: 12 }}>
                  Duration (min)
                  <input
                    type="number"
                    value={String(meeting.duration ?? "")}
                    onChange={(event) => updateMeeting("duration", Number(event.target.value))}
                    style={{ display: "block", width: "100%", marginTop: 4, padding: 7, boxSizing: "border-box" }}
                  />
                </label>
                <label style={{ display: "flex", alignItems: "center", gap: 6, minHeight: 34, fontSize: 12 }}>
                  <input
                    type="checkbox"
                    checked={meeting.lab === true}
                    onChange={(event) => updateMeeting("lab", event.target.checked)}
                  />
                  Lab meeting
                </label>
                <label style={{ flex: "1 1 120px", fontSize: 12 }}>
                  Delivery
                  <select
                    value={String(meeting.delivery ?? "in_person")}
                    onChange={(event) => updateMeeting("delivery", event.target.value)}
                    style={{ display: "block", width: "100%", marginTop: 4, padding: 7 }}
                  >
                    <option value="in_person">In person</option>
                    <option value="online">Online</option>
                  </select>
                </label>
                <button
                  type="button"
                  onClick={() => onChange(JSON.stringify(meetings.filter((_, meetingIndex) => meetingIndex !== index)))}
                  style={{ padding: 7, flexShrink: 0 }}
                >
                  Remove
                </button>
              </div>
            </fieldset>
          );
        })}
        <button
          type="button"
          onClick={() => onChange(JSON.stringify([
            ...meetings,
            { day: "MON", duration: 60, lab: false, delivery: "in_person", start_time: null },
          ]))}
          style={{ justifySelf: "start", padding: "6px 9px" }}
        >
          + Add meeting
        </button>
      </div>
    );
  }

  const isBooleanField =
    (menu === "Class Patterns" && column === "Disabled") ||
    (menu === "Courses" && column === "Reserve Room During Lab");
  if (isBooleanField) {
    return (
      <input
        autoFocus={autoFocus}
        aria-label={column}
        type="checkbox"
        checked={value === "true"}
        onChange={(event) => onChange(String(event.target.checked))}
        style={{ display: "block", marginTop: 8 }}
      />
    );
  }

  const isNumberField =
    (menu === "Timeslots" &&
      ["Max Time Gap", "Min Time Overlap"].includes(column)) ||
    (menu === "Class Patterns" && column === "Credits");
  const isTimeField =
    (menu === "Class Patterns" && column === "Start Time") ||
    (menu === "Timeslots" && column === "Start Time");
  return (
    <input
      autoFocus={autoFocus}
      aria-label={column}
      type={isNumberField ? "number" : isTimeField ? "time" : "text"}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      style={{
        display: "block",
        width: "100%",
        marginTop: 4,
        padding: 8,
        border: "1px solid #cbd5e1",
        borderRadius: 4,
        boxSizing: "border-box",
      }}
    />
  );
}

const optimizerFlagOptions = [
  { value: "faculty_course", label: "Faculty → Course Preference" },
  { value: "faculty_room", label: "Faculty → Room Preference" },
  { value: "faculty_lab", label: "Faculty → Lab Preference" },
  { value: "same_room", label: "Same Room" },
  { value: "same_lab", label: "Same Lab" },
  { value: "pack_rooms", label: "Pack Rooms" },
  { value: "pack_labs", label: "Pack Labs" },
];
/** Render navigation and panels for configuration, schedule generation, and viewing. */
export default function MainMenu() {
  const [activeMenu, setActiveMenu] = useState("Configuration Editor");
  const [configOpen, setConfigOpen] = useState(true);
  const [generationLimit, setGenerationLimit] = useState(10);
  const [optimizerFlags, setOptimizerFlags] = useState<string[]>([]);
  const [generatedScheduleCount, setGeneratedScheduleCount] = useState(0);
  const [generationStatus, setGenerationStatus] = useState("Ready to generate a schedule.");
  const [generationError, setGenerationError] = useState("");
  const [generatingSchedules, setGeneratingSchedules] = useState(false);
  const [exportingSchedule, setExportingSchedule] = useState(false);
  const [addWindowOpen, setAddWindowOpen] = useState(false);
  const [newRow, setNewRow] = useState<Record<string, string>>({});
  const [editingRowIndex, setEditingRowIndex] = useState<number | null>(null);
  const [editedRow, setEditedRow] = useState<Record<string, string>>({});
  // Keep rows separated by submenu so switching tables does not lose entered data.
  const [configRows, setConfigRows] = useState<
    Record<string, ConfigTableRow[]>
  >({});
  const [configFile, setConfigFile] = useState<File | null>(null);
  const [configLoading, setConfigLoading] = useState(false);
  const [configStatus, setConfigStatus] = useState("");
  const [configErrors, setConfigErrors] = useState<string[]>([]);
  const [originalEditorConfig, setOriginalEditorConfig] = useState<unknown>(null);
  const [editorFileName, setEditorFileName] = useState("");
  const [editorDirty, setEditorDirty] = useState(false);
  const [editorSaveStatus, setEditorSaveStatus] = useState("");
  const [editorSaving, setEditorSaving] = useState(false);
  const [editorFileController] = useState(createConfigFileController);
  const buttonStyle = (active: boolean) => ({
    width: "100%",
    padding: "10px 12px",
    border: 0,
    borderRadius: 6,
    background: active ? "#334155" : "transparent",
    color: "#f8fafc",
    textAlign: "left" as const,
    fontSize: 14,
    cursor: "pointer",
  });
  const toggleOptimizerFlag = (flag: string) => {
    setOptimizerFlags((current) =>
      current.includes(flag)
        ? current.filter((currentFlag) => currentFlag !== flag)
        : [...current, flag]
    );
  };
  const handleGenerateSchedule = async () => {
    setGeneratingSchedules(true);
    setGenerationError("");
    setGenerationStatus("Generating schedules...");
    try {
      const result = await runGenerator();
      setGeneratedScheduleCount(result.count);
      setGenerationStatus(`Generated ${result.count} schedule(s).`);
    } catch (error) {
      setGeneratedScheduleCount(0);
      setGenerationStatus("Schedule generation failed.");
      setGenerationError(
        error instanceof Error ? error.message : "Could not generate schedules.",
      );
    } finally {
      setGeneratingSchedules(false);
    }
  };
  const handleExportSchedule = async () => {
    setExportingSchedule(true);
    setGenerationError("");
    try {
      await exportScheduleCsvFile();
    } catch (error) {
      setGenerationError(
        error instanceof Error ? error.message : "Could not export schedules.",
      );
    } finally {
      setExportingSchedule(false);
    }
  };
  const handleConfigLoad = async () => {
    if (!configFile) return;

    setConfigLoading(true);
    setConfigErrors([]);
    setConfigStatus("Loading configuration...");
    try {
      const response = await uploadConfig(configFile);
      setConfigStatus(response.message || "Config loaded successfully!");
    } catch (error: any) {
      setConfigStatus("Config load failed.");
      setConfigErrors(
        error.response?.data?.detail?.errors ??
        [error.response?.data?.detail || error.message]
      );
    } finally {
      setConfigLoading(false);
    }
  };
  const handleEditorConfigSelected = (config: unknown) => {
    setOriginalEditorConfig(config);
    setConfigRows(getConfigTableRows(config));
    setEditorDirty(false);
    setEditorSaveStatus("");
    setEditingRowIndex(null);
    setEditedRow({});
    setAddWindowOpen(false);
    setNewRow({});
  };
  const handleChooseEditorFile = async (
    file: File,
  ): Promise<OpenedConfigFile> => {
    const selected = await editorFileController.open(file);
    setEditorFileName(selected.file.name);
    return selected;
  };
  const handleCreateNewConfig = () => {
    editorFileController.clear();
    setEditorFileName("");
    setOriginalEditorConfig(null);
    setConfigRows({});
    setEditorDirty(false);
    setEditorSaveStatus("");
    setEditingRowIndex(null);
    setEditedRow({});
    setAddWindowOpen(false);
    setNewRow({});
  };
  const handleSaveEditorConfig = async () => {
    if (originalEditorConfig === null || !editorFileName) {
      setEditorSaveStatus("Choose an existing configuration file before saving.");
      return;
    }

    setEditorSaving(true);
    setEditorSaveStatus("Saving changes...");
    try {
      const updatedConfig = applyConfigTableRows(originalEditorConfig, configRows);
      editorFileController.save(updatedConfig);
      setOriginalEditorConfig(updatedConfig);
      setEditorDirty(false);
      setEditorSaveStatus("");
    } catch (error) {
      setEditorSaveStatus(
        error instanceof Error ? error.message : "Could not save the configuration file.",
      );
    } finally {
      setEditorSaving(false);
    }
  };
  return (
    <div
      style={{
        height: "100vh",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        background: "#f1f5f9",
        color: "#0f172a",
        fontFamily: "Arial, sans-serif",
      }}
    >
      {" "}
      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        {" "}
        {/* Sidebar */}{" "}
        <nav
          aria-label="Main menu"
          style={{
            width: 210,
            flexShrink: 0,
            padding: 12,
            boxSizing: "border-box",
            background: "#1e293b",
            color: "#f8fafc",
            overflowY: "auto",
          }}
        >

          {/* Configuration Editor */}{" "}
          <button
            type="button"
            aria-expanded={configOpen}
            style={buttonStyle(activeMenu === "Configuration Editor")}
            onClick={() => {
              setActiveMenu("Configuration Editor");
              setConfigOpen((open) => !open);
            }}
          >
            {" "}
            <span style={{ display: "inline-block", width: 18 }}>
              {" "}
              {configOpen ? "▾" : "▸"}{" "}
            </span>{" "}
            Configuration Editor{" "}
          </button>{" "}
          {/* Configuration Editor Submenus */}{" "}
          {configOpen && (
            <div
              style={{
                margin: "2px 0 4px 18px",
                paddingLeft: 10,
                borderLeft: "1px solid #475569",
              }}
            >
              {" "}
              {configMenus.map((menu) => (
                <button
                  key={menu}
                  type="button"
                  style={{
                    ...buttonStyle(activeMenu === menu),
                    padding: "8px 10px",
                    fontSize: 13,
                  }}
                  onClick={() => {
                    setActiveMenu(menu);
                    setEditingRowIndex(null);
                    setEditedRow({});
                    setAddWindowOpen(false);
                    setNewRow({});
                  }}
                >
                  {" "}
                  {menu}{" "}
                </button>
              ))}{" "}
            </div>
          )}{" "}
          {/* Schedule Generator */}{" "}
          <button
            type="button"
            style={buttonStyle(activeMenu === "Schedule Generator")}
            onClick={() => setActiveMenu("Schedule Generator")}
          >
            {" "}
            <span style={{ display: "inline-block", width: 18 }} /> Schedule
            Generator{" "}
          </button>{" "}
          {/* Schedule Viewer */}{" "}
          <button
            type="button"
            style={buttonStyle(activeMenu === "Schedule Viewer")}
            onClick={() => setActiveMenu("Schedule Viewer")}
          >
            {" "}
            <span style={{ display: "inline-block", width: 18 }} /> Schedule
            Viewer{" "}
          </button>{" "}
        </nav>{" "}
        {/* Main Content */}{" "}
        <main
          style={{
            flex: 1,
            minWidth: 0,
            minHeight: 0,
            overflow: "auto",
            padding: 16,
            boxSizing: "border-box",
          }}
        >
          {" "}
          {/* Configuration Editor */}{" "}
          {activeMenu === "Configuration Editor" && (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                minHeight: 0,
                overflow: "hidden",
                background: "white",
                border: "1px solid #cbd5e1",
                borderRadius: 8,
                padding: 16,
                boxSizing: "border-box",
              }}
            >
              <App
                onConfigSelected={handleEditorConfigSelected}
                onChooseFile={handleChooseEditorFile}
                onCreateNew={handleCreateNewConfig}
              />{" "}
            </div>
          )}{" "}
          {/* Configuration Sections */}{" "}
          {configMenus.includes(activeMenu) && (
            <section
              style={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                minHeight: 0,
                overflow: "hidden",
                background: "white",
                border: "1px solid #cbd5e1",
                borderRadius: 8,
                padding: 24,
                boxSizing: "border-box",
              }}
            >
              {" "}
              <h1 style={{ marginTop: 0, fontSize: 28 }}>{activeMenu}</h1>{" "}
              <p style={{ color: "#64748b" }}>
                {" "}
              </p>{" "}
              {/* Render read-only rows from the selected submenu schema. */}
              <div style={{ flex: 1, minHeight: 0, overflow: "auto", width: "100%" }}>
                <table
                  style={{
                    width: "100%",
                    minWidth: 900,
                    tableLayout: "fixed",
                    borderCollapse: "collapse",
                    textAlign: "left",
                  }}
                >
                  <colgroup>
                    {configTableColumns[activeMenu].map((column) => (
                      <col
                        key={column}
                        style={{ width: Math.max(160, column.length * 12 + 40) }}
                      />
                    ))}
                    <col style={{ width: 170 }} />
                  </colgroup>
                  <thead>
                    <tr>
                      {configTableColumns[activeMenu].map((column) => (
                        <th
                          key={column}
                          scope="col"
                          style={{
                            padding: 10,
                            borderBottom: "2px solid #cbd5e1",
                            borderRight: "1px solid #e2e8f0",
                            background: "#f8fafc",
                            textAlign: "center",
                          }}
                        >
                          {column}
                        </th>
                      ))}
                      <th
                        scope="col"
                        style={{
                          padding: 10,
                          borderBottom: "2px solid #cbd5e1",
                          borderLeft: "1px solid #e2e8f0",
                          background: "#f8fafc",
                          textAlign: "center",
                        }}
                      >
                        Actions
                      </th>

                    </tr>
                  </thead>
                  <tbody>
                    {(configRows[activeMenu] ?? []).map((row, rowIndex) => (
                      <tr key={`${activeMenu}-${rowIndex}`} style={{ height: 48 }}>
                        {configTableColumns[activeMenu].map((column) => (
                          <td
                            key={column}
                            style={{
                              height: 48,
                              padding: 8,
                              borderBottom: "1px solid #e2e8f0",
                              overflowWrap: "anywhere",
                              whiteSpace: "normal",
                              textAlign: "center",
                            }}
                          >
                            {formatConfigCell(activeMenu, column, row[column])}
                          </td>
                        ))}
                        <td
                          style={{
                            position: "relative",
                            height: 48,
                            padding: 8,
                            borderBottom: "1px solid #e2e8f0",
                            textAlign: "center",
                            whiteSpace: "nowrap",
                          }}
                        >
                          <button
                            type="button"
                            aria-label={`Edit ${activeMenu} row ${rowIndex + 1}`}
                            onClick={() => {
                              setEditedRow({ ...row });
                              setEditingRowIndex(rowIndex);
                            }}
                            style={{
                              padding: "7px 8px",
                              border: "1px solid #cbd5e1",
                              borderRadius: 4,
                              background: "white",
                              color: "#0f172a",
                              fontSize: 12,
                              cursor: "pointer",
                              marginRight: 4,
                            }}
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            aria-label={`Delete ${activeMenu} row ${rowIndex + 1}`}
                            onClick={() => {
                              setConfigRows((current) => ({
                                ...current,
                                [activeMenu]: (current[activeMenu] ?? []).filter(
                                  (_, index) => index !== rowIndex
                                ),
                              }));
                              setEditorDirty(true);
                              setEditingRowIndex(null);
                              setEditedRow({});
                            }}
                            style={{
                              padding: "7px 8px",
                              border: "1px solid #cbd5e1",
                              borderRadius: 4,
                              background: "white",
                              color: "#0f172a",
                              fontSize: 12,
                              cursor: "pointer",
                            }}
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {editingRowIndex === null && !addWindowOpen && (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    flexShrink: 0,
                    marginTop: 12,
                    padding: "10px 12px",
                    background: "#d7d7d7",
                    border: "1px solid #cbd5e1",
                    borderRadius: 8,
                    boxShadow: "0 4px 12px rgba(15, 23, 42, 0.15)",
                  }}
                >
                  <span style={{ color: "#475569", fontSize: 13 }}>
                    Add to {activeMenu}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setNewRow(Object.fromEntries(configTableColumns[activeMenu].map((column) => [column, ""])));
                      setAddWindowOpen(true);
                    }}
                    style={{
                      padding: "6px 10px",
                      border: 0,
                      borderRadius: 6,
                      background: "#334155",
                      color: "#f8fafc",
                      fontSize: 13,
                      fontWeight: "bold",
                      cursor: "pointer",
                    }}
                  >
                    + Add
                  </button>
                </div>
              )}
              {editingRowIndex !== null && (
                <div
                  role="region"
                  aria-label={`Edit ${activeMenu} row`}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    flexWrap: "wrap",
                    gap: 12,
                    flexShrink: 0,
                    maxHeight: "45%",
                    marginTop: 12,
                    padding: 16,
                    background: "white",
                    border: "1px solid #cbd5e1",
                    borderRadius: 8,
                    boxShadow: "0 4px 12px rgba(15, 23, 42, 0.18)",
                    overflow: "auto",
                  }}
                >
                  {configTableColumns[activeMenu].map((column) => (
                    <label key={column} style={{ flex: "1 0 120px", fontSize: 12, color: "#475569" }}>
                      {column}
                      <ConfigFieldEditor
                        menu={activeMenu}
                        column={column}
                        value={editedRow[column] ?? ""}
                        onChange={(value) =>
                          setEditedRow((current) => ({ ...current, [column]: value }))
                        }
                      />
                    </label>
                  ))}
                  <button
                    type="button"
                    onClick={() => {
                      setEditingRowIndex(null);
                      setEditedRow({});
                    }}
                    style={{ padding: "8px 12px", flexShrink: 0 }}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setConfigRows((current) => ({
                        ...current,
                        [activeMenu]: (current[activeMenu] ?? []).map((row, index) =>
                          index === editingRowIndex ? editedRow : row
                        ),
                      }));
                      setEditorDirty(true);
                      setEditingRowIndex(null);
                      setEditedRow({});
                    }}
                    style={{ padding: "8px 12px", background: "#334155", color: "white", border: 0, borderRadius: 6, flexShrink: 0 }}
                  >
                    Apply to Draft
                  </button>
                </div>
              )}
              {addWindowOpen && (
                <form
                  onSubmit={(event) => {
                    event.preventDefault();
                    const rows = configRows[activeMenu] ?? [];
                    const newRowIndex = rows.length;
                    setConfigRows((current) => ({
                      ...current,
                      [activeMenu]: [...rows, newRow],
                    }));
                    setEditorDirty(true);
                    setAddWindowOpen(false);
                    setEditingRowIndex(newRowIndex);
                    setEditedRow({ ...newRow });
                  }}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    flexWrap: "wrap",
                    gap: 12,
                    flexShrink: 0,
                    maxHeight: "45%",
                    marginTop: 12,
                    padding: 16,
                    background: "#d7d7d7",
                    border: "1px solid #cbd5e1",
                    borderRadius: 8,
                    boxShadow: "0 4px 12px rgba(15, 23, 42, 0.18)",
                    overflow: "auto",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginRight: 8 }}>
                    <span style={{ fontWeight: "bold", color: "#0f172a" }}>Add {activeMenu}</span>
                  </div>
                  {configTableColumns[activeMenu].map((column) => (
                    <label key={column} style={{ flex: "1 0 120px", fontSize: 12, color: "#475569" }}>
                      {column}
                      <ConfigFieldEditor
                        menu={activeMenu}
                        column={column}
                        value={newRow[column] ?? ""}
                        autoFocus={column === configTableColumns[activeMenu][0]}
                        onChange={(value) =>
                          setNewRow((current) => ({ ...current, [column]: value }))
                        }
                      />
                    </label>
                  ))}
                  <button
                    type="button"
                    onClick={() => {
                      setAddWindowOpen(false);
                      setNewRow({});
                    }}
                    style={{ padding: "8px 12px", flexShrink: 0 }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    style={{
                      padding: "8px 12px",
                      background: "#334155",
                      color: "white",
                      border: 0,
                      borderRadius: 6,
                      flexShrink: 0,
                    }}
                  >
                    Add
                  </button>
                </form>
              )}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 12,
                  flexShrink: 0,
                  marginTop: 12,
                  paddingTop: 12,
                  borderTop: "1px solid #cbd5e1",
                }}
              >
                <div>
                  {editorFileName && (
                    <span style={{ color: "#475569", fontSize: 13 }}>
                      Editing {editorFileName}
                    </span>
                  )}
                  {editorSaveStatus && (
                    <p role="status" style={{ margin: "4px 0 0", color: "#475569", fontSize: 13 }}>
                      {editorSaveStatus}
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => void handleSaveEditorConfig()}
                  disabled={
                    !editorDirty ||
                    !editorFileName ||
                    editorSaving ||
                    editingRowIndex !== null ||
                    addWindowOpen
                  }
                  style={{
                    padding: "9px 14px",
                    border: 0,
                    borderRadius: 6,
                    background:
                      editorDirty && editorFileName ? "#334155" : "#94a3b8",
                    color: "white",
                    fontWeight: "bold",
                    cursor:
                      editorDirty && editorFileName ? "pointer" : "not-allowed",
                  }}
                >
                  {editorSaving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </section>
          )}{" "}
          {/* Schedule Generator */}{" "}
          {activeMenu === "Schedule Generator" && (
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
              {" "}
              <h1 style={{ marginTop: 0, fontSize: 28 }}>
                {" "}
                Schedule Generator{" "}
              </h1>{" "}
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
                  type="file"
                  accept=".json"
                  onChange={(event) =>
                    setConfigFile(event.target.files?.[0] ?? null)
                  }
                />{" "}
                <button
                  type="button"
                  onClick={handleConfigLoad}
                  disabled={!configFile || configLoading}
                >
                  {configLoading ? "Loading..." : "Load Config"}
                </button>
                {configStatus && (
                  <p role="status" style={{ marginTop: 8 }}>
                    {configStatus}
                  </p>
                )}
                {configErrors.length > 0 && (
                  <ul role="alert" style={{ color: "#b91c1c" }}>
                    {configErrors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                )}
              </div>{" "}
              {/* Generation Limit */}{" "}
              <div
                style={{
                  padding: 20,
                  border: "1px solid #cbd5e1",
                  borderRadius: 8,
                  background: "#f8fafc",
                }}
              >
                {" "}
                <h2 style={{ marginTop: 0, marginBottom: 16, fontSize: 18 }}>
                  {" "}
                  Generation Limit{" "}
                </h2>{" "}
                <label
                  htmlFor="generation-limit"
                  style={{
                    display: "block",
                    marginBottom: 8,
                    fontSize: 14,
                    fontWeight: "bold",
                  }}
                >
                  {" "}
                  Maximum schedules to generate{" "}
                </label>{" "}
                <input
                  id="generation-limit"
                  type="number"
                  min={1}
                  value={generationLimit}
                  onChange={(event) => {
                    const value = Number(event.target.value);
                    if (value >= 1) {
                      setGenerationLimit(value);
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
                />{" "}
                <p style={{ marginBottom: 0, color: "#64748b", fontSize: 12 }}>
                  {" "}
                  Number of schedules the generator should produce.{" "}
                </p>{" "}
              </div>{" "}
              {/* Optimizer Flags */}{" "}
              <div
                style={{
                  marginTop: 20,
                  padding: 20,
                  border: "1px solid #cbd5e1",
                  borderRadius: 8,
                  background: "#f8fafc",
                }}
              >
                {" "}
                <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: 18 }}>
                  {" "}
                  Optimizer Flags{" "}
                </h2>{" "}
                <p
                  style={{
                    marginTop: 0,
                    marginBottom: 18,
                    color: "#64748b",
                    fontSize: 13,
                  }}
                >
                  {" "}
                  Select optimization preferences for schedule generation.{" "}
                </p>{" "}
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
                    {" "}
                    <input
                      type="checkbox"
                      checked={optimizerFlags.includes(option.value)}
                      onChange={() => toggleOptimizerFlag(option.value)}
                    />{" "}
                    {option.label}{" "}
                  </label>
                ))}{" "}
              </div>{" "}
              {/* Generate Button */}{" "}
              <button
                type="button"
                onClick={() => void handleGenerateSchedule()}
                disabled={generatingSchedules}
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
                {generatingSchedules ? "Generating..." : "Generate Schedule"}
              </button>{" "}
              {/* Generation Status */}{" "}
              <div
                style={{
                  marginTop: 24,
                  padding: 20,
                  border: "1px solid #cbd5e1",
                  borderRadius: 8,
                }}
              >
                {" "}
                <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: 18 }}>
                  {" "}
                  Generation Status{" "}
                </h2>{" "}
                <p style={{ margin: 0, color: "#64748b" }}>
                  {generationStatus}
                </p>{" "}
                {generationError && (
                  <p role="alert" style={{ marginBottom: 0, color: "#b91c1c" }}>
                    {generationError}
                  </p>
                )}
              </div>{" "}
              <button
                type="button"
                onClick={() => void handleExportSchedule()}
                disabled={generatedScheduleCount === 0 || exportingSchedule}
                style={{
                  marginTop: 20,
                  padding: "11px 20px",
                  border: 0,
                  borderRadius: 6,
                  background: "#334155",
                  color: "#f8fafc",
                  fontSize: 14,
                  fontWeight: "bold",
                  cursor:
                    generatedScheduleCount > 0 && !exportingSchedule
                      ? "pointer"
                      : "not-allowed",
                }}
              >
                {exportingSchedule ? "Exporting..." : "Export Schedule as CSV"}
              </button>{" "}
            </section>
          )}{" "}
          {/* Schedule Viewer */}{" "}
          {activeMenu === "Schedule Viewer" && (
            <section
              style={{
                height: "100%",
                background: "white",
                border: "1px solid #cbd5e1",
                borderRadius: 8,
                padding: 24,
                boxSizing: "border-box",
              }}
            >
              {" "}
              <h1 style={{ marginTop: 0, fontSize: 28 }}>
                {" "}
                Schedule Viewer{" "}
              </h1>{" "}
              <p style={{ color: "#64748b" }}>
                {" "}
                View and export generated schedules here.{" "}
              </p>{" "}
            </section>
          )}{" "}
        </main>{" "}
      </div>{" "}
    </div>
  );
}
