"use client";

import { useRef, KeyboardEvent } from "react";

interface Props {
  value: string[];
  onChange: (items: string[]) => void;
  placeholder?: string;
  disabled?: boolean;
  maxItems?: number;
}

/**
 * Reusable editable list of strings.
 * Each item is a text input; Enter or Tab adds the next item.
 * Backspace on an empty item removes it and focuses the previous one.
 */
export default function EditableList({
  value,
  onChange,
  placeholder = "Add an item…",
  disabled = false,
  maxItems = 50,
}: Props) {
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  function updateItem(index: number, text: string) {
    const next = [...value];
    next[index] = text;
    onChange(next);
  }

  function addItem(afterIndex?: number) {
    if (value.length >= maxItems) return;
    const idx = afterIndex !== undefined ? afterIndex + 1 : value.length;
    const next = [...value];
    next.splice(idx, 0, "");
    onChange(next);
    // Focus the new input on next tick
    requestAnimationFrame(() => {
      inputRefs.current[idx]?.focus();
    });
  }

  function removeItem(index: number) {
    if (value.length === 0) return;
    const next = value.filter((_, i) => i !== index);
    onChange(next);
    // Focus previous (or next) item
    requestAnimationFrame(() => {
      const focusIdx = Math.max(0, index - 1);
      inputRefs.current[focusIdx]?.focus();
    });
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>, index: number) {
    if (e.key === "Enter") {
      e.preventDefault();
      addItem(index);
    } else if (
      e.key === "Backspace" &&
      value[index] === "" &&
      value.length > 0
    ) {
      e.preventDefault();
      removeItem(index);
    }
  }

  const items = value.length > 0 ? value : [""];

  return (
    <div className="flex flex-col gap-1.5">
      {items.map((item, idx) => (
        <div key={idx} className="flex items-center gap-2 group">
          {/* Bullet */}
          <span className="text-indigo-500 text-sm shrink-0 select-none">•</span>

          {/* Input */}
          <input
            ref={(el) => {
              inputRefs.current[idx] = el;
            }}
            type="text"
            value={item}
            disabled={disabled}
            placeholder={placeholder}
            onChange={(e) => updateItem(idx, e.target.value)}
            onKeyDown={(e) => handleKeyDown(e, idx)}
            className="flex-1 rounded border border-transparent bg-transparent px-1 py-0.5 text-sm text-white placeholder-gray-600 focus:border-gray-600 focus:bg-gray-800 focus:outline-none transition-colors"
          />

          {/* Remove button — only visible when there's more than one real item */}
          {(value.length > 1 || (value.length === 1 && value[0] !== "")) && (
            <button
              type="button"
              onClick={() => removeItem(idx)}
              disabled={disabled}
              className="opacity-0 group-hover:opacity-100 focus:opacity-100 text-gray-600 hover:text-red-400 transition-opacity shrink-0 text-sm leading-none"
              tabIndex={-1}
              aria-label="Remove item"
            >
              ×
            </button>
          )}
        </div>
      ))}

      {/* Add row */}
      {!disabled && value.length < maxItems && (
        <button
          type="button"
          onClick={() => addItem(items.length - 1)}
          className="mt-0.5 flex items-center gap-1.5 text-xs text-gray-600 hover:text-indigo-400 transition-colors self-start"
        >
          <span className="text-base leading-none">+</span>
          Add item
        </button>
      )}
    </div>
  );
}
