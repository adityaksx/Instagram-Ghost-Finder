# Instagram Ghost Finder

A simple Python tool that analyzes your Instagram data export and generates an interactive HTML report showing:

* Followers
* Following
* Mutuals
* Fans — accounts that follow you but you don't follow
* Ghosts — accounts you follow that don't follow you back

## Features

* Reads Instagram JSON data exports
* Finds mutual followers automatically
* Identifies accounts that don't follow you back
* Identifies accounts you don't follow back
* Generates a clean interactive HTML report
* Search accounts by username
* Sort accounts by newest, oldest, or username
* Open Instagram profiles directly from the report
* No external Python dependencies

## Requirements

* Python 3.x
* Instagram data export containing:

  * `followers_1.json`
  * `following.json`

## Installation

Clone the repository:

```bash
git clone https://github.com/adityaksx/Instagram-Ghost-Finder.git
cd instagram-ghost-finder
```

No additional Python packages are required.

## Usage

Place your Instagram JSON files in the project directory:

```text
instagram-ghost-finder/
├── ghost_finder.py
├── followers_1.json
└── following.json
```

Run:

```bash
python ghost_finder.py
```

The report will be generated as:

```text
instagram_report.html
```

Open the generated HTML file in any browser.

## Custom Files

You can provide different file paths:

```bash
python ghost_finder.py --followers followers_1.json --following following.json
```

You can also choose the output filename:

```bash
python ghost_finder.py --output report.html
```

## How It Works

The tool compares the follower and following lists from your Instagram export.

```text
Following - Followers = Not Following Back

Following ∩ Followers = Mutuals

Followers - Following = Fans
```

The generated report provides separate sections for each category.

## Privacy

Your Instagram JSON files are processed locally by the Python script. The generated report is also created locally on your computer.

Do not upload your Instagram data export to a public repository.

Consider adding the following files to `.gitignore`:

```gitignore
followers_*.json
following*.json
instagram_report.html
__pycache__/
```

## License

This project is available for personal and educational use.
