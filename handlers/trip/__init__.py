from .router import router
from .trip_calendar import router as calendar_router

router.include_router(calendar_router)
