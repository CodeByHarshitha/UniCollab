from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    # User table with exactly the requested fields
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False) # this will store the hashed password

class Project(Base):
    __tablename__ = "projects"

    project_id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(String, nullable=False, index=True) # Storing email for simplicity as per existing system
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    required_skills = Column(String, nullable=True) # Comma-separated or JSON string
    team_size = Column(Integer, nullable=False, default=4)

    members = relationship("ProjectMember", back_populates="project")
    join_requests = relationship("JoinRequest", back_populates="project")

class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    user_id = Column(String, nullable=False) # email
    role = Column(String, nullable=False) # e.g., "Creator", "Member"

    project = relationship("Project", back_populates="members")

class JoinRequest(Base):
    __tablename__ = "join_requests"

    request_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    requester_id = Column(String, nullable=False) # email
    status = Column(String, nullable=False, default="pending") # pending, accepted, rejected

    project = relationship("Project", back_populates="join_requests")
