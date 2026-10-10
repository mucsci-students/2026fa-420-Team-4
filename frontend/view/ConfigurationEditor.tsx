import { useState } from "react";
import axios from "axios";
import App from "./App";
import { validateConfig } from "./api";
import {
  applyConfigTableRows,
  asObject,
  configMenus,
  configTableColumns,
  getConfigTableRows,
  type ConfigTableRow,
} from "./configEditorModel";
import {
  createConfigFileController,
  type OpenedConfigFile,
} from "./front_controllers/configFileController";
import { formatConfigErrors } from "./configErrorMessages";

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
const preferenceColumns = ["Course Preferences", "Room Preferences", "Lab Preferences"];

function prepareRowForCommit(menu: string, row: ConfigTableRow): ConfigTableRow {
  if (menu !== "Faculty") return row;
  return Object.fromEntries(Object.entries(row).map(([column, value]) => [
    column,
    preferenceColumns.includes(column) && value !== ""
      ? JSON.stringify(Object.fromEntries(
          Object.entries(asObject(parseEditorJson(value, {})))
            .filter(([name]) => name.trim() !== ""),
        ))
      : value,
  ]));
}

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
    preferenceColumns.includes(column)
  ) {
    const preferencesValue = parseEditorJson(value, {});
    const preferences = asObject(preferencesValue);
    const entries = Object.entries(preferences);
    const updateEntries = (nextEntries: Array<[string, unknown]>) => {
      onChange(JSON.stringify(Object.fromEntries(nextEntries)));
    };

     return (
      <div style={{ ...structuredEditorStyle, maxHeight: "24vh" }}>
        {entries.map(([name, score], index) => (
          <div
            key={index}
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

interface ConfigurationEditorProps {
  selectedMenu: string;
}

export default function ConfigurationEditor({
  selectedMenu,
}: ConfigurationEditorProps) {
  const [previousSelectedMenu, setPreviousSelectedMenu] =
    useState(selectedMenu);
   const [addWindowOpen, setAddWindowOpen] = useState(false);
    const [newRow, setNewRow] = useState<Record<string, string>>({});
    const [editingRowIndex, setEditingRowIndex] = useState<number | null>(null);
    const [editedRow, setEditedRow] = useState<Record<string, string>>({});
    const [configRows, setConfigRows] = useState<
    Record<string, ConfigTableRow[]>
  >({});
    const [originalEditorConfig, setOriginalEditorConfig] = useState<unknown>(null);
    const [editorFileName, setEditorFileName] = useState("");
    const [editorDirty, setEditorDirty] = useState(false);
    const [editorSaveStatus, setEditorSaveStatus] = useState("");
    const [editorSaveFailed, setEditorSaveFailed] = useState(false);
    const [editorSaving, setEditorSaving] = useState(false);
    const [editorDraftStatus, setEditorDraftStatus] = useState("");
    const [editorDraftErrors, setEditorDraftErrors] = useState<string[]>([]);
    const [editorDraftChecking, setEditorDraftChecking] = useState(false);
    const [editorDraftValid, setEditorDraftValid] = useState(false);
    const [editorAddingRow, setEditorAddingRow] = useState(false);
    const [editorFileController] = useState(createConfigFileController);
  if (previousSelectedMenu !== selectedMenu) {
    setPreviousSelectedMenu(selectedMenu);
    setEditingRowIndex(null);
    setEditedRow({});
    setAddWindowOpen(false);
    setNewRow({});
  }
 const handleEditorConfigSelected = (config: unknown) => {
    setOriginalEditorConfig(config);
    setConfigRows(getConfigTableRows(config));
    setEditorDirty(false);
    setEditorSaveStatus("");
    setEditorSaveFailed(false);
    setEditorDraftStatus("");
    setEditorDraftErrors([]);
    setEditorDraftValid(true);
    setEditingRowIndex(null);
    setEditedRow({});
    setAddWindowOpen(false);
    setNewRow({});
  };
  const handleChooseEditorFile = async (
    file: File,
  ): Promise<OpenedConfigFile> => {
    await validateConfig(file);
    const selected = await editorFileController.open(file);
    setEditorFileName(selected.file.name);
    return selected;
  };
  const handleCreateNewConfig = () => {
    setEditorFileName(editorFileController.create());
    setOriginalEditorConfig({});
    setConfigRows({});
    setEditorDirty(true);
    setEditorSaveStatus("");
    setEditorSaveFailed(false);
    setEditorDraftStatus("");
    setEditorDraftErrors([]);
    setEditorDraftValid(false);
    setEditingRowIndex(null);
    setEditedRow({});
    setAddWindowOpen(false);
    setNewRow({});
  };
  const validateEditorDraft = async (
    draftTables: Record<string, ConfigTableRow[]>,
  ) => {
    if (originalEditorConfig === null || !editorFileName) return;

    setEditorDraftChecking(true);
    setEditorDraftValid(false);
    setEditorDraftStatus("Checking changes...");
    setEditorDraftErrors([]);
    try {
      const draftConfig = applyConfigTableRows(originalEditorConfig, draftTables);
      const draftFile = new File(
        [`${JSON.stringify(draftConfig, null, 2)}\n`],
        editorFileName,
        { type: "application/json" },
      );
      await validateConfig(draftFile);
      setEditorDraftStatus("Changes pass validation.");
      setEditorDraftValid(true);
    } catch (error) {
      let messages = [
        error instanceof Error
          ? error.message
          : "Could not validate the configuration changes.",
      ];
      if (
        axios.isAxiosError<{
          detail?: { errors?: string[] } | string;
        }>(error)
      ) {
        const detail = error.response?.data?.detail;
        if (typeof detail === "string") {
          messages = [detail];
        } else if (detail?.errors?.length) {
          messages = detail.errors;
        }
      }
      setEditorDraftStatus("Changes need attention.");
      setEditorDraftErrors(formatConfigErrors(messages));
      setEditorDraftValid(false);
    } finally {
      setEditorDraftChecking(false);
    }
  };
  const getValidationErrors = (error: unknown): string[] | null => {
    if (
      !axios.isAxiosError<{
        detail?: { errors?: string[] } | string;
      }>(error)
    ) {
      return null;
    }

    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return [detail];
    return detail?.errors ?? null;
  };
  const compareCandidateValidation = async (
    draftTables: Record<string, ConfigTableRow[]>,
  ): Promise<{ newErrors: string[]; candidateErrors: string[] }> => {
    if (originalEditorConfig === null || !editorFileName) {
      throw new Error("Create a new configuration or choose a file first.");
    }

    const toValidationFile = (tables: Record<string, ConfigTableRow[]>) =>
      new File(
        [
          `${JSON.stringify(
            applyConfigTableRows(originalEditorConfig, tables),
            null,
            2,
          )}\n`,
        ],
        editorFileName,
        { type: "application/json" },
      );

    let candidateErrors: string[];
    try {
      await validateConfig(toValidationFile(draftTables));
      return { newErrors: [], candidateErrors: [] };
    } catch (error) {
      candidateErrors = getValidationErrors(error) ?? [
        error instanceof Error
          ? error.message
          : "Could not validate the new item.",
      ];
    }

    let existingErrors: string[];
    try {
      await validateConfig(toValidationFile(configRows));
      existingErrors = [];
    } catch (error) {
      const validationErrors = getValidationErrors(error);
      if (!validationErrors) throw error;
      existingErrors = validationErrors;
    }

    const existingErrorCounts = new Map<string, number>();
    for (const error of existingErrors) {
      existingErrorCounts.set(error, (existingErrorCounts.get(error) ?? 0) + 1);
    }
    const newErrors = candidateErrors.filter((error) => {
      const count = existingErrorCounts.get(error) ?? 0;
      if (count === 0) return true;
      existingErrorCounts.set(error, count - 1);
      return false;
    });
    return { newErrors, candidateErrors };
  };
  const handleAddNewRow = async () => {
    const currentRows = configRows[selectedMenu] ?? [];
    const updatedTables = {
      ...configRows,
      [selectedMenu]: [...currentRows, prepareRowForCommit(selectedMenu, newRow)],
    };
    setEditorAddingRow(true);
    setEditorDraftChecking(true);
    setEditorDraftStatus("Checking item...");
    setEditorDraftErrors([]);
    try {
      const { newErrors, candidateErrors } = await compareCandidateValidation(updatedTables);
      if (newErrors.length > 0) {
        setEditorDraftStatus("Item has invalid fields.");
        setEditorDraftErrors(formatConfigErrors(newErrors));
        setEditorDraftValid(false);
        return;
      }

      setConfigRows(updatedTables);
      setEditorDirty(true);
      setAddWindowOpen(false);
      setNewRow({});
      if (candidateErrors.length === 0) {
        setEditorDraftStatus("Item added. Changes pass validation.");
        setEditorDraftErrors([]);
        setEditorDraftValid(true);
      } else {
        setEditorDraftStatus("Item added. Existing configuration issues remain.");
        setEditorDraftErrors(formatConfigErrors(candidateErrors));
        setEditorDraftValid(false);
      }
    } catch (error) {
      setEditorDraftStatus("Could not add item.");
      setEditorDraftErrors(
        formatConfigErrors([
          error instanceof Error
            ? error.message
            : "Could not validate the new item.",
        ]),
      );
      setEditorDraftValid(false);
    } finally {
      setEditorAddingRow(false);
      setEditorDraftChecking(false);
    }
  };
  const handleApplyEditedRow = async () => {
    if (editingRowIndex === null) return;
    const updatedTables = {
      ...configRows,
      [selectedMenu]: (configRows[selectedMenu] ?? []).map((row, index) =>
        index === editingRowIndex ? prepareRowForCommit(selectedMenu, editedRow) : row,
      ),
    };
    setEditorDraftChecking(true);
    setEditorDraftStatus("Checking edited item...");
    setEditorDraftErrors([]);
    try {
      const { newErrors, candidateErrors } =
        await compareCandidateValidation(updatedTables);
      if (newErrors.length > 0) {
        setEditorDraftStatus("Edited item has invalid fields. Changes were not applied.");
        setEditorDraftErrors(formatConfigErrors(newErrors));
        setEditorDraftValid(false);
        return;
      }

      setConfigRows(updatedTables);
      setEditorDirty(true);
      setEditingRowIndex(null);
      setEditedRow({});
      if (candidateErrors.length === 0) {
        setEditorDraftStatus("Edit applied. Changes pass validation.");
        setEditorDraftErrors([]);
        setEditorDraftValid(true);
      } else {
        setEditorDraftStatus("Edit applied. Existing configuration issues remain.");
        setEditorDraftErrors(formatConfigErrors(candidateErrors));
        setEditorDraftValid(false);
      }
    } catch (error) {
      setEditorDraftStatus("Could not validate edit. Changes were not applied.");
      setEditorDraftErrors(
        formatConfigErrors([
          error instanceof Error
            ? error.message
            : "Could not validate the edited item.",
        ]),
      );
      setEditorDraftValid(false);
    } finally {
      setEditorDraftChecking(false);
    }
  };
  const handleSaveEditorConfig = async () => {
    if (originalEditorConfig === null || !editorFileName) {
      setEditorSaveStatus("Create a new configuration or choose an existing file before saving.");
      return;
    }
    if (editorDraftChecking || !editorDraftValid || editorDraftErrors.length > 0) {
      setEditorSaveStatus("Fix all configuration issues and wait for validation before saving.");
      setEditorSaveFailed(true);
      return;
    }

    setEditorSaving(true);
    setEditorSaveStatus("Validating configuration...");
    setEditorSaveFailed(false);
    try {
      const updatedConfig = applyConfigTableRows(originalEditorConfig, configRows);
      const configFile = new File(
        [`${JSON.stringify(updatedConfig, null, 2)}\n`],
        editorFileName,
        { type: "application/json" },
      );
      await validateConfig(configFile);
      editorFileController.save(updatedConfig);
      setOriginalEditorConfig(updatedConfig);
      setEditorDirty(false);
      setEditorSaveStatus("Configuration validated and saved successfully.");
      setEditorSaveFailed(false);
    } catch (error) {
      let messages = [
        error instanceof Error
          ? error.message
          : "Could not validate and save the configuration file.",
      ];
      if (
        axios.isAxiosError<{
          detail?: { errors?: string[] } | string;
        }>(error)
      ) {
        const detail = error.response?.data?.detail;
        if (typeof detail === "string") {
          messages = [detail];
        } else if (detail?.errors?.length) {
          messages = detail.errors;
        }
      }
      setEditorSaveStatus(formatConfigErrors(messages).join("\n"));
      setEditorSaveFailed(true);
    } finally {
      setEditorSaving(false);
    }
  };
  return (
    <div style={{ height: "100%", minHeight: 0, overflow: "hidden" }}>
      {/* Configuration Editor */}{" "}
          {selectedMenu === "Configuration Editor" && (
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
          {configMenus.includes(selectedMenu) && (
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
              <h1 style={{ marginTop: 0, fontSize: 28 }}>{selectedMenu}</h1>{" "}
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
                    {configTableColumns[selectedMenu].map((column) => (
                      <col
                        key={column}
                        style={{ width: Math.max(160, column.length * 12 + 40) }}
                      />
                    ))}
                    <col style={{ width: 170 }} />
                  </colgroup>
                  <thead>
                    <tr>
                      {configTableColumns[selectedMenu].map((column) => (
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
                    {(configRows[selectedMenu] ?? []).map((row, rowIndex) => (
                      <tr key={`${selectedMenu}-${rowIndex}`} style={{ height: 48 }}>
                        {configTableColumns[selectedMenu].map((column) => (
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
                            {formatConfigCell(selectedMenu, column, row[column])}
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
                            aria-label={`Edit ${selectedMenu} row ${rowIndex + 1}`}
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
                            aria-label={`Delete ${selectedMenu} row ${rowIndex + 1}`}
                            onClick={() => {
                              const updatedTables = {
                                ...configRows,
                                [selectedMenu]: (configRows[selectedMenu] ?? []).filter(
                                  (_, index) => index !== rowIndex,
                                ),
                              };
                              setConfigRows(updatedTables);
                              setEditorDirty(true);
                              setEditingRowIndex(null);
                              setEditedRow({});
                              void validateEditorDraft(updatedTables);
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
                    Add to {selectedMenu}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setNewRow(Object.fromEntries(configTableColumns[selectedMenu].map((column) => [column, ""])));
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
                  aria-label={`Edit ${selectedMenu} row`}
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
                  {configTableColumns[selectedMenu].map((column) => (
                    <label key={column} style={{ flex: "1 0 120px", fontSize: 12, color: "#475569" }}>
                      {column}
                      <ConfigFieldEditor
                        menu={selectedMenu}
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
                    disabled={editorDraftChecking}
                    onClick={() => void handleApplyEditedRow()}
                    style={{ padding: "8px 12px", background: "#334155", color: "white", border: 0, borderRadius: 6, flexShrink: 0 }}
                  >
                    {editorDraftChecking ? "Checking..." : "Apply"}
                  </button>
                </div>
              )}
              {addWindowOpen && (
                <form
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleAddNewRow();
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
                    <span style={{ fontWeight: "bold", color: "#0f172a" }}>Add {selectedMenu}</span>
                  </div>
                  {configTableColumns[selectedMenu].map((column) => (
                    <label key={column} style={{ flex: "1 0 120px", fontSize: 12, color: "#475569" }}>
                      {column}
                      <ConfigFieldEditor
                        menu={selectedMenu}
                        column={column}
                        value={newRow[column] ?? ""}
                        autoFocus={column === configTableColumns[selectedMenu][0]}
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
                    disabled={editorAddingRow || editorDraftChecking}
                    style={{
                      padding: "8px 12px",
                      background: "#334155",
                      color: "white",
                      border: 0,
                      borderRadius: 6,
                      flexShrink: 0,
                    }}
                  >
                    {editorAddingRow ? "Checking..." : "Add"}
                  </button>
                </form>
              )}
              {(editorDraftStatus || editorDraftErrors.length > 0) && (
                <div
                  role={editorDraftErrors.length > 0 ? "alert" : "status"}
                  style={{
                    marginTop: 12,
                    padding: "10px 14px",
                    color: editorDraftErrors.length > 0 ? "#991b1b" : "#166534",
                    background:
                      editorDraftErrors.length > 0 ? "#fef2f2" : "#f0fdf4",
                    border: `1px solid ${
                      editorDraftErrors.length > 0 ? "#fecaca" : "#bbf7d0"
                    }`,
                    borderRadius: 6,
                  }}
                >
                  <strong>{editorDraftStatus}</strong>
                  {editorDraftErrors.length > 0 && (
                    <ul style={{ margin: "8px 0 0", paddingLeft: 20 }}>
                      {editorDraftErrors.map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  )}
                </div>
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
                    <p
                      role={editorSaveFailed ? "alert" : "status"}
                      style={{
                        margin: "4px 0 0",
                        color: editorSaveFailed ? "#b91c1c" : "#475569",
                        fontSize: 13,
                        whiteSpace: "pre-line",
                      }}
                    >
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
                    editorDraftChecking ||
                    !editorDraftValid ||
                    editorDraftErrors.length > 0 ||
                    editingRowIndex !== null ||
                    addWindowOpen
                  }
                  style={{
                    padding: "9px 14px",
                    border: 0,
                    borderRadius: 6,
                    background:
                      editorDirty &&
                      editorFileName &&
                      editorDraftValid &&
                      !editorDraftChecking &&
                      editorDraftErrors.length === 0
                        ? "#334155"
                        : "#94a3b8",
                    color: "white",
                    fontWeight: "bold",
                    cursor:
                      editorDirty &&
                      editorFileName &&
                      editorDraftValid &&
                      !editorDraftChecking &&
                      editorDraftErrors.length === 0
                        ? "pointer"
                        : "not-allowed",
                  }}
                >
                  {editorSaving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </section>
          )}{" "}
    </div>
  );
}
