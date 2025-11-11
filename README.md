# Secure Voting System Backend

A comprehensive voting system backend built with FastAPI and MySQL that supports both secured (registration-based) and anonymous voting.

## Features

### 🔐 Secured Voting
- Admin creates election and generates registration link
- Voters register using their email
- When election starts, voters receive one-time voting links via email
- Links become invalid after voting
- Tracks participation rate

### 🌐 Anonymous Voting
- Admin creates public voting link
- Anyone can vote without registration
- No email required
- Quick and simple voting process

### 👨‍💼 Admin Features
- JWT-based authentication
- Create and manage elections
- Generate registration links
- Send voting links to registered voters
- View real-time results and statistics
- Track voter participation

## Technology Stack

- **Framework**: FastAPI 0.104.1
- **Database**: MySQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with python-jose
- **Password Hashing**: bcrypt via passlib
- **Email**: SMTP (Gmail/custom)
- **Validation**: Pydantic v2

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── database.py          # Database configuration
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic schemas for validation
├── routes/
│   ├── admin.py        # Admin authentication & election management
│   ├── voter.py        # Voter registration & voting
│   └── election.py     # Election results & public info
├── utils/
│   ├── email_utils.py  # Email sending utilities
│   └── security.py     # JWT & password hashing
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- MySQL 8.0 or higher
- Gmail account (or other SMTP server)

### 2. Database Setup

Create a MySQL database:

```sql
CREATE DATABASE voting_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Configuration

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Database
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=voting_system

# JWT Secret (generate with: python -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=your-secret-key-here

# Gmail SMTP
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SENDER_EMAIL=your-email@gmail.com

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

### 5. Gmail App Password Setup

1. Go to your Google Account settings
2. Enable 2-Step Verification
3. Go to Security > App passwords
4. Generate an app password for "Mail"
5. Use the 16-character password in your `.env` file

### 6. Run the Application

```bash
# Make sure you're in the backend directory
cd backend

# Run the server
python main.py

# Or with uvicorn directly:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 7. Access API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/admin/signup` | Create admin account |
| POST | `/api/admin/login` | Admin login (returns JWT) |
| GET | `/api/admin/me` | Get current admin info |
| POST | `/api/admin/elections` | Create new election |
| GET | `/api/admin/elections` | Get admin's elections |
| GET | `/api/admin/elections/{id}` | Get election details |
| POST | `/api/admin/elections/{id}/send-voting-links` | Send voting links to voters |
| GET | `/api/admin/elections/{id}/registrations` | View registered voters |

### Voter Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/voter/register/{election_id}` | Register for election |
| GET | `/api/voter/vote-info/{token}` | Get voting info (secured) |
| POST | `/api/voter/vote/{token}` | Cast secured vote |
| GET | `/api/voter/anonymous-vote-info/{election_id}` | Get voting info (anonymous) |
| POST | `/api/voter/vote/anonymous/{election_id}` | Cast anonymous vote |

### Election Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/election/` | List all elections |
| GET | `/api/election/{id}` | Get election details |
| GET | `/api/election/{id}/results` | Get election results |
| GET | `/api/election/{id}/stats` | Get election statistics |

## Usage Workflow

### Secured Voting Flow

1. **Admin Setup**
   ```bash
   # Admin signs up
   POST /api/admin/signup
   {
     "name": "Admin Name",
     "email": "admin@example.com",
     "password": "secure_password"
   }
   
   # Admin logs in
   POST /api/admin/login
   {
     "email": "admin@example.com",
     "password": "secure_password"
   }
   # Returns JWT token
   ```

2. **Create Election**
   ```bash
   POST /api/admin/elections
   Headers: Authorization: Bearer {token}
   {
     "title": "Class President Election",
     "description": "Vote for your class president",
     "type": "secured",
     "start_time": "2025-10-25T10:00:00",
     "end_time": "2025-10-25T18:00:00"
   }
   # Returns registration link
   ```

3. **Voter Registration**
   ```bash
   # Voters use the registration link
   POST /api/voter/register/{election_id}
   {
     "email": "voter@example.com"
   }
   # Voter receives confirmation email
   ```

