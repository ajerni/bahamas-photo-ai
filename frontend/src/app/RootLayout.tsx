import { useState } from "react";
import { Outlet } from "react-router-dom";
import { GlassNav } from "../components/nav/GlassNav";
import { BurgerMenu } from "../components/nav/BurgerMenu";
import { useTrip } from "../trip/TripProvider";

export function RootLayout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { loading, error } = useTrip();

  return (
    <div className="app-shell">
      <GlassNav onOpenMenu={() => setMenuOpen(true)} />

      <main className="app-main">
        {error ? (
          <p className="app-error">{error}</p>
        ) : loading ? (
          <p className="app-loading">Opening the trip…</p>
        ) : (
          <Outlet />
        )}
      </main>

      <BurgerMenu open={menuOpen} onClose={() => setMenuOpen(false)} />
    </div>
  );
}
