import httpx
import aioftp

client: httpx.AsyncClient | None = None
ftp_client: aioftp.Client | None = None