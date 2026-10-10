export interface OpenedConfigFile {
  file: File;
  config: unknown;
}

export function createConfigFileController() {
  let fileName: string | null = null;

  return {
    async open(file: File): Promise<OpenedConfigFile> {
      const config: unknown = JSON.parse(await file.text());
      fileName = file.name;
      return { file, config };
    },
    clear(): void {
      fileName = null;
    },
    save(config: unknown): void {
      if (!fileName) {
        throw new Error("Choose a configuration file before saving.");
      }

      const blob = new Blob([`${JSON.stringify(config, null, 2)}\n`], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const downloadLink = document.createElement("a");
      downloadLink.href = url;
      downloadLink.download = fileName;
      downloadLink.click();
      URL.revokeObjectURL(url);
    },
  };
}
