from pydantic import BaseModel, EmailStr
from typing import List, Optional
import json
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    profile_completed = Column(Boolean, default=False)

    profile = relationship("DBProfile", back_populates="user", uselist=False)

class DBProfile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    full_name = Column(String)
    department = Column(String)
    course = Column(String)
    specialization = Column(String)
    year_of_study = Column(String)
    graduation_year = Column(String)
    skills_json = Column(Text, default="[]") 
    
    user = relationship("DBUser", back_populates="profile")

    @property
    def skills(self):
        return json.loads(self.skills_json) if self.skills_json else []
        
    @skills.setter
    def skills(self, value):
        self.skills_json = json.dumps(value)

class DBProject(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    required_skills_json = Column(Text, default="[]")
    team_size = Column(Integer, default=4)
    status = Column(String, default="Open") # Open, Team Full, In Progress
    
    creator = relationship("DBUser", backref="created_projects")
    members = relationship("DBProjectMember", back_populates="project")
    join_requests = relationship("DBJoinRequest", back_populates="project")

    @property
    def required_skills(self):
        return json.loads(self.required_skills_json) if self.required_skills_json else []
        
    @required_skills.setter
    def required_skills(self, value):
        self.required_skills_json = json.dumps(value)

class DBProjectMember(Base):
    __tablename__ = "project_members"
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role = Column(String, default="Member")
    
    project = relationship("DBProject", back_populates="members")
    user = relationship("DBUser")

class DBJoinRequest(Base):
    __tablename__ = "join_requests"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending") # pending, accepted, rejected
    
    project = relationship("DBProject", back_populates="join_requests")
    requester = relationship("DBUser")

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
