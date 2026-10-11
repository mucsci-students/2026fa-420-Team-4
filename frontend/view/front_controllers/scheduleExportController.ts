import {
  exportSchedule,
  type ScheduleData,
  type ScheduleExportFormat,
} from "../api";

/** Start a browser download and release its temporary object URL. */
function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const downloadLink = document.createElement("a");
  downloadLink.href = url;
  downloadLink.download = filename;
  downloadLink.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Download schedules in the requested format and release the temporary object URL. */
export async function exportScheduleFile(
  format: ScheduleExportFormat,
): Promise<void> {
  const { blob, filename } = await exportSchedule(format);
  downloadBlob(blob, filename);
}

/** Download the supplied schedules as UTF-8 JSON using the requested source-based filename. */
export function exportSchedulesAsJson(
  schedules: ScheduleData[],
  sourceFilename: string | null | undefined,
  scheduleNumber?: number,
): string {
  const content = JSON.stringify(schedules, null, 2);
  if (content === undefined) {
    throw new Error("Schedule data could not be serialized as JSON.");
  }

  const sourceBasename = (sourceFilename ?? "")
    .replaceAll("\\", "/")
    .split("/")
    .pop() ?? "";
  const sourceStem = sourceBasename.replace(/\.[^.]*$/, "");
  const safeStem = Array.from(sourceStem, (character) =>
    /[<>:"/\\|?*]/.test(character) || character.charCodeAt(0) < 32
      ? "_"
      : character,
  )
    .join("")
    .trim()
    .replace(/[. ]+$/, "");
  const filename = scheduleNumber === undefined
    ? `${safeStem || "schedules"}_allschedules.json`
    : `${safeStem || "schedules"}_schedule${scheduleNumber}.json`;
  const blob = new Blob([`${content}\n`], {
    type: "application/json;charset=utf-8",
  });
  downloadBlob(blob, filename);
  return filename;
}
