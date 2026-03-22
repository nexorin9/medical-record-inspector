import type { Template } from '@/types/template';

export interface TemplateManagerResponse {
  total: number;
  templates: Template[];
}

export interface TemplateResponse {
  id: string;
  name: string;
  description: string;
  content: string;
  created_at: string;
  updated_at: string;
  version: number;
  tags: string[];
}

export const fetchTemplates = async (): Promise<Template[]> => {
  const response = await fetch('/api/v1/templates');
  if (!response.ok) {
    throw new Error('Failed to fetch templates');
  }
  const data: TemplateManagerResponse = await response.json();
  return data.templates;
};

export const fetchTemplate = async (templateId: string): Promise<Template> => {
  const response = await fetch(`/api/v1/templates/${templateId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch template');
  }
  return await response.json();
};

export const createTemplate = async (template: Omit<Template, 'id' | 'created_at' | 'updated_at' | 'version'>): Promise<Template> => {
  const response = await fetch('/api/v1/templates', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(template),
  });
  if (!response.ok) {
    throw new Error('Failed to create template');
  }
  return await response.json();
};

export const updateTemplate = async (
  templateId: string,
  template: Partial<Omit<Template, 'id' | 'created_at' | 'updated_at'>>
): Promise<Template> => {
  const response = await fetch(`/api/v1/templates/${templateId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(template),
  });
  if (!response.ok) {
    throw new Error('Failed to update template');
  }
  return await response.json();
};

export const deleteTemplate = async (templateId: string): Promise<void> => {
  const response = await fetch(`/api/v1/templates/${templateId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete template');
  }
};
