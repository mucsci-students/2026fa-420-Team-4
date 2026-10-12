import axios from "axios";
import { useEffect, useRef, useState } from "react";
import type { ScheduleData } from "./api";
import { createScheduleViewerController } from "./front_controllers/scheduleViewerController";
import RetroConfirmDialog from "./RetroConfirmDialog";

type ViewMode = "room" | "faculty";

interface DisplayMeeting {
  course: string;
  faculty: string;
  resource: string;
  resourceType: string;
  additionalResource?: string;
  day: string;
  start: string;
  duration: string;
  end: string;
}

/** Narrow an unknown value to a non-null object that is not an array. */
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Extract a display label from a primitive or named object, falling back when absent. */
function displayValue(value: unknown, fallback = "Not assigned"): string {
  if (typeof value === "string" && value.trim()) return value;
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (isRecord(value)) {
    return displayValue(
      value.name ?? value.course_id ?? value.id ?? value.label,
      fallback,
    );
  }
  return fallback;
}

/** Format numeric or named weekdays while preserving unrecognized values. */
function formatDay(value: unknown): string {
  const numericDays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  if (typeof value === "number" && Number.isInteger(value)) {
    return numericDays[value] ?? `Day ${value}`;
  }
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    const namedDays: Record<string, string> = {
      sun: "Sun",
      sunday: "Sunday",
      mon: "Mon",
      monday: "Monday",
      tue: "Tue",
      tues: "Tue",
      tuesday: "Tuesday",
      wed: "Wed",
      wednesday: "Wednesday",
      thu: "Thu",
      thur: "Thu",
      thurs: "Thu",
      thursday: "Thursday",
      fri: "Fri",
      friday: "Friday",
      sat: "Sat",
      saturday: "Saturday",
    };
    return namedDays[normalized] ?? value;
  }
  return "Not assigned";
}

/** Format minute counts or clock strings for display, with a fallback for absent values. */
function formatClock(value: unknown): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    const minutes = Math.max(0, Math.trunc(value));
    return `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(
      minutes % 60,
    ).padStart(2, "0")}`;
  }
  if (typeof value === "string") {
    const match = value.match(/^(\d{1,2}):(\d{2})$/);
    if (match) {
      return `${match[1].padStart(2, "0")}:${match[2]}`;
    }
    return value || "Not assigned";
  }
  return "Not assigned";
}

/** Convert an H:MM or HH:MM string to minutes, returning null for other formats. */
function clockToMinutes(value: string): number | null {
  const match = value.match(/^(\d{1,2}):(\d{2})$/);
  if (!match) return null;
  return Number(match[1]) * 60 + Number(match[2]);
}

/** Append a minute unit to finite numeric durations or display the supplied value. */
function formatDuration(value: unknown): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    return `${value} min`;
  }
  return displayValue(value);
}

/** Add a numeric duration to a clock time, falling back when either cannot be used. */
function calculateEnd(start: string, duration: unknown): string {
  const startMinutes = clockToMinutes(start);
  if (startMinutes === null || typeof duration !== "number") {
    return "Not assigned";
  }
  return formatClock(startMinutes + duration);
}

/** Split a legacy CSV row while handling quoted commas and escaped double quotes. */
function parseCsvFields(line: string): string[] {
  const fields: string[] = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    if (character === '"') {
      if (quoted && line[index + 1] === '"') {
        field += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
    } else if (character === "," && !quoted) {
      fields.push(field);
      field = "";
    } else {
      field += character;
    }
  }
  fields.push(field);
  return fields;
}

/** Convert a legacy CSV assignment into display rows with room or lab meeting details. */
function legacyCsvMeetings(line: string): DisplayMeeting[] {
  const fields = parseCsvFields(line);
  const [course, faculty, room, lab, meetingText] = fields;
  if (fields.length < 5) {
    return [{
      course: line.trim() || "Not assigned",
      faculty: "Not assigned",
      resource: "Not assigned",
      resourceType: "Room",
      day: "Not assigned",
      start: "Not assigned",
      duration: "Not assigned",
      end: "Not assigned",
    }];
  }
  if (!meetingText) {
    return [{
      course: displayValue(course),
      faculty: displayValue(faculty),
      resource: displayValue(room || lab),
      resourceType: lab ? "Lab" : "Room",
      day: "Not assigned",
      start: "Not assigned",
      duration: "Not assigned",
      end: "Not assigned",
    }];
  }

  return meetingText.split(",").map((meeting) => {
    const match = meeting.trim().match(
      /^([A-Za-z]{3})\s+(\d{1,2}:\d{2})-(\d{1,2}:\d{2})(\^)?(?:@online)?$/,
    );
    const isLabMeeting = Boolean(match?.[4]);
    const start = match?.[2] ?? "Not assigned";
    const end = match?.[3] ?? "Not assigned";
    const startMinutes = clockToMinutes(start);
    const endMinutes = clockToMinutes(end);
    return {
      course: displayValue(course),
      faculty: displayValue(faculty),
      resource: displayValue(isLabMeeting ? lab : room),
      resourceType: isLabMeeting ? "Lab" : "Room",
      day: match ? formatDay(match[1]) : "Not assigned",
      start,
      duration:
        startMinutes !== null && endMinutes !== null
          ? `${endMinutes - startMinutes} min`
          : "Not assigned",
      end,
    };
  });
}

