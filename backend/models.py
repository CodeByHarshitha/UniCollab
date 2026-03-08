from pydantic import BaseModel, EmailStr
from typing import List, Optional

class LoginRequest(BaseModel):
    email: str
    password: str

class ProfileData(BaseModel):
    name: str # The user can edit their name here
    department: str
    year_of_study: str
    course: str
    specialization: str
    graduation_year: str
    skills: List[str] = []
    interests: List[str] = []

class ProjectCreate(BaseModel):
    title: str
    description: str
    skills_needed: List[str]
    team_size: int

class User(BaseModel):
    email: str
    name: str
    profile_completed: bool = False
    profile_data: Optional[ProfileData] = None
    created_projects: List[ProjectCreate] = []

class SkillAddRequest(BaseModel):
    skills: List[str]
