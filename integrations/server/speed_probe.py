"""Finite uncompressed downstream probe. Caller must authenticate before serve()."""
import os,threading,time
SIZE=16*1024*1024
CHUNK=os.urandom(65536)
_lock=threading.Lock()
_next=0.0

def serve(handler):
    global _next
    if not _lock.acquire(blocking=False):
        handler.reply(429,{'error':'probe_busy'});return
    try:
        now=time.monotonic()
        if now<_next:
            handler.reply(429,{'error':'probe_rate_limit'});return
        _next=now+60
        handler.connection.settimeout(6)
        handler.send_response(200)
        for k,v in [('Content-Type','application/octet-stream'),('Content-Length',str(SIZE)),('Cache-Control','private, no-store, no-transform'),('X-Probe-Node','RU-188.120.240.175'),('X-Content-Type-Options','nosniff')]:handler.send_header(k,v)
        handler.end_headers()
        for _ in range(SIZE//len(CHUNK)):
            if time.monotonic()-now>8:break
            handler.wfile.write(CHUNK)
    except (BrokenPipeError,ConnectionResetError,TimeoutError):pass
    finally:_lock.release()
