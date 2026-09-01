# 📋 ElderGo+ Frontend & Backend Integration Checklist

This document outlines the complete step-by-step roadmap to connect all frontend HTML/CSS/JS components with the Spring Boot REST API and MySQL database.

---

## 🗄️ Phase 1: Database & JPA Entity Foundation

- [ ] **1.1 Configure MySQL Connection in Spring Boot**
  - [ ] Open `backend/src/main/resources/application.properties`
  - [ ] Remove `spring.autoconfigure.exclude=...DataSourceAutoConfiguration,HibernateJpaAutoConfiguration`
  - [ ] Add datasource URL: `spring.datasource.url=jdbc:mysql://localhost:3306/eldergo_db?createDatabaseIfNotExist=true&useSSL=false`
  - [ ] Add datasource credentials: `spring.datasource.username=root` and `spring.datasource.password=...`
  - [ ] Configure JPA / Hibernate: `spring.jpa.hibernate.ddl-auto=update` and `spring.jpa.show-sql=true`

- [ ] **1.2 Create JPA Entity Models (`com.example.demo.model`)**
  - [ ] `User.java`: `id`, `username`, `password`, `fullName`, `phone`, `email`, `age`, `gender`, `address`, `role` (`CLIENT`, `COMPANION`, `ADMIN`), `status` (`ACTIVE`, `INACTIVE`, `PENDING_VERIFICATION`), `createdAt`
  - [ ] `ClientProfile.java`: `id`, `user` (`@OneToOne`), `emergencyContactName`, `emergencyContactPhone`, `medicalNotes`
  - [ ] `CompanionProfile.java`: `id`, `user` (`@OneToOne`), `profilePhotoUrl`, `documentUrl`, `city`, `pincode`, `languages`, `availability`, `preferredService`, `otherServiceDetails`, `skills`, `experience`, `isVerified` (boolean), `isAvailable` (boolean), `rating` (double)
  - [ ] `Booking.java`: `id`, `bookingCode` (e.g. `#EGO-9081`), `client` (`@ManyToOne`), `companion` (`@ManyToOne`), `serviceType`, `bookingDate`, `bookingTime`, `durationHours`, `pickupAddress`, `destinationAddress`, `healthNotes`, `status` (`PENDING`, `ACCEPTED`, `ONGOING`, `COMPLETED`, `CANCELLED`), `transitStage` (`BOOKED`, `PICKED_UP`, `IN_TRANSIT`, `RETURN`), `priceAmount`, `paymentStatus`
  - [ ] `Feedback.java`: `id`, `booking` (`@OneToOne`), `client` (`@ManyToOne`), `companion` (`@ManyToOne`), `rating` (1-5), `comment`, `createdAt`
  - [ ] `EmergencyAlert.java`: `id`, `client` (`@ManyToOne`), `location`, `notes`, `status` (`ACTIVE`, `RESOLVED`), `createdAt`, `resolvedAt`

- [ ] **1.3 Create Spring Data JPA Repositories (`com.example.demo.repository`)**
  - [ ] `UserRepository`: `findByUsername(String username)`, `findByEmail(String email)`, `findByRole(Role role)`
  - [ ] `ClientProfileRepository`: `findByUserId(Long userId)`
  - [ ] `CompanionProfileRepository`: `findByUserId(Long userId)`, `findByIsVerifiedTrueAndIsAvailableTrue()`
  - [ ] `BookingRepository`: `findByClientIdOrderByCreatedAtDesc(Long clientId)`, `findByCompanionIdOrderByCreatedAtDesc(Long companionId)`, `findByStatus(BookingStatus status)`
  - [ ] `FeedbackRepository`: `findByCompanionId(Long companionId)`
  - [ ] `EmergencyAlertRepository`: `findByStatusOrderByCreatedAtDesc(EmergencyStatus status)`

---

## 🔐 Phase 2: Authentication & User Registration Integration

- [ ] **2.1 Backend Auth & Registration Services**
  - [ ] Update `AuthController.java` `@PostMapping("/register")`:
    - [ ] Check if username/email already exists
    - [ ] Save `User` entity
    - [ ] Handle uploaded `profile_photo` and `identity_document` multipart files (save to local `/uploads` directory)
    - [ ] Save associated `ClientProfile` or `CompanionProfile` with document paths
    - [ ] Return JSON: `{ "success": true, "message": "User registered successfully!", "userId": 123 }`
  - [ ] Update `AuthController.java` `@PostMapping("/login")`:
    - [ ] Query user by username from `UserRepository`
    - [ ] Verify password match
    - [ ] Return JSON: `{ "success": true, "username": "...", "role": "...", "userId": 123, "fullName": "..." }`

