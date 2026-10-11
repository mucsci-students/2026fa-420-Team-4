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
  const [statusMessage, setStatusMessage] = useState("Ready.");

  return (
    <div className="retro-desktop">
      <div className="retro-window">
        <header className="retro-titlebar">
          <div className="retro-title">
            <span>MU Scheduler</span>
          </div>
          <div className="retro-window-controls" aria-hidden="true">
            <span className="retro-window-control">_</span>
            <span className="retro-window-control">□</span>
            <span className="retro-window-control">×</span>
          </div>
        </header>
        <div className="retro-window-body">
        <nav
          aria-label="Main menu"
          className="retro-sidebar"
        >
          <button
            type="button"
            aria-expanded={configurationExpanded}
            className={`retro-nav-button ${
              activeOption === "Configuration Editor" ? "is-active" : ""
            }`}
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
            <div className="retro-nav-submenu">
              {configMenus.map((menu) => (
                <button
                  key={menu}
                  type="button"
                  className={`retro-nav-button ${
                    activeOption === "Configuration Editor" &&
                    selectedEditorSection === menu
                      ? "is-active"
                      : ""
                  }`}
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
                className={`retro-nav-button ${
                  activeOption === option ? "is-active" : ""
                }`}
                onClick={() => setActiveOption(option)}
              >
                {option}
              </button>
            ))}
        </nav>
        <main
          className="retro-content"
        >
          <div
            style={{
              display: activeOption === "Configuration Editor" ? "flex" : "none",
              height: "100%",
              minHeight: 0,
            }}
          >
            <ConfigurationEditor
              selectedMenu={selectedEditorSection}
              onStatusChange={setStatusMessage}
            />
          </div>
          <div
            style={{
              display: activeOption === "Schedule Generator" ? "block" : "none",
              height: "100%",
              minHeight: 0,
            }}
          >
            <ScheduleGenerator onStatusChange={setStatusMessage} />
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
        <footer className="retro-statusbar">
          <span className="retro-status-cell" role="status" aria-live="polite">
            {statusMessage}
          </span>
        </footer>
      </div>
    </div>
  );
}
