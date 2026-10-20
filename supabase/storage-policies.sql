-- Create a private bucket named chat-media in Supabase Storage first.
create policy "Users read own chat media" on storage.objects for select to authenticated
using (bucket_id = 'chat-media' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "Users upload own chat media" on storage.objects for insert to authenticated
with check (bucket_id = 'chat-media' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "Users update own chat media" on storage.objects for update to authenticated
using (bucket_id = 'chat-media' and (storage.foldername(name))[1] = (select auth.uid())::text)
with check (bucket_id = 'chat-media' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "Users delete own chat media" on storage.objects for delete to authenticated
using (bucket_id = 'chat-media' and (storage.foldername(name))[1] = (select auth.uid())::text);

