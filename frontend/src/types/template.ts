export interface Template {
  id: string;
  name: string;
  description: string;
  content: string;
  created_at: string;
  updated_at: string;
  version: number;
  tags: string[];
}

export interface TemplateFormData {
  name: string;
  description: string;
  content: string;
  tags: string[];
}

export interface TemplateHistory {
  version: number;
  updated_at: string;
  name: string;
}
