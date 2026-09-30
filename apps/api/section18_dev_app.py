"""Development-only Section 18 app composition.

This module does not alter apps.api.main. It exists so Batch 001 can exercise
the product routes against canonical stores without claiming production
deployment or authentication.
"""

from fastapi import FastAPI

from .section18_operator import install_section18_routes

app = FastAPI(
    title="BIE Section 18 Operator Development App",
    docs_url=None,
    redoc_url=None,
)
install_section18_routes(app)
