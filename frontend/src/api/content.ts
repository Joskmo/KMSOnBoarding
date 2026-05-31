import { contentApi } from './client';
import type { Lesson, Heuristic, ModuleAssignment } from '../types';

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

// Module assignments
export const getModuleAssignments = (moduleId: string) =>
  contentApi.get<ModuleAssignment[]>(`/modules/${moduleId}/assignments`);

export const assignModule = (moduleId: string, userIds: string[]) =>
  contentApi.post<ModuleAssignment[]>(`/modules/${moduleId}/assignments`, { user_ids: userIds });

export const unassignModule = (moduleId: string, userId: string) =>
  contentApi.delete(`/modules/${moduleId}/assignments/${userId}`);
