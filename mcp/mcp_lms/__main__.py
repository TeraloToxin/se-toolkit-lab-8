"""Allow running as `python -m mcp_lms [server]`."""

import asyncio
import sys

if len(sys.argv) > 1 and sys.argv[1] == "observability":
    from mcp_lms.observability import main
else:
    from mcp_lms.server import main

asyncio.run(main())
