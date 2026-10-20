"use client";
import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Sparkles } from "lucide-react";
export function AuthForm() {
  const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [mode, setMode] = useState<"in"|"up">("in"); const [note, setNote] = useState(""); const [busy, setBusy] = useState(false);
  const configured = Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
  async function submit(e: React.FormEvent) { e.preventDefault(); setBusy(true); setNote(""); const db = createClient(); if(!db){setBusy(false);setNote("Connect a Supabase project to enable accounts.");return} const result = mode === "in" ? await db.auth.signInWithPassword({ email, password }) : await db.auth.signUp({ email, password }); setBusy(false); if (result.error) setNote(result.error.message); else if (mode === "up") setNote("Check your email to confirm your account."); else location.assign("/"); }
  if(!configured) return <section className="auth-card"><div className="brand-mark"><Sparkles size={20}/></div><p className="eyebrow">ETHER 1 PREVIEW</p><h1>Accounts aren’t connected yet</h1><p className="muted">Add a dedicated Supabase project to turn on sign-in and saved chat history. Your existing Supabase project has not been changed.</p></section>;
  return <section className="auth-card"><div className="brand-mark"><Sparkles size={20}/></div><p className="eyebrow">YOUR CREATIVE WORKSPACE</p><h1>{mode === "in" ? "Welcome back" : "Create your account"}</h1><p className="muted">Chat, make, and refine ideas in one place.</p><form onSubmit={submit}><label>Email<input type="email" required value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com"/></label><label>Password<input type="password" required minLength={8} value={password} onChange={e=>setPassword(e.target.value)} placeholder="At least 8 characters"/></label><button className="primary full" disabled={busy}>{busy?"Please wait…":mode === "in"?"Sign in":"Create account"}</button></form>{note&&<p className="form-note">{note}</p>}<button className="text-button" onClick={()=>{setMode(mode==="in"?"up":"in");setNote("")}}>{mode==="in"?"New here? Create an account":"Already have an account? Sign in"}</button></section>;
}

