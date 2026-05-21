import { contentApi } from './client';
import type { Lesson, Heuristic } from '../types';

// Lessons
export const updateLesson = (id: string, data: Partial<Lesson>) =>
  contentApi.patch<Lesson>(`/lessons/${id}`, data);

export const deleteLesson = (id: string) =>
  contentApi.delete(`/lessons/${id}`);

// Heuristics
export const updateHeuristic = (id: string, data: Partial<Heuristic>) =>
  contentApi.patch<Heuristic>(`/heuristics/${id}`, data);

export const deleteHeuristic = (id: string) =>
  contentApi.delete(`/heuristics/${id}`);

export const approveHeuristicEdit = (id: string) =>
  contentApi.post<Heuristic>(`/heuristics/${id}/approve-edit`);

export const rejectHeuristicEdit = (id: string) =>
  contentApi.post<Heuristic>(`/heuristics/${id}/reject-edit`);