- [ ] **2.2 Frontend Registration Integration (`templates/register.html`)**
  - [ ] Update submit handler to send `multipart/form-data` to `http://localhost:8080/api/auth/register`
  - [ ] On success response: display confirmation alert and automatically redirect to `login.html`
  - [ ] On error response: display backend validation error messages inline or via alert

- [ ] **2.3 Frontend Login Integration (`templates/login.html`)**
  - [ ] Remove hardcoded `demoAccounts` JS dictionary
  - [ ] Hook form submit to `POST http://localhost:8080/api/auth/login` with JSON payload `{ username, password }`
  - [ ] On success: store `eldergo_userId`, `eldergo_username`, `eldergo_role`, `eldergo_name` in `localStorage`
  - [ ] Redirect to appropriate dashboard based on `response.role`:
    - [ ] `client` -> `client_dashboard.html`
    - [ ] `companion` -> `companion_dasboard.html`
    - [ ] `admin` -> `admin_dasboard.html`
  - [ ] Fix floating image typo on line 30: `src="../static/images/ .png"` -> `src="../static/images/travelling.png"`

- [ ] **2.4 Global Authentication Guard (`static/js/auth.js`)**
  - [ ] Check if user is logged in when accessing protected dashboard pages
  - [ ] If unauthenticated, redirect immediately to `login.html`
  - [ ] Add unified `logout()` function that clears `localStorage` and redirects to `index.html`

---

## 🏠 Phase 3: Client Dashboard & Booking Flow

- [ ] **3.1 Backend Booking & Client API Endpoints (`BookingController.java`)**
  - [ ] `POST /api/bookings`: Create new booking with status `PENDING`
  - [ ] `GET /api/bookings/client/{clientId}`: Fetch all bookings for the specified client
  - [ ] `PUT /api/bookings/{bookingId}/cancel`: Cancel booking (if status is `PENDING` or `ACCEPTED`)
  - [ ] `POST /api/bookings/{bookingId}/feedback`: Submit rating and review
  - [ ] `GET /api/companions/available`: Return list of verified, available companions for the dropdown
  - [ ] `POST /api/emergency/sos`: Trigger an emergency alert record

- [ ] **3.2 Client Request Form Integration (`templates/client_dashboard.html`)**
  - [ ] On page load, fetch available companions from `GET /api/companions/available` to populate dropdown
  - [ ] Hook `#bookingForm` submission to `POST /api/bookings`
  - [ ] Clear form and refresh active booking list on successful submission

- [ ] **3.3 Dynamic Active Request Status Rendering (`templates/client_dashboard.html`)**
  - [ ] Fetch client bookings from `GET /api/bookings/client/{clientId}`
  - [ ] Dynamically render booking cards by status:
    - [ ] **Pending:** show searching animation + functional "Cancel Request" button
    - [ ] **Accepted:** display assigned companion name, rating, phone + "Call" and "Cancel" buttons
    - [ ] **Ongoing:** display live 4-step transit tracker (`Booked` -> `Picked Up` -> `In Transit` -> `Return`) reflecting backend `transitStage`
    - [ ] **Completed:** display "Leave Feedback" button
  - [ ] Connect "Cancel Request" button to `PUT /api/bookings/{id}/cancel`
  - [ ] Connect "SOS Emergency" button to `POST /api/emergency/sos`
  - [ ] Connect review modal submit to `POST /api/bookings/{id}/feedback`

---

## 🤝 Phase 4: Companion Dashboard & Job Execution

- [ ] **4.1 Backend Companion API Endpoints (`CompanionController.java`)**
  - [ ] `GET /api/companions/{id}/dashboard`: Fetch summary counts (New Requests, Active Job, Completed Jobs, Total Earnings)
  - [ ] `GET /api/companions/{id}/stats?year=...&month=...`: Dynamic analytics filtered by year and month
  - [ ] `PUT /api/companions/{id}/duty-status`: Toggle `isAvailable` (`ON_DUTY` / `OFF_DUTY`)
  - [ ] `GET /api/companions/{id}/requests`: Fetch pending booking requests matching companion's region
  - [ ] `GET /api/companions/{id}/active-job`: Fetch currently assigned active booking
  - [ ] `PUT /api/bookings/{bookingId}/accept`: Companion accepts job -> status becomes `ACCEPTED`
  - [ ] `PUT /api/bookings/{bookingId}/decline`: Companion declines job -> request returns to pool
  - [ ] `PUT /api/bookings/{bookingId}/stage`: Update transit progress (`ARRIVED`, `IN_TRANSIT`)
  - [ ] `PUT /api/bookings/{bookingId}/complete`: Finish duty, record payment, and set status to `COMPLETED`
  - [ ] `GET /api/companions/{id}/reviews`: Fetch ratings & comments submitted by clients

