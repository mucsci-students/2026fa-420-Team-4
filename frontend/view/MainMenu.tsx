import { useState } from "react";
import { configMenus } from "./configEditorModel";
import ConfigurationEditor from "./ConfigurationEditor";
import ScheduleGenerator from "./ScheduleGenerator";
import ScheduleViewer from "./ScheduleViewer";

type MainOption =
  | "Configuration Editor"
  | "Schedule Generator"
  | "Schedule Viewer";

const options: MainOption[] = [
  "Configuration Editor",
  "Schedule Generator",
  "Schedule Viewer",
];

export default function MainMenu() {
  const [activeOption, setActiveOption] =
    useState<MainOption>("Configuration Editor");
  const [configurationExpanded, setConfigurationExpanded] = useState(true);
  const [selectedEditorSection, setSelectedEditorSection] = useState(
    "Configuration Editor",
  );
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
      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
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
          <button
            type="button"
            aria-expanded={configurationExpanded}
            style={buttonStyle(activeOption === "Configuration Editor")}
            onClick={() => {
              setActiveOption("Configuration Editor");
              setSelectedEditorSection("Configuration Editor");
              setConfigurationExpanded((expanded) => !expanded);
            }}
          >
            <span style={{ display: "inline-block", width: 18 }}>
              {configurationExpanded ? "▾" : "▸"}
            </span>
            Configuration Editor
          </button>
          {configurationExpanded && (
            <div
              style={{
                margin: "2px 0 8px 18px",
                paddingLeft: 10,
                borderLeft: "1px solid #475569",
              }}
            >
              {configMenus.map((menu) => (
                <button
                  key={menu}
                  type="button"
                  style={{
                    ...buttonStyle(
                      activeOption === "Configuration Editor" &&
                        selectedEditorSection === menu,
                    ),
                    padding: "8px 10px",
                    fontSize: 13,
                  }}
                  onClick={() => {
                    setSelectedEditorSection(menu);
                    setActiveOption("Configuration Editor");
                  }}
                >
                  {menu}
                </button>
              ))}
            </div>
          )}
          {options
            .filter((option) => option !== "Configuration Editor")
            .map((option) => (
              <button
                key={option}
                type="button"
                style={buttonStyle(activeOption === option)}
                onClick={() => setActiveOption(option)}
              >
                {option}
              </button>
            ))}
        </nav>
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
          <div
            style={{
              display: activeOption === "Configuration Editor" ? "flex" : "none",
              height: "100%",
              minHeight: 0,
            }}
          >
            <ConfigurationEditor selectedMenu={selectedEditorSection} />
          </div>
          <div
            style={{
              display: activeOption === "Schedule Generator" ? "block" : "none",
              height: "100%",
              minHeight: 0,
            }}
          >
            <ScheduleGenerator />
          </div>
          <div
            style={{
              display: activeOption === "Schedule Viewer" ? "block" : "none",
              height: "100%",
              minHeight: 0,
            }}
          >
            <ScheduleViewer />
          </div>
        </main>
      </div>
    </div>
  );
}
