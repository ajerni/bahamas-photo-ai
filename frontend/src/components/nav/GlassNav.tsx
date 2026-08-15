import { NavLink } from "react-router-dom";
import { BookOpen, Images, Map, MessageCircle, Menu, Clock3 } from "lucide-react";
import { useTrip } from "../../trip/TripProvider";
import { HealthDot } from "./HealthDot";
import { ThemeToggle } from "./ThemeToggle";
import { JobProgressBar } from "./JobProgressBar";

const NAV_ITEMS = [
  { to: "/story", label: "Story", icon: BookOpen },
  { to: "/photos", label: "Photos", icon: Images },
  { to: "/timeline", label: "Timeline", icon: Clock3 },
  { to: "/map", label: "Map", icon: Map },
  { to: "/chat", label: "Chat", icon: MessageCircle }
];

export function GlassNav({ onOpenMenu }: { onOpenMenu: () => void }) {
  const { trip } = useTrip();

  return (
    <header className="glass-nav">
      <div className="glass-nav-inner">
        <div className="nav-brand">
          <h1>{trip?.title ?? "Travel memories"}</h1>
          {trip?.description ? <p>{trip.description}</p> : null}
        </div>

        <nav className="nav-links" aria-label="Trip views">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => (isActive ? "active" : "")}>
              <Icon size={16} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="nav-actions">
          <HealthDot />
          <ThemeToggle />
          <button type="button" className="burger" onClick={onOpenMenu} aria-label="Open menu">
            <Menu size={20} aria-hidden="true" />
          </button>
        </div>
      </div>
      <JobProgressBar />
    </header>
  );
}
