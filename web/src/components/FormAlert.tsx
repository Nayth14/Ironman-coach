interface FormAlertProps {
  message: string | null;
  variant?: "error" | "success";
}

export function FormAlert({ message, variant = "error" }: FormAlertProps) {
  if (!message) return null;

  const styles =
    variant === "error"
      ? "text-red-600 bg-red-50 border-red-200"
      : "text-green-700 bg-green-50 border-green-200";

  return (
    <div className={`text-sm border rounded-xl px-4 py-3 ${styles}`}>
      {message}
    </div>
  );
}
