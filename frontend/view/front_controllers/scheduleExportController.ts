import { exportScheduleCsv } from "../api";

export async function exportScheduleCsvFile(): Promise<void> {
  const { blob, filename } = await exportScheduleCsv();
  const url = URL.createObjectURL(blob);
  const downloadLink = document.createElement("a");
  downloadLink.href = url;
  downloadLink.download = filename;
  downloadLink.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
