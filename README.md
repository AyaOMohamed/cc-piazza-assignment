# Piazza Discussion Platform

A RESTful discussion platform built with Python and FastAPI. Piazza allows registered users to create topic-based posts, interact through reactions and comments, and browse discussions according to their topic and expiry status.

## Features

- **User authentication:** Register and log in using email and password.
- **JWT authentication:** Protected endpoints require a valid Bearer access token.
- **Posts:** Create and retrieve posts with a title, body, one or more topics, and an expiry timestamp.
- **Topics:** Browse posts by predefined topics:
  - Politics
  - Health
  - Sport
  - Tech
- **Reactions:** Like or dislike posts, subject to post expiry rules. Users can change their existing reaction, but cannot react to their own posts.
- **Comments:** Add comments to posts, subject to post expiry rules.
- **Post filtering:** Browse posts by topic and status (Live or Expired).
- **Most-active posts:** Retrieve the most-active live post within a selected topic, ranked by reaction count.


## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Programming language |
| FastAPI | REST API framework |
| Pydantic v2 | Request validation and response schemas |
| SQLAlchemy | ORM and database access |
| SQLite | Database |
| JWT | Authentication and access tokens |
| Pytest | Automated testing |


## Getting Started

### Prerequisites

- Python 3.10 or later
- pip

### Installation

Clone the repository:

```bash
git clone https://github.com/AyaOMohamed/cc-piazza-assignment.git
cd cc-piazza-assignment
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

On Windows:

```bash
venv\Scripts\activate
```

On macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Environment Variables

Configure the JWT secret before starting the application.

```env
JWT_SECRET=your-secure-secret-key-of-at-least-32-characters
```

Use a secure secret in production. Do not commit secrets or production credentials to version control.

### Running the Application

Start the FastAPI application using:

```bash
uvicorn application:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## API Overview

All business endpoints require authentication using a JWT Bearer token.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Authenticate a user and receive an access token |

### Posts

| Method | Endpoint | Description |
|---|---|---|
| POST | `/posts/` | Create a post |
| GET | `/posts/` | Browse posts |
| GET | `/posts/{post_id}` | Retrieve a specific post |
| PUT | `/posts/{post_id}/reaction` | Add or replace a reaction |
| POST | `/posts/{post_id}/comments` | Add a comment |

The posts browsing endpoint supports optional query parameters:

- `topic`: Filter by topic.
- `status`: Filter by `Live` or `Expired`.

Example:

```text
GET /posts?topic=Tech&status=Live
```

### Topics

| Method | Endpoint | Description |
|---|---|---|
| GET | `/topics/{topic}/most-active` | Retrieve the most-active live post for a topic |

The most-active post is determined by:

1. Highest total number of reactions.
2. Newest creation timestamp when reaction counts are equal.
3. Lowest post ID when reaction counts and timestamps are equal.

Both likes and dislikes contribute to the total reaction count.

## Business Rules

### Authentication

- Users must register before logging in.
- Passwords are stored as hashes rather than plain text.
- Successful login returns a JWT access token with an expiration claim.
- Protected endpoints reject missing, invalid and expired tokens.

### Posts

- Posts must have a valid title, body, topic and expiry timestamp.
- A post must expire after its creation timestamp.
- Posts can be retrieved after expiry.
- Expired posts cannot receive new reactions or comments.
- Existing comments and reactions remain associated with the post.

### Reactions

- Users can like or dislike posts.
- A user can have only one reaction per post.
- A user can replace their existing reaction.
- Users cannot react to their own posts.
- Reaction counts are calculated separately for likes and dislikes.

### Comments

- Comments must contain valid, non-empty text.
- Users cannot comment on expired posts.
- Existing comments remain readable after a post expires.

### Topics and Most-Active Posts

- Topics and reaction types are predefined and seeded into the database.
- Only valid topics are accepted.
- Most-active browsing excludes expired posts.
- Posts are ranked by total reactions, with deterministic tie-breaking.

## Automated Testing

The project uses Pytest and FastAPI's `TestClient` to verify application behaviour.

Tests are organised into two main categories.

### Unit Tests

Located in `tests/unit/`.

These test individual components independently, including:

- Pydantic schema validation.
- Input validation rules.
- Core application logic.

