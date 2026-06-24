import { FormEvent, KeyboardEvent, MutableRefObject, useEffect, useMemo, useRef, useState } from 'react';
import { marked } from 'marked';

const API_BASE = import.meta.env.VITE_API_URL ?? '';
const MAX_FILES = 5;
const MAX_FILE_BYTES = 10 * 1024 * 1024;

type View = 'chat' | 'kb';

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  source?: string | null;
  escalated_to?: string | null;
  loading?: boolean;
};

type ChatResponse = {
  reply: string;
  source: string | null;
  escalated_to: string | null;
  session_id: string;
};

type KbDocument = {
  id: string;
  original_filename: string;
  stored_filename: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
  pdf_path: string;
  markdown_path: string;
  status: string;
  error: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export function App() {
  const [view, setView] = useState<View>('chat');
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID());
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [documents, setDocuments] = useState<KbDocument[]>([]);
  const [kbStatus, setKbStatus] = useState('');
  const [isKbLoading, setIsKbLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const messagesRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    messagesRef.current?.scrollTo({ top: messagesRef.current.scrollHeight });
  }, [messages]);

  useEffect(() => {
    if (view === 'kb') {
      void loadDocuments();
    }
  }, [view]);

  function resetSession() {
    setSessionId(crypto.randomUUID());
    setMessages([]);
    setInput('');
    setView('chat');
  }

  async function sendMessage() {
    const text = input.trim();
    if (!text || isSending) return;

    const loadingId = crypto.randomUUID();
    setInput('');
    setIsSending(true);
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: 'user', content: text },
      { id: loadingId, role: 'assistant', content: '', loading: true },
    ]);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = (await response.json()) as ChatResponse;

      setMessages((current) =>
        current.map((message) =>
          message.id === loadingId
            ? {
                id: loadingId,
                role: 'assistant',
                content: data.reply,
                source: data.source,
                escalated_to: data.escalated_to,
              }
            : message,
        ),
      );
    } catch {
      setMessages((current) =>
        current.map((message) =>
          message.id === loadingId
            ? {
                id: loadingId,
                role: 'assistant',
                content:
                  'No se pudo conectar con el servidor. Verifica que el backend este corriendo en `localhost:8000`.',
              }
            : message,
        ),
      );
    } finally {
      setIsSending(false);
    }
  }

  async function loadDocuments() {
    setIsKbLoading(true);
    setKbStatus('');
    try {
      const response = await fetch(`${API_BASE}/kb/documents`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setDocuments((await response.json()) as KbDocument[]);
    } catch {
      setKbStatus('No se pudo cargar la knowledge base.');
    } finally {
      setIsKbLoading(false);
    }
  }

  async function uploadDocuments(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const files = Array.from(fileInputRef.current?.files ?? []);
    const validation = validatePdfSelection(files);
    if (validation) {
      setKbStatus(validation);
      return;
    }

    setIsUploading(true);
    setKbStatus('Subiendo PDFs...');

    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE}/kb/documents`, {
          method: 'POST',
          body: formData,
        });
        if (!response.ok) {
          const detail = await readErrorDetail(response);
          throw new Error(`${file.name}: ${detail}`);
        }
      }

      if (fileInputRef.current) fileInputRef.current.value = '';
      setKbStatus('PDFs subidos correctamente.');
      await loadDocuments();
    } catch (error) {
      setKbStatus(error instanceof Error ? error.message : 'No se pudieron subir los PDFs.');
    } finally {
      setIsUploading(false);
    }
  }

  async function deleteDocument(documentId: string) {
    const confirmed = window.confirm('Eliminar este documento de la knowledge base?');
    if (!confirmed) return;

    setKbStatus('Eliminando documento...');
    try {
      const response = await fetch(`${API_BASE}/kb/documents/${documentId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setDocuments((current) => current.filter((document) => document.id !== documentId));
      setKbStatus('Documento eliminado.');
    } catch {
      setKbStatus('No se pudo eliminar el documento.');
    }
  }

  return (
    <div id="app" className={view === 'kb' ? 'app-wide' : undefined}>
      <header className="header">
        <div className="header-brand">
          <span className="logo">30X</span>
          <span className="brand-sep">-</span>
          <span className="brand-name">Onboarding</span>
        </div>
        <div className="header-actions">
          <button className="btn-ghost" type="button" onClick={() => setView('chat')}>
            Chat
          </button>
          <button className="btn-ghost" type="button" onClick={() => setView('kb')}>
            Knowledge base
          </button>
          <button className="btn-ghost" type="button" onClick={resetSession}>
            <span className="plus">+</span>
            Nueva sesion
          </button>
        </div>
      </header>

      {view === 'chat' ? (
        <ChatView
          input={input}
          isSending={isSending}
          messages={messages}
          messagesRef={messagesRef}
          onInputChange={setInput}
          onSend={sendMessage}
        />
      ) : (
        <KnowledgeBaseView
          documents={documents}
          fileInputRef={fileInputRef}
          isKbLoading={isKbLoading}
          isUploading={isUploading}
          kbStatus={kbStatus}
          onDelete={deleteDocument}
          onRefresh={loadDocuments}
          onUpload={uploadDocuments}
        />
      )}
    </div>
  );
}

