# Contributing to HA Config Manager

Thank you for your interest in contributing! 🎉

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, HA version)
- **Logs and screenshots** if applicable

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** - why this would be useful
- **Possible implementation** if you have ideas

### Pull Requests

1. **Fork the repo** and create your branch from `develop`
2. **Make your changes**
3. **Add tests** if applicable
4. **Ensure tests pass**: `make test`
5. **Update documentation** if needed
6. **Follow code style**: `make format && make lint`
7. **Write good commit messages** (see below)
8. **Create PR** against `develop` branch

## Development Process

### Setup

```bash
git clone https://github.com/cmdchar/ha-config-manager.git
cd ha-config-manager
make install
```

### Branching

- `main` - stable production code
- `develop` - integration branch for features
- `feature/*` - new features
- `bugfix/*` - bug fixes
- `hotfix/*` - urgent fixes for main

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

**Examples:**
```
feat(addon): add rollback support
fix(orchestrator): resolve deployment timeout
docs: update installation guide
```

### Testing

```bash
# Run all tests
make test

# Run specific tests
pytest tests/unit/test_deployment.py

# With coverage
make coverage
```

### Code Style

**Python:**
- Follow PEP 8
- Use Black for formatting
- Use type hints
- Write docstrings

**JavaScript/Vue:**
- Follow Vue.js style guide
- Use ESLint
- Use TypeScript when possible

## Release Process

1. Update version in relevant files
2. Update CHANGELOG.md
3. Create PR to `main` from `develop`
4. After merge, create GitHub release
5. Tag release: `git tag v1.0.0`

## Getting Help

- Check [Documentation](docs/)
- Ask in [GitHub Discussions](https://github.com/cmdchar/ha-config-manager/discussions)
- Join our [Discord](https://discord.gg/ha-config-manager) (coming soon)

## Recognition

Contributors will be added to README.md and releases.

Thank you for contributing! 🙏
