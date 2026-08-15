import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { BrainCircuit, MessageCircle, Send, Trash2 } from "lucide-react";
import {
  assetUrl,
  type AskResponse,
  type Photo,
  type TripQuestion
} from "../../api/client";

type MemoryCompanionProps = {
  askDisabled: boolean;
  pending: boolean;
  askResponse: AskResponse | null;
  askError: string | null;
  questions: TripQuestion[];
  photos: Photo[];
  onAsk: (question: string) => void;
  onRestoreHistory: (item: TripQuestion) => void;
  onClearHistory: () => void;
};

const PROMPTS = [
  "What did I seem drawn to on this trip?",
  "Which moments feel most memorable?",
  "What should I revisit next time?"
];

export function MemoryCompanion({
  askDisabled,
  pending,
  askResponse,
  askError,
  questions,
  photos,
  onAsk,
  onRestoreHistory,
  onClearHistory
}: MemoryCompanionProps) {
  const [question, setQuestion] = useState(PROMPTS[0]);
  const [selectedHistoryId, setSelectedHistoryId] = useState<number | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (question.trim()) {
      setSelectedHistoryId(null);
      onAsk(question.trim());
    }
  }

  function restoreHistory(item: TripQuestion) {
    setQuestion(item.question);
    setSelectedHistoryId(item.id);
    onRestoreHistory(item);
  }

  return (
    <div className="memory-companion">
      <div className="prompt-row" aria-label="Suggested questions">
        {PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            disabled={askDisabled}
            onClick={() => setQuestion(prompt)}
          >
            {prompt}
          </button>
        ))}
      </div>

      <form className="companion-form" onSubmit={handleSubmit}>
        <MessageCircle size={17} aria-hidden="true" />
        <input
          aria-label="Ask a trip question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          disabled={askDisabled}
          placeholder="Ask about this trip..."
        />
        <button
          type="submit"
          disabled={askDisabled || pending || !question.trim()}
          title="Ask trip"
        >
          <Send size={16} aria-hidden="true" />
        </button>
      </form>

      <div className="companion-answer">
        {askError ? <p className="app-error">{askError}</p> : null}
        {pending ? (
          <div className="answer-waiting">
            <BrainCircuit size={20} aria-hidden="true" />
            <p>Reading through the memories…</p>
          </div>
        ) : askResponse ? (
          <>
            <span className="soft-kicker">Grounded answer</span>
            <p>{askResponse.answer}</p>
            <EvidenceLinks ids={askResponse.evidence_photo_ids} photos={photos} />
          </>
        ) : (
          <div className="answer-waiting">
            <BrainCircuit size={20} aria-hidden="true" />
            <p>
              {askDisabled
                ? "Questions unlock once the trip has memories."
                : "Ask anything — answers come only from what your photos show."}
            </p>
          </div>
        )}
      </div>

      {questions.length > 0 ? (
        <div className="question-history">
          <div className="question-history-header">
            <span className="soft-kicker">Asked before</span>
            <button
              type="button"
              className="ghost-action"
              onClick={onClearHistory}
              title="Clear history"
            >
              <Trash2 size={13} aria-hidden="true" />
              Clear
            </button>
          </div>
          {[...questions]
            .slice(-5)
            .reverse()
            .map((item) => (
              <button
                key={item.id}
                type="button"
                className={
                  selectedHistoryId === item.id
                    ? "history-item is-selected"
                    : "history-item"
                }
                aria-pressed={selectedHistoryId === item.id}
                onClick={() => restoreHistory(item)}
              >
                <strong>{item.question}</strong>
                <span>{item.answer}</span>
              </button>
            ))}
        </div>
      ) : null}
    </div>
  );
}

function EvidenceLinks({ ids, photos }: { ids: number[]; photos: Photo[] }) {
  if (ids.length === 0) {
    return null;
  }

  return (
    <div className="companion-evidence">
      <span>Evidence</span>
      {ids.map((id) => {
        const photo = photos.find((item) => item.id === id);
        return (
          <Link key={id} to={`/photos/${id}`}>
            {photo ? (
              <img
                src={assetUrl(photo.image_url)}
                alt={photo.analysis?.memory_caption || photo.filename}
              />
            ) : null}
            <em>#{id}</em>
          </Link>
        );
      })}
    </div>
  );
}
