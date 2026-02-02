from .router import router
from .calendar import router as calendar_router

router.include_router(calendar_router)
