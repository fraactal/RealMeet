import { cn } from "../../utils/cn";

export type IconName =
  | "calendar"
  | "chart"
  | "check"
  | "clock"
  | "dashboard"
  | "filter"
  | "logout"
  | "menu"
  | "payment"
  | "search"
  | "settings"
  | "user"
  | "users"
  | "x";

const paths: Record<IconName, string[]> = {
  calendar: ["M7 3v3M17 3v3M4 9h16", "M5 5h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Z"],
  chart: ["M4 19V5", "M4 19h16", "M8 16v-5", "M12 16V8", "M16 16v-8"],
  check: ["m5 12 4 4L19 6"],
  clock: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z", "M12 7v5l3 2"],
  dashboard: ["M4 5h7v7H4Z", "M13 5h7v4h-7Z", "M13 11h7v8h-7Z", "M4 14h7v5H4Z"],
  filter: ["M4 5h16", "M7 12h10", "M10 19h4"],
  logout: ["M10 17l5-5-5-5", "M15 12H3", "M21 5v14"],
  menu: ["M4 6h16", "M4 12h16", "M4 18h16"],
  payment: ["M4 7h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1Z", "M3 10h18", "M7 15h5"],
  search: ["M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14Z", "m16 16 4 4"],
  settings: ["M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z", "M19 12h2M3 12h2M12 3v2M12 19v2M17 5l-1.5 1.5M6.5 17.5 5 19M19 19l-1.5-1.5M6.5 6.5 5 5"],
  user: ["M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z", "M4 20a8 8 0 0 1 16 0"],
  users: ["M9 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z", "M2 20a7 7 0 0 1 14 0", "M17 8a3 3 0 0 1 0 6", "M18 17a5 5 0 0 1 4 3"],
  x: ["M6 6l12 12", "M18 6 6 18"],
};

interface IconProps {
  name: IconName;
  className?: string;
  title?: string;
}

export function Icon({ className, name, title }: IconProps) {
  return (
    <svg
      aria-hidden={title ? undefined : "true"}
      aria-label={title}
      className={cn("h-5 w-5", className)}
      fill="none"
      role={title ? "img" : undefined}
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
      viewBox="0 0 24 24"
    >
      {paths[name].map((d) => (
        <path d={d} key={d} />
      ))}
    </svg>
  );
}
