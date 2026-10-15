# Controlled material download v1

MaterialDownloader reuses CS50Executor.download unchanged, plus its digest,
safe_path, sync_directory and atomic receipt primitives. A guarding transport
validates the exact selected HTTPS URL, official host, MIME/Content-Length and
uncompressed transfer. Redirects are refused entirely: no unvalidated target
request. Proxy/environment credentials are disabled by the existing primitive.
Allowlist: cs50.harvard.edu and cdn.cs50.net. External/unreviewed sources remain
blocked; audio/video/archive/subtitle processing remains separate.

Default preview performs no writes or HTTP. Execution requires explicit approval
and license-reviewed binding plus --license-reviewed. Local import does no HTTP
and labels its origin separately; hash proves bytes, not remote authenticity.
Default serial concurrency one, 16MiB/10s socket/45s total/one retry; upper size
64MiB, retry maximum two. Network/429/5xx retries only; redirects/404/MIME/size
conflicts fail. Existing executor timeout is checked during streaming; a single
blocking read can consume its socket timeout before the deadline check.

Streaming uses a same-filesystem temporary, fsync, SHA256 write-ahead receipt,
exclusive hard-link publication and directory fsync. Existing files are never
replaced. A prepared downloaded receipt permits post-publication recovery only
when binding and exact raw hash agree. Failed/partial attempts publish no raw
artifact. Per-workspace flock prevents concurrent writers. Unknown/corrupt/stale
receipts or changed bytes conflict; no file-existence adoption. Output workspaces
must be external to this repository and cannot contain symlink paths.

Receipt replacement is atomic metadata update; immutable raw/parser/image files
are exclusively published. No auth/cookie/browser/yt-dlp/LLM/Whisper path is used.
