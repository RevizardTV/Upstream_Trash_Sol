================================================================================
                  ECORECYCLE API & PLATFORM DOCUMENTATION
================================================================================

EcoRecycle is a municipal smart waste management platform that connects urban 
households, automated IoT weight collection kiosks, staff verification portals, 
and automated banking payment rails.

--------------------------------------------------------------------------------
1. KEY SYSTEM FEATURES (PHASE 3 UPDATES)
--------------------------------------------------------------------------------
* Svelte 5 UI Layer: Fine-grained reactive front-end utilizing $state() and 
  $props() runes for sub-16ms DOM updates and instant telemetry rendering.
* IoT Load Cell Simulation: Automated weight sensor simulation broadcasting live 
  kiosk telemetry (IOT_WEIGHT_UPDATE) over WebSockets.
* Automated Razorpay Payout Engine: Instant UPI disbursements triggered upon 
  staff approval of household recycling submissions.
* Continuous Integration & Testing: Pytest test suite embedded into Render 
  Cloud build steps to prevent regression issues in production.


--------------------------------------------------------------------------------
2. DATABASE SCHEMA
--------------------------------------------------------------------------------
The application uses SQLAlchemy with SSL encryption to connect to PostgreSQL, 
MySQL, or SQLite database instances.

  +------------------+          +-------------------+          +---------------------+
  |  staff_profiles  |          |   user_profiles   |          |  recycling_entries  |
  +------------------+          +-------------------+          +---------------------+
  | id (PK)          |<---+     | id (PK)           |<---+     | entry_id (PK)       |
  | email            |    |     | email             |    |     | user_id (FK) -------+
  | full_name        |    +-----| (relationships)   |    +-----| waste_category      |
  | password_hash    |          | full_name         |          | weight_kg           |
  | assigned_pincode |          | phone_number      |          | payout_amount       |
  | created_at       |          | city              |          | station_id          |
  +------------------+          | postal_code       |          | status              |
                                | premise_type      |          | rejection_reason    |
                                | household_size    |          | reviewed_by_staff_id|
                                | upi_id            |          | razorpay_payout_id  |
                                | profile_complete  |          | utr_number          |
                                | created_at        |          | created_at          |
                                +-------------------+          +---------------------+

Table Specifications:

1. staff_profiles
   - id: Integer, PK, Auto-increment
   - email: String(255), Unique, Indexed, Required
   - full_name: String(255), Required
   - password_hash: String(255), Required
   - assigned_pincode: String(20), Indexed, Required
   - created_at: DateTime, Default: now()

2. user_profiles
   - id: Integer, PK, Auto-increment, Indexed
   - email: String(255), Unique, Indexed, Required
   - full_name: String(255), Required
   - phone_number: String(50), Required
   - city: String(100), Required
   - postal_code: String(20), Indexed, Required
   - premise_type: String(50), Default: "house"
   - household_size: Integer, Default: 1
   - upi_id: String(100), Optional (Required for Razorpay payouts)
   - profile_complete: Boolean, Default: True
   - created_at: DateTime, Default: now()

3. recycling_entries
   - entry_id: Integer, PK, Auto-increment, Indexed
   - user_id: Integer, FK -> user_profiles.id [CASCADE], Required
   - waste_category: String(100), Required
   - weight_kg: Numeric(10, 2), Required
   - payout_amount: Numeric(10, 2), Required
   - station_id: String(100), Optional
   - status: Enum('pending', 'approved', 'declined'), Default: 'pending'
   - rejection_reason: String(255), Optional
   - reviewed_by_staff_id: Integer, FK -> staff_profiles.id [SET NULL], Optional
   - razorpay_payout_id: String(100), Optional
   - utr_number: String(100), Optional
   - created_at: DateTime, Default: now()


--------------------------------------------------------------------------------
3. API ENDPOINTS REFERENCE
--------------------------------------------------------------------------------

A. Authentication & Session Endpoints
   POST /api/auth/request-otp
        Body: { email_address, type }
        Desc: Requests an OTP verification code via email.

   POST /api/auth/verify-otp
        Body: { email_address, otp_code }
        Desc: Verifies OTP and sets session cookies (staff_authenticated, user_authenticated).

   POST /api/auth/complete-profile
        Body: ProfileCreateSchema
        Desc: Creates or updates detailed user profile info.

B. User & Profile Endpoints
   GET  /api/user/profile
        Query: user_id OR email
        Desc: Fetches full user profile details including UPI ID.

C. Recycling Transactions & IoT Stream
   POST /api/recycling/entry
        Body: RecyclingEntrySchema
        Desc: Ingests kiosk waste submission (pending), triggering a WS telemetry broadcast.

   GET  /api/recycling/pending-payments
        Query: user_id OR email
        Desc: Retrieves pending entries and calculated payouts.

   GET  /api/recycling/reviewed-requests
        Query: user_id OR email
        Desc: Lists historical approved/declined submissions.

   GET  /api/recycling/summary
        Query: user_id OR email
        Desc: Fetches total earnings, eco-credits, and weight statistics.

   GET  /api/recycling/receipt/{entry_id}
        Path: entry_id
        Desc: Generates a downloadable transaction PDF receipt.

   WS   /ws/telemetry
        Desc: WebSocket pipeline broadcasting live kiosk load cell updates.

D. Staff Operations & Automated Payouts
   POST /api/staff/register
        Body: StaffRegisterSchema
        Desc: Registers a new staff/officer account.

   POST /api/staff/login
        Body: StaffLoginSchema
        Desc: Validates credentials and dispatches verification OTP.

   POST /api/staff/users/{user_id}/review
        Body: { action: "approve" | "decline" }
        Desc: Approves user profile completion status.

   GET  /api/admin/district-users
        Query: staff_pincode, search, exact_pincode
        Desc: Lists incomplete profiles in the staff member's district.

   GET  /api/admin/user-pending-entries/{user_id}
        Path: user_id
        Desc: Lists all pending recycling entries for a target household.

   POST /api/staff/entries/{entry_id}/review
        Body: { action: "approve" | "decline", rejection_reason, staff_id }
        Desc: Approves waste entry and triggers instant Razorpay UPI payout.


--------------------------------------------------------------------------------
4. FRONT-END SVELTE ROUTES
--------------------------------------------------------------------------------
Route                   Auth Required              Description
--------------------------------------------------------------------------------
/                       No                         Home landing page
/login                  No                         Household user login page
/payment                user_authenticated=true    Main recycling interface & payout tracker
/pending-payments       user_authenticated=true    Pending entry queue dashboard
/reviewed-requests      user_authenticated=true    Historical reviewed entries page
/register-profile       No                         New user profile registration
/register-staff         No                         Staff member registration page
/staff-login            No                         Staff login page
/staff-dashboard        staff_authenticated=true   Admin/Staff district control dashboard
/logout                 Any                        Clears session cookies -> /login
/staff-logout           Any                        Clears session cookies -> /staff-login


--------------------------------------------------------------------------------
5. TESTING & DEPLOYMENT PIPELINE
--------------------------------------------------------------------------------
Running Local Integration Tests:
  $env:PYTHONIOENCODING="utf-8"
  pytest tests/ -v

Render Service Commands:
  Build Command: pip install -r requirements.txt && pytest tests/ -v
  Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT

================================================================================