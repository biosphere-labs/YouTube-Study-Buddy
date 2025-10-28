import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useNote, useUpdateNote, useDeleteNote } from '../hooks/useNotes';
import { SubjectBadge } from '../components/notes/SubjectBadge';
import { NotePreview } from '../components/notes/NotePreview';
import { NoteEditorContainer } from '../components/notes/NoteEditorContainer';
import { GraphContainer } from '../components/notes/GraphContainer';
import { AssessmentPanel } from '../components/notes/AssessmentPanel';
import { formatDistanceToNow } from 'date-fns';

export function NoteDetails() {
  const { id: noteId } = useParams<{ id: string }>();
  const [isEditing, setIsEditing] = useState(false);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [title, setTitle] = useState('');
  const [showGraph, setShowGraph] = useState(false);

  if (!noteId) {
    window.location.href = '/notes';
    return null;
  }

  const { data: note, isLoading, error } = useNote(noteId);
  const updateNoteMutation = useUpdateNote();
  const deleteNoteMutation = useDeleteNote();

  useEffect(() => {
    if (note) {
      setTitle(note.title);
    }
  }, [note]);

  const handleSaveContent = async (content: string) => {
    if (!note) return;

    try {
      await updateNoteMutation.mutateAsync({
        id: note.id,
        data: { content },
      });
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to save content:', error);
      throw error; // Let the editor handle the error
    }
  };

  const handleSaveTitle = async () => {
    if (!note || title === note.title) {
      setIsEditingTitle(false);
      return;
    }

    try {
      await updateNoteMutation.mutateAsync({
        id: note.id,
        data: { title },
      });
      setIsEditingTitle(false);
    } catch (error) {
      console.error('Failed to save title:', error);
      alert('Failed to save title. Please try again.');
      setTitle(note.title);
    }
  };

  const handleDelete = async () => {
    if (!note) return;

    if (confirm(`Are you sure you want to delete "${note.title}"?`)) {
      try {
        await deleteNoteMutation.mutateAsync(note.id);
        // Navigate back to notes list
        window.location.href = '/notes';
      } catch (error) {
        console.error('Failed to delete note:', error);
        alert('Failed to delete note. Please try again.');
      }
    }
  };

  const handleWikiLinkClick = (noteTitle: string) => {
    // TODO: Search for note by title and navigate
    console.log('Wiki link clicked:', noteTitle);
    alert(`Wiki link navigation not implemented yet: ${noteTitle}`);
  };

  const handleDownloadPDF = () => {
    if (note?.pdfUrl) {
      window.open(note.pdfUrl, '_blank');
    }
  };

  const handleExportMarkdown = () => {
    if (!note) return;

    const blob = new Blob([note.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${note.title}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-8"></div>
          <div className="h-96 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !note) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">
            Failed to load note. It may have been deleted or you don't have access.
          </p>
          <button
            onClick={() => (window.location.href = '/notes')}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Back to Notes
          </button>
        </div>
      </div>
    );
  }

  const timeAgo = formatDistanceToNow(new Date(note.updatedAt), {
    addSuffix: true,
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Button */}
      <button
        onClick={() => (window.location.href = '/notes')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M10 19l-7-7m0 0l7-7m-7 7h18"
          />
        </svg>
        Back to Notes
      </button>

      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            {isEditingTitle ? (
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                onBlur={handleSaveTitle}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSaveTitle();
                  if (e.key === 'Escape') {
                    setTitle(note.title);
                    setIsEditingTitle(false);
                  }
                }}
                className="text-3xl font-bold text-gray-900 border-b-2 border-blue-500 focus:outline-none w-full"
                autoFocus
              />
            ) : (
              <h1
                className="text-3xl font-bold text-gray-900 cursor-pointer hover:text-blue-600"
                onClick={() => setIsEditingTitle(true)}
              >
                {note.title}
              </h1>
            )}

            <div className="flex items-center gap-3 mt-3">
              {note.subject && <SubjectBadge subject={note.subject} />}
              <span className="text-sm text-gray-500">Updated {timeAgo}</span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 ml-4">
            <button
              onClick={() => setIsEditing(!isEditing)}
              className={`px-4 py-2 text-sm font-medium rounded ${
                isEditing
                  ? 'bg-gray-200 text-gray-700'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {isEditing ? 'View Mode' : 'Edit'}
            </button>

            {note.pdfUrl && (
              <button
                onClick={handleDownloadPDF}
                className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded hover:bg-gray-50"
                title="Download PDF"
              >
                PDF
              </button>
            )}

            <button
              onClick={handleExportMarkdown}
              className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded hover:bg-gray-50"
              title="Export Markdown"
            >
              Export
            </button>

            <button
              onClick={handleDelete}
              className="px-4 py-2 text-sm font-medium text-red-600 border border-red-300 rounded hover:bg-red-50"
            >
              Delete
            </button>
          </div>
        </div>

        {/* Source Video Link */}
        {note.videoId && (
          <div className="mt-4 text-sm text-gray-600">
            <a
              href={`/videos/${note.videoId}`}
              className="text-blue-600 hover:text-blue-800 underline"
            >
              View source video
            </a>
          </div>
        )}
      </div>

      {/* Graph Toggle */}
      <div className="mb-6">
        <button
          onClick={() => setShowGraph(!showGraph)}
          className="flex items-center gap-2 text-gray-700 hover:text-gray-900"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          {showGraph ? 'Hide' : 'Show'} Knowledge Graph
        </button>
      </div>

      {/* Knowledge Graph */}
      {showGraph && (
        <div className="mb-6">
          <GraphContainer
            userId={note.userId}
            noteIds={[note.id]}
            onNodeClick={(id) => (window.location.href = `/notes/${id}`)}
          />
        </div>
      )}

      {/* Content Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        {isEditing ? (
          <NoteEditorContainer
            noteId={note.id}
            initialContent={note.content}
            onSave={handleSaveContent}
          />
        ) : (
          <NotePreview content={note.content} onWikiLinkClick={handleWikiLinkClick} />
        )}
      </div>

      {/* Assessment Section */}
      {note.assessmentContent && (
        <div className="mb-6">
          <AssessmentPanel content={note.assessmentContent} />
        </div>
      )}
    </div>
  );
}
