import type { AvailableSlot } from "../../types";
import { formatTime } from "../../utils/dates";
import { cn } from "../../utils/cn";

interface SlotPickerProps {
  disabled?: boolean;
  isPending?: boolean;
  onSelect: (slot: AvailableSlot) => void;
  selectedSlotStart?: string | null;
  slots: AvailableSlot[];
}

export function SlotPicker({ disabled = false, isPending = false, onSelect, selectedSlotStart, slots }: SlotPickerProps) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
      {slots.map((slot) => {
        const isSelected = selectedSlotStart === slot.start_datetime;
        return (
          <button
            className={cn(
              "min-h-11 rounded-md border px-3 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60",
              isSelected
                ? "border-brand-700 bg-brand-700 text-white"
                : "border-slate-200 bg-white text-ink-700 hover:border-brand-300 hover:bg-brand-50",
            )}
            disabled={disabled || isPending}
            key={slot.start_datetime}
            onClick={() => onSelect(slot)}
            type="button"
          >
            {formatTime(slot.start_datetime)}
          </button>
        );
      })}
    </div>
  );
}
