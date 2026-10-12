function humanizePath(path: string): string {
  if (!path) return "Configuration";

  return path
    .split("/")
    .filter(Boolean)
    .map((part) => {
      const decoded = part.replaceAll("~1", "/").replaceAll("~0", "~");
      if (/^\d+$/.test(decoded)) return `Item ${Number(decoded) + 1}`;
      return decoded
        .replaceAll("_", " ")
        .replace(/\b\w/g, (letter) => letter.toUpperCase());
    })
    .join(" → ");
}

function humanizeMessage(message: string): string {
  const normalized = message.trim().replace(/\.$/, "");
  const knownMessages: Record<string, string> = {
    "Field required": "This field is required.",
    "Input should be a valid integer": "Enter a whole number.",
    "Input should be a valid number": "Enter a number.",
    "Input should be a valid string": "Enter text.",
    "Input should be a valid boolean": "Choose true or false.",
    "Input should be a valid list": "Provide a list of values.",
    "Input should be a valid dictionary": "Provide an object with named fields.",
  };
  return knownMessages[normalized] ?? `${normalized}.`;
}

export function formatConfigError(error: string): string {
  const diagnostic = error.match(/^\[(?:SCHED\.CONFIG\.[^\]]+)\]\s*([^:]*):\s*(.*)$/);
  if (diagnostic) {
    return `${humanizePath(diagnostic[1])}: ${humanizeMessage(diagnostic[2])}`;
  }

  if (error.startsWith("Invalid JSON format")) {
    return "This file isn't valid JSON. Check its syntax and try again.";
  }

  return error.replace(/^Configuration error:\s*/, "");
}

export function formatConfigErrors(errors: string[]): string[] {
  return errors.map(formatConfigError);
}
