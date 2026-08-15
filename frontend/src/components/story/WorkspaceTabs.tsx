import { BookOpenText, Compass, MessageCircle, SlidersHorizontal } from "lucide-react";

export type WorkspaceTab = "read" | "explore" | "refine" | "ask";

type WorkspaceTabsProps = {
  activeTab: WorkspaceTab;
  onChange: (tab: WorkspaceTab) => void;
};

const tabs = [
  { id: "read", label: "Read", icon: BookOpenText },
  { id: "explore", label: "Explore", icon: Compass },
  { id: "refine", label: "Refine", icon: SlidersHorizontal },
  { id: "ask", label: "Ask", icon: MessageCircle }
] satisfies Array<{
  id: WorkspaceTab;
  label: string;
  icon: typeof BookOpenText;
}>;

export function WorkspaceTabs({ activeTab, onChange }: WorkspaceTabsProps) {
  return (
    <nav className="workspace-tabs" aria-label="Trip workspace">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            type="button"
            className={tab.id === activeTab ? "active" : ""}
            onClick={() => onChange(tab.id)}
          >
            <Icon size={16} aria-hidden="true" />
            <span>{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
