
# Deauville Festival du Rire 2027

## Python Festival Management System

A complete Python application for managing the Deauville Festival du Rire, taking place from June 10 to June 13, 2027.

The application manages artists, venues, performances, scheduling constraints, and workshop registrations.

It provides three interfaces:

- A command-line interface (CLI)
- A REST API developed with FastAPI
- A public website and an administration dashboard

The initial festival dataset contains:

- 4 venues
- 12 artists
- 23 performances
- 4 festival days

The project was developed using object-oriented programming, inheritance, abstraction, business-rule validation, JSON persistence, and automated testing.

---

## 1. Technologies

| Technology | Purpose |
|------------|---------|
| Python 3.12 | Main programming language |
| FastAPI | REST API and web server |
| Pydantic | HTTP request validation |
| Uvicorn | ASGI server |
| Pytest | Automated testing |
| uv | Python environment and dependency management |
| JSON | Data persistence |
| HTML, CSS, JavaScript | Public and administration interfaces |

---

## 2. Installation

### Requirements

- Python 3.12
- uv
- Git (for cloning the repository)

### Install uv

On Windows, open PowerShell and execute:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Clone the project

```bash
git clone <repository-url>
cd deauville-starter-main
```

Replace `<repository-url>` with the actual Git repository URL.

### Install dependencies

```bash
uv sync
```

This command creates the virtual environment and installs the dependencies defined in `pyproject.toml` and `uv.lock`.

No manual virtual environment activation is required when using `uv run`.

---

## 3. Running the Application

### 3.1 Start the FastAPI server

From the root directory:

```bash
uv run uvicorn api:app --reload
```

The server will start at:

http://127.0.0.1:8000

Available interfaces:

| Interface | URL |
|-----------|-----|
| Public website | http://127.0.0.1:8000/ |
| Administration dashboard | http://127.0.0.1:8000/admin/ |
| Interactive API documentation | http://127.0.0.1:8000/docs |
| Festival API | http://127.0.0.1:8000/api/festival |

The web interfaces communicate with the Python backend through the JSON API.

### 3.2 Command-line interface

The project also provides a CLI through `main.py`.

#### Display the programme for one festival day

```bash
uv run main.py programme 2027-06-11
```

Example output:

```text
=== PROGRAMME DU 2027-06-11 ===
11/06 10:30 | Improv for Beginners | La Cabane
11/06 15:00 | Writing a Punchline | Le Kiosque
11/06 18:00 | Nothing Serious | Théâtre des Planches
11/06 20:30 | Tall Tales | Grand Casino
11/06 21:30 | Straight Face | Théâtre des Planches
11/06 23:30 | Late Laughs | Le Kiosque
12/06 01:00 | After Hours | Le Kiosque
```

#### Display artists and their number of performances

```bash
uv run main.py artists
```

#### Display current and upcoming performances

```bash
uv run main.py now 2027-06-12T21:15
```

This command shows:

- Performances currently on stage
- The next three performances

All dates and times use local festival time without timezone information.

---

## 4. Project Structure

The project is organized into independent modules to separate responsibilities.

```text
deauville-starter-main/
|
|-- festival/
|   |-- __init__.py
|   |-- models.py
|   |-- festival.py
|   |-- errors.py
|   |-- storage.py
|   |-- service.py
|
|-- data/
|   |-- festival.json
|
|-- tests/
|   |-- test_festival.py
|   |-- test_storage.py
|   |-- test_service.py
|   |-- test_api.py
|
|-- examples/
|
|-- web/
|   |-- public/
|   |-- admin/
|
|-- main.py
|-- api.py
|-- API.md
|-- pyproject.toml
|-- uv.lock
|-- README.md
```

### Module Responsibilities

#### `festival/models.py`

Contains the domain classes:

- Artist
- Venue
- Performance
- Solo
- Lineup
- Workshop

It validates the characteristics of individual entities, including names, capacities, duration, and specific performance requirements.

#### `festival/festival.py`

Contains the `Festival` class.

It manages artists, venues, and performances while enforcing scheduling rules and detecting conflicts.

It also supports:

- Adding artists and venues
- Adding performances
- Consulting the festival programme
- Finding performances currently on stage
- Finding upcoming performances
- Moving performances
- Replacing performances
- Cancelling performances

#### `festival/errors.py`

Contains custom exception classes:

- FestivalError
- ValidationError
- NotFoundError
- ConflictError
- StorageError

These exceptions distinguish validation problems, missing resources, scheduling conflicts, and storage failures.

#### `festival/storage.py`

Manages JSON persistence.

It provides:

- `load_festival()`
- `save_festival()`

The loading process reconstructs Python objects and checks business rules.

The saving process writes a temporary file before replacing the existing JSON file to reduce the risk of partially written data.

#### `festival/service.py`

Contains `FestivalService`.

The service layer coordinates business operations and persistence.

For each successful modification, the service:

1. Loads the current festival.
2. Applies the requested operation.
3. Validates the business rules.
4. Saves the updated festival.

If a business-rule validation fails, the service does not save the change.

#### `api.py`

Defines the FastAPI application.

