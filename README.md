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