function ChatView({
  input,
  isSending,
  messages,
  messagesRef,
  onInputChange,
  onSend,
}: {
  input: string;
  isSending: boolean;
  messages: ChatMessage[];
  messagesRef: MutableRefObject<HTMLDivElement | null>;
  onInputChange: (value: string) => void;
  onSend: () => void;
}) {
  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void onSend();
    }
  }

  return (
    <>
      <main ref={messagesRef} className="messages">
        {messages.length === 0 ? (
          <div className="welcome">
            <p>Hola. Soy el agente de onboarding de 30X.</p>
            <p>Preguntame lo que necesites sobre el equipo, los programas o las herramientas.</p>
          </div>
        ) : (
          messages.map((message) => <MessageBubble key={message.id} message={message} />)
        )}
      </main>

      <footer className="input-area">
        <div className="input-wrapper">
          <textarea
            value={input}
            placeholder="Escribi tu pregunta..."
            rows={1}
            spellCheck={false}
            onChange={(event) => onInputChange(event.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button className="btn-send" type="button" title="Enviar (Enter)" disabled={isSending} onClick={onSend}>
            <span className="send-arrow">↑</span>
          </button>
        </div>
        <p className="input-hint">Enter para enviar - Shift+Enter para nueva linea</p>
      </footer>
    </>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const html = useMemo(() => String(marked.parse(message.content)), [message.content]);

  if (message.loading) {
    return (
      <div className="message message-assistant">
        <div className="bubble loading">
          <span />
          <span />
          <span />
        </div>
      </div>
    );
  }

  return (
    <div className={`message message-${message.role}`}>
      <div className="bubble">
        {message.role === 'user' ? (
          message.content
        ) : (
          <>
            <div className="bubble-content" dangerouslySetInnerHTML={{ __html: html }} />
            {message.source ? <div className="meta meta-source">{message.source}</div> : null}
            {message.escalated_to ? (
              <div className="meta meta-escalation">
                <span className="escalation-label">Escalar a</span>
                {message.escalated_to}
              </div>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}

function KnowledgeBaseView({
  documents,
  fileInputRef,
  isKbLoading,
  isUploading,
  kbStatus,
  onDelete,
  onRefresh,
  onUpload,
}: {
  documents: KbDocument[];
  fileInputRef: MutableRefObject<HTMLInputElement | null>;
  isKbLoading: boolean;
  isUploading: boolean;
  kbStatus: string;
  onDelete: (documentId: string) => void;
  onRefresh: () => void;
  onUpload: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <main className="kb-page">
      <div className="kb-toolbar">
        <div>
          <h1>Knowledge base</h1>
          <p>Subi hasta 5 PDFs por vez. Maximo 10 MB por archivo.</p>
        </div>
        <form className="kb-upload" onSubmit={onUpload}>
          <input ref={fileInputRef} type="file" accept="application/pdf,.pdf" multiple />
          <button className="btn-primary" type="submit" disabled={isUploading}>
            {isUploading ? 'Subiendo...' : 'Subir PDFs'}
          </button>
          <button className="btn-ghost" type="button" disabled={isKbLoading} onClick={onRefresh}>
            Actualizar
          </button>
        </form>
      </div>

      {kbStatus ? <div className="kb-status">{kbStatus}</div> : null}

      <div className="table-wrap">
        <table className="kb-table">
          <thead>
            <tr>
              <th>Archivo</th>
              <th>Tamano</th>
              <th>Estado</th>
              <th>Markdown</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {isKbLoading ? (
              <tr>
                <td className="empty-cell" colSpan={5}>
                  Cargando documentos...
                </td>
              </tr>
            ) : documents.length === 0 ? (
              <tr>
                <td className="empty-cell" colSpan={5}>
                  Todavia no hay documentos.
                </td>
              </tr>
            ) : (
              documents.map((document) => (
                <tr key={document.id}>
                  <td>{document.original_filename}</td>
                  <td>{formatBytes(document.size_bytes)}</td>
                  <td>{document.status}</td>
                  <td className="path-cell">{document.markdown_path}</td>
                  <td className="actions-cell">
                    <button className="btn-danger" type="button" onClick={() => onDelete(document.id)}>
                      Borrar
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}

function validatePdfSelection(files: File[]) {
  if (files.length === 0) return 'Selecciona al menos un PDF.';
  if (files.length > MAX_FILES) return 'Solo puedes subir hasta 5 PDFs a la vez.';

  const invalidType = files.find(
    (file) => file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf'),
  );
  if (invalidType) return `Solo se aceptan PDFs. Revisa: ${invalidType.name}`;

  const oversized = files.find((file) => file.size > MAX_FILE_BYTES);
  if (oversized) return `${oversized.name} supera el limite de 10 MB.`;

  return '';
}

async function readErrorDetail(response: Response) {
  try {
    const data = (await response.json()) as { detail?: string };
    return data.detail ?? `HTTP ${response.status}`;
  } catch {
    return `HTTP ${response.status}`;
  }
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
