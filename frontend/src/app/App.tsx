import { RouterProvider } from "react-router-dom";
import { TripProvider } from "../trip/TripProvider";
import { ThemeProvider } from "../theme/ThemeProvider";
import { router } from "./router";

export function App() {
  return (
    <ThemeProvider>
      <TripProvider>
        <RouterProvider router={router} />
      </TripProvider>
    </ThemeProvider>
  );
}
