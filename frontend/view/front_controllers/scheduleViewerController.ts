import {
  clearAvailableSchedules,
  getAvailableSchedules,
  importScheduleFile,
  type ScheduleData,
} from "../api";
import { exportSchedulesAsJson } from "./scheduleExportController";

/** Coordinate schedule viewer requests and JSON downloads. */
export function createScheduleViewerController() {
  return {
    load: getAvailableSchedules,
    importFile: importScheduleFile,
    clear: clearAvailableSchedules,
    /** Download the selected schedule or full collection with a source-based JSON filename. */
    exportJson: (
      schedules: ScheduleData[],
      sourceFilename: string | null | undefined,
      scheduleNumber?: number,
    ) => exportSchedulesAsJson(schedules, sourceFilename, scheduleNumber),
  };
}
