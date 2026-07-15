const dateFormatter = new Intl.DateTimeFormat("es-CL", {
  weekday: "long",
  day: "numeric",
  month: "long",
});

const compactDateFormatter = new Intl.DateTimeFormat("es-CL", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

const timeFormatter = new Intl.DateTimeFormat("es-CL", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

function toDate(value: string | number | Date): Date | null {
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatLongDate(value: string | number | Date): string {
  const date = toDate(value);
  if (!date) {
    return "Fecha no disponible";
  }

  return dateFormatter.format(date);
}

export function formatCompactDate(value: string | number | Date): string {
  const date = toDate(value);
  if (!date) {
    return "Fecha no disponible";
  }

  return compactDateFormatter.format(date).replace(".", "");
}

export function formatTime(value: string | number | Date): string {
  const date = toDate(value);
  if (!date) {
    return "--:-- h";
  }

  return `${timeFormatter.format(date)} h`;
}

export function formatDateTime(value: string | number | Date): string {
  const date = toDate(value);
  if (!date) {
    return "Fecha no disponible";
  }

  return `${formatCompactDate(date)} - ${formatTime(date)}`;
}