It provides REST endpoints for reading and modifying festival data.

It also serves the public website and administration dashboard.

#### `main.py`

Implements the command-line interface.

#### `tests/`

Contains automated tests for the model, storage, service, and REST API.

---

## 5. Object-Oriented Design

The application follows object-oriented programming principles.

### 5.1 Main Classes

| Class | Responsibility |
|-------|----------------|
| Artist | Represents an artist and their information |
| Venue | Represents a venue and its capacity |
| Performance | Abstract base class for performances |
| Solo | Represents a solo performance |
| Lineup | Represents a host and multiple acts |
| Workshop | Represents an interactive workshop |
| Festival | Manages the programme and scheduling rules |
| FestivalService | Coordinates operations and persistence |

### 5.2 Inheritance

`Performance` is an abstract base class.

The following classes inherit from it:

```text
             Performance
                  |
        +---------+---------+
        |         |         |
       Solo     Lineup    Workshop
```

Common properties include:

- Title
- Venue
- Start time
- Duration
- End time
- Festival day
- Description
- Performance identifier

Each subclass implements its own validation rules and the `artist_slugs()` method.

This design reduces code duplication and makes the system easier to extend.

### 5.3 Abstraction

The abstract class `Performance` defines the common interface for all performances.

Its subclasses must implement:

```python
artist_slugs()
```

This allows the `Festival` class to detect scheduling conflicts without needing to know whether a performance is a solo show, a lineup, or a workshop.

### 5.4 Encapsulation

Core attributes are accessed through properties.

For example:

```python
artist.name
artist.slug
performance.start
performance.end
```

The `Festival` class stores its collections internally and exposes ordered views through properties.

Business operations are implemented as methods rather than duplicated in the API or CLI.

Python's internal attributes are still technically accessible, so the current model is not fully immutable. The intended application workflow uses the public methods to preserve business rules.

---

## 6. Business Rules

### 6.1 Names and Identifiers

All names must be non-empty and are stored without surrounding whitespace.

Artists and venues use normalized slugs.

Examples:

```text
Théâtre des Planches -> theatre-des-planches
Élodie Marchal -> elodie-marchal
```

Performance identifiers contain the venue slug and start time.

Example:

```text
le-kiosque-2027-06-12-0100
```

This ensures that each scheduled performance has a predictable identifier.

### 6.2 Festival Days

A festival day begins at 06:00 and ends at 05:59 the following morning.

For example:

A performance starting on June 12 at 01:00 belongs to the June 11 programme.

The festival day is calculated using:

```python
(self.start - timedelta(hours=6)).date()
```

### 6.3 Scheduling Constraints

A performance must belong to one of the festival days.

The festival also enforces a minimum 30-minute gap between performances:

- In the same venue
- Featuring the same artist
- Regardless of the artist's role

For example, an artist cannot perform in one venue and immediately appear in another venue without the required break.

Conflict detection is implemented in the `Festival` class so that the same rules apply to the CLI, API, and tests.

### 6.4 Solo Performances

A solo performance contains one artist.

The minimum audience age must be between 0 and 18.

### 6.5 Lineup Performances

A lineup contains:

- One host
- At least two acts

The host cannot also appear as an act.

An artist cannot appear twice in the same lineup.

Each act requires at least 10 minutes.

There must also be 3 minutes between consecutive acts.

Example for three acts:

```text
3 x 10 + 2 x 3 = 36 minutes
```

### 6.6 Workshops

A workshop contains one teacher and a list of registered participants.

The effective capacity is:

```python
min(max_participants, venue.capacity)
```

Participant names are compared without case sensitivity.

For example:

```text
Camille R.
camille r.
```

These names represent the same participant.

Duplicate registrations and registrations in a full workshop are rejected with a conflict error.

---

## 7. REST API

The project implements the API contract described in `API.md`.

### 7.1 Read Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/festival` | Festival information |
| GET | `/api/venues` | List of venues |
| GET | `/api/artists` | List of artists |
| GET | `/api/artists/{slug}` | Artist details and performances |
| GET | `/api/programme` | Festival programme |
| GET | `/api/performances/{id}` | Performance details |
| GET | `/api/now` | Current and next performances |

Example:

```text
GET /api/programme?day=2027-06-11
```

The programme endpoint also supports filtering by venue.

### 7.2 Administration Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/artists` | Create an artist |
| POST | `/api/performances` | Create a performance |
| PUT | `/api/performances/{id}` | Modify or move a performance |
| DELETE | `/api/performances/{id}` | Cancel a performance |
| POST | `/api/performances/{id}/participants` | Register a workshop participant |

### 7.3 Example Request

Creating a solo performance:

```json
{
  "kind": "solo",
  "title": "New Comedy Show",
  "venue": "grand-casino",
  "start": "2027-06-11T12:00",
  "duration_minutes": 60,
  "artist": "hugo-lemaire",
  "min_age": 12
}
```

### 7.4 HTTP Error Handling

The application uses meaningful HTTP status codes.

| Status | Meaning |
|--------|---------|
| 200 | Successful request |
| 201 | Resource created |
| 204 | Resource deleted |
| 404 | Unknown resource |
| 409 | Scheduling or registration conflict |
| 422 | Invalid request |
| 500 | Data storage error |

