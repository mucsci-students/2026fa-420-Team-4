// frontend/view/api.ts
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

export const validateConfig = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/config/validate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getConfig = async () => {
  const response = await api.get('/config/');
  return response.data;
};

/** Request schedule generation with the supplied limit and return the response data; zero clears results. */
export const runGenerator = async (limit: number) => {
  const response = await api.post('/generator/run', null, {
    params: { limit },
  });
  return response.data;
};

export const exportScheduleCsv = async () => {
  const response = await api.get('/schedule/export/csv', {
    responseType: 'blob',
  });
  const contentDisposition = response.headers['content-disposition'] as
    | string
    | undefined;
  const encodedFilename = contentDisposition?.match(
    /filename\*=UTF-8''([^;]+)/i,
  )?.[1];
  const quotedFilename = contentDisposition?.match(
    /filename="([^"]+)"/i,
  )?.[1];
  const filename = encodedFilename
    ? decodeURIComponent(encodedFilename)
    : quotedFilename ?? 'schedules.csv';

  return { blob: response.data as Blob, filename };
};

export const getGeneratorProgress = async (): Promise<{
  count: number;
  running: boolean;
}> => {
  const response = await api.get('/generator/progress');
  return response.data;
};