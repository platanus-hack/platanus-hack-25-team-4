import axios, { AxiosInstance } from 'axios';
import type {
  ObserverStats,
  EventsResponse,
  UserActivityResponse,
  EventCategory,
} from '../types/observer.types';

class ObserverApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:3000/api/observer') {
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Get aggregated observer statistics
   * Returns unique users, total events, active conversations, and observer system health
   */
  async getStats(): Promise<ObserverStats> {
    const response = await this.client.get<ObserverStats>('/stats');
    return response.data;
  }

  /**
   * Get recent events by type
   * @param type - Event category to filter by ('all', 'location', 'collision', etc.)
   * @param limit - Maximum number of events to return (default: 200)
   */
  async getEvents(
    type: EventCategory = 'all',
    limit: number = 200
  ): Promise<EventsResponse> {
    const response = await this.client.get<EventsResponse>(`/events/${type}`, {
      params: { limit },
    });
    return response.data;
  }

  /**
   * Get activity for a specific user
   * @param userId - User ID to fetch activity for
   * @param limit - Maximum number of events to return (default: 100)
   */
  async getUserActivity(
    userId: string,
    limit: number = 100
  ): Promise<UserActivityResponse> {
    const response = await this.client.get<UserActivityResponse>(
      `/users/${userId}/activity`,
      {
        params: { limit },
      }
    );
    return response.data;
  }

  /**
   * Get events for multiple categories
   * Useful for filtered views
   */
  async getEventsByCategories(
    categories: EventCategory[],
    limit: number = 200
  ): Promise<EventsResponse[]> {
    const requests = categories.map((category) =>
      this.getEvents(category, limit)
    );
    return Promise.all(requests);
  }

  /**
   * Update the base URL for the API client
   * Useful for switching between development and production
   */
  setBaseURL(baseURL: string): void {
    this.client.defaults.baseURL = baseURL;
  }
}

// Export singleton instance
export const observerApi = new ObserverApiClient();

// Also export the class for testing
export { ObserverApiClient };
