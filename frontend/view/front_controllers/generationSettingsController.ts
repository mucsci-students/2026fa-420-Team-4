export const DEFAULT_GENERATION_LIMIT = 10;

export const VALID_OPTIMIZER_FLAGS = [
  "faculty_course",
  "faculty_room",
  "faculty_lab",
  "same_room",
  "same_lab",
  "pack_rooms",
  "pack_labs",
] as const;

export interface GenerationSettings {
  limit: number;
  optimizer_flags: string[];
}

/** Create a controller that retains a loaded configuration and serializes updated generation settings. */
export function createGenerationSettingsController() {
  let config: Record<string, unknown> | null = null;
  let fileName = "";

  const requireConfig = () => {
    if (!config || !fileName) {
      throw new Error("Choose a configuration file before updating settings.");
    }
    return config;
  };

  /** Reject limits that are not positive safe integers, allowing zero only when requested. */
  const validateLimit = (limit: number, allowZero = false) => {
    if (!Number.isSafeInteger(limit) || limit < (allowZero ? 0 : 1)) {
      const requirement = allowZero
        ? "a non-negative integer"
        : "a positive integer";
      throw new Error(`Generation limit must be ${requirement}.`);
    }
  };

  const validateFlags = (flags: string[]) => {
    if (!Array.isArray(flags)) {
      throw new Error("Optimizer flags must be an array.");
    }
    const invalidFlags = flags.filter(
      (flag) => !VALID_OPTIMIZER_FLAGS.some((validFlag) => validFlag === flag),
    );
    if (invalidFlags.length > 0) {
      throw new Error(`Invalid optimizer flag(s): ${invalidFlags.join(", ")}.`);
    }
  };

  return {
    async open(file: File): Promise<GenerationSettings> {
      const parsed: unknown = JSON.parse(await file.text());
      if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("Configuration JSON must contain an object.");
      }

      const nextConfig = parsed as Record<string, unknown>;
      const limit = nextConfig.limit ?? DEFAULT_GENERATION_LIMIT;
      const optimizerFlags = nextConfig.optimizer_flags ?? [];
      if (typeof limit !== "number") {
        throw new Error("Configuration limit must be a number.");
      }
      validateLimit(limit);
      if (!Array.isArray(optimizerFlags) ||
          optimizerFlags.some((flag) => typeof flag !== "string")) {
        throw new Error("Configuration optimizer_flags must be an array of strings.");
      }
      validateFlags(optimizerFlags);

      config = nextConfig;
      fileName = file.name;
      return { limit, optimizer_flags: [...optimizerFlags] };
    },
    clear(): void {
      config = null;
      fileName = "";
    },
    /** Set the loaded configuration limit, allowing zero to clear schedules; throw if invalid or unloaded. */
    setLimit(limit: number): void {
      validateLimit(limit, true);
      requireConfig().limit = limit;
    },
    setOptimizerFlags(flags: string[]): void {
      validateFlags(flags);
      requireConfig().optimizer_flags = [...flags];
    },
    toFile(): File {
      const updatedConfig = requireConfig();
      return new File(
        [`${JSON.stringify(updatedConfig, null, 2)}\n`],
        fileName,
        { type: "application/json" },
      );
    },
  };
}
