# Contributing to Pentair Water Softener Integration

Thank you for considering contributing to this Home Assistant integration!

## How to Contribute

### Reporting Bugs

1. Check if the issue has already been reported
2. Create a new issue with:
   - A clear title and description
   - Steps to reproduce the problem
   - Your Home Assistant version
   - Debug logs (see README for how to enable)

### Suggesting Features

1. Open an issue describing the feature
2. Explain why it would be useful
3. Provide examples if applicable

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test your changes
5. Commit with clear messages (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install erie-connect
   ```
3. Test the API connection:
   ```bash
   python test_connection.py
   ```

## Code Style

- Follow Home Assistant's [development guidelines](https://developers.home-assistant.io/docs/development_guidelines)
- Use type hints
- Add docstrings to functions and classes
- Run linting before submitting

## Testing

Before submitting a PR:

1. Test the connection script works
2. Test the integration in Home Assistant
3. Verify all entities are created correctly
4. Check debug logs for errors

## Questions?

Open an issue with your question and we'll try to help!
