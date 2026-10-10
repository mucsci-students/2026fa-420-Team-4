export interface OpenedConfigFile {
  file: File;
  config: unknown;
}

declare global {
  interface Window {
    showOpenFilePicker?: (options?: {
      types?: Array<{
        description?: string;
        accept: Record<string, string[]>;
      }>;
      multiple?: boolean;
    }) => Promise<FileSystemFileHandle[]>;
  }
}

export function createConfigFileController() {
  let handle: FileSystemFileHandle | null = null;

  return {
    async open(): Promise<OpenedConfigFile | null> {
      if (!window.showOpenFilePicker) {
        throw new Error(
          "Opening a file for in-place editing requires a browser that supports the File System Access API.",
        );
      }

      const [selectedHandle] = await window.showOpenFilePicker({
        multiple: false,
        types: [
          {
            description: "JSON configuration",
            accept: { "application/json": [".json"] },
          },
        ],
      });
      if (!selectedHandle) return null;

      const file = await selectedHandle.getFile();
      const config: unknown = JSON.parse(await file.text());
      handle = selectedHandle;
      return { file, config };
    },
    clear(): void {
      handle = null;
    },
    async save(config: unknown): Promise<void> {
      if (!handle) {
        throw new Error("Choose a configuration file before saving.");
      }

      const writable = await handle.createWritable();
      try {
        await writable.write(`${JSON.stringify(config, null, 2)}\n`);
        await writable.close();
      } catch (error) {
        await writable.abort();
        throw error;
      }
    },
  };
}
