import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { Question } from '../../types';

interface Props {
  question: Question;
  onEdit: (q: Question) => void;
  onDelete: (id: string) => void;
}

export function QuestionSortableItem({ question, onEdit, onDelete }: Props) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: question.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="bg-white p-4 rounded-lg shadow border border-gray-200 flex items-center gap-4"
    >
      <div
        {...attributes}
        {...listeners}
        className="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600 select-none"
        title="Перетащить"
      >
        ⋮⋮
      </div>
      <div className="flex-1">
        <div className="font-medium">{question.text}</div>
        <div className="text-sm text-gray-500 mt-1">
          Тип: {question.qtype === 'single' ? 'Одиночный' : 'Множественный'} | Вариантов: {question.options.length}
        </div>
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => onEdit(question)}
          className="text-indigo-600 hover:underline text-sm"
        >
          Редактировать
        </button>
        <button
          onClick={() => onDelete(question.id)}
          className="text-red-600 hover:underline text-sm"
        >
          Удалить
        </button>
      </div>
    </div>
  );
}
