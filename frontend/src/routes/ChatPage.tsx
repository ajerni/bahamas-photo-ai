import { useState } from "react";
import { askTrip, type AskResponse, type TripQuestion } from "../api/client";
import { MemoryCompanion } from "../components/companion/MemoryCompanion";
import { useTrip } from "../trip/TripProvider";

export function ChatPage() {
  const { trip, photos, memory, refresh, clearQuestions } = useTrip();
  const [askResponse, setAskResponse] = useState<AskResponse | null>(null);
  const [askError, setAskError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  function restoreHistory(item: TripQuestion) {
    setAskError(null);
    setAskResponse({
      answer: item.answer,
      evidence_photo_ids: item.evidence_photo_ids
    });
  }

  async function ask(question: string) {
    if (!trip) {
      return;
    }
    setPending(true);
    setAskError(null);
    try {
      setAskResponse(await askTrip(trip.id, question));
      await refresh();
    } catch (cause) {
      setAskError((cause as Error).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="page chat-page">
      <div className="section-heading">
        <div>
          <span className="soft-kicker">Ask this trip</span>
          <h2>Talk to your memories</h2>
        </div>
      </div>

      <MemoryCompanion
        askDisabled={memory === null}
        pending={pending}
        askResponse={askResponse}
        askError={askError}
        questions={trip?.questions ?? []}
        photos={photos}
        onAsk={(question) => void ask(question)}
        onRestoreHistory={restoreHistory}
        onClearHistory={() => void clearQuestions()}
      />
    </div>
  );
}
