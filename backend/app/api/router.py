"""Central API Router."""

from fastapi import APIRouter
from backend.app.api.documents import router as documents_router
from backend.app.api.links import router as links_router
from backend.app.api.stats import router as stats_router
from backend.app.api.audit import router as audit_router
from backend.app.api.recommendations import router as recommendations_router
from backend.app.api.reviews import router as reviews_router
from backend.app.api.remediations import router as remediations_router
from backend.app.api.experiments import router as experiments_router
from backend.app.api.research_export import router as research_export_router

api_router = APIRouter()

api_router.include_router(documents_router)
api_router.include_router(links_router)
api_router.include_router(stats_router)
api_router.include_router(audit_router)
api_router.include_router(recommendations_router)
api_router.include_router(reviews_router)
api_router.include_router(remediations_router)
api_router.include_router(experiments_router)
api_router.include_router(research_export_router)
