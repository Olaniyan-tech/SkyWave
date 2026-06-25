# SkyWave - Flight Booking API

## 🔹 Project Overview

SkyWave is a scalable flight booking backend API built with Django REST Framework. It allows users to search for available flights, view offers, and manage flight bookings through a secure and structured system.

The system integrates external flight data sources and is designed with clean architecture, making it suitable for real-world travel and booking applications.

---

## 🔹 User Features

- User registration and authentication (JWT-based)
- Secure login and token refresh system
- Search for available flights
- View flight offers and pricing options
- Select and book flights
- View booking history
- Cancel or manage existing bookings
- Secure logout system

---

## 🔹 Flight Features

- Real-time flight search integration (Duffel API or similar)
- View multiple airline offers per route
- Filter and select best flight options
- Handle offer expiration and validation
- Store booking records securely

---

## 🔹 Booking Features

- Create flight bookings from selected offers
- Retrieve booking details
- Track booking status (pending, confirmed, cancelled)
- Handle booking validation and errors
- Prevent booking expired offers

---

## 🔹 System & Architecture Features

- Clean Django REST Framework architecture
- Service layer separation for API logic
- External API integration (Duffel or flight provider)
- Secure JWT authentication
- Environment variable management for secrets
- Scalable backend structure for production use

---

## 🔹 Installation

1. Clone the repository
   ```bash
   git clone https://github.com/your-username/SkyWave.git
   cd SkyWave

2. Create a virtual environment
   ```bash
   python -m venv venv

3. Activate the virtual environment
   ```bash
   venv\Scripts\activate

5. Install dependencies
   ```bash
   pip install -r requirements.txt

7. Run migrations
   ```bash
   python manage.py migrate

6. Start the server
   ```bash
   python manage.py runserver


---


## 🔹 API Endpoints

### Authentication

| Endpoint | Method | Description |
|--------|--------|------------|
| `/api/accounts/register/` | POST | Register a new user |
| `/api/accounts/login/` | POST | Login user and get JWT cookies |
| `/api/accounts/token/refresh/` | POST | Refresh access token using refresh cookie |
| `/api/accounts/logout/` | POST | Logout user and blacklist refresh token |

### Profile

| Endpoint | Method | Description |
|--------|--------|------------|
| `/api/auth/my_profile/` | GET | Get logged-in user profile |


### Email Verification

| Endpoint | Method | Description |
|--------|--------|------------|
| `/api/auth/verify-email/` | POST | Verify user email with token |
| `/api/auth/resend-verification/` | POST | Resend verification email |


### Password Reset

| Endpoint | Method | Description |
|--------|--------|------------|
| `/api/auth/password-reset/request/` | POST | Request password reset email |
| `/api/auth/password-reset/confirm/` | POST | Confirm password reset with token |


###  Flights

| Endpoint | Method | Description |
|--------|--------|------------|
| `/api/flights/search/` | GET | Search available flights |
| `/api/flights/offers/` | GET | Retrieve flight offers |
| `/api/flights/<offer_id>/` | GET | Get details of a specific flight offer |

---

###  Bookings

| Endpoint | Method | Description |
|--------|--------|------------|
| `/api/bookings/create/` | POST | Create a new booking |
| `/api/bookings/` | GET | List all user bookings |
| `/api/bookings/<id>/` | GET | Get booking details |
| `/api/bookings/<id>/cancel/` | POST | Cancel a booking |

---

###  Payments

| Endpoint | Method | Description |
|--------|--------|------------|
| `/api/payments/` | GET | List all payments |
| `/api/payments/initialize/` | POST | Initialize a new payment |
| `/api/payments/verify/` | POST | Verify payment status |
| `/api/payments/<booking_reference>/` | GET | Retrieve payment details for a specific booking |

---

## 🔹 Example Request

### Search Flights

```http
GET /api/flights/search/?from=LAG&to=LON&date=2026-07-01
```


Request Body
```json
{
  "origin": "LAG",
  "destination": "LON",
  "departure_date": "2026-07-01"
}
```
### Response
```json
{
  "results": [
    {
      "airline": "British Airways",
      "price": 450000,
      "currency": "NGN",
      "duration": "6h 30m"
    }
  ]
}

```


