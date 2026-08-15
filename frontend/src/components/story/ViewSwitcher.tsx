import { Images, Map, Rows3 } from "lucide-react";

export type ExploreView = "timeline" | "map" | "photos";

type ViewSwitcherProps = {
  activeView: ExploreView;
  photoCount: number;
  onChange: (view: ExploreView) => void;
};

const views = [
  {
    id: "timeline",
    label: "Timeline",
    description: "Sequence",
    icon: Rows3
  },
  {
    id: "map",
    label: "Map",
    description: "Places",
    icon: Map
  },
  {
    id: "photos",
    label: "Photos",
    description: "Gallery",
    icon: Images
  }
] satisfies Array<{
  id: ExploreView;
  label: string;
  description: string;
  icon: typeof Rows3;
}>;

export function ViewSwitcher({
  activeView,
  photoCount,
  onChange
}: ViewSwitcherProps) {
  return (
    <nav className="view-switcher" aria-label="Memory views">
      {views.map((view) => {
        const Icon = view.icon;
        return (
          <button
            key={view.id}
            type="button"
            className={view.id === activeView ? "active" : ""}
            onClick={() => onChange(view.id)}
          >
            <Icon size={18} aria-hidden="true" />
            <span>
              <strong>{view.label}</strong>
              <em>{view.id === "photos" ? `${photoCount} photos` : view.description}</em>
            </span>
          </button>
        );
      })}
    </nav>
  );
}
