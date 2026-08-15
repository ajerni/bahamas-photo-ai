import { RouterProvider } from "react-router-dom";
import { TripProvider } from "../trip/TripProvider";
import { router } from "./router";

export function App() {
  return (
    <TripProvider>
      <RouterProvider router={router} />
    </TripProvider>
  );
}
