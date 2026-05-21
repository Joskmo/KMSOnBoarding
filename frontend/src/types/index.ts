export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string | null;
  role: 'admin' | 'methodist' | 'seminarist' | 'candidate';
  manager_id: string | null;
  full_name: string | null;
}

export interface Module {
  id: string;
  title: string;
  description: string | null;
  status: 'draft' | 'published' | 'archived';
  author_id: string;
  manager_id: string;
  lesson_count: number;
  created_at: string;
  updated_at: string;
}

export interface Lesson {
  id: string;
  title: string;
  r7_uri: string;
  module_id: string;
  order_index: number;
  author_id: string;
  created_at: string;
  updated_at: string;
}

export interface Heuristic {
  id: string;
  content: string;
  module_id: string;
  author_id: string;
  manager_id: string;
  is_approved: boolean;
  created_at: string;
  updated_at: string;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface Invitation {
  id: string;
  token: string;
  email: string | null;
  role_name: string;
  manager_id: string | null;
  created_by: string | null;
  used: boolean;
  used_by: string | null;
  expires_at: string;
  created_at: string;
}
