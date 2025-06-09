#!/usr/bin/env python3
"""
Setup script for Reddit to TikTok Video Creator

Handles installation, dependency management, and initial configuration.
"""

from setuptools import setup, find_packages
from pathlib import Path
import sys
import os

# Read README for long description
README_PATH = Path(__file__).parent / "README.md"
if README_PATH.exists():
    with open(README_PATH, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "Reddit to TikTok Video Creator - An intelligent agent for creating TikTok videos from Reddit content"

# Read requirements
def read_requirements(filename):
    """Read requirements from file."""
    req_path = Path(__file__).parent / filename
    if req_path.exists():
        with open(req_path, "r") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

# Core requirements
requirements = read_requirements("requirements.txt")

# Development requirements
dev_requirements = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0", 
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "isort>=5.12.0",
    "pre-commit>=3.0.0"
]

# Optional requirements for enhanced features
extras_require = {
    "dev": dev_requirements,
    "enhanced": [
        "opencv-python>=4.8.0",
        "librosa>=0.10.0",
        "soundfile>=0.12.0",
        "nltk>=3.8.0"
    ],
    "web": [
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "streamlit>=1.25.0"
    ],
    "monitoring": [
        "psutil>=5.9.0",
        "memory-profiler>=0.61.0"
    ]
}

# Package metadata
setup(
    name="reddit-tiktok-creator",
    version="1.0.0",
    author="Reddit TikTok Creator",
    author_email="developer@example.com",
    description="An intelligent agent that creates TikTok videos from Reddit content",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/reddit-tiktok-creator",
    packages=find_packages(include=["src", "src.*", "config", "config.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Content Creators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Video",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "reddit-tiktok=main:sync_main",
            "rtc=main:sync_main",  # Short alias
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.json", "*.yaml", "*.yml"],
        "assets": ["*"],
        "config": ["*.py", "*.json"],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/reddit-tiktok-creator/issues",
        "Source": "https://github.com/yourusername/reddit-tiktok-creator",
        "Documentation": "https://github.com/yourusername/reddit-tiktok-creator/wiki",
    },
    keywords=[
        "reddit", "tiktok", "video", "automation", "content-creation", 
        "ai", "langchain", "langgraph", "anthropic", "openai"
    ],
)


# Post-installation setup
def post_install():
    """Run post-installation setup tasks."""
    
    print("\n🎉 Reddit to TikTok Video Creator installed successfully!")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("⚠️  Warning: Python 3.8+ is recommended")
    
    # Create necessary directories
    directories = [
        "output_videos",
        "output_videos/ready_to_upload",
        "output_videos/uploaded", 
        "output_videos/archive",
        "output_videos/audio",
        "output_videos/logs",
        "assets",
        "assets/fonts",
        "assets/backgrounds"
    ]
    
    print("\n📁 Creating directory structure...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")
    
    # Create .gitkeep files
    gitkeep_files = [
        "output_videos/.gitkeep",
        "assets/fonts/.gitkeep",
        "assets/backgrounds/.gitkeep"
    ]
    
    for gitkeep in gitkeep_files:
        Path(gitkeep).touch()
    
    print("\n📋 Next Steps:")
    print("1. Set up your API credentials:")
    print("   reddit-tiktok setup")
    print("2. Test the installation:")
    print("   reddit-tiktok test")
    print("3. Create your first video:")
    print("   reddit-tiktok create")
    
    print("\n📚 Documentation:")
    print("   README.md - Complete usage guide")
    print("   .env.example - Configuration template")
    
    print("\n🚀 Ready to create amazing TikTok videos from Reddit content!")


if __name__ == "__main__":
    # Run post-installation setup if this script is executed directly
    post_install()
