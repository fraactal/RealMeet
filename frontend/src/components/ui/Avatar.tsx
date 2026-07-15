import { cn } from "../../utils/cn";

interface AvatarProps {
  name?: string | null;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-14 w-14 text-lg",
};

export function Avatar({ className, name, size = "md" }: AvatarProps) {
  const initials =
    name
      ?.split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("") || "RM";

  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full bg-brand-100 font-bold text-brand-700",
        sizeClasses[size],
        className,
      )}
      aria-hidden="true"
    >
      {initials}
    </span>
  );
}
