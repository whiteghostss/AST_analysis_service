from fastapi import APIRouter
from upload import router as upload_router
from source import router as source_router
from ast_analysis import router as ast_router
from package import router as package_router

router = APIRouter()
router.include_router(upload_router, prefix="/api")
router.include_router(source_router, prefix="/api")
router.include_router(ast_router, prefix="/api")
router.include_router(package_router, prefix="/api")

