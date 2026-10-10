export type ConfigTableRow = Record<string, string>;
export type ConfigTables = Record<string, ConfigTableRow[]>;

export const configMenus = [
  "Rooms",
  "Labs",
  "Courses",
  "Faculty",
  "Timeslots",
  "Class Patterns",
];

export const configTableColumns: Record<string, string[]> = {
  Rooms: ["Name", "Capacity", "Features", "Times"],
  Labs: ["Name", "Capacity", "Features", "Times"],
  Courses: [
    "Course ID",
    "Section ID",
    "Credits",
    "Capacity",
    "Room",
    "Lab",
    "Conflicts",
    "Faculty",
    "Alternate Faculty",
    "Modality",
    "Required Room Features",
    "Required Lab Features",
    "Reserve Room During Lab",
  ],
  Faculty: [
    "Name",
    "Maximum Credits",
    "Minimum Credits",
    "Unique Course Limit",
    "Maximum Days",
    "Mandatory Days",
    "Times",
    "Course Preferences",
    "Room Preferences",
    "Lab Preferences",
  ],
  Timeslots: ["Times", "Max Time Gap", "Min Time Overlap"],
  "Class Patterns": ["Credits", "Meetings", "Disabled", "Start Time"],
};

const sectionCollections: Record<string, string> = {
  Rooms: "rooms",
  Labs: "labs",
  Courses: "courses",
  Faculty: "faculty",
};

const numericFields: Record<string, string[]> = {
  Rooms: ["Capacity"],
  Labs: ["Capacity"],
  Courses: ["Credits", "Capacity"],
  Faculty: [
    "Maximum Credits",
    "Minimum Credits",
    "Unique Course Limit",
    "Maximum Days",
  ],
  Timeslots: ["Max Time Gap", "Min Time Overlap"],
  "Class Patterns": ["Credits"],
};

const structuredFields: Record<string, string[]> = {
  Rooms: ["Features", "Times"],
  Labs: ["Features", "Times"],
  Courses: [
    "Room",
    "Lab",
    "Conflicts",
    "Faculty",
    "Alternate Faculty",
    "Required Room Features",
    "Required Lab Features",
  ],
  Faculty: [
    "Mandatory Days",
    "Times",
    "Course Preferences",
    "Room Preferences",
    "Lab Preferences",
  ],
  Timeslots: ["Times"],
  "Class Patterns": ["Meetings"],
};

const optionalFields: Record<string, string[]> = {
  Rooms: ["Features", "Times"],
  Labs: ["Features", "Times"],
  Courses: [
    "Section ID",
    "Lab",
    "Alternate Faculty",
    "Modality",
    "Required Room Features",
    "Required Lab Features",
    "Reserve Room During Lab",
  ],
  Faculty: [
    "Maximum Days",
    "Mandatory Days",
    "Course Preferences",
    "Room Preferences",
    "Lab Preferences",
  ],
  Timeslots: ["Max Time Gap", "Min Time Overlap"],
  "Class Patterns": ["Disabled", "Start Time"],
};

export function asObject(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function cellValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  return typeof value === "string" ? value : JSON.stringify(value);
}

function toTableRows(menu: string, values: unknown): ConfigTableRow[] {
  if (!Array.isArray(values)) return [];
  const columns = configTableColumns[menu];
  return values.map((value) => {
    const source = asObject(value);
    return Object.fromEntries(
      columns.map((column) => [
        column,
        cellValue(source[column.toLowerCase().replaceAll(" ", "_")]),
      ]),
    );
  });
}

export function getConfigTableRows(configValue: unknown): ConfigTables {
  const root = asObject(configValue);
  const config = asObject(root.config);
  const timeSlotConfig = asObject(root.time_slot_config);

  return {
    Rooms: toTableRows("Rooms", config.rooms),
    Labs: toTableRows("Labs", config.labs),
    Courses: toTableRows("Courses", config.courses),
    Faculty: toTableRows("Faculty", config.faculty),
    Timeslots: toTableRows("Timeslots", [timeSlotConfig]),
    "Class Patterns": toTableRows("Class Patterns", timeSlotConfig.classes),
  };
}

function parseCellValue(menu: string, column: string, value: string): unknown {
  if (value === "" && column === "Section ID") return null;
  if (numericFields[menu]?.includes(column) && value.trim() !== "") {
    return Number(value);
  }
  if (
    (menu === "Courses" && column === "Reserve Room During Lab") ||
    (menu === "Class Patterns" && column === "Disabled")
  ) {
    return value === "true";
  }
  if (!structuredFields[menu]?.includes(column)) return value;
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

function toConfigObjects(
  menu: string,
  rows: ConfigTableRow[],
  originalValues: unknown = [],
): Record<string, unknown>[] {
  const originalRows = Array.isArray(originalValues) ? originalValues : [];
  return rows.map((row, index) => {
    const output = { ...asObject(originalRows[index]) };
    for (const column of configTableColumns[menu]) {
      const key = column.toLowerCase().replaceAll(" ", "_");
      const value = row[column] ?? "";
      if (
        optionalFields[menu]?.includes(column) &&
        (value === "" || value === null)
      ) {
        delete output[key];
      } else {
        output[key] = parseCellValue(menu, column, value);
      }
    }
    return output;
  });
}

export function applyConfigTableRows(
  originalConfig: unknown,
  tables: ConfigTables,
): Record<string, unknown> {
  const root = { ...asObject(originalConfig) };
  const config = { ...asObject(root.config) };

  for (const [menu, collection] of Object.entries(sectionCollections)) {
    config[collection] = toConfigObjects(
      menu,
      tables[menu] ?? [],
      config[collection],
    );
  }

  const originalTimeSlotConfig = asObject(root.time_slot_config);
  const timeslotRow = (tables.Timeslots ?? [])[0] ?? {};
  const timeSlotConfig = {
    ...originalTimeSlotConfig,
    ...toConfigObjects("Timeslots", [timeslotRow], [originalTimeSlotConfig])[0],
    classes: toConfigObjects(
      "Class Patterns",
      tables["Class Patterns"] ?? [],
      originalTimeSlotConfig.classes,
    ),
  };

  return { ...root, config, time_slot_config: timeSlotConfig };
}