/** Normalize structured or legacy assignments into display rows, including reserved rooms. */
function assignmentMeetings(value: unknown): DisplayMeeting[] {
  if (typeof value === "string") return legacyCsvMeetings(value);
  if (!isRecord(value)) {
    return [{
      course: displayValue(value),
      faculty: "Not assigned",
      resource: "Not assigned",
      resourceType: "Room",
      day: "Not assigned",
      start: "Not assigned",
      duration: "Not assigned",
      end: "Not assigned",
    }];
  }

  const course = displayValue(
    value.course ?? value.course_str ?? value.course_id ?? value.section,
  );
  const faculty = displayValue(value.faculty ?? value.instructor);
  const room = displayValue(value.room);
  const lab = displayValue(value.lab);
  const meetings = Array.isArray(value.times)
    ? value.times
    : Array.isArray(value.meetings)
      ? value.meetings
      : [value];
  const labIndex =
    typeof value.lab_index === "number" ? value.lab_index : null;

  return meetings.map((meeting, index) => {
    const record = isRecord(meeting) ? meeting : {};
    const isLabMeeting =
      labIndex === index || record.lab === true || (room === "Not assigned" && lab !== "Not assigned");
    const resource = isLabMeeting ? lab : room;
    const additionalResource =
      isLabMeeting &&
      value.reserve_room_during_lab === true &&
      room !== "Not assigned"
        ? room
        : undefined;
    const start = formatClock(record.start ?? record.start_time ?? value.start);
    const durationValue = record.duration ?? value.duration;
    const explicitEnd =
      record.end ?? record.end_time ?? record.stop ?? value.end;
    return {
      course,
      faculty,
      resource:
        record.delivery === "online"
          ? "Online"
          : displayValue(resource),
      resourceType: record.delivery === "online"
        ? "Delivery"
        : isLabMeeting
          ? "Lab"
          : "Room",
      additionalResource,
      day: formatDay(record.day ?? value.day),
      start,
      duration: formatDuration(durationValue),
      end:
        explicitEnd === undefined
          ? calculateEnd(start, durationValue)
          : formatClock(explicitEnd),
    };
  });
}

/** Flatten supported schedule containers into displayable course meetings. */
function scheduleMeetings(schedule: ScheduleData): DisplayMeeting[] {
  if (Array.isArray(schedule)) {
    return schedule.flatMap(assignmentMeetings);
  }
  if (!isRecord(schedule)) return [];

  const assignments = Array.isArray(schedule.courses)
    ? schedule.courses
    : Array.isArray(schedule.assignments)
      ? schedule.assignments
      : schedule.course !== undefined || schedule.course_id !== undefined
        ? [schedule]
        : [];
  return assignments.flatMap(assignmentMeetings);
}

/** Extract an API error detail or a readable fallback message. */
function errorMessage(error: unknown): string {
  if (axios.isAxiosError<{ detail?: string }>(error)) {
    return error.response?.data?.detail ?? error.message;
  }
  return error instanceof Error ? error.message : "An unexpected error occurred.";
}

