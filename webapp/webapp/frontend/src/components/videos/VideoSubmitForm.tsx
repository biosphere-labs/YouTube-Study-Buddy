import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { useCreateVideo } from '../../hooks/useVideos';
import type { CreateVideoDto } from '../../types';

const videoSchema = z.object({
  url: z
    .string()
    .min(1, 'URL is required')
    .url('Invalid URL')
    .regex(
      /(youtube\.com\/watch\?v=|youtu\.be\/)/,
      'Must be a YouTube URL (youtube.com or youtu.be)'
    ),
  subject: z.string().optional(),
  generateAssessments: z.boolean().optional(),
});

type VideoFormData = z.infer<typeof videoSchema>;

export const VideoSubmitForm: React.FC = () => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<VideoFormData>({
    resolver: zodResolver(videoSchema),
    defaultValues: {
      url: '',
      subject: '',
      generateAssessments: true,
    },
  });

  const createVideo = useCreateVideo();

  const onSubmit = async (data: VideoFormData) => {
    try {
      const payload: CreateVideoDto = {
        url: data.url,
        subject: data.subject || undefined,
        generateAssessments: data.generateAssessments ?? true,
      };

      await createVideo.mutateAsync(payload);
      toast.success('Video submitted for processing!');
      reset();
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Failed to submit video';
      toast.error(errorMessage);
      console.error('Video submission error:', error);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Submit YouTube Video</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* URL Input */}
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-1">
            YouTube URL <span className="text-red-500">*</span>
          </label>
          <input
            id="url"
            type="text"
            {...register('url')}
            placeholder="https://www.youtube.com/watch?v=..."
            autoFocus
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              errors.url ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.url && (
            <p className="mt-1 text-sm text-red-600">{errors.url.message}</p>
          )}
        </div>

        {/* Subject Input */}
        <div>
          <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-1">
            Subject (Optional)
          </label>
          <input
            id="subject"
            type="text"
            {...register('subject')}
            placeholder="e.g., Mathematics, History, Computer Science"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="mt-1 text-xs text-gray-500">
            Helps categorize your notes (leave empty for auto-detection)
          </p>
        </div>

        {/* Generate Assessments Checkbox */}
        <div className="flex items-center">
          <input
            id="generateAssessments"
            type="checkbox"
            {...register('generateAssessments')}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="generateAssessments" className="ml-2 block text-sm text-gray-700">
            Generate assessments and quiz questions
          </label>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting || createVideo.isPending}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting || createVideo.isPending ? (
            <span className="flex items-center justify-center gap-2">
              <svg
                className="animate-spin h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Submitting...
            </span>
          ) : (
            'Submit Video'
          )}
        </button>
      </form>
    </div>
  );
};
