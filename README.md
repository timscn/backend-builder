# backend-builder

A log processing pipeline for parsing JSONL files, validating structure, and aggregating user/feature metrics.

## Project Structure

```
backend-builder/
├── part0_generation/     # Generate sample log data
├── part1_parsing/        # Parse and validate logs
├── part2_aggregation/    # Compute aggregated metrics
├── utils/                # Shared utilities
├── tests/                # Test suite
└── output/               # Generated output files
```

## Setup

```bash
pip install -r requirements.txt
```

## Quick Start

Run the full pipeline in order:

```bash
# 1. Generate sample log data
python3 part0_generation/generate_practice_file.py

# 2. Parse and validate logs
python3 part1_parsing/parse_logs.py

# 3. Aggregate metrics
python3 part2_aggregation/aggregate_metrics.py
```

## Flow Explanation

1. **Start:** The process begins with the input file `output/logs.jsonl`.

2. **Part 1 (Parsing):**
   - Part1_Parser (`parse_logs.py`) reads the file.
   - It validates each line into a `RawLog` object (checking timestamps, required fields).
   - It groups these logs and saves them to `output/parsed_summary.json`.

3. **Part 2 (Aggregation):**
   - Part2_Aggregator (`aggregate_metrics.py`) reads the intermediate JSON.
   - It pairs "start" and "end" logs to create Session objects (calculating duration).
   - It aggregates these sessions by User, Feature, and Time.

4. **End:** The final metrics are saved to `output/final_summary.json`.

---

## Part 0: Log Generation

**Script:** `part0_generation/generate_practice_file.py`

Generates a sample JSONL file with ~100 lines for testing the pipeline. Includes deliberate error cases (malformed JSON, missing fields, invalid timestamps) to validate error handling.

### Usage

```bash
python3 part0_generation/generate_practice_file.py
```

### Output

- `output/logs.jsonl` — Sample log data

---

## Part 1: Parsing and Understanding Log Structure

**Script:** `part1_parsing/parse_logs.py`

Parses JSONL files, validates structure, groups data by user and feature, and produces clean statistics.

### Features

- **Error Handling**: Gracefully handles malformed JSON, missing fields, and invalid data
- **Structure Validation**: Validates required fields (user_id, feature, timestamp, action)
- **Data Grouping**: Groups logs by user_id and feature for analysis
- **Summary Generation**: Creates comprehensive statistics and saves to JSON

### Usage

```bash
python3 part1_parsing/parse_logs.py
```

### Output

- Console: Parsing statistics, user/feature/action statistics
- `output/parsed_summary.json` — Complete structured data

### Error Types Handled

1. **Parse Errors**: Malformed JSON (broken strings)
2. **Validation Errors**:
   - Missing required fields (e.g., missing "feature")
   - Invalid timestamp format
   - Invalid action or feature values

---

## Part 2: Aggregation and Time-Based Metrics

**Script:** `part2_aggregation/aggregate_metrics.py`

Builds on Part 1 to compute higher-level metrics involving time intervals and related entities.

### Features

- **Session Duration Calculation**: Matches start/end actions to calculate how long users spend in each feature
- **Time Interval Grouping**: Groups sessions by hourly intervals to identify usage patterns
- **Feature-Level Aggregation**: Higher-level metrics grouped by feature (total sessions, durations, unique users)
- **User-Level Aggregation**: Higher-level metrics grouped by user (total sessions, durations, features used)
- **Final Summary**: Combines Part 1 and Part 2 results into a comprehensive report

### Usage

```bash
python3 part2_aggregation/aggregate_metrics.py
```

### Output

- Console: Aggregated metrics by feature, user, and time intervals
- `output/final_summary.json` — Complete aggregated data

### Metrics Calculated

1. **Session Durations**: Time between start and end actions for each user-feature pair
2. **Feature Aggregation**:
   - Total sessions per feature
   - Total and average duration per feature
   - Min/max durations
   - Unique users per feature
3. **User Aggregation**:
   - Total sessions per user
   - Total and average duration per user
   - Features used by each user
   - Sessions breakdown by feature
4. **Time Interval Aggregation**:
   - Sessions grouped by hourly intervals
   - Total and average durations per time period

### Notes

- Incomplete sessions (unmatched start/end pairs) are tracked but excluded from duration calculations
- All durations are calculated in seconds and formatted for human readability
- The script reuses the `parsed_summary.json` output from Part 1

---

## Tests

```bash
pytest
```
