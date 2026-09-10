const API_BASE_URL = 'http://localhost:8000';

export const getAuthToken = () => localStorage.getItem('cogni_token');
export const setAuthToken = (token) => localStorage.setItem('cogni_token', token);
export const removeAuthToken = () => localStorage.removeItem('cogni_token');

export const apiCall = async (endpoint, options = {}) => {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const config = { ...options, headers };
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    if (response.status === 204) {
      return null;
    }
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      if (response.status === 401) {
        removeAuthToken();
        window.dispatchEvent(new Event('auth:unauthorized'));
      }
      throw new Error(data?.detail || data?.message || 'API Error');
    }
    return data;
  } catch (error) {
    console.error(`API Error on ${endpoint}:`, error);
    throw error;
  }
};

export const api = {
  // Auth
  login: (data) => apiCall('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  register: (data) => apiCall('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  getMe: () => apiCall('/me'),

  // Rooms
  createRoom: (data) => apiCall('/rooms', { method: 'POST', body: JSON.stringify(data) }),
  joinRoom: (code) => apiCall(`/rooms/join/${code}`, { method: 'POST' }),
  getMyRooms: () => apiCall('/rooms/my'),
  getRoomEvents: (roomId) => apiCall(`/rooms/${roomId}/events`),

  // Load
  postLoad: (roomId, payload) => apiCall(`/rooms/${roomId}/load/`, { method: 'POST', body: JSON.stringify(payload) }),

  // Quizzes
  createQuiz: (roomId, data) => apiCall(`/rooms/${roomId}/quizzes`, { method: 'POST', body: JSON.stringify(data) }),
  getQuizzes: (roomId) => apiCall(`/rooms/${roomId}/quizzes`),
  submitQuiz: (quizId, data) => apiCall(`/quizzes/${quizId}/attempts`, { method: 'POST', body: JSON.stringify(data) }),
  getQuizStats: (roomId) => apiCall(`/rooms/${roomId}/stats/quiz`),
  generateQuiz: (data) => apiCall('/llm/quiz/generate', { method: 'POST', body: JSON.stringify(data) }),

  // Flashcards
  createFlashcardDeck: (roomId, data) => apiCall(`/rooms/${roomId}/flashcards/decks`, { method: 'POST', body: JSON.stringify(data) }),
  getFlashcardDecks: (roomId) => apiCall(`/rooms/${roomId}/flashcards/decks`),
  getFlashcardDeck: (deckId) => apiCall(`/flashcards/decks/${deckId}`),

  // Analytics & ML
  getUserAnalytics: () => apiCall('/users/me/analytics'),
  getUserActivity: (userId) => apiCall(`/analytics/user/${userId}/activity`),
  getRoomAnalytics: (roomId) => apiCall(`/rooms/${roomId}/analytics`),
  getRoomActivity: (roomId) => apiCall(`/analytics/room/${roomId}/activity`),
  getLiveMetrics: (roomId) => apiCall(`/rooms/${roomId}/metrics/live`),
  getAgentSuggestions: () => apiCall('/users/me/agent/suggestions'),
  getRoomSuggestions: (roomId) => apiCall(`/rooms/${roomId}/agent/suggestions`),
  sendLoadScore: (data) => apiCall('/debug/send-load', { method: 'POST', body: JSON.stringify(data) }),

  // Dashboards
  getMentorOverview: () => apiCall('/mentor/overview'),
  getAdminOverview: () => apiCall('/admin/overview'),
};
