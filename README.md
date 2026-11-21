# F.R.E.D. (Fantasy Recognition Evaluation Determinator)

A Python-based fantasy football analytics and decision-support project designed to help fantasy managers evaluate players, identify roster movements, and make data-informed decisions.


## Project Overview

Fantasy Recognition Evaluation Determinator (FRED) is a personal sports analytics project that combines fantasy football data collection, statistical analysis, and recommendation algorithms.

The project initially focuses on a 16-team ESPN fantasy football league using half-PPR scoring.

Its long-term goal is to develop an AI-assisted fantasy football manager capable of evaluating waiver-wire opportunities, analyzing trades, optimizing starting lineups, and explaining recomendations using quantitative evidence.

The project also serves as a practical application of Python, SQL, data engineering, statistical analysis, and software testing.


## Current Features

### ESPN Data Collection
- Retrieve fantasy league settings, teams, and player rosters
- Collect player statistics and projections
- Retrieve available free agents
- Collect weekly fantasy scoring histories

### Data Storage Processing
- Store league and player information in SQLite
- Maintain structured player, roster, and free-agent datasets
- Validate data integrity and player ownership
- Export analytical results to CSV

### Player Evaluation
- Calculate Value Over Replacement (VOR)
- Estimate position-specific replacement levels
- Account for positional scarcity and league roster requirements

### Waive-Wire Analysis
- Evaluate potential player additions and drops
- Compare historical production and projected performance
- Account for positional depth and roster needs
- Classify transactions by recommendation strength
- Analyze recent player performance usign three-game and five-game scoring averages

### Testing and Validation
- Automated tests using pytest
- Data integrity validation
- Positional-depth safeguards
- Validation of waiver recommendation classifications and recent performance signals


## Technology Stack

### Currently used
- Python 3.12
- pandas
- SQLite
- ESPN Fantasy Football API (`espn-api`)
- pytest
- Git and Github

### Planned/Under consideration
- Streamlit for interactive dashboards
- LLM APIs for natural language explanations and recommendations
- Additional statistical modeling and optimization teechniques


## Installation

### Prerequisites
- Python 3.12 or later (project developed using Python 3.12)
- Git
- An ESPN Fantasy Football league
- ESPN authenticaion cookies for private leagues

### Step 1: Clone the Repository
```
git clone https://github.com/YOUR_USERNAME/fantasy-recognition-evaluation-determinator
cd fantasy-recognition-evaluation-determinator
```

Replace `YOUR_USERNAME` with the GitHub account hosting the repository.

### Step 2: Create a Virtual Environment
```
python3 -m venv .venv
```

Activate the environment.

macOS/Linux:
```
source .venv/bin/activate
```

Windows (PowerShell):
```
.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```
python -m pip install -r requirements.txt
```

The project currently uses:
- pandas and NumPy for data processing and numerical analysis
- `espn-api` for ESPN Fantasy Football data access
- `python-dotenv` for environment variable management
- pytest for automated testing

### Step 4: Configure Environment Variables
Copy the example environment file:

macOS/Linux:
```
cp .env.example .env
```

Windows (PowerShell):
```
Copy-Item .env.example .env
```

Update .env with your ESPN league configuration:
```
ESPN_LEAGUE_ID=your_league_id
ESPN_SEASON=2026

ESPN_S2=your_espn_s2_cookie
ESPN_SWID=your_espn_swid_cookie
```

The `ESPN_S2` and `ESPN_SWID` values are required for accessing private ESPN fantasy leagues.

The `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` fields are reserved for future AI integration and are not currently required.

**Security**: Never commit .env, authentication cookies, or API keys to GitHub. The project's `.gitignore` excludes local environment files.

### Step 5: Verify Installation
Run:
```
python main.py
```

Expected output:
```
======================================================
F.R.E.D. (Fantasy Recognition Evaluation Determinator)
======================================================
Team: A Thousand Myles
League: 16 Teams
Scoring: Half-PPR
Format: One QB

