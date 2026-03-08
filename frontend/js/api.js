/**
 * Centralized API configuration and interaction layer for UniCollab.
 */

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:10000'
    : 'https://unicollab-4zgf.onrender.com';

const API = {
    async request(endpoint, method = 'GET', data = null) {
        const token = localStorage.getItem('uc_token');
        const headers = {
            'Content-Type': 'application/json',
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            method,
            headers,
        };

        if (data) {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
            const responseData = await response.json();

            if (!response.ok) {
                throw new Error(responseData.detail || 'API Request Failed');
            }

            return responseData;
        } catch (error) {
            console.error(`API Error on ${endpoint}:`, error);
            throw error;
        }
    },

    // Authentication
    async login(email, password) {
        const res = await this.request('/login', 'POST', { email, password });
        localStorage.setItem('uc_token', res.token);
        localStorage.setItem('uc_user', JSON.stringify(res.user));
        return res;
    },

    logout() {
        localStorage.removeItem('uc_token');
        localStorage.removeItem('uc_user');
        window.location.href = 'login.html';
    },

    getUser() {
        const userStr = localStorage.getItem('uc_user');
        return userStr ? JSON.parse(userStr) : null;
    },

    isAuthenticated() {
        return !!localStorage.getItem('uc_token');
    },

    // Profile & Skills
    async createProfile(profileData) {
        const res = await this.request('/create-profile', 'POST', profileData);
        localStorage.setItem('uc_user', JSON.stringify(res.user));
        return res;
    },

    async saveSkills(skillsList) {
        return await this.request('/skills', 'POST', { skills: skillsList });
    },

    // Discover & Projects
    async getDiscoverFeed() {
        return await this.request('/discover');
    },

    async getProjects() {
        return await this.request('/project/list');
    },

    async createProject(projectData) {
        return await this.request('/project/create', 'POST', projectData);
    }
};

// Utilities for UI
function enforceAuth() {
    if (!API.isAuthenticated()) {
        window.location.href = 'login.html';
    }
}
