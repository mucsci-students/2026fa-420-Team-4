import { exportSchedule, type ScheduleExportFormat } from "../api";

export async function exportScheduleFile(
  format: ScheduleExportFormat,
): Promise<void> {
  const { blob, filename } = await exportSchedule(format);
  const url = URL.createObjectURL(blob);
  const downloadLink = document.createElement("a");
  downloadLink.href = url;
  downloadLink.download = filename;
  downloadLink.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
