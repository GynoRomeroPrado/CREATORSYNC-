# Contributing to CreatorSync

Thank you for your interest in contributing to CreatorSync! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the behavior
- **Expected vs actual behavior**
- **Screenshots** if applicable
- **Environment details** (OS, browser, versions)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** and **motivation**
- **Proposed implementation** (if applicable)
- **Alternative solutions** considered

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the code style** of the project
3. **Write tests** for new features
4. **Update documentation** as needed
5. **Ensure all tests pass**
6. **Submit a pull request**

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-org/creatorsync.git
cd creatorsync

# Start infrastructure
docker-compose up -d postgres redis kafka elasticsearch

# Backend setup (choose the module you're working on)
cd backend/attribution-engine  # or tax-optimizer, invoice-factoring
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend setup
cd frontend/web-app
npm install
npm run dev
```

## Code Style Guidelines

### Python

- Follow **PEP 8** style guide
- Use **type hints** for function parameters and return values
- Use **docstrings** for classes and functions
- Maximum line length: **100 characters**
- Use **Black** for formatting: `black .`
- Use **Ruff** for linting: `ruff check .`

Example:
```python
from typing import List, Optional
from pydantic import BaseModel

class Creator(BaseModel):
    """Represents a content creator."""

    id: int
    name: str
    email: str
    platforms: Optional[List[str]] = None

    def get_total_income(self, year: int) -> float:
        """
        Calculate total income for a given year.

        Args:
            year: The tax year

        Returns:
            Total income amount
        """
        # Implementation here
        pass
```

### TypeScript/JavaScript

- Follow **Airbnb Style Guide**
- Use **TypeScript** for type safety
- Use **ESLint** and **Prettier**
- Prefer **functional components** with hooks
- Use **async/await** over promises

Example:
```typescript
interface Creator {
  id: number;
  name: string;
  email: string;
  platforms?: string[];
}

async function fetchCreator(id: number): Promise<Creator> {
  const response = await fetch(`/api/creators/${id}`);

  if (!response.ok) {
    throw new Error('Failed to fetch creator');
  }

  return response.json();
}
```

## Testing

### Python Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_attribution.py
```

### JavaScript/TypeScript Tests

```bash
# Run all tests
npm test

# Run in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage
```

## Documentation

- Update **README.md** for significant changes
- Add **API documentation** for new endpoints
- Include **code comments** for complex logic
- Update **architecture docs** if changing system design

## Commit Messages

Follow the **Conventional Commits** specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(attribution): add TikTok API integration

Implements TikTok Display API integration for content fetching
and analytics retrieval.

Closes #123
```

```
fix(tax): correct quarterly tax calculation

Fixed issue where self-employment tax was not being
included in quarterly estimates.

Fixes #456
```

## Project Structure

```
creatorsync/
├── backend/
│   ├── attribution-engine/   # Income tracking & forecasting
│   ├── tax-optimizer/         # Tax calculations & forms
│   ├── brand-crm/             # Brand deals management
│   └── invoice-factoring/     # Invoice advances
├── frontend/
│   └── web-app/               # Next.js web application
├── infrastructure/            # Docker, K8s configs
├── docs/                      # Documentation
└── tests/                     # Integration tests
```

## Module-Specific Guidelines

### Attribution Engine

- All platform integrations must implement `PlatformIntegration` base class
- ML models must be versioned and stored in `ml-models/`
- Forecasting must use Prophet library
- Cache API responses appropriately

### Tax Optimizer

- OCR processing must validate confidence scores
- Tax calculations must follow IRS guidelines
- All forms must be validated before generation
- Expense categorization must be auditable

### Brand CRM

- GraphQL schema must be strongly typed
- Deal stages must follow defined workflow
- Media kits must auto-refresh stats
- Contract signatures must be tracked

### Invoice Factoring

- Risk assessment must be ML-based
- All payments must be idempotent
- Collections must follow FDCPA guidelines
- KYC verification is mandatory

## Release Process

1. **Version bump** in package files
2. **Update CHANGELOG.md**
3. **Create release branch** (`release/v1.0.0`)
4. **Run full test suite**
5. **Create pull request** to `main`
6. **Tag release** after merge
7. **Deploy to production**

## Questions?

- Open an **issue** for questions
- Join our **Discord** community
- Email: **dev@creatorsync.com**

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to CreatorSync! 🚀
