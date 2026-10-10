import { useState } from "react";
import App from "./App";
import { uploadConfig } from "./api";
const configMenus = [
  "Rooms",
  "Labs",
  "Courses",
  "Faculty",
  "Timeslots",
  "Class Patterns",
  "Meetings",
];
// Each configuration submenu gets its own table schema and matching input fields.
const configTableColumns: Record<string, string[]> = {
  Rooms: ["Name", "Capacity", "Features", "Times"],
  Labs: ["Name", "Capacity", "Features", "Times"],
  Courses: [
    "Course ID",
    "Section ID",
    "Credits",
    "Capacity",
    "Room",
    "Lab",
    "Conflicts",
    "Faculty",
    "Alternate Faculty",
    "Modality",
    "Required Room Features",
    "Required Lab Features",
    "Reserve Room During Lab",
  ],
  Faculty: [
    "Name",
    "Maximum Credits",
    "Minimum Credits",
    "Unique Course Limit",
    "Maximum Days",
    "Mandatory Days",
    "Times",
    "Course Preferences",
    "Room Preferences",
    "Lab Preferences",
  ],
  Timeslots: ["Times", "Classes", "Max Time Gap", "Min Time Overlap"],
  "Class Patterns": ["Credits", "Meetings", "Disabled", "Start Time"],
  Meetings: ["Day", "Start Time", "Duration", "Lab", "Delivery"],
};

type ConfigTableRow = Record<string, string>;

function asObject(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function toCellValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  return typeof value === "string" ? value : JSON.stringify(value);
}

function toTableRows(
  menu: string,
  values: unknown,
): ConfigTableRow[] {
  if (!Array.isArray(values)) return [];

  const columns = configTableColumns[menu];
  return values.map((value) => {
    const source = asObject(value);
    return Object.fromEntries(
      columns.map((column) => {
        const key = column.toLowerCase().replaceAll(" ", "_");
        return [column, toCellValue(source[key])];
      }),
    );
  });
}

function getConfigTableRows(configValue: unknown): Record<string, ConfigTableRow[]> {
  const root = asObject(configValue);
  const config = asObject(root.config);
  const timeSlotConfig = asObject(root.time_slot_config);
  const classes = Array.isArray(timeSlotConfig.classes)
    ? timeSlotConfig.classes
    : [];
  const meetings = classes.flatMap((classPattern) => {
    const pattern = asObject(classPattern);
    return Array.isArray(pattern.meetings) ? pattern.meetings : [];
  });

  return {
    Rooms: toTableRows("Rooms", config.rooms),
    Labs: toTableRows("Labs", config.labs),
    Courses: toTableRows("Courses", config.courses),
    Faculty: toTableRows("Faculty", config.faculty),
    Timeslots: toTableRows("Timeslots", [timeSlotConfig]),
    "Class Patterns": toTableRows("Class Patterns", classes),
    Meetings: toTableRows("Meetings", meetings),
  };
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
    setConfigRows(getConfigTableRows(config));
    setEditingRowIndex(null);
    setEditedRow({});
    setAddWindowOpen(false);
    setNewRow({});
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
              <App onConfigSelected={handleEditorConfigSelected} />{" "}
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
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                              textAlign: "center",
                            }}
                          >
                            {row[column] ?? ""}
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
                    alignItems: "flex-end",
                    gap: 12,
                    flexShrink: 0,
                    marginTop: 12,
                    padding: 16,
                    background: "white",
                    border: "1px solid #cbd5e1",
                    borderRadius: 8,
                    boxShadow: "0 4px 12px rgba(15, 23, 42, 0.18)",
                    overflowX: "auto",
                  }}
                >
                  {configTableColumns[activeMenu].map((column) => (
                    <label key={column} style={{ flex: "1 0 120px", fontSize: 12, color: "#475569" }}>
                      {column}
                      <input
                        value={editedRow[column] ?? ""}
                        onChange={(event) => setEditedRow((current) => ({ ...current, [column]: event.target.value }))}
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
                      setEditingRowIndex(null);
                      setEditedRow({});
                    }}
                    style={{ padding: "8px 12px", background: "#334155", color: "white", border: 0, borderRadius: 6, flexShrink: 0 }}
                  >
                    Save
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
                    setAddWindowOpen(false);
                    setEditingRowIndex(newRowIndex);
                    setEditedRow({ ...newRow });
                  }}
                  style={{
                    display: "flex",
                    alignItems: "flex-end",
                    gap: 12,
                    flexShrink: 0,
                    marginTop: 12,
                    padding: 16,
                    background: "#d7d7d7",
                    border: "1px solid #cbd5e1",
                    borderRadius: 8,
                    boxShadow: "0 4px 12px rgba(15, 23, 42, 0.18)",
                    overflowX: "auto",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginRight: 8 }}>
                    <span style={{ fontWeight: "bold", color: "#0f172a" }}>Add {activeMenu}</span>
                  </div>
                  {configTableColumns[activeMenu].map((column) => (
                    <label key={column} style={{ flex: "1 0 120px", fontSize: 12, color: "#475569" }}>
                      {column}
                      <input
                        autoFocus={column === configTableColumns[activeMenu][0]}
                        value={newRow[column] ?? ""}
                        onChange={(event) =>
                          setNewRow((current) => ({ ...current, [column]: event.target.value }))
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
                onClick={() => {
                  console.log("Generation request:", {
                    limit: generationLimit,
                    optimizer_flags: optimizerFlags,
                  });
                }}
                style={{
                  marginTop: 24,
                  padding: "11px 20px",
                  border: 0,
                  borderRadius: 6,
                  background: "#334155",
                  color: "#f8fafc",
                  fontSize: 14,
                  fontWeight: "bold",
                  cursor: "pointer",
                }}
              >
                Generate Schedule
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
                  Ready to generate a schedule.
                </p>{" "}
              </div>{" "}
              <button
                type="button"
                style={{
                  marginTop: 20,
                  padding: "11px 20px",
                  border: 0,
                  borderRadius: 6,
                  background: "#334155",
                  color: "#f8fafc",
                  fontSize: 14,
                  fontWeight: "bold",
                  cursor: "pointer",
                }}
              >
                Export Schedule as CSV
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
