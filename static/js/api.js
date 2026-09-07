// ElderGo+ Unified Flask API Connector Helper

const ElderGoAPI = {
    // Create new booking
    async createBooking(bookingData) {
        try {
            const response = await fetch('/api/bookings/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bookingData)
            });
            return await response.json();
        } catch (e) {
            console.error('API Error:', e);
            return { success: False, message: e.toString() };
        }
    },

    // Get active booking
    async getActiveBooking() {
        try {
            const response = await fetch('/api/bookings/client/active');
            return await response.json();
        } catch (e) {
            return { success: false };
        }
    },

    // Cancel booking
    async cancelBooking(bookingId) {
        try {
            const response = await fetch(`/api/bookings/${bookingId}/cancel`, { method: 'POST' });
            return await response.json();
        } catch (e) {
            return { success: false };
        }
    },

    // Pay booking
    async payBooking(bookingId, paymentMethod) {
        try {
            const response = await fetch(`/api/bookings/${bookingId}/pay`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ paymentMethod })
            });
            return await response.json();
        } catch (e) {
            return { success: false };
        }
    },

    // Submit feedback
    async submitFeedback(bookingId, companionId, rating, comment) {
        try {
            const response = await fetch(`/api/bookings/${bookingId}/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ companionId, rating, comment })
            });
            return await response.json();
        } catch (e) {
            return { success: false };
        }
    },

    // Companion APIs
    async getCompanionRequests() {
        try {
            const response = await fetch('/api/companion/requests');
            return await response.json();
        } catch (e) {
            return { success: false, requests: [] };
        }
    },

    async updateCompanionRate(rate) {
        try {
            const response = await fetch('/api/companion/rate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ hourlyRate: rate })
            });
            return await response.json();
        } catch (e) {
            return { success: false };
        }
    },

    async toggleCompanionDuty(status) {
        try {
            const response = await fetch('/api/companion/status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status })
            });
            return await response.json();
        } catch (e) {
            return { success: false };
        }
    },

    async acceptBooking(bookingId) {
        try {
            const response = await fetch(`/api/bookings/${bookingId}/accept`, { method: 'POST' });
            return await response.json();
        } catch (e) {
            return { success: false };
        }
    },

    async verifyOtp(bookingId, otp) {
        try {
            const response = await fetch(`/api/bookings/${bookingId}/verify-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ otp })
            });
            return await response.json();
        } catch (e) {
            return { success: false };
        }
    },

    async completeBooking(bookingId) {
        try {
            const response = await fetch(`/api/bookings/${bookingId}/complete`, { method: 'POST' });
            return await response.json();
        } catch (e) {
            return { success: false };
        }
    },

    // Admin APIs
    async getAdminStats() {
        try {
            const response = await fetch('/api/admin/stats');
            return await response.json();
        } catch (e) {
            return { success: false };
        }
    },

    async verifyCompanion(verifId, action) {
        try {
            const response = await fetch(`/api/admin/verify-companion/${verifId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action })
            });
            return await response.json();
        } catch (e) {
            return { success: false };
        }
    }
};
