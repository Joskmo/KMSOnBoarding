import { assessmentApi } from './client';
import type {
  Test,
  Question,
  Attempt,
  AttemptStart,
  AttemptListItem,
  Paginated,
} from '../types';

// Tests
export const getTests = (params?: { module_id?: string; page?: number; size?: number }) =>
  assessmentApi.get<Paginated<Test>>('/tests', { params });

export const getTest = (id: string) =>
  assessmentApi.get<Test>(`/tests/${id}`);

export const createTest = (data: {
  module_id: string;
  title: string;
  description?: string;
  pass_score?: number;
}) => assessmentApi.post<Test>('/tests', data);

export const updateTest = (id: string, data: Partial<Test>) =>
  assessmentApi.patch<Test>(`/tests/${id}`, data);

export const deleteTest = (id: string) =>
  assessmentApi.delete(`/tests/${id}`);

// Questions
export const getQuestions = (testId: string) =>
  assessmentApi.get<Question[]>(`/tests/${testId}/questions`);

export const createQuestion = (
  testId: string,
  data: {
    text: string;
    qtype: 'single' | 'multiple';
    order_index?: number;
    options: { id: string; text: string; is_correct: boolean }[];
  }
) => assessmentApi.post<Question>(`/tests/${testId}/questions`, data);

export const updateQuestion = (id: string, data: Partial<Question>) =>
  assessmentApi.patch<Question>(`/questions/${id}`, data);

export const reorderQuestion = (id: string, order_index: number) =>
  assessmentApi.patch<Question>(`/questions/${id}/reorder`, { order_index });

export const deleteQuestion = (id: string) =>
  assessmentApi.delete(`/questions/${id}`);

// Attempts
export const startAttempt = (testId: string) =>
  assessmentApi.get<AttemptStart>(`/attempts/start/${testId}`);

export const submitAttempt = (data: { test_id: string; answers: Record<string, string[]> }) =>
  assessmentApi.post<Attempt>('/attempts', data);

export const getMyAttempts = (params?: { test_id?: string; page?: number; size?: number }) =>
  assessmentApi.get<Paginated<AttemptListItem>>('/attempts/my', { params });

export const getTestAttempts = (testId: string, params?: { page?: number; size?: number }) =>
  assessmentApi.get<Paginated<AttemptListItem>>(`/attempts/test/${testId}`, { params });

export const getAttempt = (id: string) =>
  assessmentApi.get<Attempt>(`/attempts/${id}`);
