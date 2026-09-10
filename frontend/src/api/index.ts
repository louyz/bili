import axios, { type AxiosRequestConfig } from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

export default api;

export interface VideoItem {
  id: number;
  bvid: string;
  title: string;
  cover_url: string;
  play_count: number;
  danmaku_count: number;
  comment_count: number;
  like_count: number;
  coin_count: number;
  favorite_count: number;
  share_count: number;
  duration: number;
  pub_time: string;
  partition_main: string;
  partition_sub: string;
  interaction_rate: number;
  heat_score: number;
  up_nickname: string;
  up_follower_count: number;
  tags: string[];
  crawl_time: string;
}

export interface VideoDetail {
  id: number;
  bvid: string;
  title: string;
  cover_url: string;
  description: string;
  play_count: number;
  danmaku_count: number;
  comment_count: number;
  like_count: number;
  coin_count: number;
  favorite_count: number;
  share_count: number;
  duration: number;
  pub_time: string;
  partition_main: string;
  partition_sub: string;
  interaction_rate: number;
  heat_score: number;
  up_user: UpUserInfo;
  tags: string[];
  crawl_time: string;
}

export interface UpUserInfo {
  id: number;
  up_uid: number;
  nickname: string;
  sex: string;
  level: number;
  sign: string;
  avatar_url: string;
  official_role: number;
  official_title: string;
  follower_count: number;
  following_count: number;
  total_likes: number;
  total_plays: number;
  video_count: number;
}

export interface DashboardStats {
  total_videos: number;
  today_new_videos: number;
  avg_play_count: number;
  active_up_count: number;
}

export interface ListResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface TagFrequency {
  tag_name: string;
  video_count: number;
  avg_play_count: number;
  avg_heat_score: number;
}

export interface PartitionStat {
  partition: string;
  count: number;
  avg_heat_score: number;
}

export interface TrendPoint {
  date: string;
  avg_play_count: number;
  video_count: number;
}

export interface UpContribution {
  up_uid: number;
  up_nickname: string;
  avatar_url: string | null;
  level: number;
  video_count: number;
  audio_count: number;
  image_text_count: number;
  elec: number;
  follower_count: number;
  total_contribution: number;
}

export interface UserInfo {
  id: number;
  username: string;
  email: string;
  nickname: string;
  avatar_url: string;
  role: string;
  created_at: string;
}

export interface CrawlLog {
  id: number;
  task_type: string;
  status: string;
  trigger_type: string;
  total_videos: number;
  success_count: number;
  failed_count: number;
  skipped_count: number;
  error_msg: string;
  started_at: string;
  finished_at: string;
  duration_ms: number;
}

// Auth
export const authApi = {
  register: (data: { username: string; email: string; password: string }) =>
    api.post<UserInfo>("/auth/register", data),
  login: (data: { username: string; password: string }) =>
    api.post<{ access_token: string; token_type: string; user: UserInfo }>("/auth/login", data),
  getMe: () => api.get<UserInfo>("/auth/me"),
  updateMe: (data: { nickname?: string; avatar_url?: string }) =>
    api.put<UserInfo>("/auth/me", data),
};

// Videos
export const videoApi = {
  getRanking: (params: {
    page?: number;
    page_size?: number;
    sort_by?: string;
    partition?: string;
    keyword?: string;
  }) => api.get<ListResponse<VideoItem>>("/videos/ranking", { params }),
  getDetail: (bvid: string, config?: AxiosRequestConfig) => api.get<VideoDetail>(`/videos/detail/${bvid}`, config),
  getPartitions: () => api.get<{ name: string; count: number }[]>("/videos/partitions"),
};

// Analysis
export const analysisApi = {
  getDashboard: () => api.get<DashboardStats>("/analysis/dashboard"),
  getTrends: (days: number = 7) =>
    api.get<TrendPoint[]>("/analysis/trends", { params: { days } }),
  getPartitions: () => api.get<PartitionStat[]>("/analysis/partitions"),
  getTags: (limit: number = 50) =>
    api.get<TagFrequency[]>("/analysis/tags", { params: { limit } }),
  getUpRank: (limit: number = 20) =>
    api.get<{ up_uid: number; up_nickname: string; video_count: number; avg_play_count: number; avg_heat_score: number }[]>(
      "/analysis/up-rank",
      { params: { limit } }
    ),
  getUpContribution: (limit: number = 20) =>
    api.get<UpContribution[]>("/analysis/up-contribution", { params: { limit } }),
};

// Favorites
export const favApi = {
  getFolders: () => api.get<any[]>("/favorites/folders"),
  createFolder: (name: string, description?: string) =>
    api.post("/favorites/folders", null, { params: { name, description } }),
  deleteFolder: (id: number) => api.delete(`/favorites/folders/${id}`),
  getVideos: (params: { folder_id?: number; page?: number; page_size?: number }) =>
    api.get("/favorites/videos", { params }),
  addVideo: (bvid: string, folder_id?: number, note?: string) =>
    api.post(`/favorites/videos/${bvid}`, null, { params: { folder_id, note } }),
  removeVideo: (bvid: string, folder_id?: number) =>
    api.delete(`/favorites/videos/${bvid}`, { params: { folder_id } }),
};

// Admin
export const adminApi = {
  getUsers: (params: { page?: number; page_size?: number }) =>
    api.get("/admin/users", { params }),
  createUser: (data: { username: string; email: string; password: string; nickname?: string; role?: string }) =>
    api.post("/admin/users", data),
  updateUser: (id: number, data: { email?: string; nickname?: string; role?: string; is_active?: boolean }) =>
    api.put(`/admin/users/${id}`, data),
  resetUserPassword: (id: number, new_password: string) =>
    api.put(`/admin/users/${id}/reset-password`, { new_password }),
  toggleUserActive: (id: number) =>
    api.put(`/admin/users/${id}/toggle-active`),
  triggerCrawl: (taskType: string = "full_sync") =>
    api.post("/admin/crawl/trigger", null, { params: { task_type: taskType } }),
  stopCrawl: () => api.post("/admin/crawl/stop"),
  getCrawlStatus: () => api.get("/admin/crawl/status"),
  getCrawlLogs: (params: { page?: number; page_size?: number }) =>
    api.get("/admin/crawl/logs", { params }),
};