Error responses contain a `detail` field describing the problem.

---

## 8. JSON Persistence

The application uses:

```text
data/festival.json
```

The file contains the festival information, venues, artists, and performances.

When the application starts or performs an operation, the stored data can be reconstructed as Python objects.

Each performance is validated through the model.

The service saves modifications after successful operations.

### Safe Modifications

When an administrator modifies a performance:

1. The existing festival is loaded.
2. The updated performance is constructed.
3. Scheduling rules are checked.
4. If validation succeeds, the new festival state is saved.
5. If validation fails, the original data file remains unchanged.

The file-saving implementation uses a temporary file and replacement operation to reduce the risk of incomplete writes.

The current implementation does not provide database transactions or concurrent-write protection.

---

## 9. Command-Line Features

The command-line interface provides three main commands.

### Festival Programme

```bash
uv run main.py programme 2027-06-11
```

Displays all performances for a festival day in chronological order.

### Artist Statistics

```bash
uv run main.py artists
```

Displays artists and their number of performances.

### Current and Next Performances

```bash
uv run main.py now 2027-06-12T21:15
```

Displays performances currently on stage and the next three scheduled performances.

---

## 10. Web Interfaces

### Public Website

URL:

http://127.0.0.1:8000/

The public interface allows visitors to explore the festival programme, artists, and performances.

### Administration Dashboard

URL:

http://127.0.0.1:8000/admin/

The administration dashboard supports:

- Viewing the festival schedule
- Creating artists
- Adding performances
- Editing performances
- Moving performances
- Cancelling performances
- Registering workshop participants

These features communicate directly with the FastAPI backend.

The administration interface was manually tested to verify successful performance modification and workshop registration.

---

## 11. Automated Testing

Automated tests are written using Pytest.

Run all tests:

```bash
uv run pytest -q
```

Latest verified result:

```text
34 passed
```

The test suite covers:

- Festival creation and validation
- Scheduling constraints
- Venue and artist conflicts
- JSON storage and reloading
- Service-layer operations
- REST API read endpoints
- Artist creation
- Solo creation
- Lineup creation
- Workshop creation
- Performance modification
- Performance cancellation
- Workshop registration
- Duplicate participant rejection
- Full workshop rejection
- HTTP error handling
- Modification conflicts
- Preservation of the JSON file after failed modifications
- Identifier changes after successful performance moves

Tests that modify festival data use temporary JSON files to avoid changing the original dataset.

---

## 12. Design Decisions

### Why Use a Separate Domain Model?

Business rules belong to the domain model rather than the web interface.

This means that the same rules apply whether operations are triggered by the CLI, API, or automated tests.

### Why Use an Abstract Performance Class?

Solo performances, lineups, and workshops share common properties but have different constraints.

An abstract base class allows common functionality to be reused while requiring each type to implement its own artist references.

### Why Use Custom Exceptions?

Custom exceptions make errors easier to identify and convert into appropriate HTTP responses.

For example:

- `NotFoundError` for missing resources
- `ConflictError` for scheduling conflicts
- `ValidationError` for invalid values
- `StorageError` for persistence problems

### Why Separate Storage and Business Logic?

The domain model does not need to know how data is stored.

Storage operations are implemented separately.

If JSON storage were replaced by SQLite, the main changes would concern the persistence and service layers rather than the domain entities or scheduling rules.

### Why Use a Service Layer?

`FestivalService` coordinates loading, modifying, and saving the festival.

This avoids duplicating persistence logic across different API endpoints.

---

## 13. Project Status and Limitations

### Implemented

- Object-oriented domain model
- Abstract classes and inheritance
- Artist and venue management
- Performance scheduling and conflict detection
- Three performance types
- Workshop registration
- JSON loading and saving
- Command-line interface
- FastAPI REST API
- Public website hosting
- Administration dashboard
- Automated tests

### Current Limitations

- JSON is the only storage backend.
- Simultaneous writes are not protected by database transactions or file locking.
- The administration API does not currently implement authentication.
- Some model attributes remain internally mutable in Python.
- SQLite persistence is not implemented.
- Ruff formatting and linting have not yet been verified.
- Building an installable Python package with `uv build` has not yet been verified.

These improvements can be implemented in future versions.

---

## 14. Future Improvements

Potential future extensions include:

- SQLite database integration
- SQLModel or SQLAlchemy persistence
- Administrator authentication
- Concurrent-write protection
- Improved API input validation
- Additional automated tests
- Better logging and monitoring
- Automated CI testing with GitHub Actions
- Deployment to a production hosting platform
- Improved reporting and statistics

---

## 15. Conclusion

The Deauville Festival du Rire management application demonstrates the design and development of a Python backend based on object-oriented programming principles.

The system separates domain logic, persistence, API endpoints, and user interfaces.

It implements scheduling rules, supports three different types of performances, provides JSON persistence, and exposes a functional FastAPI interface.

The application has been validated through 34 successful automated tests and manual verification of key administration features.

The project is designed to remain understandable, maintainable, and extensible for future festival editions.
