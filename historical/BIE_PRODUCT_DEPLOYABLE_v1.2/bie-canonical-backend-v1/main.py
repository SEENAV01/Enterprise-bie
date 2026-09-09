from __future__ import annotations

import os
from http.server import ThreadingHTTPServer

from app.server import Handler


def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    print(f"BIE Product running on http://0.0.0.0:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
