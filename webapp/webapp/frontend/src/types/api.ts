export interface ApiError {
  statusCode: number;
  message: string;
  error: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}
