from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import pages, parking, members, admin
from app.routes.login import router as login_router

app = FastAPI(title="Forum Operating System")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(login_router, tags=["auth"])
app.include_router(pages.router)
app.include_router(parking.router, prefix="/parking", tags=["parking"])
app.include_router(members.router, prefix="/members", tags=["members"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
