export type Artifact = { id: string; type: "text" | "code" | "document" | "image" | "audio"; title: string; content?: string; language?: string; url?: string };
export type ChatMessage = { id: string; role: "user" | "assistant"; content: string; artifacts: Artifact[]; route?: string[]; created_at?: string };

