import { useState } from 'react';
import { useNotes, useDeleteNote } from '../hooks/useNotes';
import { NotesQuery, Note } from '../types/note';
import { NotesFilters } from '../components/notes/NotesFilters';
import { NotesGrid } from '../components/notes/NotesGrid';
import { NotesList } from '../components/notes/NotesList';

export function Notes() {
  const [query, setQuery] = useState<NotesQuery>({
    page: 1,
    limit: 12,
    sortBy: 'date',
    sortOrder: 'desc',
  });
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const { data, isLoading, error } = useNotes(query);
  const deleteNoteMutation = useDeleteNote();

  // Extract unique subjects from notes for filter dropdown
  const subjects = data?.data
    ? Array.from(new Set(data.data.map((n) => n.subject).filter(Boolean)))
    : [];

  const handleNoteClick = (note: Note) => {
    // Navigate to note details page
    // This will be wired up with router
    window.location.href = `/notes/${note.id}`;
  };

  const handleNoteDelete = async (id: string) => {
    try {
      await deleteNoteMutation.mutateAsync(id);
    } catch (error) {
      console.error('Failed to delete note:', error);
      alert('Failed to delete note. Please try again.');
    }
  };

  const handleSubjectClick = (subject: string) => {
    setQuery((prev) => ({
      ...prev,
      subject,
      page: 1,
    }));
  };

  const handlePageChange = (page: number) => {
    setQuery((prev) => ({ ...prev, page }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">
            Failed to load notes. Please try again later.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Notes</h1>
        <p className="mt-2 text-gray-600">
          View and manage all your study notes
        </p>
      </div>

      {/* Filters */}
      <NotesFilters
        query={query}
        onQueryChange={setQuery}
        subjects={subjects}
      />

      {/* Notes Grid/List */}
      {viewMode === 'grid' ? (
        <NotesGrid
          notes={data?.data || []}
          onNoteClick={handleNoteClick}
          onNoteDelete={handleNoteDelete}
          onSubjectClick={handleSubjectClick}
          isLoading={isLoading}
        />
      ) : (
        <NotesList
          notes={data?.data || []}
          onNoteClick={handleNoteClick}
          onNoteDelete={handleNoteDelete}
          onSubjectClick={handleSubjectClick}
          isLoading={isLoading}
        />
      )}

      {/* Pagination */}
      {data && data.meta.totalPages > 1 && (
        <div className="mt-8 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing{' '}
            <span className="font-medium">
              {(data.meta.page - 1) * data.meta.limit + 1}
            </span>{' '}
            to{' '}
            <span className="font-medium">
              {Math.min(data.meta.page * data.meta.limit, data.meta.total)}
            </span>{' '}
            of <span className="font-medium">{data.meta.total}</span> results
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => handlePageChange(data.meta.page - 1)}
              disabled={data.meta.page === 1}
              className={`px-4 py-2 text-sm font-medium rounded ${
                data.meta.page === 1
                  ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                  : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
              }`}
            >
              Previous
            </button>

            {/* Page Numbers */}
            <div className="flex gap-1">
              {Array.from({ length: data.meta.totalPages }, (_, i) => i + 1)
                .filter((page) => {
                  // Show first, last, current, and adjacent pages
                  return (
                    page === 1 ||
                    page === data.meta.totalPages ||
                    Math.abs(page - data.meta.page) <= 1
                  );
                })
                .map((page, index, array) => {
                  // Add ellipsis
                  if (index > 0 && page - array[index - 1] > 1) {
                    return (
                      <>
                        <span
                          key={`ellipsis-${page}`}
                          className="px-3 py-2 text-gray-500"
                        >
                          ...
                        </span>
                        <button
                          key={page}
                          onClick={() => handlePageChange(page)}
                          className={`px-4 py-2 text-sm font-medium rounded ${
                            page === data.meta.page
                              ? 'bg-blue-600 text-white'
                              : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                          }`}
                        >
                          {page}
                        </button>
                      </>
                    );
                  }

                  return (
                    <button
                      key={page}
                      onClick={() => handlePageChange(page)}
                      className={`px-4 py-2 text-sm font-medium rounded ${
                        page === data.meta.page
                          ? 'bg-blue-600 text-white'
                          : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                      }`}
                    >
                      {page}
                    </button>
                  );
                })}
            </div>

            <button
              onClick={() => handlePageChange(data.meta.page + 1)}
              disabled={data.meta.page === data.meta.totalPages}
              className={`px-4 py-2 text-sm font-medium rounded ${
                data.meta.page === data.meta.totalPages
                  ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                  : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
              }`}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