4. **Send Voting Links**
   ```bash
   # Admin triggers email sending when election starts
   POST /api/admin/elections/{id}/send-voting-links
   Headers: Authorization: Bearer {token}
   # All registered voters receive voting links
   ```

5. **Cast Vote**
   ```bash
   # Voter clicks their unique link and votes
   POST /api/voter/vote/{token}
   {
     "choice": "Candidate A"
   }
   # Vote recorded, link becomes invalid
   ```

6. **View Results**
   ```bash
   # Anyone can view results
   GET /api/election/{id}/results
   ```

### Anonymous Voting Flow

1. Admin creates election with `type: "anonymous"`
2. Admin shares the public voting link
3. Anyone can vote directly without registration
4. Results are publicly visible

## Security Features

- ✅ JWT-based authentication
- ✅ Bcrypt password hashing
- ✅ One-time voting links (secured voting)
- ✅ Token-based vote verification
- ✅ Timeline enforcement (votes only during election period)
- ✅ Anonymous vote recording (no voter ID stored)
- ✅ CORS protection
- ✅ SQL injection prevention (SQLAlchemy ORM)

## Database Schema

### users
- id, name, email, password (hashed), role, created_at

### elections
- id, title, description, type, start_time, end_time, admin_id, created_at

### registrations
- id, election_id, voter_email, registration_time, unique_token, has_voted

### votes
- id, election_id, voter_id (nullable), choice, created_at

## Development Notes

- All passwords are hashed using bcrypt
- JWT tokens expire after 24 hours
- Voting links are 64-character hexadecimal tokens
- Database sessions are automatically managed
- Email sending is synchronous (can be made async)

## Troubleshooting

### Database Connection Issues
- Verify MySQL is running
- Check database credentials in `.env`
- Ensure database exists

### Email Not Sending
- Verify Gmail App Password is correct
- Check 2-Step Verification is enabled
- Try with different SMTP server

### JWT Token Issues
- Ensure JWT_SECRET_KEY is set in `.env`
- Check token hasn't expired
- Verify Authorization header format: `Bearer {token}`

## Production Considerations

1. **Security**
   - Change JWT_SECRET_KEY to a strong random value
   - Use environment variables for all secrets
   - Enable HTTPS
   - Implement rate limiting

2. **Anonymous Voting**
   - Add IP-based duplicate vote prevention
   - Implement CAPTCHA
   - Add browser fingerprinting

3. **Database**
   - Use connection pooling
   - Set up database backups
   - Add database indexes for performance

4. **Email**
   - Use async email sending for better performance
   - Implement email queue for bulk sending
   - Add email retry mechanism

5. **Monitoring**
   - Add logging
   - Set up error tracking (e.g., Sentry)
   - Monitor API performance

## Testing

You can test the API using the interactive Swagger UI at `http://localhost:8000/docs` or using curl/Postman.

### Example Test with curl

```bash
# 1. Create admin
curl -X POST http://localhost:8000/api/admin/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Admin","email":"admin@test.com","password":"password123"}'

# 2. Login
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"password123"}'

# 3. Create election (use token from login)
curl -X POST http://localhost:8000/api/admin/elections \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "title":"Test Election",
    "description":"Testing the system",
    "type":"secured",
    "start_time":"2025-10-25T10:00:00",
    "end_time":"2025-10-25T18:00:00"
  }'
```

## License

This project is created for educational purposes.

## Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review this README
3. Check the inline code comments
4. Verify your `.env` configuration

## Contributing

This is a student project. Feel free to:
- Add features (e.g., multiple choice options, ranked voting)
- Improve security
- Add tests
- Enhance documentation

## Future Enhancements

- [ ] Add support for multiple candidates/options
- [ ] Implement real-time results updates (WebSockets)
- [ ] Add election templates
- [ ] Support for ranked-choice voting
- [ ] Admin dashboard with analytics
- [ ] Voter verification via SMS
- [ ] Export results to PDF/CSV
- [ ] Multi-language support
- [ ] Email templates customization
- [ ] Scheduled email sending
- [ ] Vote verification receipts