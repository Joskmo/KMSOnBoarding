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
  content: string | null;
  module_id: string;
  order_index: number;
  author_id: string;
  created_at: string;
  updated_at: string;
}

export interface Heuristic {
  id: string;
  content: string;
  pending_content: string | null;
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

export interface Test {
  id: string;
  module_id: string;
  title: string;
  description: string | null;
  pass_score: number;
  author_id: string;
  manager_id: string;
  is_active: boolean;
  question_count: number;
  created_at: string;
  updated_at: string;
}

export interface OptionItem {
  id: string;
  text: string;
  is_correct: boolean;
}

export interface OptionForAttempt {
  id: string;
  text: string;
}

export interface Question {
  id: string;
  test_id: string;
  order_index: number;
  text: string;
  qtype: 'single' | 'multiple';
  options: OptionItem[];
  created_at: string;
  updated_at: string;
}

export interface QuestionForAttempt {
  id: string;
  order_index: number;
  text: string;
  qtype: 'single' | 'multiple';
  options: OptionForAttempt[];
}

export interface AttemptStart {
  test_id: string;
  title: string;
  pass_score: number;
  questions: QuestionForAttempt[];
}

export interface Attempt {
  id: string;
  test_id: string;
  user_id: string;
  manager_id: string;
  answers: Record<string, string[]>;
  score: number;
  is_passed: boolean;
  started_at: string;
  finished_at: string;
}

export interface AttemptListItem {
  id: string;
  test_id: string;
  user_id: string;
  manager_id: string;
  score: number;
  is_passed: boolean;
  started_at: string;
  finished_at: string;
}
