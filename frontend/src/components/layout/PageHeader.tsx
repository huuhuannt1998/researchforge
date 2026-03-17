interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  back?: React.ReactNode;
}

export default function PageHeader({
  title,
  subtitle,
  action,
  back,
}: PageHeaderProps) {
  return (
    <div className="border-b border-gray-200 bg-white px-8 py-5">
      {back && <div className="mb-2">{back}</div>}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>
          )}
        </div>
        {action && <div>{action}</div>}
      </div>
    </div>
  );
}
