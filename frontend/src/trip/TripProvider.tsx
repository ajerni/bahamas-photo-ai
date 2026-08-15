import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode
} from "react";
import {
  analyzePhoto,
  createTrip,
  deleteAllTripPhotos,
  deletePhoto,
  getHealth,
  getJob,
  getLatestTripJob,
  getTrip,
  importPhotos,
  listTrips,
  retryJob,
  updatePhoto,
  updateTrip,
  updateTripMemory,
  clearTripAnalysis,
  clearTripQuestions,
  type AnalysisJob,
  type HealthResponse,
  type Photo,
  type PhotoImportResponse,
  type TripDetail,
  type TripMemory
} from "../api/client";
import { isJobActive } from "./jobStatus";

const DEFAULT_TRIP_TITLE = "Bahamas 2026";
const POLL_INTERVAL_MS = 1200;

type TripContextValue = {
  trip: TripDetail | null;
  photos: Photo[];
  memory: TripMemory | null;
  health: HealthResponse | null;
  healthError: string | null;
  job: AnalysisJob | null;
  loading: boolean;
  error: string | null;
  /** Set when a photo is re-analyzed on its own, since that leaves the trip story stale. */
  storyStale: boolean;
  refresh: () => Promise<void>;
  upload: (files: FileList | File[]) => Promise<PhotoImportResponse>;
  savePhoto: (
    photoId: number,
    payload: Parameters<typeof updatePhoto>[1]
  ) => Promise<void>;
  removePhoto: (photoId: number) => Promise<void>;
  reanalyzePhoto: (photoId: number) => Promise<void>;
  saveTrip: (payload: Parameters<typeof updateTrip>[1]) => Promise<void>;
  saveMemory: (payload: Parameters<typeof updateTripMemory>[1]) => Promise<void>;
  removeAllPhotos: () => Promise<void>;
  clearMemories: () => Promise<void>;
  clearQuestions: () => Promise<void>;
  dismissJob: () => void;
  retryFailedJob: () => Promise<void>;
};

const TripContext = createContext<TripContextValue | null>(null);

export function useTrip(): TripContextValue {
  const value = useContext(TripContext);
  if (value === null) {
    throw new Error("useTrip must be used inside TripProvider");
  }
  return value;
}

export function TripProvider({ children }: { children: ReactNode }) {
  const [trip, setTrip] = useState<TripDetail | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [storyStale, setStoryStale] = useState(false);
  const tripIdRef = useRef<number | null>(null);
  const resolvingRef = useRef(false);

  const refresh = useCallback(async () => {
    const tripId = tripIdRef.current;
    if (tripId === null) {
      return;
    }
    setTrip(await getTrip(tripId));
  }, []);

  // Resolve the single trip once. The ref guards against StrictMode's double
  // effect, which would otherwise create two trips on a fresh database.
  useEffect(() => {
    if (resolvingRef.current) {
      return;
    }
    resolvingRef.current = true;

    (async () => {
      try {
        const trips = await listTrips();
        const resolved = trips[0] ?? (await createTrip({ title: DEFAULT_TRIP_TITLE }));
        tripIdRef.current = resolved.id;
        setTrip(await getTrip(resolved.id));
        setJob(await getLatestTripJob(resolved.id));
      } catch (cause) {
        setError((cause as Error).message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    getHealth()
      .then((payload) => {
        setHealth(payload);
        setHealthError(null);
      })
      .catch((cause: Error) => {
        setHealth(null);
        setHealthError(cause.message);
      });
  }, []);

  useEffect(() => {
    if (!isJobActive(job)) {
      return;
    }
    const timer = window.setInterval(async () => {
      try {
        const next = await getJob(job!.id);
        setJob(next);
        // Pull in photos as their memories land, not just at the end.
        if (next.completed_steps !== job!.completed_steps || !isJobActive(next)) {
          await refresh();
        }
        if (next.status === "completed") {
          setStoryStale(false);
        }
      } catch {
        // A transient poll failure shouldn't tear down the job UI.
      }
    }, POLL_INTERVAL_MS);

    return () => window.clearInterval(timer);
  }, [job, refresh]);

  const value = useMemo<TripContextValue>(() => {
    const tripId = () => {
      const id = tripIdRef.current;
      if (id === null) {
        throw new Error("Trip is not loaded yet");
      }
      return id;
    };

    return {
      trip,
      photos: trip?.photos ?? [],
      memory: trip?.memory ?? null,
      health,
      healthError,
      job,
      loading,
      error,
      storyStale,
      refresh,
      async upload(files) {
        const result = await importPhotos(tripId(), files);
        await refresh();
        if (result.job) {
          setJob(result.job);
        }
        return result;
      },
      async savePhoto(photoId, payload) {
        await updatePhoto(photoId, payload);
        await refresh();
      },
      async removePhoto(photoId) {
        await deletePhoto(photoId);
        await refresh();
      },
      async reanalyzePhoto(photoId) {
        await analyzePhoto(photoId);
        await refresh();
        setStoryStale(true);
      },
      async saveTrip(payload) {
        await updateTrip(tripId(), payload);
        await refresh();
      },
      async saveMemory(payload) {
        await updateTripMemory(tripId(), payload);
        await refresh();
      },
      async removeAllPhotos() {
        await deleteAllTripPhotos(tripId());
        await refresh();
        setJob(null);
        setStoryStale(false);
      },
      async clearMemories() {
        await clearTripAnalysis(tripId());
        await refresh();
        setStoryStale(false);
      },
      async clearQuestions() {
        await clearTripQuestions(tripId());
        await refresh();
      },
      dismissJob() {
        setJob(null);
      },
      async retryFailedJob() {
        if (job === null) {
          return;
        }
        setJob(await retryJob(job.id));
      }
    };
  }, [trip, health, healthError, job, loading, error, storyStale, refresh]);

  return <TripContext.Provider value={value}>{children}</TripContext.Provider>;
}
