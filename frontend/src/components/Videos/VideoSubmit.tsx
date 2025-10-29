import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { videosApi } from '@/api/videos';
import { Loader2 } from 'lucide-react';

export function VideoSubmit() {
  const [url, setUrl] = useState('');
  const [subject, setSubject] = useState('');
  const queryClient = useQueryClient();

  const submitMutation = useMutation({
    mutationFn: videosApi.submitVideo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
      setUrl('');
      setSubject('');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    submitMutation.mutate({
      url: url.trim(),
      subject: subject.trim() || undefined,
    });
  };

  const isValidYouTubeUrl = (urlString: string) => {
    try {
      const url = new URL(urlString);
      return url.hostname.includes('youtube.com') || url.hostname.includes('youtu.be');
    } catch {
      return false;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Submit Video</CardTitle>
        <CardDescription>
          Enter a YouTube URL to generate study notes
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="url" className="text-sm font-medium">
              YouTube URL
            </label>
            <Input
              id="url"
              type="url"
              placeholder="https://www.youtube.com/watch?v=..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="mt-1"
              required
            />
            {url && !isValidYouTubeUrl(url) && (
              <p className="text-sm text-destructive mt-1">
                Please enter a valid YouTube URL
              </p>
            )}
          </div>

          <div>
            <label htmlFor="subject" className="text-sm font-medium">
              Subject (Optional)
            </label>
            <Input
              id="subject"
              type="text"
              placeholder="e.g., Computer Science, History, etc."
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="mt-1"
            />
          </div>

          {submitMutation.isError && (
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
              <p className="text-sm text-destructive">
                {submitMutation.error?.message || 'Failed to submit video'}
              </p>
            </div>
          )}

          {submitMutation.isSuccess && (
            <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
              <p className="text-sm text-green-800 dark:text-green-200">
                Video submitted successfully! Processing will begin shortly.
              </p>
            </div>
          )}

          <Button
            type="submit"
            className="w-full"
            disabled={submitMutation.isPending || !isValidYouTubeUrl(url)}
          >
            {submitMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              'Submit Video'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
