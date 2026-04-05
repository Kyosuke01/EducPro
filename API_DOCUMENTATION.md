# API Documentation - EduPro

**Version:** 1.0  
**Date:** April 5, 2026  
**Base URL:** `http://backend:5000/api`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Authorization](#authorization)
3. [Users Management](#users-management)
4. [Authentication Routes](#authentication-routes)
5. [Classes Management](#classes-management)
6. [Attendance Tracking](#attendance-tracking)
7. [Schedule (EDT)](#schedule-edt)
8. [Grades Management](#grades-management)
9. [Messages & Support Tickets](#messages--support-tickets)
10. [Error Responses](#error-responses)
11. [Security Headers](#security-headers)

---

## Authentication

All API endpoints (except public routes) require:

### Headers Required

```http
X-API-Key: <API_SECRET_KEY>
User-Agent: educrpro/1.0 | educpro-admin/1.0
X-User-ID: <user_id>          # For session validation
X-Session-UA: <user_agent>    # For session security
```

### Public Routes (No Auth Required)
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`

---

## Authorization

Role-Based Access Control (RBAC) with three roles:

| Role | Can Access | Can Modify |
|------|-----------|-----------|
| **student** | Own data only | Messages, profile, grades (read) |
| **teacher** | Class data | Attendance, grades, EDT, messages |
| **admin** | All data | All resources |

**Validation:** Applied via `@require_role('admin')` decorators and `check_idor_access()` for row-level security.

---

## Users Management

### GET /api/users/
**Description:** List all users (students + teachers)  
**Auth:** ✅ Required  
**Role:** admin, teacher  
**Response:**
```json
[
  {
    "username": "John Doe",
    "email": "john@example.com",
    "role": "student"
  }
]
```

### POST /api/users/
**Description:** Create new user (student or teacher)  
**Auth:** ✅ Required  
**Role:** admin  
**Request Body:**
```json
{
  "user_type": "student|teacher",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "password": "secure_password",
  "class_name": "1A",           // required for students
  "topic_name": "Mathematics"   // required for teachers
}
```
**Response:** `201 Created`
```json
{
  "message": "Utilisateur (student) créé avec succès."
}
```
**Errors:**
- `400` - Missing required fields
- `409` - Email already exists

### PUT /api/users/<user_type>/<user_id>
**Description:** Update user profile  
**Auth:** ✅ Required  
**Role:** admin  
**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane@example.com",
  "class_name": "2B",           // optional for students
  "topic_name": "Physics"       // optional for teachers
}
```
**Response:** `200 OK`

### DELETE /api/users/<user_type>/<user_id>
**Description:** Delete user and related data  
**Auth:** ✅ Required  
**Role:** admin  
**Response:** `200 OK`
```json
{
  "message": "Utilisateur supprimé avec succès."
}
```

---

## Authentication Routes

### POST /api/auth/login
**Description:** User login with 2FA support  
**Auth:** ❌ Not Required  
**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```
**Response:** `200 OK`
```json
{
  "user_id": 5,
  "email": "user@example.com",
  "first_name": "John",
  "role": "student",
  "has_2fa": true
}
```

### POST /api/auth/verify-otp
**Description:** Verify 2FA OTP code  
**Auth:** ✅ Required (Session)  
**Request Body:**
```json
{
  "code": "123456"
}
```
**Response:** `200 OK`
```json
{
  "message": "OTP valide. Authentification complétée."
}
```

### POST /api/auth/logout
**Description:** User logout  
**Auth:** ✅ Required  
**Response:** `200 OK`

### POST /api/auth/forgot-password
**Description:** Request password reset  
**Auth:** ❌ Not Required  
**Request Body:**
```json
{
  "email": "user@example.com"
}
```
**Response:** `200 OK`

### POST /api/auth/reset-password
**Description:** Reset password with token  
**Auth:** ❌ Not Required  
**Request Body:**
```json
{
  "email": "user@example.com",
  "reset_token": "token_from_email",
  "new_password": "new_secure_password"
}
```
**Response:** `200 OK`

---

## Classes Management

### GET /api/classes
**Description:** List all classes  
**Auth:** ✅ Required  
**Role:** admin, teacher  
**Response:**
```json
{
  "classes": [
    {
      "name": "1A",
      "max_capacity": 35,
      "current_count": 28
    }
  ]
}
```

### GET /api/classes/<class_name>/students
**Description:** Get all students in class  
**Auth:** ✅ Required  
**Role:** admin, teacher  
**Response:**
```json
{
  "class_name": "1A",
  "students": [
    {
      "student_id": 1,
      "first_name": "Alice",
      "last_name": "Martin"
    }
  ]
}
```

### GET /api/topics
**Description:** List all subjects  
**Auth:** ✅ Required  
**Response:**
```json
{
  "topics": ["Mathematics", "Physics", "French"]
}
```

### PUT /api/classes/<class_id>/assign-teacher
**Description:** Assign teacher to class  
**Auth:** ✅ Required  
**Role:** admin  
**Request Body:**
```json
{
  "teacher_id": 5,
  "topic_name": "Mathematics"
}
```
**Response:** `200 OK`

---

## Attendance Tracking

### GET /api/attendance/stats
**Description:** Global attendance statistics  
**Auth:** ✅ Required  
**Role:** admin, teacher  
**Response:**
```json
{
  "stats": {
    "total": 450,
    "late": 45,
    "onTime": 405
  }
}
```

### GET /api/attendance/student/<student_id>
**Description:** Get student's absences/late arrivals  
**Auth:** ✅ Required  
**IDOR Protected:** ✅ Students can only access own data  
**Response:**
```json
{
  "student_id": 5,
  "attendance": [
    {
      "attendance_id": 1,
      "late": 0,
      "absent": false,
      "date": "2026-04-05"
    }
  ]
}
```

### GET /api/attendance/class/<class_name>
**Description:** Get class attendance records  
**Auth:** ✅ Required  
**Role:** admin, teacher  
**Response:**
```json
{
  "class_name": "1A",
  "attendance": [
    {
      "student_id": 1,
      "first_name": "Alice",
      "late": 0,
      "absent": false
    }
  ]
}
```

### POST /api/attendance
**Description:** Add/update attendance record  
**Auth:** ✅ Required  
**Role:** admin, teacher  
**Request Body:**
```json
{
  "student_id": 5,
  "late": 0,
  "absent": false
}
```
**Response:** `200 OK` or `201 Created`

---

## Schedule (EDT)

### GET /api/edt/class/<class_name>
**Description:** Get weekly class schedule  
**Auth:** ✅ Required  
**Response:**
```json
{
  "class_name": "1A",
  "schedule": [
    {
      "day": "Monday",
      "hour": "08:00",
      "subject": "Mathematics",
      "teacher": "John Smith"
    }
  ]
}
```

### POST /api/edt
**Description:** Create schedule entry  
**Auth:** ✅ Required  
**Role:** admin, teacher  
**Request Body:**
```json
{
  "class_name": "1A",
  "day": "Monday",
  "hour": "08:00",
  "subject": "Mathematics",
  "teacher_id": 5
}
```
**Response:** `201 Created`

### PUT /api/edt/<edt_id>
**Description:** Update schedule entry  
**Auth:** ✅ Required  
**Role:** admin, teacher  

### DELETE /api/edt/<edt_id>
**Description:** Delete schedule entry  
**Auth:** ✅ Required  
**Role:** admin, teacher  

---

## Grades Management

### GET /api/grades/student/<student_id>
**Description:** Get student's grades  
**Auth:** ✅ Required  
**IDOR Protected:** ✅ Students can only access own grades  
**Response:**
```json
{
  "student_id": 5,
  "grades": [
    {
      "grade_id": 1,
      "grade": 85,
      "topic_name": "Mathematics",
      "date": "2026-04-05"
    }
  ]
}
```

### GET /api/grades/topic/<topic_name>
**Description:** Get all grades for a subject  
**Auth:** ✅ Required  
**Role:** admin, teacher  

### GET /api/grades/class/<class_name>
**Description:** Get all grades for a class  
**Auth:** ✅ Required  
**Role:** admin, teacher  

### POST /api/grades
**Description:** Add student grade  
**Auth:** ✅ Required  
**Role:** admin, teacher  
**Request Body:**
```json
{
  "student_id": 5,
  "grade": 85,
  "topic_name": "Mathematics"
}
```
**Response:** `201 Created`

---

## Messages & Support Tickets

### GET /api/notifications
**Description:** Get user notifications  
**Auth:** ✅ Required  
**Response:**
```json
{
  "notifications": [
    {
      "title": "Welcome",
      "body": "Your account is ready.",
      "type": "system"
    }
  ]
}
```

### GET /api/messages/recipients
**Description:** Search for message recipients  
**Auth:** ✅ Required  
**Query Parameters:**
- `type=all|student|teacher` (default: all)
- `q=query` (search by name/email)
- `limit=15` (max results)

**Response:**
```json
{
  "results": [
    {
      "id": 5,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "role": "student"
    }
  ]
}
```

### GET /api/messages/conversations
**Description:** List support conversations  
**Auth:** ✅ Required  
**Query Parameters:**
- `role=student|teacher|admin`
- `user_id=<id>`

**Response:**
```json
{
  "tickets": [
    {
      "ticket_id": 1,
      "subject": "Help request",
      "status": "open",
      "updated_at": "2026-04-05T10:30:00"
    }
  ]
}
```

### POST /api/messages/conversations
**Description:** Create new support ticket  
**Auth:** ✅ Required  
**Request Body:**
```json
{
  "subject": "Help with assignment",
  "message": "I need help with...",
  "starter_role": "student",
  "starter_id": 5,
  "recipient_role": "teacher",
  "recipient_id": 10
}
```
**Response:** `201 Created`

### GET /api/messages/conversations/<ticket_id>
**Description:** Get conversation details  
**Auth:** ✅ Required  
**IDOR Protected:** ✅ Users can only access their conversations  

### POST /api/messages/conversations/<ticket_id>/messages
**Description:** Add message to conversation  
**Auth:** ✅ Required  
**Request Body:**
```json
{
  "body": "Thank you for your help!",
  "sender_role": "student",
  "sender_id": 5
}
```
**Response:** `201 Created`

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request data",
  "details": "Missing required field: email"
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized: Invalid API Key"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "You don't have permission to access this resource"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 409 Conflict
```json
{
  "error": "This email is already in use"
}
```

### 500 Internal Server Error
```json
{
  "error": "Server error: [details]"
}
```

---

## Security Headers

All responses include security headers:

| Header | Value |
|--------|-------|
| `Content-Security-Policy` | Strict policy (XSS prevention) |
| `X-Frame-Options` | DENY (Clickjacking prevention) |
| `X-Content-Type-Options` | nosniff |
| `X-XSS-Protection` | 1; mode=block |
| `Strict-Transport-Security` | Production only |
| `Referrer-Policy` | strict-origin-when-cross-origin |

---

## Rate Limiting & Best Practices

### Recommendations
1. **Never** send passwords in query parameters
2. Use HTTPS in production (enforced via HSTS)
3. Refresh `X-User-ID` header on each session
4. Store API keys securely (environment variables, secrets manager)
5. Implement request timeouts (typically 10 seconds)
6. Log all API calls for audit trails

### Example Request (cURL)
```bash
curl -X GET "http://backend:5000/api/users/" \
  -H "X-API-Key: your_api_key" \
  -H "User-Agent: educrpro/1.0" \
  -H "X-User-ID: 5"
```

### Example Request (Python)
```python
import requests

headers = {
    "X-API-Key": "your_api_key",
    "User-Agent": "educrpro/1.0",
    "X-User-ID": "5"
}

response = requests.get(
    "http://backend:5000/api/users/",
    headers=headers,
    timeout=10
)
print(response.json())
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-05 | Initial API documentation |

---

**Last Updated:** April 5, 2026  
**Maintainer:** EduPro Team  
**Contact:** support@educpro.local
