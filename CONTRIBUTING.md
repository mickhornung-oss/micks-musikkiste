# Contributing Guidelines

Thank you for your interest in contributing to MicksMusikkiste! This document provides guidelines and instructions for contributing to this project.

## Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- Node.js (for frontend)
- FastAPI knowledge

### Local Setup
1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/micks-musikkiste.git`
3. Navigate to the project: `cd micks-musikkiste`

**Backend Setup:**
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
python backend/run.py
# Server runs on http://localhost:8000
```

**Database Setup:**
```bash
psql -U postgres
CREATE DATABASE musikkiste;
```

## Development Workflow

### Creating a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### Code Guidelines
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python
- Use meaningful variable and function names
- Add docstrings to functions
- Keep API endpoints RESTful

### Testing Your Changes
- Test API endpoints locally: `curl http://localhost:8000/api/...`
- Verify database integrity
- Check frontend-backend integration

## Submitting Changes

### Commit Messages
- Use clear, descriptive commit messages
- Format: `type: brief description`
- Examples: `feat: add playlist shuffle`, `fix: database connection pool`, `docs: update API docs`

### Pull Request Process
1. Push your changes to your fork
2. Open a Pull Request with:
   - Clear title describing the feature or fix
   - Description of changes made
   - Testing steps (if applicable)
   - Related issues

3. Wait for review and address feedback

## Areas for Contribution

### Backend
- New music processing algorithms
- API performance optimization
- Database query optimization

### Frontend
- UI/UX improvements
- New features
- Responsive design enhancements

### Database
- Schema optimization
- Index improvements
- Query efficiency

## Questions?

Feel free to:
- Open an Issue for feature requests or bugs
- Start a Discussion for ideas
- Email the maintainer: [mick.hornung@googlemail.com](mailto:mick.hornung@googlemail.com)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Happy Contributing!** 🚀
