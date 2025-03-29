# Conference Outreach Automation Agent (MVP)

An automated tool for finding and contacting event organizers for relevant tech conferences in Europe.

## Overview

This tool automates the process of:
1. Scraping conference information from popular event listing websites
2. Extracting contact details of event organizers
3. Generating personalized outreach emails
4. Exporting the results to a CSV file

## Features

- **Multi-source scraping**: Extracts conference data from multiple sources (conferenceindex.org, 10times.com, eventbrite.com)
- **Smart contact extraction**: Intelligently identifies and extracts organizer contact information from conference websites
- **Personalized email generation**: Uses OpenAI's GPT-4 to create human-like, personalized outreach emails
- **Anti-blocking measures**: Implements delays and user-agent rotation to avoid being blocked by websites
- **Flexible filtering**: Filter conferences by keywords, location, and date range
- **CSV export**: Exports results in a structured format for easy integration with other tools
- **Python 3.12 Windows compatibility**: Special handling for Windows + Python 3.12 environments

## Installation

### Prerequisites

- Python 3.8 or higher
- Playwright (for web scraping)
- OpenAI API key (for email generation)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/conference-outreach-agent.git
   cd conference-outreach-agent
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```
   playwright install
   ```

4. Run the setup wizard to create your configuration file:
   ```
   python cli.py --setup
   ```
   
   This will guide you through setting up your:
   - OpenAI API key
   - Scraping settings
   - Company and speaker information

## Usage

### Basic Usage

Run the tool with default settings:

```
python cli.py
```

This will:
- Search for AI and Tech conferences in Europe
- Extract organizer contact information
- Generate personalized outreach emails
- Export results to `conference_outreach_results.csv`

### Web Interface

For a more user-friendly experience, you can use the Streamlit web interface:

```
streamlit run streamlit_app.py
```

This provides a graphical interface for:
- Setting up your configuration
- Running the scraper with custom settings
- Viewing and downloading results

### Advanced Usage

Customize the search with command-line arguments:

```
python cli.py --sources conferenceindex 10times --keywords "Artificial Intelligence" "Machine Learning" --location "Europe" --start-date 2025-01-01 --end-date 2025-12-31 --max-conferences 20 --output results.csv --headless
```

### Command-line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--sources` | List of sources to scrape | conferenceindex, 10times, eventbrite |
| `--keywords` | Keywords to filter conferences | AI, Tech, Artificial Intelligence, Machine Learning |
| `--location` | Location to filter conferences | Europe |
| `--start-date` | Start date for conference search (YYYY-MM-DD) | Current date |
| `--end-date` | End date for conference search (YYYY-MM-DD) | None (no end date) |
| `--max-conferences` | Maximum number of conferences to process | 10 |
| `--output` | Output file path | conference_outreach_results.csv |
| `--headless` | Run browser in headless mode | False (browser visible) |
| `--setup` | Run the setup wizard | False |

## Output Format

The tool generates a CSV file with the following columns:

- `conference_name`: Name of the conference
- `date`: Start date of the conference
- `end_date`: End date of the conference (if available)
- `location`: Location of the conference
- `website_url`: URL of the conference website
- `organizer_name`: Name of the conference organizer
- `organizer_role`: Role of the organizer (if available)
- `email`: Email address of the organizer
- `phone`: Phone number of the organizer (if available)
- `linkedin`: LinkedIn profile of the organizer (if available)
- `generated_email_message`: Personalized outreach email for the organizer

## Compatibility Notes

### Python 3.12 on Windows

This tool includes special handling for Python 3.12 on Windows, which has known compatibility issues with Playwright's API. When running on Windows with Python 3.12, the tool automatically switches to a mock implementation that doesn't use Playwright at all.

**IMPORTANT**: The mock implementation only provides sample conference and contact data to demonstrate the functionality. **If you need real conference data and contacts, you must use a different platform or Python version.**

The mock implementation:
- Provides sample conferences across various industries (tech, healthcare, finance, logistics, entrepreneurship, etc.)
- Filters these sample conferences based on your keywords, location, and date criteria
- Generates fictional contact information for demonstration purposes

For real data and full functionality, you must:
1. Use Python 3.11 or earlier on Windows
2. Use a non-Windows platform (macOS or Linux)
3. Wait for Playwright to add full support for Python 3.12 on Windows

## Limitations

- The tool relies on the structure of third-party websites, which may change over time
- Some conference websites may implement anti-scraping measures
- Email generation requires an OpenAI API key and incurs usage costs
- The tool may not find contact information for all conferences
- **On Windows with Python 3.12, the tool uses mock data instead of actual web scraping - the contacts are not real**
- For real contact information, you must use Python 3.11 or earlier, or a non-Windows platform

## Future Enhancements

- Add more conference sources
- Implement email sending via SMTP or Gmail API
- Create a more advanced web interface
- Add support for more regions beyond Europe
- Implement more advanced contact extraction techniques
- Full async implementation for better Windows + Python 3.12 support

## Running Tests

To run the tests:

```
python run_tests.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
