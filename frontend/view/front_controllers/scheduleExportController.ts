import { exportScheduleCsv } from "../api";

export async function exportScheduleCsvFile(): Promise<void> {
  const csv = await exportScheduleCsv();
  const url = URL.createObjectURL(csv);
  const downloadLink = document.createElement("a");
  downloadLink.href = url;
  downloadLink.download = "schedules.csv";
  downloadLink.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