/** Display, import, navigate, and export generated or imported schedules. */
export default function ScheduleViewer({
  isActive,
  onStatusChange,
}: {
  isActive: boolean;
  onStatusChange: (message: string) => void;
}) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [controller] = useState(createScheduleViewerController);
  const [schedules, setSchedules] = useState<ScheduleData[]>([]);
  const [sourceFilename, setSourceFilename] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [viewMode, setViewMode] = useState<ViewMode>("room");
  const [loading, setLoading] = useState(true);
  const [actionInProgress, setActionInProgress] = useState(false);
  const [error, setError] = useState("");
  const [confirmClearSchedules, setConfirmClearSchedules] = useState(false);

  useEffect(() => {
    if (!isActive) return;
    let active = true;
    setLoading(true);
    void controller.load()
      .then((result) => {
        if (!active) return;
        setSchedules(result.schedules);
        setSourceFilename(result.source_filename ?? null);
        setSelectedIndex((index) => index < result.schedules.length ? index : 0);
        setError("");
      })
      .catch((loadError: unknown) => {
        if (!active) return;
        const message = `Could not load available schedules: ${errorMessage(loadError)}`;
        setError(message);
        onStatusChange(message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [controller, isActive, onStatusChange]);

  const selectedSchedule = schedules[selectedIndex];
  const displayedMeetings = selectedSchedule
    ? scheduleMeetings(selectedSchedule)
    : [];
  const groups = new Map<string, DisplayMeeting[]>();
  displayedMeetings.forEach((meeting) => {
    if (viewMode === "room") {
      const resources = [
        { resource: meeting.resource, resourceType: meeting.resourceType },
        ...(meeting.additionalResource
          ? [{ resource: meeting.additionalResource, resourceType: "Room" }]
          : []),
      ];
      resources.forEach(({ resource, resourceType }) => {
        const groupName = `${resourceType}: ${resource}`;
        const groupedMeeting = { ...meeting, resource, resourceType };
        groups.set(groupName, [
          ...(groups.get(groupName) ?? []),
          groupedMeeting,
        ]);
      });
    } else {
      groups.set(meeting.faculty, [
        ...(groups.get(meeting.faculty) ?? []),
        meeting,
      ]);
    }
  });

  /** Import the selected JSON file, reset selection, and report progress or errors. */
  const handleImport = async (file: File | undefined) => {
    if (!file) return;
    setActionInProgress(true);
    setError("");
    onStatusChange(`Loading schedules from ${file.name}...`);
    try {
      const result = await controller.importFile(file);
      setSchedules(result.schedules);
      setSourceFilename(result.source_filename ?? file.name);
      setSelectedIndex(0);
      const message =
        `Loaded ${result.count} schedule(s) from ${file.name}. ` +
        "Schedules are ready to view.";
      onStatusChange(message);
      setError("");
    } catch (importError) {
      const message = `Could not load schedules: ${errorMessage(importError)}`;
      setError(message);
      onStatusChange(message);
    } finally {
      setActionInProgress(false);
    }
  };

  /** Clear stored schedules and viewer selection, reporting any request failure. */
  const clearSchedules = async () => {
    setActionInProgress(true);
    setError("");
    try {
      await controller.clear();
      setSchedules([]);
      setSourceFilename(null);
      setSelectedIndex(0);
      onStatusChange("Available schedules cleared.");
    } catch (clearError) {
      const message = `Could not clear schedules: ${errorMessage(clearError)}`;
      setError(message);
      onStatusChange(message);
    } finally {
      setActionInProgress(false);
    }
  };

  const handleClear = () => {
    setConfirmClearSchedules(true);
  };

  /** Download the selected schedule or complete collection and report the result. */
  const handleExport = (scope: "selected" | "all") => {
    setActionInProgress(true);
    setError("");
    try {
      const exportedSchedules =
        scope === "selected" && selectedSchedule
          ? [selectedSchedule]
          : scope === "all"
            ? schedules
            : [];
      if (exportedSchedules.length === 0) {
        throw new Error("No schedules are available to export.");
      }
      const filename = controller.exportJson(
        exportedSchedules,
        sourceFilename,
        scope === "selected" ? selectedIndex + 1 : undefined,
      );
      onStatusChange(
        `JSON export download started: ${filename}. Check your browser's downloads location.`,
      );
    } catch (exportError) {
      const message = `Could not export schedules: ${errorMessage(exportError)}`;
      setError(message);
      onStatusChange(message);
    } finally {
      setActionInProgress(false);
    }
  };

  const selectStyle = {
    minHeight: 30,
    padding: "4px 8px",
    border: "1px solid #808080",
    background: "white",
  };
  const tableStyle = {
    width: "100%",
    borderCollapse: "collapse" as const,
    textAlign: "left" as const,
  };
  const cellStyle = {
    padding: "7px 8px",
    border: "1px solid #808080",
    verticalAlign: "top" as const,
  };

  return (
    <section
      style={{
        minHeight: "100%",
        background: "white",
        border: "1px solid #cbd5e1",
        padding: 24,
        boxSizing: "border-box",
      }}
    >
      <h1 style={{ marginTop: 0, fontSize: 28 }}>Schedule Viewer</h1>
      <p>
        {schedules.length} available schedule{schedules.length === 1 ? "" : "s"}
        {selectedSchedule
          ? ` · Showing schedule ${selectedIndex + 1} of ${schedules.length}`
          : ""}
        {isRecord(selectedSchedule) && selectedSchedule.schedule_id !== undefined
          ? ` (ID ${displayValue(selectedSchedule.schedule_id)})`
          : ""}
      </p>

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: 8,
          marginBottom: 16,
        }}
      >
        <button
          type="button"
          onClick={() => fileInput.current?.click()}
          disabled={actionInProgress || loading}
        >
          Load JSON Schedules
        </button>
        <input
          ref={fileInput}
          type="file"
          accept=".json,application/json"
          aria-label="Choose schedule JSON file"
          onChange={(event) => {
            void handleImport(event.target.files?.[0]);
            event.currentTarget.value = "";
          }}
          style={{ display: "none" }}
        />
        <button
          type="button"
          onClick={() => handleExport("selected")}
          disabled={!selectedSchedule || actionInProgress || loading}
        >
          Export Selected JSON
        </button>
        <button
          type="button"
          onClick={() => handleExport("all")}
          disabled={schedules.length === 0 || actionInProgress || loading}
        >
          Export All JSON
        </button>
        <button
          type="button"
          onClick={() => void handleClear()}
          disabled={schedules.length === 0 || actionInProgress || loading}
        >
          Clear Schedules
        </button>
      </div>

      {error && (
        <p role="alert" style={{ padding: 10, border: "1px solid #800000" }}>
          {error}
        </p>
      )}
      {loading && <p role="status">Loading available schedules...</p>}
      <p>
        Exports are saved to your browser&apos;s configured downloads location.
      </p>

      {schedules.length > 0 && (
        <>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "center",
              gap: 8,
              marginBottom: 18,
            }}
          >
            <button
              type="button"
              onClick={() =>
                setSelectedIndex((index) => Math.max(0, index - 1))
              }
              disabled={selectedIndex === 0}
              aria-label="Previous schedule"
            >
              Previous
            </button>
            <label htmlFor="schedule-viewer-select">Schedule</label>
            <select
              id="schedule-viewer-select"
              value={selectedIndex}
              onChange={(event) => setSelectedIndex(Number(event.target.value))}
              style={selectStyle}
            >
              {schedules.map((schedule, index) => {
                const scheduleId =
                  isRecord(schedule) && schedule.schedule_id !== undefined
                    ? ` (ID ${displayValue(schedule.schedule_id)})`
                    : "";
                return (
                  <option key={index} value={index}>
                    Schedule {index + 1}{scheduleId}
                  </option>
                );
              })}
            </select>
            <button
              type="button"
              onClick={() =>
                setSelectedIndex((index) =>
                  Math.min(schedules.length - 1, index + 1),
                )
              }
              disabled={selectedIndex >= schedules.length - 1}
              aria-label="Next schedule"
            >
              Next
            </button>
          </div>

          <div
            role="group"
            aria-label="Schedule organization"
            style={{ display: "flex", gap: 8, marginBottom: 16 }}
          >
            <button
              type="button"
              aria-pressed={viewMode === "room"}
              onClick={() => setViewMode("room")}
            >
              View by Room / Lab
            </button>
            <button
              type="button"
              aria-pressed={viewMode === "faculty"}
              onClick={() => setViewMode("faculty")}
            >
              View by Faculty
            </button>
          </div>

          {displayedMeetings.length === 0 ? (
            <p role="status">
              This schedule contains no readable course assignments.
            </p>
          ) : (
            [...groups.entries()].map(([groupName, meetings]) => (
              <section
                key={groupName}
                aria-label={groupName}
                style={{ marginBottom: 20, padding: 12 }}
              >
                <h2 style={{ marginBottom: 10, fontSize: 18 }}>
                  {viewMode === "room" ? "Physical resource" : "Faculty"}:{" "}
                  {groupName}
                </h2>
                <div style={{ overflowX: "auto" }}>
                  <table style={tableStyle}>
                    <thead>
                      <tr>
                        {[
                          "Course / Section",
                          "Faculty",
                          "Room / Lab",
                          "Day",
                          "Start",
                          "Duration",
                          "End",
                        ].map((heading) => (
                          <th key={heading} scope="col" style={cellStyle}>
                            {heading}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {meetings.map((meeting, index) => (
                        <tr key={`${groupName}-${index}`}>
                          <td style={cellStyle}>{meeting.course}</td>
                          <td style={cellStyle}>{meeting.faculty}</td>
                          <td style={cellStyle}>
                            {meeting.resourceType}: {meeting.resource}
                            {viewMode === "faculty" &&
                              meeting.additionalResource &&
                              `; Room: ${meeting.additionalResource}`}
                          </td>
                          <td style={cellStyle}>{meeting.day}</td>
                          <td style={cellStyle}>{meeting.start}</td>
                          <td style={cellStyle}>{meeting.duration}</td>
                          <td style={cellStyle}>{meeting.end}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            ))
          )}
        </>
      )}
      {!loading && schedules.length === 0 && (
        <p role="status">
          No schedules are available. Generate schedules or load a schedule JSON
          file to view them.
        </p>
      )}
      {confirmClearSchedules && (
        <RetroConfirmDialog
          title="Clear Available Schedules"
          message={`Clear all ${schedules.length} available schedule(s)? This cannot be undone.`}
          confirmLabel="Clear Schedules"
          onCancel={() => setConfirmClearSchedules(false)}
          onConfirm={() => {
            setConfirmClearSchedules(false);
            void clearSchedules();
          }}
        />
      )}
    </section>
  );
}
