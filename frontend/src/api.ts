// frontend/src/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

export interface ScheduleCourse {
  course_id?: string;
  room?: string;
  time_slot?: string;
  [key: string]: any;
}

// Ensure 'export' is explicitly here:
export interface GeneratedSchedule {
  schedule_id: number;
  courses: string[];
}

export const uploadConfig = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/config/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getConfig = async () => {
  const response = await api.get('/config/');
  return response.data;
};

export const runGenerator = async () => {
  const response = await api.post('/generator/run');
  return response.data;
};