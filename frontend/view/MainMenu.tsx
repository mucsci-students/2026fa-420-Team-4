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
                  onClick={() => setActiveMenu(menu)}
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
                height: "100%",
                overflow: "auto",
                background: "white",
                border: "1px solid #cbd5e1",
                borderRadius: 8,
                padding: 16,
                boxSizing: "border-box",
              }}
            >
              {" "}
              <App />{" "}
            </div>
          )}{" "}
          {/* Configuration Sections */}{" "}
          {configMenus.includes(activeMenu) && (
            <section
              style={{
                height: "100%",
                overflow: "auto",
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
                {activeMenu}{" "}
              </h1>{" "}
              <p style={{ color: "#64748b" }}>
                {" "}
                Manage {activeMenu.toLowerCase()} here.{" "}
              </p>{" "}
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
                onClick={() => {
                  console.log("Generation request:", {
                    limit: generationLimit,
                    optimizer_flags: optimizerFlags,
                  });
                }}
              >
                {" "}
                Generate Schedule{" "}
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
