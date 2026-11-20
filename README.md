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
