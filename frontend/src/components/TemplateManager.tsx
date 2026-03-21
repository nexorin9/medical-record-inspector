import { useState, useEffect } from 'react';
import { fetchTemplates, createTemplate, updateTemplate, deleteTemplate } from '@/hooks/useTemplates';
import { Template, TemplateFormData } from '@/types/template';

const TemplateManager = () => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [formData, setFormData] = useState<TemplateFormData>({
    name: '',
    description: '',
    content: '',
    tags: [],
  });

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const data = await fetchTemplates();
      setTemplates(data);
      setError(null);
    } catch (err) {
      setError('Failed to load templates');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClick = () => {
    setFormData({ name: '', description: '', content: '', tags: [] });
    setShowCreateModal(true);
    setSelectedTemplate(null);
    setShowEditModal(false);
  };

  const handleEditClick = (template: Template) => {
    setSelectedTemplate(template);
    setFormData({
      name: template.name,
      description: template.description,
      content: template.content,
      tags: template.tags,
    });
    setShowEditModal(true);
    setShowCreateModal(false);
  };

  const handleDeleteClick = async (templateId: string) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }

    try {
      await deleteTemplate(templateId);
      setTemplates(templates.filter((t) => t.id !== templateId));
      setError(null);
    } catch (err) {
      setError('Failed to delete template');
      console.error(err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (selectedTemplate) {
        // Update existing template
        const updated = await updateTemplate(selectedTemplate.id, formData);
        setTemplates(templates.map((t) => (t.id === selectedTemplate.id ? updated : t)));
        setSelectedTemplate(updated);
      } else {
        // Create new template
        const newTemplate = await createTemplate(formData);
        setTemplates([...templates, newTemplate]);
      }
      setShowCreateModal(false);
      setShowEditModal(false);
      setError(null);
    } catch (err) {
      setError('Failed to save template');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setShowCreateModal(false);
    setShowEditModal(false);
    setSelectedTemplate(null);
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  };

  if (loading && templates.length === 0) {
    return <div className="template-manager loading">Loading templates...</div>;
  }

  return (
    <div className="template-manager">
      <div className="header">
        <h2>Template Manager</h2>
        <button onClick={handleCreateClick} className="btn-primary">
          + Create Template
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="templates-grid">
        {templates.map((template) => (
          <div key={template.id} className="template-card">
            <div className="card-header">
              <h3>{template.name}</h3>
              <span className="version">v{template.version}</span>
            </div>
            <p className="card-description">{template.description}</p>
            <div className="card-footer">
              <span className="tags">
                {template.tags.length > 0 && template.tags.map((tag, idx) => (
                  <span key={idx} className="tag">{tag}</span>
                ))}
              </span>
              <div className="card-actions">
                <button onClick={() => handleEditClick(template)} className="btn-secondary">
                  Edit
                </button>
                <button onClick={() => handleDeleteClick(template.id)} className="btn-danger">
                  Delete
                </button>
              </div>
            </div>
            <div className="card-meta">
              <span>Last updated: {formatDateTime(template.updated_at)}</span>
            </div>
          </div>
        ))}
      </div>

      {showCreateModal && (
        <Modal title="Create Template" onClose={handleCancel}>
          <TemplateForm
            formData={formData}
            setFormData={setFormData}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            loading={loading}
          />
        </Modal>
      )}

      {showEditModal && selectedTemplate && (
        <Modal title={`Edit Template: ${selectedTemplate.name}`} onClose={handleCancel}>
          <TemplateForm
            formData={formData}
            setFormData={setFormData}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            loading={loading}
          />
        </Modal>
      )}
    </div>
  );
};

interface ModalProps {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}

const Modal = ({ title, children, onClose }: ModalProps) => {
  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h3>{title}</h3>
          <button onClick={onClose} className="btn-close">&times;</button>
        </div>
        <div className="modal-body">
          {children}
        </div>
      </div>
    </div>
  );
};

interface TemplateFormProps {
  formData: TemplateFormData;
  setFormData: React.Dispatch<React.SetStateAction<TemplateFormData>>;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  loading: boolean;
}

const TemplateForm = ({ formData, setFormData, onSubmit, onCancel, loading }: TemplateFormProps) => {
  return (
    <form onSubmit={onSubmit} className="template-form">
      <div className="form-group">
        <label htmlFor="name">Template Name *</label>
        <input
          id="name"
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          required
          minLength={1}
          maxLength={100}
          placeholder="Enter template name"
        />
      </div>

      <div className="form-group">
        <label htmlFor="description">Description *</label>
        <textarea
          id="description"
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          required
          minLength={1}
          maxLength={500}
          placeholder="Enter template description"
          rows={3}
        />
      </div>

      <div className="form-group">
        <label htmlFor="content">Template Content *</label>
        <textarea
          id="content"
          value={formData.content}
          onChange={(e) => setFormData({ ...formData, content: e.target.value })}
          required
          minLength={1}
          placeholder="Paste the high-quality medical record template content here..."
          rows={10}
        />
      </div>

      <div className="form-group">
        <label htmlFor="tags">Tags (comma-separated)</label>
        <input
          id="tags"
          type="text"
          value={formData.tags.join(', ')}
          onChange={(e) => setFormData({ ...formData, tags: e.target.value.split(',').map(t => t.trim()).filter(t => t) })}
          placeholder="Enter tags separated by commas"
        />
      </div>

      <div className="form-actions">
        <button type="button" onClick={onCancel} className="btn-secondary" disabled={loading}>
          Cancel
        </button>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Saving...' : 'Save Template'}
        </button>
      </div>
    </form>
  );
};

export default TemplateManager;
