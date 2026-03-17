import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export default function Card({
  children,
  className,
  onClick,
  hoverable = false,
}: CardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "bg-white rounded-xl border border-gray-200 shadow-sm",
        hoverable &&
          "cursor-pointer hover:border-gray-300 hover:shadow-md transition-all duration-150",
        onClick && "cursor-pointer",
        className
      )}
    >
      {children}
    </div>
  );
}
