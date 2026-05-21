import { useState, useEffect } from 'react';
import type { Question } from '../../types';

interface QuestionEditorProps {
  question?: Question | null;
  onSave: (data: {
    text: string;
    qtype: 'single' | 'multiple';
    options: { id: string; text: string; is_correct: boolean }[];
  }) => void;
  onCancel: () => void;
}

export function QuestionEditor({ question, onSave, onCancel }: QuestionEditorProps) {
  const [text, setText] = useState('');
  const [qtype, setQtype] = useState<'single' | 'multiple'>('single');
  const [options, setOptions] = useState<{ id: string; text: string; is_correct: boolean }[]>([
    { id: 'a', text: '', is_correct: false },
    { id: 'b', text: '', is_correct: false },
  ]);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    if (question) {
      setText(question.text);
      setQtype(question.qtype as 'single' | 'multiple');
      setOptions(question.options.map((o) => ({ ...o })));
    }
  }, [question]);

  const addOption = () => {
    const nextId = String.fromCharCode(97 + options.length);
    setOptions([...options, { id: nextId, text: '', is_correct: false }]);
  };

  const removeOption = (index: number) => {
    if (options.length <= 2) return;
    const newOptions = options.filter((_, i) => i !== index);
    const reassigned = newOptions.map((opt, i) => ({ ...opt, id: String.fromCharCode(97 + i) }));
    setOptions(reassigned);
  };

  const updateOption = (index: number, field: 'text' | 'is_correct', value: string | boolean) => {
    const newOptions = [...options];
    newOptions[index] = { ...newOptions[index], [field]: value };
    setOptions(newOptions);
  };

  const validate = (): boolean => {
    const errs: string[] = [];
    if (!text.trim()) errs.push('Введите текст вопроса');
    if (options.length < 2) errs.push('Минимум 2 варианта ответа');
    if (options.some((o) => !o.text.trim())) errs.push('Все варианты должны содержать текст');
    const correctCount = options.filter((o) => o.is_correct).length;
    if (qtype === 'single' && correctCount !== 1) errs.push('Одиночный выбор: ровно 1 правильный ответ');
    if (qtype === 'multiple' && correctCount < 1) errs.push('Множественный выбор: минимум 1 правильный ответ');
    setErrors(errs);
    return errs.length === 0;
  };

  const handleSave = () => {
    if (!validate()) return;
    onSave({ text, qtype, options });
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow border border-gray-200 mb-6">
      <h3 className="text-lg font-semibold mb-4">
        {question ? 'Редактирование вопроса' : 'Новый вопрос'}
      </h3>

      {errors.length > 0 && (
        <div className="bg-red-50 text-red-700 p-3 rounded mb-4">
          {errors.map((e, i) => (
            <div key={i}>• {e}</div>
          ))}
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Текст вопроса</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={2}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Тип вопроса</label>
          <select
            value={qtype}
            onChange={(e) => setQtype(e.target.value as 'single' | 'multiple')}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="single">Одиночный выбор</option>
            <option value="multiple">Множественный выбор</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Варианты ответов</label>
          <div className="space-y-2">
            {options.map((opt, index) => (
              <div key={opt.id} className="flex items-center gap-2">
                <span className="text-sm font-mono w-6">{opt.id})</span>
                <input
                  type="text"
                  value={opt.text}
                  onChange={(e) => updateOption(index, 'text', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="Текст варианта"
                />
                <label className="flex items-center gap-1 text-sm whitespace-nowrap">
                  <input
                    type={qtype === 'single' ? 'radio' : 'checkbox'}
                    name="correct"
                    checked={opt.is_correct}
                    onChange={() => {
                      if (qtype === 'single') {
                        setOptions(options.map((o, i) => ({ ...o, is_correct: i === index })));
                      } else {
                        updateOption(index, 'is_correct', !opt.is_correct);
                      }
                    }}
                  />
                  Правильный
                </label>
                <button
                  type="button"
                  onClick={() => removeOption(index)}
                  disabled={options.length <= 2}
                  className="text-red-600 hover:text-red-800 disabled:opacity-30 text-sm"
                >
                  Удалить
                </button>
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={addOption}
            className="mt-2 text-sm text-indigo-600 hover:underline"
          >
            + Добавить вариант
          </button>
        </div>

        <div className="flex gap-4 pt-2">
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            Сохранить
          </button>
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
          >
            Отмена
          </button>
        </div>
      </div>
    </div>
  );
}
