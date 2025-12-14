# Contributing to PNAE Simplificado

Thank you for your interest in contributing! This document outlines our code standards and contribution process.

## Code Standards

### General Principles

- **Clarity over cleverness**: Code should be readable by any team member
- **Single Responsibility**: Functions and classes should do one thing well
- **DRY**: Don't Repeat Yourself - extract common logic
- **Fail Fast**: Validate inputs early, provide clear error messages
- **Testability**: Write testable code (pure functions where possible)

### Backend (Python)

**Style:**
- Follow PEP 8
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use `ruff` for linting and formatting

**Error Handling:**
- Use proper logging (no `print()` statements)
- Include context in error messages
- Use structured logging with `extra` parameter

**Example:**
```python
logger.error(
    "Failed to process request",
    exc_info=True,
    extra={"user_id": user_id, "operation": "process_request"}
)
```

**Testing:**
- Write unit tests for business logic
- Write integration tests for API endpoints
- Aim for >80% code coverage on new code

### Frontend (TypeScript/React)

**Style:**
- Use TypeScript strict mode
- Prefer functional components with hooks
- Extract complex logic to custom hooks
- Keep components under 200 lines (extract sub-components)

**Error Handling:**
- Use error boundaries for React errors
- Handle API errors gracefully with user-friendly messages
- Log errors to console in development

**Testing:**
- Write unit tests for utility functions and hooks
- Write E2E tests for critical user flows
- Use Page Object Model pattern for E2E tests

## Development Workflow

1. **Create a branch** from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** following code standards

3. **Run tests** before committing
   ```bash
   # Backend
   cd backend && python -m pytest tests/
   
   # Frontend
   cd frontend && npm run test:unit
   ```

4. **Commit** with clear messages
   ```bash
   git commit -m "feat: add file validation to upload"
   ```

5. **Push** and create a Pull Request

## Commit Message Format

Use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

Example: `feat: add file size validation to document upload`

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Request review from at least one team member
4. Address review feedback
5. Merge after approval

## Code Review Guidelines

**Reviewers should check:**
- Code follows style guidelines
- Tests are included and pass
- Error handling is appropriate
- No security issues (no hardcoded secrets, proper validation)
- Documentation is updated if needed

**Authors should:**
- Keep PRs focused (one feature/fix per PR)
- Write clear PR descriptions
- Respond to feedback promptly

## Questions?

Open an issue or contact the maintainers.