- [ ] **4.2 Companion Controls Integration (`templates/companion_dasboard.html`)**
  - [ ] Hook duty toggle switch to `PUT /api/companions/{id}/duty-status`
  - [ ] Hook Year & Month filters to `GET /api/companions/{id}/stats?year=...&month=...`
  - [ ] Dynamically render incoming requests from `GET /api/companions/{id}/requests`
  - [ ] Connect "Accept Booking" button to `PUT /api/bookings/{id}/accept`
  - [ ] Connect "Decline" button to `PUT /api/bookings/{id}/decline`
  - [ ] Dynamically populate Active Job card with real client info, pickup, and medical notes
  - [ ] Connect "Arrived at Location" & "Start Transit" buttons to `PUT /api/bookings/{id}/stage`
  - [ ] Connect "Mark Job Complete" modal to `PUT /api/bookings/{id}/complete`
  - [ ] Dynamically render client reviews from `GET /api/companions/{id}/reviews`

---

## 🛡️ Phase 5: Admin Dashboard & Emergency Hub

- [ ] **5.1 Backend Admin API Endpoints (`AdminController.java`)**
  - [ ] `GET /api/admin/metrics`: Return platform totals (Total Clients, Total Companions, Pending Verifications, Active Bookings)
  - [ ] `GET /api/admin/clients`: Return all registered clients with search query support
  - [ ] `GET /api/admin/companions`: Return all registered companions with search/status filters
  - [ ] `GET /api/admin/verifications`: Return all companions with `isVerified = false`
  - [ ] `PUT /api/admin/verifications/{id}/approve`: Set companion `isVerified = true`
  - [ ] `PUT /api/admin/verifications/{id}/reject`: Reject companion application
  - [ ] `GET /api/admin/bookings`: Return all bookings across the platform
  - [ ] `GET /api/admin/activity-feed`: Return recent platform audit log events
  - [ ] `GET /api/admin/emergencies`: Return live active SOS emergency alerts
  - [ ] `PUT /api/admin/emergencies/{id}/resolve`: Mark emergency alert as resolved

- [ ] **5.2 Admin Dashboard Integration (`templates/admin_dasboard.html`)**
  - [ ] Load top metric stat cards dynamically from `GET /api/admin/metrics`
  - [ ] Populate Client Management table from `GET /api/admin/clients` (bind search input to live filter)
  - [ ] Populate Companion Management table from `GET /api/admin/companions`
  - [ ] Populate Pending Verification table from `GET /api/admin/verifications`:
    - [ ] Connect "View Document" button to open uploaded PDF/ID inside `#docModal`
    - [ ] Connect "Approve" button to `PUT /api/admin/verifications/{id}/approve`
    - [ ] Connect "Reject" button to `PUT /api/admin/verifications/{id}/reject`
  - [ ] Populate Booking Management table from `GET /api/admin/bookings`
  - [ ] Populate Recent Activity feed from `GET /api/admin/activity-feed`
  - [ ] Populate Live Emergency SOS feed from `GET /api/admin/emergencies`:
    - [ ] Display active SOS cards with client details & location
    - [ ] Connect "Resolve" button to `PUT /api/admin/emergencies/{id}/resolve`

---

## ⚙️ Phase 6: Static File Serving, Security & Polish

- [ ] **6.1 Configure Static File Resource Handler**
  - [ ] Add resource handler in Spring Boot (`WebMvcConfigurer`) to serve uploaded identity documents and avatar photos from `uploads/` directory via `/uploads/**` URL
- [ ] **6.2 Centralized Frontend API Configuration**
  - [ ] Create `static/js/api.js` defining `const API_BASE_URL = 'http://localhost:8080/api';`
  - [ ] Include `api.js` across all templates to avoid hardcoded URLs
- [ ] **6.3 Global Exception Handling (`GlobalExceptionHandler.java`)**
  - [ ] Handle validation errors, entity not found exceptions, and file upload size limits with uniform JSON error responses
- [ ] **6.4 End-to-End Flow Verification**
  - [ ] Test full user lifecycle:
    1. Client & Companion Registration
    2. Admin document verification & approval
    3. Client logs in & books a companion
    4. Companion receives & accepts request
    5. Companion updates transit stages (live-tracked by client)
    6. Companion completes duty & records payment
    7. Client rates companion (updates companion average rating & reviews)
    8. Emergency SOS trigger & Admin resolution