Application initialized successfully!
```

This verifies that the initial application script executes. It does not test ESPN authentication or database connectivity.


## Getting Started
FRED is currently a command-line analytics project under active development.

The application collecs ESPN fantasy football data, stores it in SQLite, and uses statistical methods to evaluate players and potential roster improvements.

### Run Automated Tests
From the project root:
```
pytest -v
```
The existing test suite covers waiver recommendation classifications, positional-depth safeguards, and recent-performance signals.

### Explore the Analytics Modules
The following modules are available:
| Module                             | Purpose                                          |
|------------------------------------|--------------------------------------------------|
| `src.collect_rosters`              | Collect fantasy team rosters                     |
| `src.collect_free_agents`          | Retrieve available free agents                   |
| `src.collect_weekly_stats`         | Collect weekly player scoring histories          |
| `src.calculate_vor`                | Calculate Value Over Replacement                 |
| `src.calculate_recent_performance` | Analyze recent scoring performance               |
| `src.explore_waiver_candidates`    | Evaluate potential waiver transactions           |
| `src.evaluate_trades`              | Evaluate proposed player trades (in development) |

These modules are implemented as separate development scripts rather than a single automated application workflow.

### Local Data Requirements
The project currently uses CSV files and a SQLite database stored in the `data/` and `database/` directories.

These files are excluded from version control because they contain league-specific information or generated data.

A fresh installation will require collecting and importing league data before running analytics that depend on the database.

A fully documented, reproducible data pipeline is planned as a future improvement.

### Current Development Limitations
- The project is configured around a 16-team, half-PPR ESPN league.
- Some analytics scripts require locally generated datasets.
- The complete data collection and database initialization workflow is not yet automated.
- Trade evaluation is under development.
- Interactive dashboards and AI-generated recommendations are planned features.

## Project Structure
```
fantasy-recognition-evaluation-determinator/
|--- README.md
|--- main.py
|--- requirements.txt
|--- pytest.ini
|--- .env.example
|--- .gitignore
|
|--- src/
|   |--- espn_connection.py
|   |--- collect_rosters.py
|   |--- collect_free_agents.py
|   |--- collect_weekly_stats.py
|   |--- create_database.py
|   |--- load_roster_data.py
|   |--- load_weekly_stats.py
|   |--- calculate_vor.py
|   |--- calculate_recent_performance.py
|   |--- explore_waiver_candidates.py
|   |--- evaluate_trades.py
|   |--- ...
|
|--- tests/
|   |--- test_wavier_candidates.py
|   |--- test_recent_form.py
|
|--- data/
|   |--- teams.csv
|   |--- rosters.csv
|   |--- free_agents.csv
|   |--- player_weekly_stats.csv
|   |--- vor_rankings.csv
|
|--- database/
    |--- fantasy_league.db
```

### Directory Responsibilities

`src/` - Application Logic
Contains ESPN data collection, database operations, player evaluation, statistical analysis, and recommendation algorithms.

`tests/` - Automated Testing
Contains pytest tests for analytical calcuations, recommendation classifications, and data validation.

`data/` - Intermeidate Datasets
Stores collected and processed CSV files used by the analytics pipeline.

`database/` - Persistent Storage
Contains the local SQLite database holding league information, player records, roster assignments, and historical scoring data.

`main.py` - Initialization Script
Displays the current project configuration and confirms that the intial application script runs.

**Note**: The CSV datasets and SQLite database shown above are generated locally and are excluded from Git. They may not exist immediately after cloning the repository.


## Development Roadmap

| Phase | Description                                  | Status      |
|-------|----------------------------------------------|-------------|
| 1     | Development environment and repository setup | Complete    |
| 2     | ESPN league data collection                  | Complete    |
| 3     | Database development and validation          | Complete    |
| 4     | Player evaluation and VOR analysis           | Complete    |
| 5     | Waiver-wire recommendation engine            | Complete    |
| 6     | Trade evaluation engine                      | In progress |
| 7     | Matchup analysis                             | Planned     |
| 8     | AI assisted recommendations                  | Planned     |
| 9     | Analytics dashboard                          | Planned     |


## Analytical Methodology

### Value Over Replacement (VOR)

VOR measures a player's fantasy production relative to an estimated replacement-level player at the same position.

Replacement levels are estimated using league roster requirements, positional demand, and available player production.

### Recent Performance

The project calculates recent player performance using recorded weekly fantasy scores, including:
- Last 3 recorded games
- Last 5 recorded games
- Season-long scoring average
- Recent performance relative to season average
- Data freshness indicators

### Waiver Recommendations

Potential add/drop transactions are evaluated using player value, historical production, projections, positional needs, and minimum roster-depth requirements.

The recommendation engine distinguishes between strong candidates, transactions worth considering, and low-priority moves.

### Trade Evaluation (in development)

The trade evaluation engine will assess proposed player exchanges between fantasy teams.

Planned capabilities include:
- Player ownership validation
- 1 for 1 and multi-player trade analysis
- VOR and projected production comparisons
- Positional roster-fit analysis
- Starting lineup impact
- Evaluation of potential benefits for both teams

### Known Limitations

- Initial implemenation targets a specific ESPN fantasy football league and scoring format
- Historical fantasy production does not guarantee future performance
- VOR estimates depend on replacement-level assumptions
- Recent performance statistics may be incomplete for players with limited recorded games
- Current waiver recommendations do not guarantee that a transaction will improve future results
- Trade evaluation, lineup optimization, and AI integration remain under development

### Future improvements

- Automated trade candidate discovery
- Starting lineup optimization
- Weekly matchup projections
- Enhanced statistical forecasting
- AI generated recommendation explanations
- Interactive analytics dashboards


## Project Status

**Active development - Phase 6: Trade Evaluation Engine**

This project is being developed incrementally, with an emphasis on data quality, interpretatble analytics, automated testing, and maintainable Python code.
