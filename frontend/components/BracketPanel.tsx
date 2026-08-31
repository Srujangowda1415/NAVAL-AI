import type { ReactNode } from "react";
import clsx from "clsx";

export default function BracketPanel({
  children,
  className,
  as: Component = "div",
}: {
  children: ReactNode;
  className?: string;
  as?: "div" | "section" | "article";
}) {
  return <Component className={clsx("bracket-panel p-6", className)}>{children}</Component>;
}
