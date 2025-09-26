# Contributing to Agentic Red-Team Manager

We welcome contributions to the Agentic Red-Team Manager project! This document provides guidelines for contributing.

## 🤝 How to Contribute

### Reporting Issues
- Use the GitHub issue tracker
- Provide clear, detailed descriptions
- Include steps to reproduce bugs
- Specify your environment (OS, Python version, etc.)

### Suggesting Features
- Open an issue with the "enhancement" label
- Describe the feature and its use case
- Explain why it would be valuable

### Contributing Code

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Add tests** for new functionality
5. **Run the test suite**
   ```bash
   pytest
   ```
6. **Run linting and formatting**
   ```bash
   black src/ tests/
   flake8 src/ tests/
   ```
7. **Commit your changes**
   ```bash
   git commit -m "Add feature: your feature description"
   ```
8. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
9. **Create a Pull Request**

## 📋 Development Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use Black for code formatting
- Use type hints for all functions
- Write docstrings for all public methods

### Testing
- Write unit tests for all new functionality
- Aim for >90% test coverage
- Use pytest for testing framework
- Mock external dependencies in tests

### Documentation
- Update README.md if needed
- Add docstrings to all new functions/classes
- Update configuration examples
- Add usage examples for new features

### Security
- Never commit API keys or secrets
- Follow secure coding practices
- Report security issues privately
- Consider security implications of new features

## 🏗️ Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ajaykallepalli/AgenticRedTeam.git
   cd AgenticRedTeam
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Run tests**
   ```bash
   pytest
   ```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

## 📝 Commit Message Format

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
- `feat(scenarios): add new attack vector type`
- `fix(sandbox): resolve Docker container cleanup issue`
- `docs: update API documentation`

## 🔒 Security Guidelines

- **Never commit sensitive data** (API keys, passwords, etc.)
- **Use environment variables** for configuration
- **Validate all inputs** to prevent injection attacks
- **Follow principle of least privilege**
- **Regularly update dependencies**

## 🎯 Areas for Contribution

We especially welcome contributions in these areas:

### High Priority
- Additional attack vectors and scenarios
- Improved safety evaluation algorithms
- Better reporting and visualization
- Performance optimizations

### Medium Priority
- UI/UX improvements
- Additional LLM integrations
- Enhanced monitoring and alerting
- Documentation improvements

### Research Areas
- Novel adversarial techniques
- Automated scenario generation
- Advanced safety metrics
- Ethical AI considerations

## 📞 Community

- **Discord**: [Join our community](https://discord.gg/agenticredteam)
- **Discussions**: Use GitHub Discussions for questions
- **Email**: support@agenticredteam.com

## 🏷️ Labels

We use these labels to organize issues and PRs:

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `priority:high`: High priority items
- `security`: Security-related issues

## ✅ Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventional format
- [ ] No merge conflicts
- [ ] PR description explains the changes

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Project documentation

Thank you for contributing to Agentic Red-Team Manager!