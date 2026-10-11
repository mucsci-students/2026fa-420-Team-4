import {
  clearAvailableSchedules,
  getAvailableSchedules,
  importScheduleFile,
} from "../api";
import { exportScheduleFile } from "./scheduleExportController";

/** Coordinate schedule viewer requests and downloads. */
export function createScheduleViewerController() {
  return {
    load: getAvailableSchedules,
    importFile: importScheduleFile,
    clear: clearAvailableSchedules,
    exportJson: () => exportScheduleFile("json"),
  };
}
