import { type ReactNode, useId } from "react";

// Label, control frame, unit and error line shared by every form in the app.
// The control itself comes in as a render prop so it can take the generated id.
export function FieldShell({
  label,
  optional,
  unit,
  error,
  children,
}: {
  label: string;
  optional?: boolean;
  unit?: string;
  error?: string;
  children: (id: string) => ReactNode;
}) {
  const id = useId();
  return (
    <div className="field">
      <label className="field-label" htmlFor={id}>
        <span>{label}</span>
        {optional && <span className="field-opt">optional</span>}
      </label>
      <div className={error ? "control invalid" : "control"}>
        {children(id)}
        {unit && <span className="unit">{unit}</span>}
      </div>
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
