# CrimeScrape

CrimeScrape is a Python tool that enables users to search for individuals across various law enforcement databases. It supports both direct search through Python functions and RESTful API endpoints, making it suitable for a range of integrations.

## Features

- **Multi-database search**: CrimeScrape searches amongst an extensive list of sites under `/sources`.
- **Headless Mode**: Optionally run searches in headless mode for automated, GUI-less operation.
- **REST API**: Query and retrieve results using convenient API endpoints.
- **Cache management**: Cache results and serve the cache for faster calls while passively detecting for stale cache.

## Returned JSON Structure

The tool returns a JSON object with the following structure:

```json
{
    "risk": "low",
    "notices": {
        "source_1": {
            "id": "id",
            "charges": [
                "charge1",
                "charge2"
            ]
        }
    }
}
```

### Fields

- **risk**: Indicates the risk level associated with the individual (e.g., "Low", "Medium", "High", "Dangerous").
- **notices**: Contains details about notices from various sources:
  - **source_1**: Placeholder for the specific source (e.g., "FBI", "Interpol").
    - **id**: Identifier for the notice.
    - **charges**: Array of charges associated with the individual.

## REST API Documentation

### Base URL

`http://localhost:5000/api`

#### Search by name

**Endpoint**: `/search/<fname>/<lname>`

**Description**: Searches for criminal records for given name.

**URL Parameters**:

- `fname` - First name of the individual
- `lname` - Last name of the individual

#### **Examples**

**Example Request**:

```http
GET /api/search/John/Doe
```

**Example Response**:

```json
{
  "status": "fresh",
  "data": [
    {
      "risk": "low",
      "notices": {
        "fbi": {
          "id": "123",
          "charges": ["fraud", "theft"]
        },
        "interpol": {
          "id": "456",
          "charges": ["terrorism"]
        }
      }
    }
  ]
}
```

There are 3 different status codes for this:

1. "fresh" - The query has been just searched.
2. "cached" - The served results were found in the cache and served.
3. "error" - An error occured. Followed by some info for the user.

**Error Response**:

```json
{
    "status": "error",
    "info": "An internal error has arisen"
}
```

## Requirements

The code brings a `requirements.txt` file to install dependencies by using the command `python3 -m pip install -r requirements.txt`. Using a venv
is recommended but not necessary.

For using a venv, there are instructions below.

## Installation

### Creating a Virtual Environment

#### Windows

1. Open a command prompt and navigate to your project directory.
2. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment:

   ```bash
   .venv\Scripts\activate
   ```

#### Linux

1. Open a terminal and navigate to your project directory.
2. Create a virtual environment:

   ```bash
   python3 -m venv .venv
   ```

3. Activate the virtual environment:

   ```bash
   source .venv/bin/activate
   ```

### Installing Dependencies

With your virtual environment activated (both Windows and Linux), install the required packages:

```bash
python -m pip install -r requirements.txt # install python dependencies
playwright install # finish playwright installation
playwright install-deps # install dependencies
```

## Usage

To start the CrimeScrape API, run the following command in your terminal. Use `--help` to see more options:

```bash
python crimescrape.py --run-as-api
```

### Standalone mode

The standalone mode is the default and requires two arguments:

1. `--query`: This is the file containing the query to search
2. `--results`: This is the file on which results will be stored after the search

#### Query format

The format of the query should be as follows, since as of now there is only name-based modules:

```json
{
    "fname": "RUJA",
    "lname": "IGNATOVA"
}
```

#### Results format

The results format is similar to what would be expected from the API mode:

```json
{
    "FBISearch": {
        "notices": {
            "fbi-most-wanted": {
                "charges": [
                    "Conspiracy to commit wire fraud",
                    "Wire fraud",
                    "Conspiracy to commit money laundering",
                    "Conspiracy to commit securities fraud",
                    "Securities fraud"
                ],
                "id": ""
            }
        },
        "risk": "High"
    },
    "InterpolSearch": {
        "notices": {
            "interpol-red-notice": {
                "charges": [
                    "Jointly committed especially serious case of fraud, money laundering"
                ],
                "id": "2020/9611"
            }
        },
        "risk": "Dangerous"
    },
    "OpenSanctionsSearch": {
        "notices": {
            "opensanctions": {
                "charges": [
                    "https://www.opensanctions.org/entities/Q20819716/"
                ],
                "id": ""
            }
        },
        "risk": "Dangerous"
    }
}
```