### API Tests

Located in `tests/api/`.

These tests use FastAPI's `TestClient` to send HTTP requests and verify the application's behaviour through its API endpoints.

The API tests are divided into two categories:

**Individual API tests**

Verify that each endpoint behaves correctly on its own under different conditions, including valid requests, invalid input, missing data, authentication failures and other error cases.

They cover:

- Registration and login.
- Authentication and JWT validation.
- Post creation and retrieval.
- Topic and status filtering.
- Reactions and reaction counts.
- Comments.
- Post expiry.
- Most-active post selection.

**Scenario tests**

Verify that multiple endpoints work together to support the specific user workflows described in the Piazza scenario.

These tests simulate interactions between users and check that the application behaves correctly across a sequence of actions, rather than testing each endpoint in isolation.

The scenario tests cover:

- Four users registering and logging in.
- Creating and browsing posts across different topics.
- Adding and counting reactions.
- Preventing users from reacting to their own posts.
- Adding and retrieving comments.
- Handling post expiry, including preventing reactions to expired posts while keeping them readable.
- Identifying the most-active post in a topic.

This scenario is covered in `tests/api/test_piazza_scenario.py`.

**The scenarios are grouped into independent workflows rather than being implemented as one continuous test.** Each workflow establishes the users and data it needs, performs the relevant actions, and verifies the expected results.

This makes tests easier to maintain and failures easier to identify while still demonstrating the required application behaviour.

### Scenario coverage table

| ID | Scenario | Expected result | Automated test |
|---|---|---|---|
| TC01 | Olga, Nick, Mary and Nestor register | All four registrations succeed | `test_four_users_register_and_login` |
| TC02 | All four users log in | Each receives an access token | `test_four_users_register_and_login` |
| TC03 | Olga requests a protected endpoint without a token | Request is rejected with HTTP 401 | `test_tech_discussion_scenario` |
| TC04–TC07 | Users create three Tech posts and browse the topic | All three posts are returned with no initial reactions or comments | `test_tech_discussion_scenario` |
| TC08–TC10 | Users add likes and dislikes to the Tech posts | Reactions are accepted and the reaction counts are correct | `test_tech_discussion_scenario` |
| TC11 | Mary attempts to react to her own post | Request is rejected with HTTP 403 | `test_tech_discussion_scenario` |
| TC12–TC13 | Nick and Olga comment on Mary's post, and Tech posts are browsed again | All comments are accepted and the correct comments and reaction counts are returned | `test_tech_discussion_scenario` |
| TC14–TC16 | Nestor creates a Health post and Mary comments on it while it is live | Post and comment are created successfully | `test_health_post_expiry_scenario` |
| TC17 | Mary attempts to react after the Health post expires | Request is rejected with HTTP 409 | `test_health_post_expiry_scenario` |
| TC18 | The expired Health post is retrieved | Post remains readable with its existing comment | `test_health_post_expiry_scenario` |
| TC19 | Expired Sport posts are requested when none exist | An empty list is returned | `test_expired_sport_browsing_returns_empty_list` |
| TC20 | The most-active Tech post is requested | Mary's post is returned | `test_tech_discussion_scenario` |

### Running Tests

Run the complete test suite:

```bash
pytest
```

Run only API tests:

```bash
pytest tests/api/ -v
```

Run only unit tests:

```bash
pytest tests/unit/ -v
```

Run the required Piazza scenario tests:

```bash
pytest tests/api/test_piazza_scenario.py -v
```

## Controllable Clock

Expiry-related tests use a controllable application clock rather than waiting for real time to pass.

This allows tests to:
- Create posts with future expiry timestamps.
- Advance the application clock beyond the expiry timestamp.
- Verify that expired posts reject new interactions.
- Confirm that expired posts remain readable with their existing data.

This approach avoids slow, timing-dependent tests and makes expiry behaviour deterministic.

## Database Seeding

The application seeds predefined topics and reaction types during application initialisation.

This ensures that the required reference data is available when the application starts.

The seed functions are designed to avoid creating duplicate records when initialisation is repeated.

## Health Check

The application exposes a simple health endpoint:

```text
GET /health
```

It returns a welcome message to confirm that the API is running.
