import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export default function MarkdownEditor({ value, onChange, placeholder }: MarkdownEditorProps) {
  const [tab, setTab] = useState<'edit' | 'preview'>('edit');

  return (
    <div className="border border-gray-300 rounded-md overflow-hidden">
      <div className="flex border-b border-gray-300 bg-gray-50">
        <button
          type="button"
          onClick={() => setTab('edit')}
          className={`px-4 py-2 text-sm font-medium ${
            tab === 'edit'
              ? 'border-b-2 border-blue-500 text-blue-600 bg-white'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Редактирование
        </button>
        <button
          type="button"
          onClick={() => setTab('preview')}
          className={`px-4 py-2 text-sm font-medium ${
            tab === 'preview'
              ? 'border-b-2 border-blue-500 text-blue-600 bg-white'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Предпросмотр
        </button>
      </div>
      <div className="p-3 min-h-[120px]">
        {tab === 'edit' ? (
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className="w-full h-32 resize-y p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
        ) : (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{value || '_Нет содержимого для предпросмотра_'}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
