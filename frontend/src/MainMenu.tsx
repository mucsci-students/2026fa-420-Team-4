import { useState } from "react";
import App from "./App";

const secondaryMenus = ["a", "b", "c"];
const mockMessages = Array.from(
    { length: 50 },
    (_, index) => `[12:${String(Math.floor(index / 60)).padStart(2, "0")}:${String(index % 60).padStart(2, "0")}] Mock log message ${index + 1}`
);

export default function MainMenu() {
    const [activeMenu, setActiveMenu] = useState("View");
    const [editOpen, setEditOpen] = useState(false);

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
                        width: 160,
                        flexShrink: 0,
                        padding: 12,
                        boxSizing: "border-box",
                        background: "#1e293b",
                        color: "#f8fafc",
                    }}
                >
                    <button
                        type="button"
                        style={buttonStyle(activeMenu === "View")}
                        onClick={() => setActiveMenu("View")}
                    >
                        View
                    </button>
                    <button
                        type="button"
                        aria-expanded={editOpen}
                        style={{ ...buttonStyle(editOpen), marginTop: 4 }}
                        onClick={() => setEditOpen((open) => !open)}
                    >
                        Edit <span style={{ float: "right" }}>{editOpen ? "▾" : "▸"}</span>
                    </button>
                    {editOpen && (
                        <div style={{ padding: "4px 0 0 14px" }}>
                            {secondaryMenus.map((menu) => (
                                <button
                                    key={menu}
                                    type="button"
                                    style={buttonStyle(activeMenu === menu)}
                                    onClick={() => setActiveMenu(menu)}
                                >
                                    {menu}
                                </button>
                            ))}
                        </div>
                    )}
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
                    {activeMenu === "View" ? (
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
                            <App />
                        </div>
                    ) : (
                        <section
                            style={{
                                height: "100%",
                                display: "grid",
                                placeItems: "center",
                                background: "white",
                                border: "1px solid #cbd5e1",
                                borderRadius: 8,
                            }}
                        >
                            <h1 style={{ margin: 0, fontSize: 32 }}>{activeMenu}</h1>
                        </section>
                    )}
                </main>
            </div>

            <section
                aria-label="Log window"
                style={{
                    height: 100,
                    flexShrink: 0,
                    boxSizing: "border-box",
                    padding: "12px 16px",
                    overflow: "auto",
                    background: "#0f172a",
                    color: "#cbd5e1",
                    borderTop: "1px solid #475569",
                }}
            >
                <strong style={{ color: "#f8fafc" }}>Log</strong>
                <div>
                    {mockMessages.map((message) => (
                        <div key={message}>{message}</div>
                    ))}
                </div>
            </section>
        </div>
    );
}
