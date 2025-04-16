from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv
from pydantic import BaseModel

# .env dosyasını yükle
load_dotenv()

# Database URL'sini al
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# User model for database
class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    points = Column(Float, default=2500.0)
    level = Column(String, default="Gümüş Üye")

# Pydantic models for API
class User(BaseModel):
    id: int
    username: str
    points: float
    level: str
    
    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    points: float

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI(title="Zuzzuu API")

# CORS ayarları (React uygulamasının API'ye erişebilmesi için)
origins = [
    "http://localhost:3000",  # Local geliştirme ortamı
    "https://animated-moonbeam-8518e3.netlify.app/",  # Netlify URL'nizi buraya ekleyin
    "*"  # Geliştirme sırasında tüm originlere izin ver, production'da spesifik originleri belirtin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB bağlantısı için dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Başlangıç verisini oluştur
@app.on_event("startup")
async def startup_db_client():
    db = SessionLocal()
    # Örnek kullanıcı varsa ekleme
    user_exists = db.query(UserDB).filter(UserDB.username == "Ahmet Özdemir").first()
    if not user_exists:
        default_user = UserDB(username="Ahmet Özdemir", points=2500.0, level="Gümüş Üye")
        db.add(default_user)
        db.commit()
    db.close()

# API endpoints
@app.get("/")
def read_root():
    return {"message": "Zuzzuu API'ye Hoş Geldiniz"}

@app.get("/api/users/{user_id}", response_model=User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return user

@app.get("/api/users/by-username/{username}", response_model=User)
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return user

@app.put("/api/users/{user_id}", response_model=User)
def update_user_points(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    db_user.points = user_update.points
    
    # Puana göre seviye atama
    if db_user.points >= 5000:
        db_user.level = "Altın Üye"
    elif db_user.points >= 2500:
        db_user.level = "Gümüş Üye"
    else:
        db_user.level = "Bronz Üye"
    
    db.commit()
    db.refresh(db_user)
    return db_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)