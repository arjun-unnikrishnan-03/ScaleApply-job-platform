"""
Tests for KnowledgeLoader.
"""

import os
from pathlib import Path

import pytest

from loaders.knowledge_loader import KnowledgeLoader
from models.knowledge_document import KnowledgeDocument

@pytest.fixture
def temp_knowledge_dir(tmp_path):
    """Creates a temporary directory structure mimicking the knowledge base."""
    # Create valid files
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "docker.md").write_text("Docker content")
    (skills_dir / "redis.md").write_text("Redis content")
    
    # Create empty file
    ats_dir = tmp_path / "ats"
    ats_dir.mkdir()
    (ats_dir / "empty.md").write_text("")
    
    # Create non-md file
    (ats_dir / "config.json").write_text('{"key": "value"}')
    
    # Files in root
    (tmp_path / "root_file.md").write_text("Root content")

    return tmp_path

def test_loader_scans_files_correctly(temp_knowledge_dir):
    loader = KnowledgeLoader(temp_knowledge_dir)
    docs = loader.load_documents()
    
    # Expecting: docker.md, redis.md, root_file.md (empty.md is skipped, json is skipped)
    assert len(docs) == 3
    
    titles = [d.title for d in docs]
    assert "Docker" in titles
    assert "Redis" in titles
    assert "Root File" in titles

def test_loader_infers_category_and_tags(temp_knowledge_dir):
    loader = KnowledgeLoader(temp_knowledge_dir)
    docs = loader.load_documents()
    
    docker_doc = next(d for d in docs if d.title == "Docker")
    assert docker_doc.category == "skills"
    assert "skills" in docker_doc.tags
    assert "docker" in docker_doc.tags
    
    root_doc = next(d for d in docs if d.title == "Root File")
    # If in root, category defaults to 'general'
    assert root_doc.category == "general"
    assert "general" in root_doc.tags

def test_loader_empty_directory(tmp_path):
    loader = KnowledgeLoader(tmp_path)
    docs = loader.load_documents()
    assert len(docs) == 0

def test_loader_nonexistent_directory():
    loader = KnowledgeLoader("does/not/exist")
    docs = loader.load_documents()
    assert len(docs) == 0
