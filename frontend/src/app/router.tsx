import { createBrowserRouter, Navigate } from "react-router-dom";
import { RootLayout } from "./RootLayout";
import { StoryPage } from "../routes/StoryPage";
import { PhotosPage } from "../routes/PhotosPage";
import { TimelinePage } from "../routes/TimelinePage";
import { MapPage } from "../routes/MapPage";
import { ChatPage } from "../routes/ChatPage";
import { PhotoDetailPage } from "../routes/PhotoDetailPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    children: [
      { index: true, element: <Navigate to="/story" replace /> },
      { path: "story", element: <StoryPage /> },
      { path: "photos", element: <PhotosPage /> },
      { path: "photos/:photoId", element: <PhotoDetailPage /> },
      { path: "timeline", element: <TimelinePage /> },
      { path: "map", element: <MapPage /> },
      { path: "chat", element: <ChatPage /> },
      { path: "*", element: <Navigate to="/story" replace /> }
    ]
  }
]);
